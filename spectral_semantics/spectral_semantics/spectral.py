"""
Core spectral operations on embedding sequences E in R^{d x L}.

This implements the DFT decomposition / magnitude modulation / IDFT
reconstruction described in the source papers, with one correction the
papers omit: a real-valued signal has a conjugate-symmetric spectrum
(Ehat[omega] = conj(Ehat[L - omega])). If you modulate the magnitude with
an arbitrary mask M(omega) that is not itself symmetric under
omega -> L - omega, the inverse transform is no longer real and the
"reconstructed embedding" silently acquires an imaginary component that
naive code (e.g. `.real`) throws away, quietly corrupting the result.

Every mask-generation function in masks.py enforces this symmetry so the
round trip below is exact (see tests/test_spectral.py).
"""
from __future__ import annotations

import numpy as np


def dft_decompose(E: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """1D DFT of each row of E (d x L) along the sequence axis.

    Returns (magnitude, phase), both shape (d, L).
    """
    if E.ndim != 2:
        raise ValueError(f"E must be (d, L), got shape {E.shape}")
    Ehat = np.fft.fft(E, axis=1)
    return np.abs(Ehat), np.angle(Ehat)


def idft_reconstruct(magnitude: np.ndarray, phase: np.ndarray) -> np.ndarray:
    """Inverse DFT recombining magnitude and phase back into a real (d, L) matrix.

    Raises if the spectrum isn't (numerically) conjugate-symmetric, since in
    that case the "real" embedding returned would not equal what actually
    comes out of ifft — silently taking `.real` would hide a bug.
    """
    Ehat = magnitude * np.exp(1j * phase)
    E_complex = np.fft.ifft(Ehat, axis=1)
    imag_energy = np.abs(E_complex.imag).max() if E_complex.size else 0.0
    real_energy = np.abs(E_complex.real).max() if E_complex.size else 1.0
    if imag_energy > 1e-6 * max(real_energy, 1e-12):
        raise ValueError(
            "Spectrum is not conjugate-symmetric: inverse DFT has a "
            f"non-negligible imaginary component (max |imag|={imag_energy:.3g} "
            f"vs max |real|={real_energy:.3g}). The modulation mask must satisfy "
            "mask[omega] == mask[(L - omega) % L] for the result to stay real. "
            "See masks.py."
        )
    return E_complex.real


def bandpass_mask(L: int, omega_min: int, omega_max: int) -> np.ndarray:
    """Symmetric radial bandpass B(omega): 1 inside [omega_min, omega_max]
    (and its mirror image around L - omega), 0 elsewhere. Symmetric by
    construction, so it never breaks realness on its own.
    """
    if not (0 <= omega_min <= omega_max <= L // 2):
        raise ValueError(f"require 0 <= omega_min <= omega_max <= L//2, got L={L}, "
                          f"omega_min={omega_min}, omega_max={omega_max}")
    B = np.zeros(L, dtype=float)
    for w in range(L):
        w_mirror = (-w) % L
        if omega_min <= w <= omega_max or omega_min <= w_mirror <= omega_max:
            B[w] = 1.0
    return B


def modulate_magnitude(
    magnitude: np.ndarray,
    mask_signal: np.ndarray,
    band: np.ndarray,
    strength: float,
) -> np.ndarray:
    """|E~(omega)| = |E(omega)| * (1 + strength * mask_signal(omega) * band(omega))

    magnitude: (d, L). mask_signal, band: (L,), broadcast across d.
    Magnitude is clipped at 0 (a magnitude cannot go negative; the source
    papers don't address this edge case, but strength * mask can drive the
    factor below zero for strength close to or above 1).
    """
    factor = 1.0 + strength * mask_signal * band
    modulated = magnitude * factor[None, :]
    return np.clip(modulated, a_min=0.0, a_max=None)
