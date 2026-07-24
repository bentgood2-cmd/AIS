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

## Second follow-up: is WordNet specifically the bottleneck?

The previous experiment pinned the blame on "single-word lexical
substitution has a hard, per-word expressiveness ceiling." But that ceiling
could be a property of *WordNet synonymy specifically* (true synonyms sit
close together in embedding space by construction) rather than of
word-level substitution in general. I tested this directly:
`rewrite.lm_proposal_candidates` proposes substitution words by local
two-sided trigram fluency across the **entire** vocabulary (14,104 words),
not just WordNet's synset for the original word — so it's free to suggest
words that are nowhere near the original in embedding space, as long as
they'd read fluently in context. `guided_rewrite(..., use_lm_candidates=True)`
searches over the union of both sources.

Result, one example (`"the old man walked slowly across the quiet garden"`,
urgent persona mask): band-restricted distance to the spectral target fell
from 308.65 (WordNet-only) to 244.73 (WordNet+LM-proposed) — confirming
WordNet's narrowness genuinely was costing real reachable distance. But the
output was `"the president man told abandon across the still abandon"` —
incoherent, with a word duplicated. Cranking the fluency penalty from 2x to
20x changed nothing; the chosen words were identical every time.

Digging into why revealed something more fundamental than "the fluency
penalty needs retuning": I compared raw trigram statistics for the
nonsensical substitution against a genuinely fluent one:

| trigram | seen in training? | log-prob |
|---|---|---|
| `(the, old, man)` | yes, 5 times | −8.58 |
| `(man, walked, slowly)` — grammatical, but not this *exact* trigram | no | −10.37 |
| `(man, told, abandon)` — the nonsensical one | no | −10.37 |
| `(still, abandon, </s>)` | no | −10.37 |

**A perfectly grammatical trigram that simply doesn't appear verbatim in
30,000 training sentences gets scored identically to a nonsensical one.**
With a 32K-word vocabulary and Laplace smoothing, any unseen trigram's
probability collapses to roughly `1/(context_count + V)` regardless of
context — the model can only tell fluent from incoherent by exact
memorization, not by generalizing ("walked" and "told abandon" are
equally "unseen" to it, even though a human reader isn't confused by one
and is by the other). Scaling the fluency weight can't fix this because
the fluency signal itself carries almost no information once you're off
the training data verbatim — there's nothing for a higher weight to
amplify.

This sharpens recommendation #1 in the "Bottom line" below: the missing
piece isn't just "a bigger candidate space" (which `lm_proposal_candidates`
proves helps) or "a bigger fluency weight" (which does nothing) — it's a
model that can **generalize**, the way a neural LM's learned embeddings let
it recognize "man walked slowly" as fine and "man told abandon" as broken
even though neither exact trigram was memorized. I checked whether that was
obtainable here: both `huggingface.co` and `download.pytorch.org` return
`403` in this environment's network sandbox (only `pypi.org` /
`files.pythonhosted.org` are reachable), so a pretrained model (GPT-2 or
similar) can't be fetched. The remaining path — training a small neural LM
from scratch on this same ~30K-sentence local corpus via a
`pip install torch`-obtained CPU build — is a materially bigger effort
with genuinely uncertain payoff (30K sentences is thin for a neural LM to
learn much beyond what the n-gram counts already capture), and I stopped
here rather than open-endedly pursue it without checking scope first.

## Third follow-up: does training a small neural LM from scratch fix it?

I went ahead and trained one anyway (`spectral_semantics/neural_lm.py`): a
1-layer, 128-dim-embedding/256-hidden-unit word-level LSTM, trained for 5
epochs on the same ~30K-sentence local corpus (no external download — torch
itself installs fine from PyPI; it's only pretrained *weights* that are
blocked). Val perplexity plateaued around 430-440, which is weak by
neural-LM standards but categorically different from the trigram model: it
generalizes through learned embeddings instead of exact n-gram
memorization. Wired it in as both a candidate proposer
(`neural_candidates`, using the model's real next-token distribution) and
a fluency judge (`NeuralLM` implements the same
`sentence_logprob_per_token` interface as `TrigramLM`, so it drops
straight into `guided_rewrite`'s scoring). Then ran all three decoder
configurations — WordNet-only, WordNet+trigram-proposed, WordNet+neural-
proposed-and-judged — through the identical measurement pipeline on the
same 30 sentences (`experiments/compare_decoders.py`).

| metric | WordNet-only | +trigram candidates | +neural candidates & fluency |
|---|---|---|---|
| Watermark TPR | 3.3% | 6.7% | 3.3% |
| Mean semantic cosine to original | 0.999 | 0.977 | **0.969** |
| Mean fluency delta (per the *scorer being optimized against*) | −0.018 | **+0.202** | **+0.145** |
| Mean substitutions per sentence | 1.2 | 3.0 | 2.7 |
| Urgent realized roughness (target 36.5, orig 25.7) | 25.7 | 28.8 | **31.9** |
| Empathetic realized roughness (target 21.7, orig 25.7) | 25.5 | 25.2 | 25.3 |

Genuinely mixed, not a clean win in either direction:

- **The good part**: "urgent" persona differentiation, which was
  essentially zero with WordNet-only, does now partially show up — 25.7 →
  28.8 → 31.9 against a target of 36.5, closing roughly 58% of the gap with
  the neural decoder, its best showing anywhere in this investigation.
- **The bad part**: watermark detection stayed flat at chance level
  (3.3%) with the neural decoder specifically — no better than doing
  nothing, despite the extra reach. My read: a PRNG watermark mask needs
  precise, sign-correct control across many independent frequency bins
  simultaneously (a fine-grained, high-dimensional target), while "make it
  generally spikier" (urgent) is a coarse, forgiving one that many
  different substitutions satisfy. Decoder expressiveness helps the coarse
  task and not the fine one.
- **"Empathetic" (smoothing) stayed flat everywhere** — 25.5/25.2/25.3,
  regardless of decoder, vs. a target of 21.7. *Increasing* trajectory
  roughness is easy: almost any substitution that changes a value creates
  local discontinuity. *Decreasing* it requires finding words that make
  neighboring embeddings more similar than they already were — a narrower
  target that more candidates and a better fluency judge didn't help hit.
  This directional asymmetry (roughening is easy, smoothing is hard) isn't
  mentioned anywhere in the source material and only shows up once you
  actually measure it.
- **Fidelity got worse, not better, with the neural decoder** — mean
  semantic cosine to the original dropped further (0.969 vs. 0.977 for
  trigram-only), for only a marginal gain in target-distance. And the
  *positive* fluency deltas (both expanded configs score their own outputs
  as more fluent than the unedited original) are a red flag, not good
  news: it means the search is at least partly optimizing against
  exploitable blind spots in whichever fluency model is judging it, not
  producing genuinely better text. Spot-checking the actual output
  confirms this — e.g. `"between it was an the same of an"` (neural) and
  `"between it even more the end of af"` (trigram), both scored as *more*
  fluent than the grammatical original by their respective judges.

So: a from-scratch small neural LM is a real, different mechanism (and it
does move the one metric — urgent-persona roughness — furthest of
anything tried), but at 30K training sentences and this model size it's
not a fix, it's a different set of tradeoffs. It confirms the "uncertain
payoff" concern from the previous section was warranted — the honest
takeaway is that closing this gap for real needs a properly pretrained
model (blocked in this environment) or substantially more local training
data and capacity than was practical to pursue further here.

## Fourth follow-up: does more local training data close the gap?

Worth checking before assuming a bigger pretrained model is the only way
forward: the 30K-sentence neural LM turned out to never see a single
Gutenberg sentence at all — `training_sentences()`'s default 30,000-
sentence cap is reached from Brown alone (57,340 sentences), so Gutenberg
never got appended. I retrained on the true full local corpus — all of
Brown + all of Gutenberg, 144,918 sentences, 3.1M tokens, ~5.2x more data
— same architecture, and reran the identical comparison
(`experiments/compare_full_corpus_neural_lm.py`).

| metric | 30k sentences | 145k sentences |
|---|---|---|
| Validation perplexity | 430-440 | 610-616 (**worse**) |
| Watermark TPR | 3.3% | 3.3% (unchanged) |
| Urgent realized roughness (target 36.5) | 31.9 | **29.7 (worse)** |
| Empathetic realized roughness (target 21.7) | 25.3 | 25.2 (unchanged) |
| Mean fluency delta | +0.145 (reward-hacking the judge) | **−0.538** |

**More data did not help — on the main metrics it's a wash or slightly
worse**, not the fix I'd hoped for when proposing this as the "cheap
thing to try first." Two results worth separating out:

- The *bad* news: watermark detection is exactly as stuck as before, and
  urgent-persona differentiation (the one clear win from the smaller
  model) went backward, 31.9 → 29.7. The qualitative outputs are just as
  broken (`"between it was an the same of an"`, `"it was miss smith and
  mind which first to sorrow"`).
- The *interesting* news: the fluency delta flipped from **positive**
  (+0.145 — the search fooling its own judge into rating garbled output as
  more fluent than the original) to **negative** (−0.538 — the judge now
  correctly recognizes most candidate substitutions as degrading fluency,
  and the search knowingly trades that away for target-distance instead of
  getting fooled). That's a real, measurable improvement in the model's
  discriminative honesty — but it didn't translate into better final text,
  because the search's fluency penalty is a soft, weighted term, not a
  hard constraint, so a harder-to-fool judge just changes *which* penalty
  gets paid, not whether one does.

Likely confounds, so this isn't a clean "more data doesn't help, period"
result: I also cut epochs from 5 to 3 (to keep training time bounded) and
the vocabulary more than doubled (14,108 → 30,551 words) alongside the
harder, more stylistically heterogeneous corpus (Brown's news/fiction/
academic mix plus 18 full Gutenberg novels) — both of which make the
underlying classification problem harder independent of how much data the
model saw. What this result does support is the specific, narrower claim
that "just add more of the locally-available text" is not a free win — it
did not obviously outperform the smaller run on any end-to-end metric that
matters (detection rate, persona differentiation, coherence), so it isn't
worth pursuing further as a low-effort fix. A real pretrained model
remains the more promising lever, and that path is blocked here.

## Bottom line

If you want to build a real system out of this idea, the buildable,
citable-lineage version is: **spectral (DFT-domain) manipulation of
sentence-embedding sequences, in the same family as embedding-space
steering methods (PPLM, COLD decoding, MuCoLa) and semantic text
watermarking (SemStamp, Kirchenbauer et al.)** — not "Active Inference"
and not "eradicating autoregressive myopia." Concretely, to make the
persona/watermark effect survive contact with real text, you'd need one of:

1. **A properly pretrained, generalizing LM as the decoder**, sampling/
   searching over full phrasings scored by embedding-distance + LM
   likelihood — not just a bigger candidate list, and, per the third
   follow-up, not just *any* neural LM either. Three experiments narrow
   this down in sequence: the paragraph experiment showed a 12x increase in
   substitution budget left persona differentiation at zero (a per-word
   ceiling more text doesn't relax); the WordNet-vs-LM-proposal experiment
   showed that relaxing *which* words are eligible does close real
   distance, but a trigram model can't judge whether the result stays
   coherent; training an actual neural LM from scratch confirmed the
   *mechanism* (generalizing past memorized n-grams) is necessary but found
   it isn't *sufficient* at 30K sentences and modest model size — it helped
   the coarse "roughen the trajectory" objective but not the fine-grained
   watermark one, and both expanded configs still ended up exploiting blind
   spots in whichever fluency model was judging them rather than producing
   genuinely fluent text. The fourth follow-up then ruled out the cheap
   version of this fix specifically: retraining on 5x more local data (the
   full 145K-sentence corpus, not the 30K-sentence subset that never
   actually included any Gutenberg text) didn't improve detection or
   persona differentiation, and on some metrics made them slightly worse.
   A real fix needs an actually pretrained model — blocked in this
   environment — not just more locally-available training text.
2. **Redesign the watermark as a coarse per-token signal instead of a
   fine-grained continuous spectral target** — e.g. Kirchenbauer et al.'s
   "green-list" token biasing, which is what real LLM watermarking
   actually uses. Every experiment here shows the same shape: coarse,
   forgiving objectives (roughen a trajectory) get partially achieved by
   whichever decoder is used, fine-grained, sign-correct ones (matching a
   PRNG mask across many frequency bins simultaneously) never do, no
   matter how much the decoder improves. That's a strong signal the
   watermark mechanism itself — not just the decoder searching for it — is
   the wrong shape for discrete text, and is probably the single highest-
   leverage change left untried in this investigation.
3. **Longer units of text** (paragraphs/documents, not sentences) for the
   watermark — tested above, and it helps a little (TPR ~3% → ~10%, still
   far from usable) but doesn't touch persona modulation. Worth combining
   with #2, not a substitute for it.
4. **Proper significance calibration** (permutation p-values, which I
   built) instead of an ad hoc correlation threshold, regardless of the above.
5. **Empirical validation of the phase=facts/magnitude=style split**
   before relying on it further — it's the framework's central assumption
   and it is currently untested even here.

None of that requires inventing a new cognitive-science framework. It's an
interesting, legitimate applied-NLP research direction; it is not the
paradigm shift the source documents describe, and the mechanism that would
need to do the real work (turning a modulated embedding back into fluent,
on-target text) is exactly the part the source material never specifies.
