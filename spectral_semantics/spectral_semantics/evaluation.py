"""
Shared evaluation logic for the feasibility experiments (used by both
experiments/run_feasibility_eval.py at sentence scale and
experiments/run_paragraph_experiment.py at paragraph scale, so the two are
measuring the exact same thing on different-sized text units).
"""
from __future__ import annotations

import random
import statistics as stats

import numpy as np

from .detector import permutation_pvalue
from .embeddings import Embedder
from .masks import persona_mask, prng_mask
from .ngram_lm import TrigramLM
from .rewrite import content_positions, guided_rewrite, synonym_candidates
from .spectral import bandpass_mask, dft_decompose, idft_reconstruct, modulate_magnitude

WRONG_KEY = "not-the-real-key"


def roughness(E: np.ndarray) -> float:
    """Discrete-Laplacian 'curvature energy' of an embedding trajectory:
    sum_j sum_t (E[j,t+1] - 2E[j,t] + E[j,t-1])^2, averaged over dims.
    Higher = spikier/rougher trajectory, lower = smoother.
    """
    if E.shape[1] < 3:
        return 0.0
    d2 = E[:, 2:] - 2 * E[:, 1:-1] + E[:, :-2]
    return float(np.mean(np.sum(d2**2, axis=1)))


def adversarial_edit(tokens: list[str], embedder: Embedder, rng: random.Random) -> list[str]:
    """Simulate light post-hoc editing: replace one random content word with
    a random WordNet synonym unrelated to any mask, to test whether
    detection survives a small perturbation.
    """
    positions = content_positions(tokens)
    if not positions:
        return list(tokens)
    p = rng.choice(positions)
    cands = synonym_candidates(tokens, p, embedder)
    if len(cands) <= 1:
        return list(tokens)
    new_tokens = list(tokens)
    new_tokens[p] = rng.choice(cands[1:])
    return new_tokens


def evaluate_corpus(
    text_units: list[list[str]],
    embedder: Embedder,
    lm: TrigramLM,
    watermark_key: str,
    strength: float = 0.8,
    n_permutations: int = 300,
    sig_level: float = 0.05,
    beam_size: int = 8,
    seed: int = 0,
    decoder_kwargs: dict | None = None,
) -> tuple[dict, list[dict], list[dict]]:
    """decoder_kwargs is forwarded to every guided_rewrite() call (e.g.
    {"use_neural_candidates": True, "neural_lm": nlm, "fluency_scorer": nlm})
    so different decoder configurations can be run through the exact same
    measurement pipeline for a like-for-like comparison.
    """
    decoder_kwargs = decoder_kwargs or {}
    rng = random.Random(seed)
    watermark_rows: list[dict] = []
    persona_rows: list[dict] = []

    for tokens in text_units:
        L = len(tokens)
        if L < 6:
            continue
        band = bandpass_mask(L, max(2, L // 6), max(2, L // 2 - 1))

        # ---- Watermarking ----
        wm_mask = prng_mask(watermark_key, L)
        wm_result = guided_rewrite(tokens, embedder, lm, wm_mask, band, strength=strength, beam_size=beam_size, **decoder_kwargs)

        _, p_correct_on_watermarked = permutation_pvalue(
            embedder, wm_result.tokens, watermark_key, band, n_permutations=n_permutations, seed=1
        )
        _, p_correct_on_original = permutation_pvalue(
            embedder, tokens, watermark_key, band, n_permutations=n_permutations, seed=2
        )
        _, p_wrong_on_watermarked = permutation_pvalue(
            embedder, wm_result.tokens, WRONG_KEY, band, n_permutations=n_permutations, seed=3
        )
        edited = adversarial_edit(wm_result.tokens, embedder, rng)
        _, p_correct_on_edited = permutation_pvalue(
            embedder, edited, watermark_key, band, n_permutations=n_permutations, seed=4
        )

        watermark_rows.append(dict(
            length_tokens=L,
            original=" ".join(tokens),
            watermarked=" ".join(wm_result.tokens),
            num_substitutions=wm_result.num_substitutions,
            semantic_cosine=wm_result.semantic_cosine_to_original,
            fluency_delta=wm_result.fluency_per_token - wm_result.baseline_fluency_per_token,
            p_correct_key_on_watermarked=p_correct_on_watermarked,
            p_correct_key_on_original=p_correct_on_original,
            p_wrong_key_on_watermarked=p_wrong_on_watermarked,
            p_correct_key_on_edited=p_correct_on_edited,
        ))

        # ---- Persona modulation ----
        orig_E = embedder.encode(tokens)
        orig_roughness = roughness(orig_E)
        row = dict(length_tokens=L, original=" ".join(tokens), orig_roughness=orig_roughness)
        for kind in ["empathetic", "urgent"]:
            mask = persona_mask(kind, L)
            target_mag, target_phase = dft_decompose(orig_E)
            target_E = idft_reconstruct(
                modulate_magnitude(target_mag, mask, band, strength), target_phase
            )
            result = guided_rewrite(tokens, embedder, lm, mask, band, strength=strength, beam_size=beam_size, **decoder_kwargs)
            realized_E = embedder.encode(result.tokens)
            row[f"{kind}_target_roughness"] = roughness(target_E)
            row[f"{kind}_realized_roughness"] = roughness(realized_E)
            row[f"{kind}_semantic_cosine"] = result.semantic_cosine_to_original
            row[f"{kind}_num_substitutions"] = result.num_substitutions
            row[f"{kind}_fluency_delta"] = result.fluency_per_token - result.baseline_fluency_per_token
            row[f"{kind}_text"] = " ".join(result.tokens)
        persona_rows.append(row)

    tpr = stats.mean(r["p_correct_key_on_watermarked"] < sig_level for r in watermark_rows)
    fpr_unwatermarked = stats.mean(r["p_correct_key_on_original"] < sig_level for r in watermark_rows)
    fpr_wrongkey = stats.mean(r["p_wrong_key_on_watermarked"] < sig_level for r in watermark_rows)
    survival_after_edit = stats.mean(r["p_correct_key_on_edited"] < sig_level for r in watermark_rows)
    mean_cosine = stats.mean(r["semantic_cosine"] for r in watermark_rows)
    mean_fluency_delta = stats.mean(r["fluency_delta"] for r in watermark_rows)
    mean_subs = stats.mean(r["num_substitutions"] for r in watermark_rows)
    mean_length = stats.mean(r["length_tokens"] for r in watermark_rows)

    emp_target_rough = stats.mean(r["empathetic_target_roughness"] for r in persona_rows)
    urg_target_rough = stats.mean(r["urgent_target_roughness"] for r in persona_rows)
    emp_realized_rough = stats.mean(r["empathetic_realized_roughness"] for r in persona_rows)
    urg_realized_rough = stats.mean(r["urgent_realized_roughness"] for r in persona_rows)
    orig_rough = stats.mean(r["orig_roughness"] for r in persona_rows)
    emp_cosine = stats.mean(r["empathetic_semantic_cosine"] for r in persona_rows)
    urg_cosine = stats.mean(r["urgent_semantic_cosine"] for r in persona_rows)

    summary = dict(
        n_text_units=len(watermark_rows),
        mean_length_tokens=mean_length,
        watermark=dict(
            true_positive_rate=tpr,
            false_positive_rate_unwatermarked_text=fpr_unwatermarked,
            false_positive_rate_wrong_key=fpr_wrongkey,
            detection_survival_after_1_word_edit=survival_after_edit,
            mean_semantic_cosine_to_original=mean_cosine,
            mean_fluency_delta_per_token=mean_fluency_delta,
            mean_substitutions_per_text_unit=mean_subs,
        ),
        persona=dict(
            original_trajectory_roughness=orig_rough,
            empathetic_target_roughness=emp_target_rough,
            urgent_target_roughness=urg_target_rough,
            empathetic_realized_roughness_after_discretization=emp_realized_rough,
            urgent_realized_roughness_after_discretization=urg_realized_rough,
            empathetic_semantic_cosine_to_original=emp_cosine,
            urgent_semantic_cosine_to_original=urg_cosine,
        ),
    )
    return summary, watermark_rows, persona_rows
