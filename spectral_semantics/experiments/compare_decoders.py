"""
Three-way decoder comparison: WordNet-only vs. WordNet+trigram-proposed
candidates vs. WordNet+neural-proposed candidates (with the neural LM also
used as the fluency judge in the latter case).

Directly tests the hypothesis from FEASIBILITY.md's "is WordNet the
bottleneck?" section: that a trigram model can propose candidates beyond
WordNet synonyms (closing real distance to the spectral target) but can't
judge whether the result stays coherent, because it can only recognize
fluency it has memorized verbatim. A neural LM should generalize past that.

Usage: PYTHONPATH=. python3 experiments/compare_decoders.py
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
from spectral_semantics.neural_lm import get_neural_lm
from spectral_semantics.rewrite import guided_rewrite
from spectral_semantics.spectral import bandpass_mask

WATERMARK_KEY = "spectral-semantics-demo-key-2026"
STRENGTH = 0.8
N_SENTENCES = 30
N_PERMUTATIONS = 300

CONFIGS = {
    "wordnet_only": dict(),
    "wordnet_plus_trigram_candidates": dict(use_lm_candidates=True),
    "wordnet_plus_neural_candidates_and_fluency": dict(use_neural_candidates=True),  # neural_lm/fluency_scorer filled in below
}


def qualitative_example(embedder, lm, neural_lm):
    tokens = "the old man walked slowly across the quiet garden".split()
    L = len(tokens)
    band = bandpass_mask(L, 2, L // 2 - 1)
    mask = persona_mask("urgent", L)

    print("=== Qualitative example (urgent persona) ===")
    print("ORIGINAL:", " ".join(tokens))
    for name, kwargs in CONFIGS.items():
        kwargs = dict(kwargs)
        if "neural" in name:
            kwargs["neural_lm"] = neural_lm
            kwargs["fluency_scorer"] = neural_lm
        result = guided_rewrite(tokens, embedder, lm, mask, band, strength=STRENGTH, beam_size=8, **kwargs)
        print(f"{name:<42} dist={result.band_distance:8.2f}  -> {' '.join(result.tokens)}")
    print()


def main():
    embedder = Embedder()
    lm = get_lm()
    print("Loading/training neural LM (this reuses the cached model if already trained)...")
    neural_lm = get_neural_lm()

    qualitative_example(embedder, lm, neural_lm)

    sentences = eval_sentences(n=N_SENTENCES)
    print(f"Loaded {len(sentences)} evaluation sentences.\n")

    all_summaries = {}
    for name, kwargs in CONFIGS.items():
        kwargs = dict(kwargs)
        if "neural" in name:
            kwargs["neural_lm"] = neural_lm
            kwargs["fluency_scorer"] = neural_lm
        print(f"--- running config: {name} ---")
        summary, watermark_rows, persona_rows = evaluate_corpus(
            sentences, embedder, lm, WATERMARK_KEY, strength=STRENGTH,
            n_permutations=N_PERMUTATIONS, decoder_kwargs=kwargs,
        )
        all_summaries[name] = summary
        out_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, f"decoder_compare_{name}.json"), "w") as f:
            json.dump(dict(summary=summary, watermark_rows=watermark_rows, persona_rows=persona_rows), f, indent=2)
        print(json.dumps(summary, indent=2))
        print()

    print("=== Side-by-side ===")
    metrics = list(all_summaries["wordnet_only"]["watermark"].keys()) + list(all_summaries["wordnet_only"]["persona"].keys())
    header = f"{'metric':<50}" + "".join(f"{name[:16]:>18}" for name in CONFIGS)
    print(header)
    for m in metrics:
        row = f"{m:<50}"
        for name in CONFIGS:
            s = all_summaries[name]
            v = s["watermark"].get(m, s["persona"].get(m))
            row += f"{v:>18.3f}"
        print(row)

    with open(os.path.join(os.path.dirname(__file__), "results", "decoder_compare_summary.json"), "w") as f:
        json.dump(all_summaries, f, indent=2)


if __name__ == "__main__":
    main()
