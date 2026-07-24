# Decision 0003 — FGSGR 2026 Upgrade: Three-Phase Roadmap (SFEC → STARS → Lagrange MLF)

**Date:** 2026  
**Status:** Decided — implementation in progress

## Decision

The FGSGR framework is upgraded in three sequential phases, each targeting a different probabilistic reasoning block.

## The three phases

### Phase 1 — SFEC (Spiking Free Energy Constrainers)
**Reference:** arXiv:2603.09729  
**Target:** `fgsgr/input/band_vae.py`, `fgsgr/dynamics/coupled_oscillator.py`  
**Replaces:** Continuous VAE-KL Bayesian-surprise signal  
**With:** Sparse spiking neural controller that gates on free-energy reduction

### Phase 2 — STARS (Stabilizing Recurrent Dynamics)
**Reference:** arXiv:2605.26733  
**Target:** `fgsgr/sgr/q_verifier.py`  
**Replaces:** Simple diminishing Gaussian noise search in `PTRMVerifier` + hard-coded depth limit of 8  
**With:** Random loop sampling + iterative trajectory stabilisation + convergence-based depth

### Phase 3 — Lagrange MLF (Energy-Based Safety Lattices)
**Reference:** arXiv:2606.20274  
**Target:** `fgsgr/sgr/lattice_projection.py`, `fgsgr/governance/constraints.py`  
**Replaces:** Static `invariant_lattice` registered-buffer heuristics in `LDTLatticeProjection`  
**With:** Lagrangian physical energy field; kinematic energy envelope as hard abstention boundary

## Why this order

1. SFEC first — reduces power overhead; its sparse spike output is the input signal to STARS and Lagrange
2. STARS second — stabilises the reasoning trajectory that the Lagrange layer then evaluates
3. Lagrange MLF last — the safety layer must operate on the stabilised trajectories from STARS

## Consequences

- `fgsgr/` directory must be created from scratch (it does not exist in the repo)
- `tests/test_agent_step.py` must be created and updated with Phase 3 coverage
- `test_batch_level_isolation` must test Lagrangian energy bounds (not old static integers)
- `test_ldt_explicit_abstention_override` must test kinematic envelope rejection
- All three phases must run within the Jetson Orin Nano VRAM budget
