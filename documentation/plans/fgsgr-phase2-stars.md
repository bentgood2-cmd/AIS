# Plan — FGSGR Phase 2: STARS Implementation

**Reference:** arXiv:2605.26733 — *Stabilizing Recurrent Dynamics for Test-Time Scalable Latent Reasoning*  
**Status:** Not started  
**File to create/refactor:** `fgsgr/sgr/q_verifier.py`

---

## What this plan achieves

Prevents latent trajectory collapse in `PTRMVerifier` during deep test-time compute loops. The agent can "think longer" on complex physical puzzles without the latent state diverging to NaN. `max_recursion_depth` becomes dynamic.

## Current state (to be replaced)

`PTRMVerifier` injects simple, diminishing Gaussian noise to search local solution basins. `max_recursion_depth` is hard-coded to 8. At depth > 8 or in low-noise regimes, the latent state collapses or diverges.

## STARS implementation

### 1. Random loop sampling

Instead of a single trajectory from the current latent state, sample `K` candidate trajectories by perturbing the initial state with structured noise:

```
z_candidates = [z_0 + ε_k  for k in range(K)]   # ε_k ~ STARS prior
```

### 2. Iterative trajectory stabilisation

For each candidate trajectory, apply the recurrent update rule iteratively:

```
z_{t+1} = f_recurrent(z_t) + λ * (z_target - z_t)
```

where `λ` is the stabilisation coefficient and `z_target` is the best trajectory found so far. This anchors the dynamics without a fixed step limit.

### 3. Convergence criterion (replaces hard depth limit)

Terminate when:
```
||z_{t+1} - z_t||_2 < δ_convergence
```

`δ_convergence` is a configurable hyperparameter (suggested initial value: `1e-4`). This replaces `max_recursion_depth = 8`. There is no fixed maximum — the loop runs until convergence or a wall-clock timeout (separate from depth).

### 4. Q-head uncertainty reduction

After convergence, the Q-head evaluates all `K` trajectories and selects the one with minimum uncertainty. This is the output.

## Constraints

- No gradient tracking — the entire loop runs under `torch.no_grad()`
- `K` (number of candidates) must be tuned for Jetson VRAM — start with K=4
- NaN guard: if any trajectory produces NaN at any step, discard it and continue with remaining candidates. If all K candidates produce NaN, the verifier raises `PTRMDivergenceError`

## Test criteria

- On the hardest test sequences, the verifier reaches a valid answer without hitting depth-8 limit
- No NaN values in Q-head output across all test cases
- Convergence delta decreases monotonically (or the trajectory is discarded)
