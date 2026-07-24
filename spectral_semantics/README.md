# spectral_semantics

A working implementation of the buildable core of the "Spectral Persona
Modulation" / FGSGR concept (spectral decomposition and magnitude
modulation of embedding sequences, blind correlation-based detection, and
an honest, scoped-down decoding step), built to answer one question: **is
this idea actually feasible, and if so, how well does it work in practice?**

Read **[FEASIBILITY.md](FEASIBILITY.md)** first — it has the verdict, the
measured numbers, and what specifically is real vs. unsubstantiated in the
source material.

## Setup

```bash
pip install -r requirements.txt
python3 -c "import nltk; [nltk.download(p) for p in ['wordnet','omw-1.4','punkt','punkt_tab','brown','gutenberg','averaged_perceptron_tagger_eng']]"
```

No internet access is needed beyond that one-time nltk download and the
pip install — there is deliberately no dependency on a large pretrained
embedding model or LLM (see FEASIBILITY.md for why).

## Run the tests

```bash
PYTHONPATH=. pytest tests/ -v
```

## Run the feasibility experiments

```bash
PYTHONPATH=. python3 experiments/run_feasibility_eval.py       # single sentences
PYTHONPATH=. python3 experiments/run_paragraph_experiment.py   # paragraph-length text
```

Writes `experiments/results/*.json`. First run also trains and caches a
small local Word2Vec model (~5s) into `.cache/`.

## Layout

- `spectral_semantics/spectral.py` — DFT/IDFT decomposition, bandpass
  filter, magnitude modulation. The real, load-bearing, well-defined math.
- `spectral_semantics/masks.py` — watermark (PRNG-keyed) and persona
  (empathetic/urgent) frequency masks.
- `spectral_semantics/embeddings.py` — local Word2Vec backend (`Phi`).
- `spectral_semantics/ngram_lm.py` — trigram fluency model.
- `spectral_semantics/rewrite.py` — the "decoding" step: WordNet-synonym
  beam search that tries to realize a spectral target in actual text, plus
  an opt-in LM-proposed-candidate mode (`use_lm_candidates=True`) that
  tests whether WordNet's narrowness was the real bottleneck.
- `spectral_semantics/detector.py` — blind correlation detector, plus a
  permutation-test-based significance calibration the source paper lacks.
- `spectral_semantics/evaluation.py` — shared per-corpus evaluation logic
  used by both experiment scripts, so sentence- and paragraph-scale runs
  measure the exact same thing.
- `experiments/run_feasibility_eval.py` / `run_paragraph_experiment.py` —
  end-to-end measurement at two text-length scales.
- `tests/` — unit tests, including several that document real bugs/
  limitations found while building this (Hermitian symmetry, false-positive
  rate, trigram-smoothing blindness to unseen-but-fluent phrasing).
