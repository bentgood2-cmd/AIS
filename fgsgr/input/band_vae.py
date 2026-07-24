from __future__ import annotations

from typing import NamedTuple

import torch
import torch.nn as nn


class SpikeOutput(NamedTuple):
    spikes: torch.Tensor       # binary sparse: 1.0 where spike lowers KL divergence
    z: torch.Tensor            # reparameterised latent sample
    free_energy: torch.Tensor  # KL divergence proxy (lower = more surprising)


class BandVAEEncoder(nn.Module):
    """Single-band VAE encoder with SFEC spike gating."""

    def __init__(self, input_dim: int, latent_dim: int) -> None:
        super().__init__()
        self.encoder = nn.Linear(input_dim, latent_dim * 2, bias=False)
        self.latent_dim = latent_dim

    def encode(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.encoder(x)
        mu, log_var = h.chunk(2, dim=-1)
        return mu, log_var

    def compute_free_energy(
        self, mu: torch.Tensor, log_var: torch.Tensor
    ) -> torch.Tensor:
        # KL divergence: D_KL(q || N(0,1)) = -½ Σ(1 + log_var - μ² - exp(log_var))
        return -0.5 * (1 + log_var - mu.pow(2) - log_var.exp()).sum(dim=-1)

    def spike_gate(self, mu: torch.Tensor, z: torch.Tensor) -> torch.Tensor:
        # Fires only when sample z agrees in sign with posterior mean μ —
        # the sign-check equivalent of "spike reduces KL divergence."
        return (mu * z > 0).float()

    def forward(self, x: torch.Tensor) -> SpikeOutput:
        with torch.no_grad():
            mu, log_var = self.encode(x)
            std = (log_var * 0.5).exp()
            z = mu + std * torch.randn_like(std)
            free_energy = self.compute_free_energy(mu, log_var)
            spikes = self.spike_gate(mu, z)
        return SpikeOutput(spikes=spikes, z=z, free_energy=free_energy)
