# Reference — FGSGR Architecture

_Stable reference for the FGSGR reasoning engine. Update this if the architecture changes._

---

## Overview

FGSGR (Frequency-Governed Self-Graph Reasoning) is an on-board edge-AI reasoning engine for autonomous robotic agents. It processes multi-band sensory input, maintains a self-updating graph representation of the world, and outputs physically safe motor commands — all on the NVIDIA Jetson Orin Nano with no cloud dependency.

---

## Signal flow (current architecture, pre-upgrade)

```
Sensor input (raw multi-spectral data)
         │
         ▼
┌────────────────────────────────────┐
│     Tri-Frequency Spectral Layer   │
│  ┌──────────┐ ┌────────┐ ┌──────┐ │
│  │High-Band │ │Mid-Band│ │ Low  │ │
│  │   KAN    │ │  KAN   │ │ Band │ │
│  └────┬─────┘ └───┬────┘ └──┬───┘ │
└───────┼───────────┼─────────┼─────┘
        │           │         │
        └─────┬─────┘         │
              │               │
              ▼               ▼
    VAE-KL Bayesian-    Low-band direct
    surprise gating     motor control
              │
              ▼
   ┌─────────────────────┐
   │  5-State Meta-      │
   │  cognitive Grid     │
   │  [EXPLORE, EXPLOIT, │
   │   CONSOLIDATE,      │
   │   RECOVER, IDLE]    │
   └──────────┬──────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
  GRAM       PTRM       LDT
 (Graph    (Trajectory (Lattice
  Reasoning  Verifier)  Projection)
  & Mutation            │
  Module)    │          │
    │        │          ▼
    │        │   validity_mask
    │        │   (1.0=safe, 0.0=block)
    └────────┴──────────┘
              │
              ▼
        Motor commands
```

---

## Component descriptions

### Tri-Frequency Spectral Layer

| Band | Frequency range | Role |
|------|----------------|------|
| High | Fast-changing signals | Surprise detection, obstacle avoidance |
| Mid | Medium dynamics | Navigation, path planning |
| Low | Slow-changing baseline | Attitude, altitude, station keeping |

High and Mid bands output continuous latent representations → fed into VAE-KL gating (pre-SFEC) or spike gating (post-SFEC).  
Low band outputs directly to motor control for steady-state stability.

### VAE-KL Bayesian-Surprise Gating (pre-SFEC)

A variational autoencoder computes the KL divergence between the predictive prior `p(z)` and the posterior `q(z|x)` given the incoming sensory state. High KL = surprise → triggers deeper reasoning. Low KL = predicted state → pass through.

**Post-SFEC:** replaced by sparse spike gating. See `fgsgr/input/band_vae.py`.

### 5-State Metacognitive Grid

The agent maintains one of five metacognitive states:

| State | Meaning |
|-------|---------|
| EXPLORE | Low confidence; gather new information |
| EXPLOIT | High confidence; execute known-good plan |
| CONSOLIDATE | Integrating new information into graph |
| RECOVER | Error state; seeking safe return to known region |
| IDLE | No active task; maintain position |

State transitions are governed by the GRAM + PTRM outputs and the current energy level.

### GRAM (Graph Reasoning & Mutation Module)

Maintains the agent's world model as a self-graph. Proposes mutations (additions, deletions, edge weight updates) in response to metacognitive state and sensory surprises. Outputs proposed `δG` (graph mutation) to LDT for safety validation.

### PTRM (Probabilistic Trajectory Reasoning Module) / PTRMVerifier

Verifies that a proposed trajectory (implied by the graph mutation) is reachable given the current world model. Currently uses diminishing Gaussian noise search with `max_recursion_depth = 8`.

**Post-STARS:** uses random loop sampling + convergence-based depth. See `fgsgr/sgr/q_verifier.py`.

### LDT (Lattice Decision Transformer) / LDTLatticeProjection

Projects proposed graph mutations onto a safe action lattice. Currently uses static `invariant_lattice` integer heuristics.

**Post-Lagrange MLF:** uses a Lagrangian physical energy field. `validity_mask = 0.0` is a hard abstention that blocks execution. See `fgsgr/sgr/lattice_projection.py`.

---

## Key invariants

1. Spike fires ↔ free energy decreases (post-SFEC)
2. Trajectory depth is convergence-based, not fixed (post-STARS)
3. `validity_mask = 0.0` always terminates execution immediately (post-Lagrange MLF)
4. All inference runs under `torch.no_grad()`
5. No module in `fgsgr/` makes network calls
