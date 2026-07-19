"""
Mask generation for spectral modulation.

Every mask here is built to satisfy mask[omega] == mask[(L - omega) % L],
i.e. Hermitian symmetry, which spectral.idft_reconstruct requires to
produce a real-valued embedding (see spectral.py docstring).
"""
from __future__ import annotations

import hashlib

import numpy as np


def _symmetrize(values_half: np.ndarray, L: int) -> np.ndarray:
    """Given values for omega = 0 .. L//2, mirror them onto L//2+1 .. L-1."""
    out = np.zeros(L, dtype=float)
    half_len = L // 2 + 1
    out[:half_len] = values_half[:half_len]
    for w in range(half_len, L):
        out[w] = out[(-w) % L]
    return out


def prng_mask(key: str, L: int, seed_extra: int = 0) -> np.ndarray:
    """Deterministic pseudo-random mask M(omega) in [-1, 1], seeded from `key`.

    Used as the watermark signature: the same key always regenerates the
    same mask, which is what makes blind (source-free) detection possible
    in detector.py — the verifier only needs the key, not the original text.
    """
    digest = hashlib.sha256(f"{key}:{seed_extra}".encode()).digest()
    seed = int.from_bytes(digest[:8], "big") % (2**32)
    rng = np.random.default_rng(seed)
    half_len = L // 2 + 1
    values_half = rng.uniform(-1.0, 1.0, size=half_len)
    return _symmetrize(values_half, L)


def persona_mask(kind: str, L: int) -> np.ndarray:
    """Stylistic masks matching the paper's own figure ("Persona Frequency
    Mask"): 'empathetic' is smooth/low-variance, 'urgent' is high-variance
    and rhythmic/spiky. Both are illustrative shapes, not learned from data
    — see FEASIBILITY.md for why that matters.
    """
    half_len = L // 2 + 1
    omega = np.arange(half_len)
    if kind == "empathetic":
        values_half = 0.6 * np.sin(2 * np.pi * omega / max(half_len, 1))
    elif kind == "urgent":
        values_half = np.where(omega % 2 == 0, 1.0, -1.0)
    elif kind == "neutral":
        values_half = np.zeros(half_len)
    else:
        raise ValueError(f"unknown persona kind: {kind!r} (expected empathetic/urgent/neutral)")
    return _symmetrize(values_half, L)
