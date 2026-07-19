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

## Run the feasibility experiment

```bash
PYTHONPATH=. python3 experiments/run_feasibility_eval.py
```

Writes `experiments/results/{summary,watermark_rows,persona_rows}.json`.
First run also trains and caches a small local Word2Vec model (~5s) into
`.cache/`.

## Layout

- `spectral_semantics/spectral.py` — DFT/IDFT decomposition, bandpass
  filter, magnitude modulation. The real, load-bearing, well-defined math.
- `spectral_semantics/masks.py` — watermark (PRNG-keyed) and persona
  (empathetic/urgent) frequency masks.
- `spectral_semantics/embeddings.py` — local Word2Vec backend (`Phi`).
- `spectral_semantics/ngram_lm.py` — trigram fluency model.
- `spectral_semantics/rewrite.py` — the "decoding" step: WordNet-synonym
  beam search that tries to realize a spectral target in actual text.
- `spectral_semantics/detector.py` — blind correlation detector, plus a
  permutation-test-based significance calibration the source paper lacks.
- `experiments/run_feasibility_eval.py` — end-to-end measurement.
- `tests/` — unit tests, including two that document real bugs/limitations
  found while building this (Hermitian symmetry, false-positive rate).
