import numpy as np
import pytest

from spectral_semantics.spectral import (
    bandpass_mask,
    dft_decompose,
    idft_reconstruct,
    modulate_magnitude,
)
from spectral_semantics.masks import prng_mask, persona_mask


def _random_E(d=8, L=12, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(size=(d, L))


def test_round_trip_identity_at_zero_strength():
    E = _random_E()
    mag, phase = dft_decompose(E)
    band = bandpass_mask(E.shape[1], 2, 4)
    mask = prng_mask("key", E.shape[1])
    mag2 = modulate_magnitude(mag, mask, band, strength=0.0)
    E2 = idft_reconstruct(mag2, phase)
    np.testing.assert_allclose(E, E2, atol=1e-8)


def test_symmetric_mask_round_trip_stays_real_and_recoverable():
    E = _random_E()
    L = E.shape[1]
    mag, phase = dft_decompose(E)
    band = bandpass_mask(L, 2, 4)
    mask = prng_mask("watermark-key", L)
    mag_mod = modulate_magnitude(mag, mask, band, strength=0.5)
    # Should not raise (spectrum stays conjugate-symmetric -> real ifft).
    E_mod = idft_reconstruct(mag_mod, phase)
    assert np.isrealobj(E_mod)
    # Modulation actually changed something inside the band...
    assert not np.allclose(E, E_mod)
    # ...but low frequencies outside the band are exactly untouched.
    mag_check, phase_check = dft_decompose(E_mod)
    outside = band == 0
    np.testing.assert_allclose(mag_check[:, outside], mag[:, outside], atol=1e-8)
    # Compare via the complex exponential to avoid a spurious failure at the
    # +/-pi wraparound (cos(pi) == cos(-pi) even though the raw angles differ).
    np.testing.assert_allclose(
        np.exp(1j * phase_check[:, outside]), np.exp(1j * phase[:, outside]), atol=1e-6
    )


def test_asymmetric_mask_breaks_realness_and_is_caught():
    """This is the bug the source papers' equations have if implemented
    literally: an arbitrary (non-symmetric) M(omega) makes the "reconstructed"
    embedding complex. We assert idft_reconstruct refuses to silently drop
    the imaginary part.
    """
    E = _random_E()
    L = E.shape[1]
    mag, phase = dft_decompose(E)
    band = bandpass_mask(L, 2, 4)
    rng = np.random.default_rng(1)
    bad_mask = rng.uniform(-1, 1, size=L)  # NOT symmetrized on purpose
    mag_mod = modulate_magnitude(mag, bad_mask, band, strength=0.9)
    with pytest.raises(ValueError, match="conjugate-symmetric"):
        idft_reconstruct(mag_mod, phase)


def test_prng_mask_deterministic_and_symmetric():
    m1 = prng_mask("abc", 16)
    m2 = prng_mask("abc", 16)
    m3 = prng_mask("xyz", 16)
    np.testing.assert_array_equal(m1, m2)
    assert not np.array_equal(m1, m3)
    for w in range(16):
        assert m1[w] == pytest.approx(m1[(-w) % 16])


@pytest.mark.parametrize("kind", ["empathetic", "urgent", "neutral"])
def test_persona_mask_symmetric_and_bounded(kind):
    m = persona_mask(kind, 20)
    assert m.shape == (20,)
    assert np.all(np.abs(m) <= 1.0 + 1e-9)
    for w in range(20):
        assert m[w] == pytest.approx(m[(-w) % 20])


def test_bandpass_mask_shape_and_symmetry():
    L = 16
    B = bandpass_mask(L, 3, 5)
    assert B.shape == (L,)
    assert set(np.unique(B)).issubset({0.0, 1.0})
    for w in range(L):
        assert B[w] == B[(-w) % L]


def test_bandpass_mask_rejects_invalid_range():
    with pytest.raises(ValueError):
        bandpass_mask(16, 5, 3)
    with pytest.raises(ValueError):
        bandpass_mask(16, 0, 20)
