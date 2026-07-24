from __future__ import annotations

import torch
import torch.nn as nn

from fgsgr.governance.constraints import (
    AIRFRAME_MASS_KG,
    MAX_KINETIC_ENERGY_RATE,
    GRAVITY_MS2,
    KinematicEnvelopeViolation,
)


class LDTLatticeProjection(nn.Module):
    def __init__(self, state_dim: int, lattice_dim: int) -> None:
        super().__init__()
        self.projection = nn.Linear(state_dim, lattice_dim, bias=False)

    def compute_lagrangian_energy(self, phi: torch.Tensor) -> torch.Tensor:
        ke = 0.5 * AIRFRAME_MASS_KG * (phi ** 2).sum(dim=-1)
        pe = GRAVITY_MS2 * AIRFRAME_MASS_KG * phi.abs().mean(dim=-1)
        return ke + pe

    def compute_kinetic_energy_derivative(self, phi: torch.Tensor, dt: float) -> torch.Tensor:
        ke = 0.5 * AIRFRAME_MASS_KG * (phi ** 2).sum(dim=-1)
        return ke / dt

    def project(self, grid_output: torch.Tensor, dt: float = 0.01) -> torch.Tensor:
        phi = self.projection(grid_output)
        dke_dt = self.compute_kinetic_energy_derivative(phi, dt)
        violation = dke_dt > MAX_KINETIC_ENERGY_RATE
        if violation.any():
            max_rate = dke_dt.max().item()
            raise KinematicEnvelopeViolation(
                f"validity_mask = 0.0 — proposed mutation dKE/dt={max_rate:.4f} "
                f"exceeds kinematic limit={MAX_KINETIC_ENERGY_RATE}"
            )
        return phi

    def forward(self, grid_output: torch.Tensor, dt: float = 0.01) -> torch.Tensor:
        with torch.no_grad():
            return self.project(grid_output, dt)
