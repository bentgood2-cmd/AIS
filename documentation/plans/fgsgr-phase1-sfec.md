# Plan — FGSGR Phase 1: SFEC Implementation

**Reference:** arXiv:2603.09729 — *Efficient and robust control with spikes that constrain free energy*  
**Status:** Not started  
**Files to create:** `fgsgr/input/band_vae.py`, `fgsgr/dynamics/coupled_oscillator.py`

---

## What this plan achieves

Converts the VAE-KL Bayesian-surprise signal into a sparse spiking neural controller. The Mid-Band and High-Band KAN outputs stop producing continuous latent representations and instead gate into discrete spikes. These spikes drive the coupled oscillator asynchronously, maintaining steady-state flight at near-zero compute overhead.

## Firing rule (non-negotiable)

A neuron fires **if and only if** the proposed spike **reduces** the variational free energy — i.e., the VAE-KL divergence between the predictive prior and the incoming sensory state decreases as a result of the spike.

Implementation: compute `ΔF = F_post_spike - F_pre_spike`. Fire if `ΔF < 0`.  
Do NOT use a magnitude threshold. The sign of the gradient is the condition.

## band_vae.py changes

1. After the Mid-Band and High-Band KAN encoders produce `z_mu` and `z_log_var`, compute the current free energy `F = KL(q(z|x) || p(z)) - E[log p(x|z)]`
2. For each latent dimension, propose a spike (discrete activation)
3. Compute the counterfactual free energy `F_spike` with the spike applied
4. Emit spike if `F_spike < F` (free energy reduced); otherwise suppress
5. Output: sparse binary spike tensor, same shape as the continuous latent output it replaces

## coupled_oscillator.py changes

1. Accept sparse spike tensor as input (instead of continuous latent vector)
2. Each spike triggers an asynchronous phase update in the corresponding oscillator
3. Zero spikes → oscillator maintains current phase (near-zero compute)
4. Motor action output is derived from oscillator phase, not from continuous latent integration

## Constraints

- All computation under `torch.no_grad()`
- No new large layers — the KAN encoders already exist; this adds only the spike gating logic
- Spike tensor must be on the same device as the latent tensor (Jetson CUDA)

## Test criteria

- Steady-state: spike rate approaches zero when sensory input is predictable
- Surprise event: spike rate increases proportionally to KL divergence
- Energy: `F_post` < `F_pre` for all fired spikes (verifiable per-sample)
