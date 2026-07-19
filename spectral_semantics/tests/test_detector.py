import numpy as np
import pytest

from spectral_semantics.detector import auc, correlation_score, permutation_pvalue, roc_points, DetectionTrial
from spectral_semantics.masks import prng_mask
from spectral_semantics.spectral import bandpass_mask, dft_decompose, idft_reconstruct, modulate_magnitude


class _FixedEmbedder:
    """Duck-typed stand-in for Embedder: always returns a fixed (d, L)
    matrix regardless of the tokens passed in. Lets us unit-test the
    statistical behavior of the detector against a matrix we constructed
    directly, without paying for a real Word2Vec model in every test run.
    """

    def __init__(self, E: np.ndarray):
        self._E = E

    def encode(self, tokens):
        return self._E


def _make_watermarked_matrix(key: str, L: int, d: int, band: np.ndarray, strength: float, seed: int = 0):
    rng = np.random.default_rng(seed)
    E = rng.normal(size=(d, L))
    mag, phase = dft_decompose(E)
    mask = prng_mask(key, L)
    mag_mod = modulate_magnitude(mag, mask, band, strength)
    return idft_reconstruct(mag_mod, phase)


def test_correlation_high_for_correct_key_low_for_wrong_key():
    L, d = 32, 40
    band = bandpass_mask(L, 4, 12)
    E_wm = _make_watermarked_matrix("the-real-key", L, d, band, strength=0.9)
    embedder = _FixedEmbedder(E_wm)
    dummy_tokens = ["x"] * L

    correct_rho = correlation_score(embedder, dummy_tokens, "the-real-key", band)

    wrong_rhos = [
        correlation_score(embedder, dummy_tokens, f"wrong-key-{i}", band) for i in range(200)
    ]

    assert correct_rho > 0.5, f"expected strong positive correlation for correct key, got {correct_rho}"
    assert abs(np.mean(wrong_rhos)) < 0.15, "wrong keys should not systematically correlate"
    # the correct key should clearly separate from the wrong-key distribution
    assert correct_rho > np.percentile(wrong_rhos, 99)


def test_naive_threshold_has_high_false_positive_rate():
    """This documents a real limitation, not a bug: Expand.pdf's detector
    asserts "rho >> 0 confirms the watermark" with no stated threshold or
    false-positive control. Because the mask is forced to be Hermitian-
    symmetric (see masks.py), a band of ~9 bins has only ~9 independent
    random values, so Pearson correlation against unrelated random keys has
    high sampling variance. Empirically, a naive rho > 0.5 cutoff on
    completely unwatermarked text fires far more often than "rare".
    """
    L, d = 32, 40
    band = bandpass_mask(L, 4, 12)
    rng = np.random.default_rng(42)
    E_clean = rng.normal(size=(d, L))  # never modulated by any mask
    embedder = _FixedEmbedder(E_clean)
    dummy_tokens = ["x"] * L

    rhos = [correlation_score(embedder, dummy_tokens, f"some-key-{i}", band) for i in range(200)]
    false_positive_rate = np.mean([abs(r) > 0.5 for r in rhos])
    # The point of this test is the measurement itself: a fixed rho>0.5
    # threshold is nowhere near as reliable as "rho >> 0" implies.
    assert false_positive_rate > 0.05, (
        f"expected to reproduce the known false-positive problem, got rate={false_positive_rate}; "
        "if this now fails because the rate dropped near 0, the band/DOF tradeoff changed and "
        "FEASIBILITY.md's numbers need re-checking, not this assertion loosened blindly."
    )


def test_permutation_pvalue_controls_false_positive_rate():
    """The fix for the above: calibrate significance empirically per-text
    instead of trusting a fixed correlation threshold. Under the null (key
    unrelated to the text), p-values should be ~Uniform(0,1), so roughly
    5% of trials should show p < 0.05.
    """
    L, d = 32, 40
    band = bandpass_mask(L, 4, 12)
    rng = np.random.default_rng(7)
    E_clean = rng.normal(size=(d, L))
    embedder = _FixedEmbedder(E_clean)
    dummy_tokens = ["x"] * L

    p_values = [
        permutation_pvalue(embedder, dummy_tokens, f"unrelated-key-{i}", band, n_permutations=200, seed=i)[1]
        for i in range(60)
    ]
    false_positive_rate_at_05 = np.mean([p < 0.05 for p in p_values])
    assert false_positive_rate_at_05 < 0.15, (
        f"permutation test should roughly control the false-positive rate near 0.05, got {false_positive_rate_at_05}"
    )


def test_detection_strength_scales_with_alpha():
    L, d = 32, 40
    band = bandpass_mask(L, 4, 12)
    key = "scaling-key"
    pvals = []
    for strength in [0.0, 0.3, 0.6, 0.9]:
        E_wm = _make_watermarked_matrix(key, L, d, band, strength=strength, seed=1)
        embedder = _FixedEmbedder(E_wm)
        _, p = permutation_pvalue(embedder, ["x"] * L, key, band, n_permutations=300, seed=1)
        pvals.append(p)
    # more modulation strength -> at least as significant (p-value non-increasing)
    assert pvals == sorted(pvals, reverse=True)
    assert pvals[-1] < 0.05  # strength 0.9 -> reliably detectable once calibrated properly


def test_auc_and_roc_sanity_perfect_separation():
    trials = (
        [DetectionTrial("watermarked", s) for s in [0.9, 0.8, 0.7, 0.6]]
        + [DetectionTrial("clean", s) for s in [0.1, 0.0, -0.1, -0.2]]
    )
    assert auc(trials) == pytest.approx(1.0)
    points = roc_points(trials)
    assert any(tpr == 1.0 and fpr == 0.0 for _, tpr, fpr in points)


def test_auc_chance_level_for_indistinguishable_scores():
    trials = (
        [DetectionTrial("watermarked", s) for s in [0.5, 0.3, 0.1, -0.1]]
        + [DetectionTrial("clean", s) for s in [0.5, 0.3, 0.1, -0.1]]
    )
    assert auc(trials) == pytest.approx(0.5, abs=0.05)
