"""
Spectral Semantics: a working, honestly-scoped implementation of the
buildable core of the "Spectral Persona Modulation" / FGSGR concept
(DFT-domain magnitude modulation of embedding sequences, plus blind
correlation-based detection).

See ../FEASIBILITY.md for what is real, what is not, and what the
experiments in experiments/run_feasibility_eval.py actually measured.
"""

from .spectral import dft_decompose, idft_reconstruct, bandpass_mask, modulate_magnitude
from .masks import prng_mask, persona_mask

__all__ = [
    "dft_decompose",
    "idft_reconstruct",
    "bandpass_mask",
    "modulate_magnitude",
    "prng_mask",
    "persona_mask",
]
