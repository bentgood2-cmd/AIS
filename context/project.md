# Project Context — AIS / FGSGR

## What we're building

Two interrelated systems that form a single intelligence stack for autonomous edge robotics:

**AIS (Autocatalytic Intelligence System) v3.2.1** — a Python web-API platform that provides the orchestration brain. Five modular cognitive components (Operational, Regulatory, Optimization, Adaptive, Identity) are exposed over a FastAPI server with health monitoring, metrics collection, and an optional PyQt6 GUI. This layer runs today.

**FGSGR (Frequency-Governed Self-Graph Reasoning)** — an on-board edge-AI reasoning engine that governs the physical actions of robotic agents (e.g., decentralised drone swarms). FGSGR runs directly on the NVIDIA Jetson Orin Nano and is currently being upgraded with three 2026 research paradigms (SFEC, STARS, Lagrange MLF) to improve thermodynamic efficiency, recursion depth, and kinematically guaranteed safety.

## Why it matters

Current autonomous drone systems either require cloud connectivity for reasoning (unacceptable for contested or latency-sensitive environments) or operate on fixed heuristics that cannot adapt to novel physical situations. FGSGR closes this gap: a self-graph reasoning engine that runs entirely on-board, updates its world model in real time, and guarantees safe physical actions through mathematically enforced energy bounds.

## The shape of "done" (current phase)

The 2026 upgrade is complete when:
1. **Phase 1 (SFEC)** — `fgsgr/input/band_vae.py` and `fgsgr/dynamics/coupled_oscillator.py` implement sparse spiking free-energy constrainers; power consumption in steady-state flight is near-zero
2. **Phase 2 (STARS)** — `fgsgr/sgr/q_verifier.py` implements stabilised recurrent dynamics; `max_recursion_depth` is dynamic; no NaN explosions during deep test-time compute
3. **Phase 3 (Lagrange MLF)** — `fgsgr/sgr/lattice_projection.py` and `fgsgr/governance/constraints.py` implement energy-based safety lattices; `validity_mask = 0.0` physically prevents unsafe manoeuvres
4. `tests/test_agent_step.py` covers all three phases with updated unit tests

## What we're NOT building

- Cloud-hosted inference or model serving
- GPU server deployments — target is Jetson Orin Nano only
- A general-purpose robotics SDK — this is purpose-built for drone swarm autonomy
- A user-facing product — this is a research and engineering system
- New AIS API endpoints beyond what's documented — the web layer is stable
