from __future__ import annotations

AIRFRAME_MASS_KG: float = 0.85
MAX_KINETIC_ENERGY_RATE: float = 12.5  # W — max dKE/dt for Orin Nano airframe
GRAVITY_MS2: float = 9.81


class KinematicEnvelopeViolation(Exception):
    """validity_mask = 0.0 — raised when a proposed lattice mutation exceeds the kinematic energy envelope."""
