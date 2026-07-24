# User Context — AIS / FGSGR

## Who the user is

**Brett Goodwin** — Author/PI on the FGSGR project. An engineer/researcher building autonomous edge-AI systems for physical robotics. Works at the intersection of probabilistic reasoning, spiking neural networks, and real-time robotics control. Deploying to constrained hardware (Jetson Orin Nano) in physical environments where software failures have real consequences.

## What they want

A working FGSGR reasoning engine that:
- Runs fully on-board the Jetson Orin Nano with no cloud dependency
- Upgrades the existing Tri-Frequency / VAE-KL / metacognitive grid architecture with the three 2026 paradigms
- Guarantees kinematically safe actions (no drone crashes) through mathematically enforced energy bounds
- Scales reasoning depth dynamically without trajectory collapse or NaN values
- Consumes near-zero additional power during steady-state flight

## What they're trying to avoid

- Heuristic safety invariants that can be bypassed — safety must be mathematically guaranteed, not hoped for
- Latent trajectory collapse during long reasoning chains — the agent must be able to "think longer" on hard problems
- VRAM overflows on the Jetson — every architectural choice must be memory-budget-aware
- Cloud API dependencies — the system must operate in disconnected, contested environments
- Regressions in the existing test suite — the upgrade adds to the system, not breaks it

## What they've tried before

The current FGSGR architecture already has:
- Tri-Frequency Spectral layer (High, Mid, Low bands) with KAN-based processing
- Bayesian-surprise gating via VAE-KL divergence
- 5-state metacognitive grid
- GRAM, PTRM, and LDT reasoning blocks

These work but hit limits: power consumption during Bayesian gating is too high (SFEC fixes this), the verifier collapses at depth > 8 (STARS fixes this), and safety invariants are heuristic integers (Lagrange MLF fixes this).

## How they'll know it's working

- SFEC: steady-state flight with near-zero spiking activity
- STARS: verifier runs to convergence on the hardest test cases without NaN or depth-limit errors
- Lagrange MLF: test_ldt_explicit_abstention_override passes; unsafe manoeuvre commands are blocked at the projection layer
- All existing tests still pass
