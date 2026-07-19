"""
Blind (source-free) watermark detection, following the "Zero-Knowledge
Provenance Verification" scheme in Expand.pdf: correlate the suspect text's
own band-restricted magnitude spectrum against the mask regenerated from
the known key, via Pearson's rho.

The source PDF defines X = |F{Phi(T_suspect)}| ⊙ B(omega) as if it were a
single vector, but Phi(T) is a (d, L) matrix, so |F{Phi(T)}| is (d, L) too
-- there's no d axis in the mask Y = M(omega) ⊙ B(omega), which is (L,).
The PDF doesn't say how to go from a (d, L) magnitude matrix to something
comparable with an (L,)-shaped mask. This module fills that gap by
averaging magnitude across embedding dimensions to get a single per-
frequency energy profile, and documents that as an explicit design choice
(see FEASIBILITY.md) rather than a claim the original paper actually made.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .embeddings import Embedder
from .masks import prng_mask
from .spectral import dft_decompose


def band_energy_profile(embedder: Embedder, tokens: list[str], band: np.ndarray) -> np.ndarray:
    """Per-frequency energy profile x(omega) = mean_j |Ehat_j(omega)|, shape (L,)."""
    E = embedder.encode(tokens)
    mag, _ = dft_decompose(E)
    return mag.mean(axis=0)


def correlation_score(embedder: Embedder, tokens: list[str], key: str, band: np.ndarray) -> float:
    """Pearson correlation between the suspect text's band energy profile
    and the mask regenerated from `key`, restricted to the band's frequency
    bins. Returns 0.0 (no evidence either way) if either series is constant
    on the band, since Pearson's rho is undefined in that degenerate case.
    """
    profile = band_energy_profile(embedder, tokens, band)
    mask = prng_mask(key, len(tokens))
    idx = band.astype(bool)
    x, y = profile[idx], (mask * band)[idx]
    if x.std() < 1e-12 or y.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def permutation_pvalue(
    embedder: Embedder,
    tokens: list[str],
    key: str,
    band: np.ndarray,
    n_permutations: int = 500,
    seed: int = 0,
) -> tuple[float, float]:
    """A statistically calibrated alternative to eyeballing "rho >> 0".

    The source paper (Expand.pdf, section V) asserts detection whenever the
    correlation "significantly exceeds the null hypothesis (rho >> 0)" but
    never specifies a threshold or how to calibrate one. In practice, a
    fixed threshold like rho > 0.5 is unreliable: because mask generation
    enforces Hermitian symmetry (mask[w] == mask[L-w], required for the
    inverse DFT to stay real -- see spectral.py), a band of width B only
    contains roughly B/2 statistically independent values. For short texts
    this means very few independent samples feed the correlation, and its
    sampling variance under the null (no watermark present) is large enough
    that "rho > 0.5 by pure chance" is common, not rare (see
    tests/test_detector.py::test_naive_threshold_has_high_false_positive_rate
    for a measured false-positive rate).

    This function replaces the fixed threshold with an empirical p-value:
    it compares the observed correlation against a null distribution built
    from `n_permutations` unrelated random keys applied to the *same* text,
    and reports what fraction of those unrelated keys correlate at least as
    strongly as the real one. That number is directly interpretable and
    controls the false-positive rate by construction, regardless of how few
    independent frequency bins the band contains.
    """
    observed = correlation_score(embedder, tokens, key, band)
    rng = np.random.default_rng(seed)
    null_scores = np.array(
        [
            correlation_score(embedder, tokens, f"__null_{rng.integers(0, 2**31)}", band)
            for _ in range(n_permutations)
        ]
    )
    p_value = (np.sum(null_scores >= observed) + 1) / (n_permutations + 1)
    return observed, float(p_value)


@dataclass
class DetectionTrial:
    label: str  # "watermarked" or "clean"
    score: float


def roc_points(trials: list[DetectionTrial]) -> list[tuple[float, float, float]]:
    """Sweep thresholds over observed scores, return (threshold, TPR, FPR)."""
    thresholds = sorted({t.score for t in trials}, reverse=True)
    watermarked = [t.score for t in trials if t.label == "watermarked"]
    clean = [t.score for t in trials if t.label == "clean"]
    points = []
    for thr in thresholds:
        tpr = sum(s >= thr for s in watermarked) / max(len(watermarked), 1)
        fpr = sum(s >= thr for s in clean) / max(len(clean), 1)
        points.append((thr, tpr, fpr))
    return points


def auc(trials: list[DetectionTrial]) -> float:
    """Trapezoidal-rule AUC over the ROC curve (0.5 = chance, 1.0 = perfect)."""
    points = roc_points(trials)
    points = sorted(points, key=lambda p: p[2])  # sort by FPR ascending
    fprs = [0.0] + [p[2] for p in points] + [1.0]
    tprs = [0.0] + [p[1] for p in points] + [1.0]
    area = 0.0
    for i in range(1, len(fprs)):
        area += (fprs[i] - fprs[i - 1]) * (tprs[i] + tprs[i - 1]) / 2.0
    return area
