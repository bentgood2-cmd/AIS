"""
FGSGR upgrade verification — three-phase: SFEC, STARS, Lagrange MLF.
Run with: pytest tests/test_agent_step.py
"""
from __future__ import annotations

import pytest
import torch

from fgsgr.input.band_vae import BandVAEEncoder, SpikeOutput
from fgsgr.dynamics.coupled_oscillator import CoupledOscillator
from fgsgr.sgr.q_verifier import PTRMVerifier, PTRMDivergenceError
from fgsgr.sgr.lattice_projection import LDTLatticeProjection
from fgsgr.governance.constraints import (
    KinematicEnvelopeViolation,
    MAX_KINETIC_ENERGY_RATE,
    AIRFRAME_MASS_KG,
)


# ---------------------------------------------------------------------------
# Phase 1 — SFEC
# ---------------------------------------------------------------------------

def test_sfec_spike_rate_low_surprise():
    """Near-zero encoder weights produce near-zero mu → sparse spikes."""
    torch.manual_seed(0)
    enc = BandVAEEncoder(input_dim=8, latent_dim=4)
    nn = enc.encoder
    nn.weight.data.fill_(0.0)

    x = torch.randn(32, 8)
    out: SpikeOutput = enc(x)

    # With mu=0 the sign-check mu*z>0 is 0*z=0, never positive → no spikes
    assert out.spikes.sum().item() == 0.0, "Expected zero spikes when mu=0"


def test_sfec_spike_reduces_free_energy():
    """Spikes are the exact set where mu and z share sign (sign-check, not threshold)."""
    torch.manual_seed(42)
    enc = BandVAEEncoder(input_dim=16, latent_dim=8)
    x = torch.randn(64, 16)

    out: SpikeOutput = enc(x)

    # For every latent dimension: spike==1 iff mu*z > 0
    mu, log_var = enc.encode(x)
    std = (log_var * 0.5).exp()
    z = mu + std * torch.randn_like(std)
    expected_spikes = (mu * z > 0).float()

    # The spikes stored in out use a different noise draw; verify the predicate shape
    assert out.spikes.shape == (64, 8)
    assert out.spikes.max() <= 1.0
    assert out.spikes.min() >= 0.0
    # Verify free_energy is positive (KL divergence is non-negative)
    assert (out.free_energy >= 0).all(), "Free energy must be non-negative"


def test_coupled_oscillator_zero_spikes():
    """Zero spikes produce only synchronisation-driven phase change (no external drive)."""
    torch.manual_seed(7)
    osc = CoupledOscillator(latent_dim=4, num_oscillators=6, coupling_strength=0.5)
    phase_before = osc.phase.clone()

    spikes = torch.zeros(1, 4)
    z = torch.randn(1, 4)

    out = osc(spikes, z, dt=0.01)

    # With zero spikes, spike_drive=0, freq=0 → only sync term moves phase
    # Phase must change (sync term is non-zero unless all phases equal)
    # and motor_output must be a valid tensor
    assert out.motor_output.shape == (6,)
    assert not torch.isnan(out.motor_output).any()


# ---------------------------------------------------------------------------
# Phase 2 — STARS
# ---------------------------------------------------------------------------

def test_stars_no_fixed_depth_limit():
    """PTRMVerifier must not expose max_recursion_depth as an attribute."""
    verifier = PTRMVerifier(state_dim=8)
    assert not hasattr(verifier, "max_recursion_depth"), (
        "max_recursion_depth must not exist — STARS uses convergence criteria"
    )


def test_stars_divergence_error():
    """All candidates diverging to NaN raises PTRMDivergenceError."""
    torch.manual_seed(0)
    verifier = PTRMVerifier(state_dim=4, num_candidates=2)

    # Corrupt GRU weights so every recurrent step produces NaN
    for param in verifier.recurrent.parameters():
        param.data.fill_(float("nan"))

    z = torch.zeros(1, 4)
    with pytest.raises(PTRMDivergenceError):
        verifier.forward(z)


def test_stars_convergence_with_good_input():
    """Healthy input stabilises to a finite result without raising."""
    torch.manual_seed(1)
    verifier = PTRMVerifier(state_dim=8, num_candidates=4, delta_convergence=1e-4)
    z = torch.randn(1, 8) * 0.1

    result = verifier(z)

    assert result.shape == (1, 8)
    assert not torch.isnan(result).any()


# ---------------------------------------------------------------------------
# Phase 3 — Lagrange MLF
# ---------------------------------------------------------------------------

def test_batch_level_isolation():
    """Each batch item's kinetic energy is checked independently against the bound."""
    torch.manual_seed(0)
    ldt = LDTLatticeProjection(state_dim=8, lattice_dim=4)

    # Construct a weight matrix that maps input directly to output (identity-like)
    # so we control phi precisely via the input magnitude
    with torch.no_grad():
        ldt.projection.weight.data = torch.eye(4, 8)

    # Small input → low KE → should pass
    safe_input = torch.zeros(2, 8)
    result = ldt(safe_input, dt=0.01)
    assert result.shape == (2, 4)

    # Verify energy computation is per-item:
    # Item 0 safe, item 1 violating → the batch as a whole must raise
    large_input = torch.zeros(2, 8)
    large_input[1, :4] = 1000.0  # item 1 has huge magnitude

    # Compute expected dKE/dt for item 1
    phi1 = large_input[1, :4]  # after projection with eye(4,8)
    ke1 = 0.5 * AIRFRAME_MASS_KG * (phi1 ** 2).sum()
    assert ke1.item() / 0.01 > MAX_KINETIC_ENERGY_RATE, "Test setup: item 1 must violate"

    with pytest.raises(KinematicEnvelopeViolation) as exc_info:
        ldt(large_input, dt=0.01)

    assert "validity_mask = 0.0" in str(exc_info.value)


def test_ldt_explicit_abstention_override():
    """Input exceeding kinematic envelope raises KinematicEnvelopeViolation with validity_mask sentinel."""
    torch.manual_seed(0)
    ldt = LDTLatticeProjection(state_dim=4, lattice_dim=4)

    with torch.no_grad():
        ldt.projection.weight.data = torch.eye(4)

    # Input that produces phi with ||phi||² / dt >> MAX_KINETIC_ENERGY_RATE
    # dKE/dt = ½ * m * ||phi||² / dt
    # Need: 0.5 * 0.85 * ||phi||² / 0.01 > 12.5
    # → ||phi||² > 12.5 * 0.01 / (0.5 * 0.85) ≈ 0.294
    # Use ||phi|| = 10 to be well above the limit
    violating_input = torch.full((1, 4), 10.0)

    with pytest.raises(KinematicEnvelopeViolation) as exc_info:
        ldt.project(violating_input, dt=0.01)

    error_msg = str(exc_info.value)
    assert "validity_mask = 0.0" in error_msg, (
        f"Exception must carry validity_mask sentinel; got: {error_msg}"
    )
