# Verification Checks — AIS / FGSGR

_Run these before calling any change done. "The AI said it works" is not evidence._

---

## AIS baseline checks (run after any change to app.py, health.py, metrics.py, middleware.py, process.py)

- [ ] `python setup_ais.py` completes without errors (if `ais/` does not exist)
- [ ] `python test_basic.py` passes — import + component lifecycle
- [ ] `python test_refactored_ais.py` passes — full integration
- [ ] `python test_system.py` passes — lightweight smoke test
- [ ] `python test_core_only.py` passes — no GUI dependency
- [ ] `python app.py` starts without errors; `GET http://localhost:8000/health` returns `{"status": "healthy", ...}`
- [ ] No new bare `except Exception` blocks introduced
- [ ] No new `datetime.now()` without `timezone.utc`
- [ ] Every new log statement with external data uses `sanitize_log_input()`

## FGSGR checks (run after any change to fgsgr/)

- [ ] `python -m pytest tests/test_agent_step.py -v` passes
- [ ] All `forward()` methods verified to run under `torch.no_grad()` — check with `torch.is_grad_enabled()` assertion
- [ ] No network calls in any FGSGR module — grep for `requests`, `httpx`, `aiohttp`, `urllib`
- [ ] VRAM usage measured on Jetson-equivalent; no OOM on standard test sequences

## Phase-specific checks

### Phase 1 — SFEC

- [ ] Spike rate approaches zero on predictable (low-surprise) input sequences
- [ ] Spike rate increases proportionally to KL divergence on surprise events
- [ ] For all fired spikes: `F(z_post_spike) < F(z_pre_spike)` (free energy reduced)
- [ ] Coupled oscillator maintains phase correctly when spike rate is zero

### Phase 2 — STARS

- [ ] Verifier runs to convergence on hardest test sequences without hitting any depth cap
- [ ] No NaN values in Q-head output across all test cases
- [ ] Convergence delta decreases monotonically per trajectory (or the trajectory is discarded)
- [ ] `PTRMDivergenceError` raised when all K candidates produce NaN

### Phase 3 — Lagrange MLF

- [ ] `test_ldt_explicit_abstention_override` passes — unsafe command raises `KinematicEnvelopeViolation`
- [ ] `test_batch_level_isolation` passes — energy violation in one batch item does not affect others
- [ ] `validity_mask == 0.0` is set before any exception is raised
- [ ] No static `invariant_lattice` buffer present in `LDTLatticeProjection`
- [ ] Physical constants (`AIRFRAME_MASS_KG`, `MAX_KINETIC_ENERGY_RATE`) live in `constraints.py`, not inlined

---

## Edge cases to test

- Empty input / zero-length sensory stream
- All-zero latent vector (degenerate case)
- Maximum-surprise input (all KL divergence maximised)
- Proposed mutation that exactly hits the kinematic energy limit (boundary case)
- K=1 candidate all produce NaN (STARS fallback)
- Rapid state transitions between all 5 metacognitive states

---

## What "found one thing wrong" means

If verification finds zero issues on the first pass, you didn't look hard enough. AI-built code almost always has at least one subtle bug, wrong default, or edge case. Finding it is what separates "shipped" from "good enough to keep."
