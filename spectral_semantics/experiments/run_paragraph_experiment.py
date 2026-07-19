"""
Same evaluation as run_feasibility_eval.py, but on paragraph-length text
(100-200 words) instead of single sentences (7-14 words).

Tests the hypothesis from FEASIBILITY.md: that the sentence-level failures
(watermark TPR ~= FPR, persona roughness differentiation vanishing) are a
statistical-power / substitution-budget problem -- too few independent
frequency bins, too few content words to substitute -- rather than a
deeper limitation of spectral modulation + lexical-substitution decoding.
More text directly gives more of both, at zero implementation cost.

Usage: PYTHONPATH=. python3 experiments/run_paragraph_experiment.py
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spectral_semantics.corpus import eval_paragraphs
from spectral_semantics.embeddings import Embedder
from spectral_semantics.evaluation import evaluate_corpus
from spectral_semantics.ngram_lm import get_lm

WATERMARK_KEY = "spectral-semantics-demo-key-2026"
STRENGTH = 0.8
N_PARAGRAPHS = 10
N_PERMUTATIONS = 300


def main():
    embedder = Embedder()
    lm = get_lm()

    paragraphs = eval_paragraphs(n=N_PARAGRAPHS, min_words=100, max_words=200)
    lengths = [len(p) for p in paragraphs]
    print(f"Loaded {len(paragraphs)} evaluation paragraphs from Gutenberg (austen-emma.txt), "
          f"lengths={lengths} words.")

    t0 = time.time()
    summary, watermark_rows, persona_rows = evaluate_corpus(
        paragraphs, embedder, lm, WATERMARK_KEY, strength=STRENGTH, n_permutations=N_PERMUTATIONS
    )
    print(f"Evaluation took {time.time() - t0:.1f}s")

    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "paragraph_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(out_dir, "paragraph_watermark_rows.json"), "w") as f:
        json.dump(watermark_rows, f, indent=2)
    with open(os.path.join(out_dir, "paragraph_persona_rows.json"), "w") as f:
        json.dump(persona_rows, f, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"\nFull per-paragraph data written to {out_dir}/")

    # Side-by-side comparison against the sentence-level baseline, if present.
    sentence_summary_path = os.path.join(out_dir, "summary.json")
    if os.path.exists(sentence_summary_path):
        with open(sentence_summary_path) as f:
            sentence_summary = json.load(f)
        print("\n--- sentence-level (baseline) vs paragraph-level ---")
        print(f"{'metric':<45} {'sentence':>10} {'paragraph':>10}")
        for key in summary["watermark"]:
            s = sentence_summary["watermark"].get(key)
            p = summary["watermark"][key]
            print(f"{key:<45} {s:>10.3f} {p:>10.3f}")
        for key in summary["persona"]:
            s = sentence_summary["persona"].get(key)
            p = summary["persona"][key]
            print(f"{key:<45} {s:>10.3f} {p:>10.3f}")


if __name__ == "__main__":
    main()
