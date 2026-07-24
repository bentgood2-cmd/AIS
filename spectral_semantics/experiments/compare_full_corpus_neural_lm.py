"""
Does training the neural LM on the full local corpus (~145k sentences,
3.1M tokens -- Brown + all of Gutenberg) instead of the 30k-sentence
subset close the gap found in compare_decoders.py?

The earlier neural LM never actually saw any Gutenberg text: Brown alone
(57,340 sentences) exceeds training_sentences()'s default 30,000-sentence
cap, so the cap was reached before Gutenberg was ever appended. This
reruns the exact same measurement (urgent/empathetic persona roughness,
watermark TPR, semantic fidelity, fluency-delta "reward hacking" check)
with a neural LM trained on the full corpus instead, via the same shared
evaluate_corpus pipeline, so the two runs are directly comparable.

Usage: PYTHONPATH=. python3 experiments/compare_full_corpus_neural_lm.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spectral_semantics.corpus import eval_sentences
from spectral_semantics.embeddings import Embedder
from spectral_semantics.evaluation import evaluate_corpus
from spectral_semantics.masks import persona_mask
from spectral_semantics.ngram_lm import get_lm
from spectral_semantics.neural_lm import get_neural_lm, load_neural_lm
from spectral_semantics.rewrite import guided_rewrite
from spectral_semantics.spectral import bandpass_mask

WATERMARK_KEY = "spectral-semantics-demo-key-2026"
STRENGTH = 0.8
N_SENTENCES = 30
N_PERMUTATIONS = 300
FULL_LM_PATH = os.path.join(os.path.dirname(__file__), "..", ".cache", "neural_lm_full.pt")


def qualitative_example(embedder, lm, neural_lm_30k, neural_lm_full):
    tokens = "the old man walked slowly across the quiet garden".split()
    L = len(tokens)
    band = bandpass_mask(L, 2, L // 2 - 1)
    mask = persona_mask("urgent", L)

    print("=== Qualitative example (urgent persona) ===")
    print("ORIGINAL:", " ".join(tokens))
    for name, nlm in [("neural_30k_sentences", neural_lm_30k), ("neural_145k_sentences", neural_lm_full)]:
        result = guided_rewrite(
            tokens, embedder, lm, mask, band, strength=STRENGTH, beam_size=8,
            use_neural_candidates=True, neural_lm=nlm, fluency_scorer=nlm,
        )
        print(f"{name:<24} dist={result.band_distance:8.2f}  -> {' '.join(result.tokens)}")
    print()


def main():
    embedder = Embedder()
    lm = get_lm()
    neural_lm_30k = get_neural_lm()
    print(f"Loading full-corpus neural LM from {FULL_LM_PATH} ...")
    neural_lm_full = load_neural_lm(FULL_LM_PATH)

    qualitative_example(embedder, lm, neural_lm_30k, neural_lm_full)

    sentences = eval_sentences(n=N_SENTENCES)
    print(f"Loaded {len(sentences)} evaluation sentences.\n")

    print("--- running config: neural_145k_sentences ---")
    summary, watermark_rows, persona_rows = evaluate_corpus(
        sentences, embedder, lm, WATERMARK_KEY, strength=STRENGTH,
        n_permutations=N_PERMUTATIONS,
        decoder_kwargs=dict(use_neural_candidates=True, neural_lm=neural_lm_full, fluency_scorer=neural_lm_full),
    )
    print(json.dumps(summary, indent=2))

    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "decoder_compare_neural_full_corpus.json"), "w") as f:
        json.dump(dict(summary=summary, watermark_rows=watermark_rows, persona_rows=persona_rows), f, indent=2)

    # Side-by-side against the 30k-sentence run, if available.
    prior_path = os.path.join(out_dir, "decoder_compare_wordnet_plus_neural_candidates_and_fluency.json")
    if os.path.exists(prior_path):
        prior = json.load(open(prior_path))["summary"]
        print("\n--- 30k-sentence neural LM vs 145k-sentence neural LM ---")
        print(f"{'metric':<50}{'30k':>12}{'145k':>12}")
        for section in ["watermark", "persona"]:
            for k in summary[section]:
                a = prior[section].get(k)
                b = summary[section][k]
                print(f"{k:<50}{a:>12.3f}{b:>12.3f}")


if __name__ == "__main__":
    main()
