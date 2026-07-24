# Plan — FGSGR Phase 3: Lagrange MLF Implementation

**Reference:** arXiv:2606.20274 — *Lagrange: An Open-Vocabulary, Energy-Based Sparse Framework*  
**Status:** Not started  
**Files to create/refactor:** `fgsgr/sgr/lattice_projection.py`, `fgsgr/governance/constraints.py`

---

## What this plan achieves

Replaces heuristic safety invariants (static registered-buffer integers in `invariant_lattice`) with physics-backed kinematic energy boundaries. Collision avoidance and safe flight envelopes are guaranteed by mathematics, not by tuned constants.

## Current state (to be removed)

`LDTLatticeProjection` holds a registered buffer `invariant_lattice` containing static integer heuristics. If a proposed graph mutation violates these integers, it is soft-penalised. This can be overridden by sufficiently high-confidence mutations — a safety gap.

## lattice_projection.py changes

### 1. Remove static invariant_lattice

Delete the `self.register_buffer("invariant_lattice", ...)` call and all code that reads from it.

### 2. Map metacognitive grid output to Lagrangian energy field

The 5-state metacognitive grid outputs a continuous latent field `Φ ∈ R^n`. Map this to a physical energy representation:

```
E(Φ) = ½ m ||v(Φ)||² + V(Φ)
```

where:
- `m` = airframe mass (configurable constant from `constraints.py`)
- `v(Φ)` = velocity implied by the proposed graph mutation
- `V(Φ)` = potential energy from the environmental model

### 3. Compute kinetic energy derivative of proposed mutation

For a proposed graph mutation `δG`:

```
ΔKE = E_kinetic(Φ + δG) - E_kinetic(Φ)
```

### 4. Explicit Abstention trigger

```python
if abs(dKE_dt) > self.kinematic_energy_limit:
    validity_mask = 0.0
    raise KinematicEnvelopeViolation(
        f"Proposed mutation implies dKE/dt={dKE_dt:.4f}, "
        f"exceeds limit {self.kinematic_energy_limit:.4f}"
    )
```

`validity_mask = 0.0` is the signal to the governance layer that the projection has failed. The exception must propagate — callers must not catch it and proceed.

## constraints.py changes

Define the physical constants and the `KinematicEnvelopeViolation` exception:

```python
AIRFRAME_MASS_KG = 0.85          # configurable per airframe
MAX_KINETIC_ENERGY_RATE = 12.5   # J/s — kinematically feasible limit
GRAVITY_MS2 = 9.81

class KinematicEnvelopeViolation(Exception):
    """Raised when a proposed action exceeds the airframe's kinematic energy envelope."""
    pass
```

## tests/test_agent_step.py changes

### test_batch_level_isolation

Update to assert that batch-level processing respects Lagrangian energy bounds — a mutation that would violate the energy envelope in one batch item must not leak to other items.

### test_ldt_explicit_abstention_override

Update to:
1. Construct a `LDTLatticeProjection` with a known `kinematic_energy_limit`
2. Feed it a mutation that exceeds the limit
3. Assert `KinematicEnvelopeViolation` is raised
4. Assert `validity_mask == 0.0` was set before the raise
5. Assert the downstream action was NOT executed

## Constraints

- No soft penalties. The raise must terminate execution.
- Physical constants in `constraints.py`, not hard-coded in `lattice_projection.py`
- Energy computation under `torch.no_grad()` — no gradient tracking
- The exception class must be importable from `fgsgr.governance.constraints`
