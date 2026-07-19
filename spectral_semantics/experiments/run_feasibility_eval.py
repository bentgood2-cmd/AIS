"""
End-to-end feasibility evaluation.

Runs the two capabilities the source papers claim (blind watermark
detection, and persona-driven stylistic modulation) on a real sample of
sentences, and reports actual measured numbers rather than assertions.
Output feeds directly into FEASIBILITY.md.

Usage: PYTHONPATH=. python3 experiments/run_feasibility_eval.py
"""
from __future__ import annotations

import json
import os
import random
import statistics as stats
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spectral_semantics.corpus import eval_sentences
from spectral_semantics.detector import permutation_pvalue
from spectral_semantics.embeddings import Embedder
from spectral_semantics.masks import persona_mask, prng_mask
from spectral_semantics.ngram_lm import get_lm
from spectral_semantics.rewrite import guided_rewrite, synonym_candidates, content_positions
from spectral_semantics.spectral import bandpass_mask, dft_decompose, idft_reconstruct, modulate_magnitude


WATERMARK_KEY = "spectral-semantics-demo-key-2026"
STRENGTH = 0.8
N_SENTENCES = 30
N_PERMUTATIONS = 300
SIG_LEVEL = 0.05


def roughness(E: np.ndarray) -> float:
    """Discrete-Laplacian 'curvature energy' of an embedding trajectory:
    sum_j sum_t (E[j,t+1] - 2E[j,t] + E[j,t-1])^2, averaged over dims.
    Higher = spikier/rougher trajectory, lower = smoother. Used to check
    whether the 'empathetic = smooth, urgent = spiky' claim actually shows
    up in the embedding geometry, independent of whether discrete lexical
    substitution can fully realize the idealized spectral target.
    """
    if E.shape[1] < 3:
        return 0.0
    d2 = E[:, 2:] - 2 * E[:, 1:-1] + E[:, :-2]
    return float(np.mean(np.sum(d2**2, axis=1)))


def adversarial_edit(tokens: list[str], embedder, rng: random.Random) -> list[str]:
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


def main():
    embedder = Embedder()
    lm = get_lm()
    rng = random.Random(0)

    sentences = eval_sentences(n=N_SENTENCES)
    print(f"Loaded {len(sentences)} evaluation sentences from Gutenberg (austen-emma.txt).")

    watermark_rows = []
    persona_rows = []

    for tokens in sentences:
        L = len(tokens)
        if L < 6:
            continue
        band = bandpass_mask(L, max(2, L // 6), max(2, L // 2 - 1))

        # ---- Watermarking ----
        wm_mask = prng_mask(WATERMARK_KEY, L)
        wm_result = guided_rewrite(tokens, embedder, lm, wm_mask, band, strength=STRENGTH, beam_size=8)

        _, p_correct_on_watermarked = permutation_pvalue(
            embedder, wm_result.tokens, WATERMARK_KEY, band, n_permutations=N_PERMUTATIONS, seed=1
        )
        _, p_correct_on_original = permutation_pvalue(
            embedder, tokens, WATERMARK_KEY, band, n_permutations=N_PERMUTATIONS, seed=2
        )
        wrong_key = "not-the-real-key"
        _, p_wrong_on_watermarked = permutation_pvalue(
            embedder, wm_result.tokens, wrong_key, band, n_permutations=N_PERMUTATIONS, seed=3
        )
        edited = adversarial_edit(wm_result.tokens, embedder, rng)
        _, p_correct_on_edited = permutation_pvalue(
            embedder, edited, WATERMARK_KEY, band, n_permutations=N_PERMUTATIONS, seed=4
        )

        watermark_rows.append(dict(
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
        row = dict(original=" ".join(tokens), orig_roughness=orig_roughness)
        for kind in ["empathetic", "urgent"]:
            mask = persona_mask(kind, L)
            target_mag, target_phase = dft_decompose(orig_E)
            target_E = idft_reconstruct(
                modulate_magnitude(target_mag, mask, band, STRENGTH), target_phase
            )
            result = guided_rewrite(tokens, embedder, lm, mask, band, strength=STRENGTH, beam_size=8)
            realized_E = embedder.encode(result.tokens)
            row[f"{kind}_target_roughness"] = roughness(target_E)
            row[f"{kind}_realized_roughness"] = roughness(realized_E)
            row[f"{kind}_semantic_cosine"] = result.semantic_cosine_to_original
            row[f"{kind}_num_substitutions"] = result.num_substitutions
            row[f"{kind}_fluency_delta"] = result.fluency_per_token - result.baseline_fluency_per_token
            row[f"{kind}_text"] = " ".join(result.tokens)
        persona_rows.append(row)

    # ---- Aggregate watermarking numbers ----
    tpr = stats.mean(r["p_correct_key_on_watermarked"] < SIG_LEVEL for r in watermark_rows)
    fpr_unwatermarked = stats.mean(r["p_correct_key_on_original"] < SIG_LEVEL for r in watermark_rows)
    fpr_wrongkey = stats.mean(r["p_wrong_key_on_watermarked"] < SIG_LEVEL for r in watermark_rows)
    survival_after_edit = stats.mean(r["p_correct_key_on_edited"] < SIG_LEVEL for r in watermark_rows)
    mean_cosine = stats.mean(r["semantic_cosine"] for r in watermark_rows)
    mean_fluency_delta = stats.mean(r["fluency_delta"] for r in watermark_rows)
    mean_subs = stats.mean(r["num_substitutions"] for r in watermark_rows)

    # ---- Aggregate persona numbers ----
    emp_target_rough = stats.mean(r["empathetic_target_roughness"] for r in persona_rows)
    urg_target_rough = stats.mean(r["urgent_target_roughness"] for r in persona_rows)
    emp_realized_rough = stats.mean(r["empathetic_realized_roughness"] for r in persona_rows)
    urg_realized_rough = stats.mean(r["urgent_realized_roughness"] for r in persona_rows)
    orig_rough = stats.mean(r["orig_roughness"] for r in persona_rows)
    emp_cosine = stats.mean(r["empathetic_semantic_cosine"] for r in persona_rows)
    urg_cosine = stats.mean(r["urgent_semantic_cosine"] for r in persona_rows)

    summary = dict(
        n_sentences=len(watermark_rows),
        watermark=dict(
            true_positive_rate=tpr,
            false_positive_rate_unwatermarked_text=fpr_unwatermarked,
            false_positive_rate_wrong_key=fpr_wrongkey,
            detection_survival_after_1_word_edit=survival_after_edit,
            mean_semantic_cosine_to_original=mean_cosine,
            mean_fluency_delta_per_token=mean_fluency_delta,
            mean_substitutions_per_sentence=mean_subs,
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

    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(out_dir, "watermark_rows.json"), "w") as f:
        json.dump(watermark_rows, f, indent=2)
    with open(os.path.join(out_dir, "persona_rows.json"), "w") as f:
        json.dump(persona_rows, f, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"\nFull per-sentence data written to {out_dir}/")


if __name__ == "__main__":
    main()
