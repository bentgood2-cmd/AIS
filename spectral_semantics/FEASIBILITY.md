# Feasibility assessment: "Spectral Persona Modulation" / FGSGR

## Verdict, up front

The **signal-processing framing is real and buildable**: treating an
embedding sequence as a discrete-time signal, decomposing it with a DFT,
and modulating its magnitude in a frequency band while preserving phase is
ordinary, correct math. I implemented it, tested it, and it works exactly
as specified — modulo one bug the source material never mentions (below).

The **"Active Inference" / decoding layer is not real**. It's the part of
the paper that does the actual work (turning a modulated continuous target
back into text that a human would read), and it is never actually
specified — no algorithm, no pseudocode, not even a sketch of how a
candidate discrete sequence's embedding (`Ψ(T)`) gets proposed in the first
place. I built the most literal, honest interpretation the papers'
own text supports ("the agent selects synonymous vocabulary") and measured
it. It does not work at realistic sentence lengths: watermark detection
collapses to chance level, and the stylistic effect the persona mask
produces in the idealized continuous math nearly disappears once forced
through actual word substitution. This isn't a tuning problem — it holds
across a 6x range of aggressiveness settings (see below).

"Active Inference", "Variational Free Energy", "eradicating autoregressive
myopia", "NP-hard", "edge deployment on NVIDIA Jetson Orin Nano", and
"FGSGR" are all asserted, not derived or demonstrated, anywhere in the
seven source documents. None of them show up as necessary once you
actually build the thing.

## What the source material actually is

All seven uploaded files trace back to the same short (~4-page) core
"paper," expanded through repeated prompts to what looks like an AI
chatbot — the filenames are the prompts themselves: `Expand.pdf`,
`Full_scientific_rigor.pdf`, `Present_the_finished_paper.pdf`. The two
large PDFs (`Spectral_Active_Inference.pdf`, `Spectral_Topography.pdf`)
looked alarming at first — the upload metadata claimed 164 and 195 pages —
but on direct inspection each is actually a 15-page NotebookLM-generated
infographic slide deck (15.9–19MB of images, near-zero embedded text).
They re-illustrate the same handful of equations from the text papers with
progressively fancier art; they contain no new algorithmic detail, no
pseudocode, no citations to prior work (not even to Friston's actual
Active Inference literature, or to real LLM watermarking papers like
Kirchenbauer et al.), and no experiments or evaluation numbers. There is
nothing in the full bundle beyond what's quoted and addressed below.

## What's real (and what I found wrong with it)

### The spectral decomposition itself

`E = Φ(T) ∈ R^{d×L}`, DFT along the sequence axis, split into magnitude
(style) and phase (facts), bandpass-modulate the magnitude, inverse DFT.
This is legitimate and I implemented it as `spectral.dft_decompose` /
`modulate_magnitude` / `idft_reconstruct`.

**Bug the source papers never address**: a real-valued signal has a
conjugate-symmetric spectrum. If the modulation mask `M(ω)` (or `P(ω)`) is
not itself symmetric under `ω → L−ω`, the inverse DFT is complex, and
naively taking `.real` (which any literal implementation of the paper's
equations would do) silently throws away information and corrupts the
result. `spectral.idft_reconstruct` raises instead of hiding this;
`masks.py` builds every mask to be symmetric so the round trip is exact.
See `tests/test_spectral.py::test_asymmetric_mask_breaks_realness_and_is_caught`
for a reproduction, and
`test_symmetric_mask_round_trip_stays_real_and_recoverable` for the fix
verified (low frequencies outside the band are provably untouched; the
band is provably where all the change happens).

### The "phase = facts, magnitude = style" assumption

Asserted in every one of the source documents, never derived, never
tested, never cited. It's a *plausible-sounding* borrowing from image/audio
processing (where phase does carry most of the perceptually relevant
structure) applied to an arbitrary learned embedding space without
justification. I did not find a way to validate or refute this claim
within scope — it would require its own study (e.g., ablating phase-only
vs. magnitude-only reconstruction against a factuality/style probe on real
sentence embeddings). Flagging it as **an assumption load-bearing enough
that the whole framework depends on it, and untested**.

### Blind correlation detection ("Zero-Knowledge Provenance Verification")

`Expand.pdf` proposes correlating a suspect text's extracted magnitude
spectrum against a PRNG-keyed mask, and treating `ρ ≫ 0` as proof of
watermark presence. I implemented this (`detector.correlation_score`) —
and also implemented a permutation-test-based p-value
(`detector.permutation_pvalue`) that the source paper doesn't have.

**Finding**: the naive version is unreliable. Because masks must be
Hermitian-symmetric (see above), a band of width *B* only contains ~*B*/2
independent random values. For realistic single-sentence band widths
(~9 bins), Pearson correlation against unrelated random keys has high
enough sampling variance that a fixed `ρ > 0.5` threshold fires on
**~20% of completely unwatermarked text**, not "rarely" as the source
paper's language implies — see
`tests/test_detector.py::test_naive_threshold_has_high_false_positive_rate`.
The permutation-test fix (`permutation_pvalue`) controls this properly (I
verified: false positive rate at nominal `p<0.05` stays near 5% —
`test_permutation_pvalue_controls_false_positive_rate`) and is what the
end-to-end experiment below actually uses.

## What's not real, or not shown

- **"Active Inference" / "Variational Free Energy minimization"**: no
  generative model `P(Ẽ, T)` is ever defined, no entropy term `H[Q(T)]` is
  ever computed, no prior/posterior structure exists anywhere in the math.
  What's actually described — "traverse the discrete vocabulary space to
  minimize `‖Ψ(T) − Ẽ‖²`" — is nearest-neighbor search / guided beam
  search. Calling it Active Inference borrows the name of a specific,
  well-defined neuroscience framework (Friston et al.) without any of its
  actual content.
- **`Ψ(T)`, the embedding of a candidate discrete trajectory, is never
  defined.** This is the actual crux of the whole framework — how do you
  even generate candidate `T`'s to search over? — and it is not addressed
  anywhere in the seven documents, including the two that are explicitly
  framed as "expand further" and "full scientific rigor."
- **"NP-hard"** is asserted about the `argmin_T` search with no proof.
  Informally plausible (combinatorial argmax over sequences), not
  rigorously established as stated.
- **Edge deployment on NVIDIA Jetson Orin Nano, real-time inference
  claims**: no benchmark, no latency number, no memory figure anywhere.
- **"Continuous-Relaxation Beam Search" and "FGSGR" (Frequency-Governed
  Self-Graph Reasoning)**: these read as plausible ML terminology but do
  not correspond to any citable, established method. They appear to be
  invented names for the (undefined) decoding procedure.

## What I built to actually test this

Rather than either dismiss the whole thing or credulously reimplement the
buzzwords, I extracted the part that's mathematically well-defined and
built the smallest honest thing that fills the undefined "decoding" gap:
WordNet-synonym substitution at content-word positions, searched with beam
search that minimizes band-restricted embedding distance to the spectral
target while penalizing fluency loss under a local trigram LM. This is a
literal, concrete instance of the papers' own language ("the agent...
selects synonymous vocabulary... to satisfy the mask") — scoped down from
open-ended generation (which the papers also never specify how to do) to
the one sub-problem that's actually tractable to search exactly.

Everything runs fully offline: a local Word2Vec model trained in ~5s on
nltk's bundled Brown + Gutenberg corpora (an attempt to fetch a larger
pretrained GloVe model via `gensim.downloader` was blocked by this
environment's network policy — HTTP 403 — so the embedding backend is
honestly small; the spectral math is agnostic to embedding source and
would work identically with a bigger model), and a Laplace-smoothed
trigram LM trained on the same corpus for fluency scoring.

## Measured results (30 real sentences, Jane Austen's *Emma*, via nltk Gutenberg corpus)

Full numbers: `experiments/results/summary.json`, per-sentence detail in
`watermark_rows.json` / `persona_rows.json`. Reproduce with
`PYTHONPATH=. python3 experiments/run_feasibility_eval.py`.

### Watermarking

| metric | value |
|---|---|
| True positive rate (correct key, watermarked text) | **3.3%** |
| False positive rate (correct key, *un*watermarked text) | 3.3% |
| False positive rate (wrong key, watermarked text) | 10% |
| Detection survival after 1-word adversarial edit | 3.3% |
| Mean semantic cosine similarity to original | 0.9985 |
| Mean fluency delta (nats/token) | −0.018 (negligible) |
| Mean substitutions per sentence | 1.2 |

The true positive rate is statistically indistinguishable from the false
positive rate. **The watermark is not detectable in practice.** I checked
whether this was just weak search settings: sweeping strength from 0.8 to
5.0 and disabling the fluency penalty entirely (beam=20) moved TPR from
3.3% to at best 10% — still near the 5% chance level.
(`experiments/results/watermark_rows.json` has the qualitative reason why:
mean substitutions per sentence stays around 2 *even with zero fluency
penalty*, because WordNet synonym sets are small and embedding-space-local
— synonyms sit close to the original word by construction, so no amount of
search aggressiveness can move the aggregate trajectory far. This is a
structural bandwidth limit of lexical substitution as a "decoder," not a
hyperparameter problem.)

Example (from `watermark_rows.json`):
```
ORIG: she dearly loved her father but he was no companion for her
WM  : she dearly bang her founder but he was no familiar for her   (p=0.033, detected)
```
```
ORIG: between it was more the intimacy of sisters
WM  : between it was more the liaison of sister                    (p=1.000, NOT detected)
```

### Persona modulation

| metric | original | empathetic | urgent |
|---|---|---|---|
| Trajectory roughness — **idealized continuous target** | 25.70 | 21.65 (smoother ✓) | 36.45 (rougher ✓) |
| Trajectory roughness — **after real word substitution** | 25.70 | 25.53 | 25.67 |
| Semantic cosine to original | — | 0.9987 | 0.9971 |

"Roughness" is the discrete-Laplacian curvature energy of the embedding
trajectory — a direct, quantitative test of the paper's own claim that an
"empathetic" mask produces smooth transitions and an "urgent" mask
produces spiky ones.

**This is the clearest result in the whole investigation.** At the
idealized continuous level — before any discretization — the spectral math
does exactly what's claimed: the empathetic mask measurably smooths the
trajectory, the urgent mask measurably roughens it. The mechanism is real.
But once you force that target through actual word substitution (the only
concrete "decoding" procedure the source papers' language supports), the
differentiation nearly vanishes: 25.53 vs. 25.67 realized, against 25.70
original — both personas end up statistically indistinguishable from doing
nothing, despite their idealized targets being ±25% apart. The generation
step is where the whole idea breaks down in practice, exactly mirroring
the watermarking result.

### A limitation I didn't fix, and want to be upfront about

Looking at the qualitative outputs, some WordNet substitutions pick the
wrong *sense* of a polysemous word — e.g. "loss" (grief) → "entropy loss"
(information theory), "father" → "founder", "friend" → "champion" /
"quaker", and inflected forms breaking grammar ("felt" → "find", losing
past tense: *"would be find every hour"*). This is word-sense
disambiguation, a real and separately hard NLP problem that the source
papers wave away with "the agent organically selects synonymous
vocabulary" as if it were free. My trigram LM's fluency penalty catches
some of this but not all of it. I'm not fixing this here — it would take
real WSD (e.g. Lesk-style context disambiguation) or a proper generative
LM, either of which is a substantial project in its own right — but it's
worth naming as a second, independent reason the "decoding" step is
harder than the source material implies.

## Follow-up experiment: does more text length fix it?

The natural next question is whether the sentence-level failure is a
*statistical-power* problem (too few independent frequency bins, too few
substitutable words) that simply goes away with longer text, or a deeper
limitation of lexical-substitution decoding. I reran the identical
pipeline (`experiments/run_paragraph_experiment.py`, same code path via
the shared `evaluation.evaluate_corpus`) on 10 paragraphs (100-200 words,
mean 120 tokens vs. 10 for sentences) instead of single sentences:

| metric | sentence (mean 10 tok) | paragraph (mean 120 tok) |
|---|---|---|
| Watermark true positive rate | 3.3% | 10% |
| Watermark false positive rate (wrong key) | 10% | 20% |
| Mean substitutions per unit | 1.2 | 14.4 |
| Original trajectory roughness | 25.7 | 291.2 |
| Empathetic **target** roughness | 21.7 | 161.8 |
| Urgent **target** roughness | 36.5 | 460.7 |
| Empathetic **realized** roughness | 25.5 | 286.1 |
| Urgent **realized** roughness | 25.7 | 284.5 |

(`n=10` texts, so the watermark percentages above are noisy — read them as
directional, not precise.)

**The answer is: partially, and unevenly.** Watermark TPR did move up (3x,
though the base rates are too small-sample to be confident it's not just
noise), consistent with more independent frequency bins giving the
statistic more to work with. But the persona-modulation result is the
clean one: even with **12x more substitutions available** (14.4 words
changed in a 120-word paragraph vs. 1.2 in a 10-word sentence), the
realized roughness gap between empathetic and urgent output is still
essentially zero (286.1 vs. 284.5) against an idealized target gap that
grew just as dramatically as everything else with length (161.8 vs.
460.7, a ~3x spread). More substitution budget did not translate into more
realized stylistic differentiation, even proportionally.

The reason is structural, not a search-budget problem: `synonym_candidates`
ranks WordNet substitutions by embedding-cosine similarity to the original
word, and true synonyms *are* close together in embedding space by
definition. Each individual substitution is capped at a small nudge no
matter how many of them you make or how long the text is — the ceiling is
per-word, not per-document. Paragraph length fixes the *statistical*
half of the problem (more independent bins → somewhat better watermark
detection power) but does nothing for the *expressive* half (single-word
lexical substitution structurally cannot span the distance to an arbitrary
spectral target). That's the harder, second fix from the list below, and
these numbers are the evidence that it's the one that actually matters.

## Bottom line

If you want to build a real system out of this idea, the buildable,
citable-lineage version is: **spectral (DFT-domain) manipulation of
sentence-embedding sequences, in the same family as embedding-space
steering methods (PPLM, COLD decoding, MuCoLa) and semantic text
watermarking (SemStamp, Kirchenbauer et al.)** — not "Active Inference"
and not "eradicating autoregressive myopia." Concretely, to make the
persona/watermark effect survive contact with real text, you'd need one of:

1. **A real generative LM as the decoder**, sampling/searching over full
   phrasings (not just single-word swaps) scored by embedding-distance +
   LM likelihood — much larger search space, much more expressive, and
   actually closer to what "Active Inference decoding" would need to mean
   to work. **This is the one that matters most** — see the paragraph
   experiment above: even a 12x increase in substitution budget left
   persona differentiation essentially at zero, because single-word
   synonym substitution has a hard, per-word expressiveness ceiling that
   more text doesn't relax.
2. **Longer units of text** (paragraphs/documents, not sentences) for the
   watermark — tested above, and it helps, but only partially (TPR ~3%
   → ~10%, still far from usable) and it does nothing for persona
   modulation. A necessary companion to #1, not a substitute for it.
3. **Proper significance calibration** (permutation p-values, which I
   built) instead of an ad hoc correlation threshold, regardless of #1/#2.
4. **Empirical validation of the phase=facts/magnitude=style split**
   before relying on it further — it's the framework's central assumption
   and it is currently untested even here.

None of that requires inventing a new cognitive-science framework. It's an
interesting, legitimate applied-NLP research direction; it is not the
paradigm shift the source documents describe, and the mechanism that would
need to do the real work (turning a modulated embedding back into fluent,
on-target text) is exactly the part the source material never specifies.
