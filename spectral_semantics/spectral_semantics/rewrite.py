"""
Guided lexical-substitution rewriting: the "decoding" step.

The source papers assert that a generative agent can solve

    T* = argmin_T || Psi(T) - E_target ||_2^2

over "the discrete vocabulary space" via "Active Inference" / "Continuous-
Relaxation Beam Search", without ever defining Psi (the embedding of a
*candidate discrete sequence*) or how candidates are proposed in the first
place. That's the load-bearing gap in the whole framework: you cannot
gradient-descend into token space, and nothing in the papers explains what
generates candidate T's for the argmin to range over.

This module fills that gap with the smallest honest thing that actually
works: WordNet-synonym substitution at content-word positions, searched
with a real (bounded, tractable) beam search that minimizes distance to the
spectral target's *band-restricted* magnitude spectrum while penalizing
fluency loss under a local trigram LM. It is a concrete instance of "select
synonymous vocabulary to satisfy the mask" -- scoped down from free-form
generation to lexical substitution, which is the part that's actually
well-defined and computationally tractable.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import nltk
import numpy as np
from nltk.corpus import wordnet as wn

from .embeddings import Embedder
from .ngram_lm import TrigramLM
from .spectral import dft_decompose, idft_reconstruct, modulate_magnitude


_PENN_TO_WN = {"N": wn.NOUN, "V": wn.VERB, "J": wn.ADJ, "R": wn.ADV}
_CONTENT_TAGS = ("NN", "VB", "JJ", "RB")


def _wn_pos(tag: str) -> str | None:
    return _PENN_TO_WN.get(tag[0]) if tag[:2] in _CONTENT_TAGS else None


def content_positions(tokens: list[str]) -> list[int]:
    tagged = nltk.pos_tag(tokens)
    return [i for i, (_, tag) in enumerate(tagged) if tag[:2] in _CONTENT_TAGS]


def synonym_candidates(tokens: list[str], position: int, embedder: Embedder, max_candidates: int = 6) -> list[str]:
    """Candidate substitutions for tokens[position], always including the
    original word first (so guided_rewrite's search can never be forced
    away from a no-op at this position), followed by WordNet synonyms
    ranked by embedding-cosine similarity to the original word.

    Ranking (rather than relying on set/dict iteration order, which is
    hash-randomized per process in Python) makes the candidate selection
    deterministic and reproducible across runs -- an earlier version of
    this function used raw set order, which could silently drop the
    original word once more than max_candidates synonyms were found,
    breaking the beam search's ability to fall back to "no substitution"
    (see tests/test_rewrite.py::test_synonym_candidates_deterministic).
    """
    word = tokens[position]
    tag = nltk.pos_tag(tokens)[position][1]
    pos = _wn_pos(tag)
    if pos is None:
        return [word]
    found: set[str] = set()
    for syn in wn.synsets(word, pos=pos):
        for lemma in syn.lemma_names():
            lemma = lemma.lower().replace("_", " ")
            if " " in lemma or lemma == word:
                continue
            if embedder.in_vocab(lemma):
                found.add(lemma)
    if not found:
        return [word]
    orig_vec = embedder.word_vector(word)
    orig_norm = np.linalg.norm(orig_vec) + 1e-12

    def cosine_to_original(w: str) -> float:
        v = embedder.word_vector(w)
        return float(np.dot(orig_vec, v) / (orig_norm * (np.linalg.norm(v) + 1e-12)))

    ranked = sorted(found, key=lambda w: (-cosine_to_original(w), w))
    return [word] + ranked[: max_candidates - 1]


@dataclass
class RewriteResult:
    tokens: list[str]
    band_distance: float
    fluency_per_token: float
    baseline_fluency_per_token: float
    semantic_cosine_to_original: float
    num_substitutions: int
    beam_trace: list[float] = field(default_factory=list)


def _band_magnitude(embedder: Embedder, tokens: list[str], band: np.ndarray) -> np.ndarray:
    E = embedder.encode(tokens)
    mag, _ = dft_decompose(E)
    return mag[:, band.astype(bool)]


def spectral_target(embedder: Embedder, tokens: list[str], mask_signal: np.ndarray, band: np.ndarray, strength: float) -> np.ndarray:
    E = embedder.encode(tokens)
    mag, phase = dft_decompose(E)
    mag_mod = modulate_magnitude(mag, mask_signal, band, strength)
    return idft_reconstruct(mag_mod, phase)


def guided_rewrite(
    tokens: list[str],
    embedder: Embedder,
    lm: TrigramLM,
    mask_signal: np.ndarray,
    band: np.ndarray,
    strength: float,
    beam_size: int = 6,
    fluency_weight: float = 2.0,
) -> RewriteResult:
    target_E = spectral_target(embedder, tokens, mask_signal, band, strength)
    target_mag, _ = dft_decompose(target_E)
    target_band_mag = target_mag[:, band.astype(bool)]

    baseline_fluency = lm.sentence_logprob_per_token(tokens)

    positions = content_positions(tokens)
    candidate_lists = {p: synonym_candidates(tokens, p, embedder) for p in positions}

    def score(cand_tokens: list[str]) -> float:
        dist = float(np.sum((_band_magnitude(embedder, cand_tokens, band) - target_band_mag) ** 2))
        fluency = lm.sentence_logprob_per_token(cand_tokens)
        fluency_penalty = fluency_weight * max(0.0, baseline_fluency - fluency)
        return dist + fluency_penalty

    beam: list[tuple[list[str], float]] = [(list(tokens), score(tokens))]
    trace = [beam[0][1]]
    for p in positions:
        expanded = []
        for cand_tokens, _ in beam:
            for word in candidate_lists[p]:
                new_tokens = list(cand_tokens)
                new_tokens[p] = word
                expanded.append((new_tokens, score(new_tokens)))
        expanded.sort(key=lambda x: x[1])
        beam = expanded[:beam_size]
        trace.append(beam[0][1])

    best_tokens, best_score = beam[0]

    orig_E = embedder.encode(tokens).mean(axis=1)
    new_E = embedder.encode(best_tokens).mean(axis=1)
    cosine = float(
        np.dot(orig_E, new_E) / (np.linalg.norm(orig_E) * np.linalg.norm(new_E) + 1e-12)
    )
    final_dist = float(np.sum((_band_magnitude(embedder, best_tokens, band) - target_band_mag) ** 2))
    num_subs = sum(1 for a, b in zip(tokens, best_tokens) if a != b)

    return RewriteResult(
        tokens=best_tokens,
        band_distance=final_dist,
        fluency_per_token=lm.sentence_logprob_per_token(best_tokens),
        baseline_fluency_per_token=baseline_fluency,
        semantic_cosine_to_original=cosine,
        num_substitutions=num_subs,
        beam_trace=trace,
    )
