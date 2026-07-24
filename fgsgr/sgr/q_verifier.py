from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn


class PTRMDivergenceError(Exception):
    pass


class PTRMVerifier(nn.Module):
    """STARS-upgraded trajectory verifier — convergence-based depth, no fixed limit."""

    _ITER_CEILING = 1024  # safety ceiling only; convergence criterion terminates first

    def __init__(
        self,
        state_dim: int,
        num_candidates: int = 4,
        delta_convergence: float = 1e-4,
        stabilisation_rate: float = 0.1,
    ) -> None:
        super().__init__()
        self.recurrent = nn.GRUCell(state_dim, state_dim)
        self.num_candidates = num_candidates
        self.delta_convergence = delta_convergence
        self.stabilisation_rate = stabilisation_rate

    def _sample_candidates(self, z: torch.Tensor) -> torch.Tensor:
        noise = torch.randn(
            self.num_candidates, *z.shape, device=z.device, dtype=z.dtype
        )
        return z.unsqueeze(0) + noise * 0.01

    def _stabilise_step(
        self, z: torch.Tensor, z_target: torch.Tensor
    ) -> torch.Tensor:
        recurrent_out = self.recurrent(z, z)
        return recurrent_out + self.stabilisation_rate * (z_target - z)

    def verify(
        self, z: torch.Tensor, z_target: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        if z_target is None:
            z_target = z.detach().clone()

        candidates = self._sample_candidates(z)
        best: Optional[torch.Tensor] = None
        best_dist = float("inf")

        for k in range(self.num_candidates):
            z_cur = candidates[k]

            for _ in range(self._ITER_CEILING):
                z_next = self._stabilise_step(z_cur, z_target)
                if torch.isnan(z_next).any():
                    z_cur = z_next  # mark as diverged
                    break
                delta = (z_next - z_cur).norm()
                z_cur = z_next
                if delta < self.delta_convergence:
                    break

            if torch.isnan(z_cur).any():
                continue

            dist = (z_cur - z_target).norm().item()
            if dist < best_dist:
                best = z_cur
                best_dist = dist

        if best is None:
            raise PTRMDivergenceError(
                f"All {self.num_candidates} STARS candidates diverged to NaN"
            )

        return best

    def forward(
        self, z: torch.Tensor, z_target: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        with torch.no_grad():
            return self.verify(z, z_target)
