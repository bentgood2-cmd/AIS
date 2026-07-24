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

guided_rewrite(..., use_lm_candidates=True) additionally offers
lm_proposal_candidates: substitutions proposed by local n-gram fluency
across the whole vocabulary rather than WordNet-synonym proximity, to test
whether WordNet's narrow, embedding-space-local candidate sets were the
actual bottleneck found in the sentence/paragraph experiments (see
FEASIBILITY.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import nltk
import numpy as np
from nltk.corpus import wordnet as wn

from .embeddings import Embedder
from .ngram_lm import BOS, EOS, TrigramLM
from .spectral import dft_decompose, idft_reconstruct, modulate_magnitude


_PENN_TO_WN = {"N": wn.NOUN, "V": wn.VERB, "J": wn.ADJ, "R": wn.ADV}
_CONTENT_TAGS = ("NN", "VB", "JJ", "RB")


def _wn_pos(tag: str) -> str | None:
    return _PENN_TO_WN.get(tag[0]) if tag[:2] in _CONTENT_TAGS else None


def content_positions(tokens: list[str], tags: list[tuple[str, str]] | None = None) -> list[int]:
    tags = tags if tags is not None else nltk.pos_tag(tokens)
    return [i for i, (_, tag) in enumerate(tags) if tag[:2] in _CONTENT_TAGS]


def synonym_candidates(
    tokens: list[str],
    position: int,
    embedder: Embedder,
    max_candidates: int = 6,
    tags: list[tuple[str, str]] | None = None,
) -> list[str]:
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
    tags = tags if tags is not None else nltk.pos_tag(tokens)
    tag = tags[position][1]
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


def lm_proposal_candidates(
    tokens: list[str],
    position: int,
    lm: TrigramLM,
    embedder: Embedder,
    top_k: int = 12,
) -> list[str]:
    """Candidate substitutions proposed by the language model itself,
    scored by local two-sided trigram context fluency across the *entire*
    embedding vocabulary -- not restricted to WordNet synonyms.

    synonym_candidates only ever offers words that are already close to the
    original in embedding space (true synonyms cluster tightly by
    construction), which caps how far a single substitution can move the
    trajectory regardless of how much beam search or how many positions are
    available (see FEASIBILITY.md's paragraph-length experiment). This
    function instead asks "what word would still read fluently here",
    independent of embedding-space proximity to the original word, to test
    whether relaxing that constraint lets the decoder actually reach a
    spectral target that plain synonym substitution cannot.
    """
    L = len(tokens)
    left2 = tokens[position - 2] if position >= 2 else BOS
    left1 = tokens[position - 1] if position >= 1 else BOS
    right1 = tokens[position + 1] if position + 1 < L else EOS

    def context_score(w: str) -> float:
        return lm.trigram_logprob(left2, left1, w) + lm.trigram_logprob(left1, w, right1)

    vocab = embedder.model.wv.index_to_key
    ranked = sorted(vocab, key=lambda w: (-context_score(w), w))
    return ranked[:top_k]


def neural_candidates(
    tokens: list[str],
    position: int,
    neural_lm,  # neural_lm.NeuralLM -- not type-hinted to avoid a hard torch import here
    top_k: int = 12,
) -> list[str]:
    """Candidate substitutions proposed by a real neural LM's next-token
    distribution given the left context, instead of trigram counts. Unlike
    TrigramLM, an unseen-but-fluent continuation isn't automatically
    indistinguishable from a nonsensical one, because the model generalizes
    through learned embeddings rather than exact n-gram memorization (see
    neural_lm.py's docstring and FEASIBILITY.md for why that distinction
    turned out to matter).
    """
    return neural_lm.topk_next_words(tokens[:position], top_k=top_k)


def candidate_words(
    tokens: list[str],
    position: int,
    embedder: Embedder,
    lm: TrigramLM | None = None,
    neural_lm=None,
    tags: list[tuple[str, str]] | None = None,
    max_wordnet: int = 6,
    max_lm: int = 10,
    max_neural: int = 10,
) -> list[str]:
    """Union of WordNet synonyms, (if `lm` given) trigram-LM-proposed words,
    and (if `neural_lm` given) neural-LM-proposed words, original word
    always first. See synonym_candidates / lm_proposal_candidates /
    neural_candidates for what each source contributes.
    """
    word = tokens[position]
    wn_cands = synonym_candidates(tokens, position, embedder, max_candidates=max_wordnet, tags=tags)
    extra: list[str] = []
    if lm is not None:
        extra += lm_proposal_candidates(tokens, position, lm, embedder, top_k=max_lm)
    if neural_lm is not None:
        extra += [w for w in neural_candidates(tokens, position, neural_lm, top_k=max_neural) if embedder.in_vocab(w)]
    if not extra:
        return wn_cands
    seen = {word}
    merged = [word]
    for w in wn_cands[1:] + extra:
        if w not in seen:
            seen.add(w)
            merged.append(w)
    return merged


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
    use_lm_candidates: bool = False,
    max_lm_candidates: int = 10,
    neural_lm=None,
    use_neural_candidates: bool = False,
    max_neural_candidates: int = 10,
    fluency_scorer=None,
) -> RewriteResult:
    """
    lm: TrigramLM, used for the fluency penalty by default, and as a
        candidate proposer when use_lm_candidates=True.
    neural_lm: optional neural_lm.NeuralLM. When given with
        use_neural_candidates=True, it proposes candidates instead of (or
        alongside) the trigram proposer. It implements the same
        sentence_logprob_per_token interface as TrigramLM, so pass
        fluency_scorer=neural_lm to also use it (instead of `lm`) as the
        fluency judge in the search objective -- the two roles are
        independent, since FEASIBILITY.md found that a better *proposer*
        alone (trigram-based) wasn't enough; the *judge* needed to
        generalize too.
    """
    fluency_scorer = fluency_scorer if fluency_scorer is not None else lm
    target_E = spectral_target(embedder, tokens, mask_signal, band, strength)
    target_mag, _ = dft_decompose(target_E)
    target_band_mag = target_mag[:, band.astype(bool)]

    baseline_fluency = fluency_scorer.sentence_logprob_per_token(tokens)

    # Tag once and reuse: synonym_candidates used to re-run nltk.pos_tag on the
    # full token list for every position, which is quadratic in sequence
    # length. Fine for a 10-word sentence, not for a 150-word paragraph.
    tags = nltk.pos_tag(tokens)
    positions = content_positions(tokens, tags=tags)
    candidate_lists = {
        p: candidate_words(
            tokens, p, embedder,
            lm=lm if use_lm_candidates else None,
            neural_lm=neural_lm if use_neural_candidates else None,
            tags=tags,
            max_lm=max_lm_candidates,
            max_neural=max_neural_candidates,
        )
        for p in positions
    }

    def score(cand_tokens: list[str]) -> float:
        dist = float(np.sum((_band_magnitude(embedder, cand_tokens, band) - target_band_mag) ** 2))
        fluency = fluency_scorer.sentence_logprob_per_token(cand_tokens)
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
        fluency_per_token=fluency_scorer.sentence_logprob_per_token(best_tokens),
        baseline_fluency_per_token=baseline_fluency,
        semantic_cosine_to_original=cosine,
        num_substitutions=num_subs,
        beam_trace=trace,
    )
