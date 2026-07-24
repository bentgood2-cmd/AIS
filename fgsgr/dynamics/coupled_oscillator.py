from __future__ import annotations

from typing import NamedTuple

import torch
import torch.nn as nn


class OscillatorOutput(NamedTuple):
    motor_output: torch.Tensor
    phase: torch.Tensor


class CoupledOscillator(nn.Module):
    """Kuramoto-coupled phase oscillator driven by SFEC spike emissions."""

    def __init__(
        self,
        latent_dim: int,
        num_oscillators: int,
        coupling_strength: float = 0.5,
    ) -> None:
        super().__init__()
        self.drive_map = nn.Linear(latent_dim, num_oscillators, bias=False)
        self.output_map = nn.Linear(num_oscillators, num_oscillators, bias=False)
        self.coupling_strength = coupling_strength
        self.register_buffer("phase", torch.zeros(num_oscillators))

    def step(
        self,
        spikes: torch.Tensor,
        z_gated: torch.Tensor,
        dt: float = 0.01,
    ) -> OscillatorOutput:
        # Gate the latent by spikes: zero-spike dims contribute no drive
        spike_drive = spikes * z_gated  # (batch, latent_dim)

        # Kuramoto frequency input — mean over batch for VRAM efficiency
        freq = self.drive_map(spike_drive).mean(dim=0)  # (num_oscillators,)

        # Synchronisation: dθ/dt includes K·sin(mean_θ − θ_i) coupling
        mean_phase = self.phase.mean()
        sync = self.coupling_strength * torch.sin(mean_phase - self.phase)

        self.phase = (self.phase + (freq + sync) * dt).detach()

        motor = self.output_map(self.phase.unsqueeze(0)).squeeze(0)
        return OscillatorOutput(motor_output=motor, phase=self.phase.clone())

    def forward(
        self,
        spikes: torch.Tensor,
        z_gated: torch.Tensor,
        dt: float = 0.01,
    ) -> OscillatorOutput:
        with torch.no_grad():
            return self.step(spikes, z_gated, dt)
