# Definition of Done — AIS / FGSGR

_What "done" means for each current work item._

---

## AIS baseline (stable — no active changes planned)

Done = all of these are true:
- `python test_basic.py` and `python test_refactored_ais.py` pass
- `GET /health` returns `{"status": "healthy"}`
- No security regressions (see `SECURITY_FIXES.md` for the baseline)

---

## FGSGR Phase 1 — SFEC

Done when:
- [ ] `fgsgr/input/band_vae.py` exists and implements spike gating on Mid/High-Band KAN output
- [ ] `fgsgr/dynamics/coupled_oscillator.py` accepts sparse spike tensor and drives asynchronous motor phases
- [ ] Firing rule is implemented as a sign-check on free-energy gradient (not a magnitude threshold)
- [ ] Spike rate is near-zero on low-surprise input (verified by test)
- [ ] All computation runs under `torch.no_grad()`
- [ ] No new dependencies beyond `torch` and `numpy`

---

## FGSGR Phase 2 — STARS

Done when:
- [ ] `fgsgr/sgr/q_verifier.py` exists with `PTRMVerifier` implementing STARS
- [ ] `max_recursion_depth` hard-coded limit of 8 is removed
- [ ] Convergence criterion is `||z_{t+1} - z_t||_2 < δ_convergence` (configurable)
- [ ] `PTRMDivergenceError` is raised when all K candidate trajectories produce NaN
- [ ] No NaN in Q-head output on any standard test case
- [ ] Depth reaches > 8 successfully on at least one hard test case

---

## FGSGR Phase 3 — Lagrange MLF

Done when:
- [ ] `fgsgr/sgr/lattice_projection.py` exists with no `invariant_lattice` buffer
- [ ] `fgsgr/governance/constraints.py` defines `KinematicEnvelopeViolation`, airframe constants
- [ ] `validity_mask = 0.0` triggers `KinematicEnvelopeViolation` which terminates execution
- [ ] `tests/test_agent_step.py` exists and both `test_batch_level_isolation` and `test_ldt_explicit_abstention_override` pass
- [ ] Lagrangian energy computation is under `torch.no_grad()`
- [ ] Physical constants are in `constraints.py`, not inlined

---

## Overall upgrade done when

All three phases complete AND `python -m pytest tests/test_agent_step.py -v` shows all tests green AND all existing AIS baseline tests still pass.
