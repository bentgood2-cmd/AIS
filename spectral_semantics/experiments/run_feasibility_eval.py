"""
End-to-end feasibility evaluation at single-sentence scale.

Runs the two capabilities the source papers claim (blind watermark
detection, and persona-driven stylistic modulation) on a real sample of
sentences, and reports actual measured numbers rather than assertions.
Output feeds directly into FEASIBILITY.md.

Usage: PYTHONPATH=. python3 experiments/run_feasibility_eval.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spectral_semantics.corpus import eval_sentences
from spectral_semantics.embeddings import Embedder
from spectral_semantics.evaluation import evaluate_corpus
from spectral_semantics.ngram_lm import get_lm

WATERMARK_KEY = "spectral-semantics-demo-key-2026"
STRENGTH = 0.8
N_SENTENCES = 30
N_PERMUTATIONS = 300


def main():
    embedder = Embedder()
    lm = get_lm()

    sentences = eval_sentences(n=N_SENTENCES)
    print(f"Loaded {len(sentences)} evaluation sentences from Gutenberg (austen-emma.txt).")

    summary, watermark_rows, persona_rows = evaluate_corpus(
        sentences, embedder, lm, WATERMARK_KEY, strength=STRENGTH, n_permutations=N_PERMUTATIONS
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
