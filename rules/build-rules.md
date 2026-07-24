# Build Rules — AIS / FGSGR

_What the AI will and won't do on this project. Every session, every change._

---

## Rule 1 — Run setup before touching ais.*

`ais/` is generated, not committed. Run `python setup_ais.py` to create it. Never edit files under `ais/` directly — edit the corresponding `.py.txt` template in the project root.

**Why:** The generated directory is the deployed form; the template is the source of truth.

---

## Rule 2 — The SFEC spike condition is a sign-check

A FGSGR neuron fires if and only if the spike **reduces** the VAE-KL divergence between the predictive prior and the incoming sensory state. Implement as a check on the sign of the free-energy gradient. A heuristic threshold is wrong and must not be used.

**Why:** The mathematical constraint is the physical meaning. A threshold would fire on magnitude, not direction — that violates the Free Energy Principle.

---

## Rule 3 — Lagrange abstention is a hard failure

When `validity_mask = 0.0` in `LDTLatticeProjection`, execution must terminate entirely. Raise an exception or return a sentinel that the caller is required to check. No soft penalties, no degraded output, no logged warning that proceeds anyway.

**Why:** This is a physical safety guarantee. A drone manoeuvre that exceeds the kinematic energy envelope must never execute, regardless of other system state.

---

## Rule 4 — STARS recursion depth is convergence-based

Do not reintroduce any fixed upper bound on `max_recursion_depth` in `PTRMVerifier`. The current hard-coded limit of 8 is being removed. Use convergence criteria (e.g., latent state delta below a threshold) to terminate the loop.

**Why:** The whole point of STARS is to allow the agent to "think longer" on hard problems. A fixed depth reintroduces exactly the limitation we're removing.

---

## Rule 5 — Sanitize every logged external value

```python
def sanitize_log_input(value: Any) -> str:
    log_str = str(value)
    log_str = re.sub(r'[\r\n]', ' ', log_str)
    return log_str[:200] + "..." if len(log_str) > 200 else log_str
```

Every value from outside the system (user input, sensor data, external requests) must pass through this function before appearing in any log statement. The equivalent `sanitize_for_logging` variant in `app.py`/`metrics.py` is also acceptable.

**Why:** Log injection (CWE-117) is a real vulnerability. The fix is already applied to `process.py`, `middleware.py`, `app.py`, and `metrics.py`. New code must replicate the pattern.

---

## Rule 6 — Specific exceptions only

Never use bare `except Exception` in new code. Never return internal error details in HTTP responses. HTTP 500s use:

```python
raise HTTPException(status_code=500, detail="<generic message>")
```

Log the real error internally.

**Why:** Bare catches hide bugs. Leaking internal details in HTTP responses is an information-disclosure vulnerability.

---

## Rule 7 — No live backpropagation in forward()

All FGSGR `forward()` methods run under `torch.no_grad()`. No gradient tracking during inference.

**Why:** The Jetson Orin Nano has a fixed VRAM budget. Gradient tapes allocated during inference will exhaust it. There is also no training step at runtime — backprop in forward() is always a bug here.

---

## Rule 8 — Timezone-aware datetimes everywhere

Always `datetime.now(timezone.utc)`. Never `datetime.now()` (naive).

**Why:** Naive datetimes cause silent comparison bugs when timestamps cross timezone boundaries. Already fixed across the codebase; don't reintroduce.

---

## Rule 9 — Component registration before submission

```python
# At module level — register once
process_manager.register_process("name", create_task_process("name", handler))

# At call time — submit
process_id = await process_manager.submit_process("name", priority=ProcessPriority.HIGH)
```

New request types go in `component_map` inside `AISSystem.__init__`, not inside `process_request()`.

**Why:** Pre-registration enables consistent priority queuing and retry configuration. Adding routing logic to `process_request()` creates untestable branching.

---

## Rule 10 — fgsgr/ is built from scratch

`fgsgr/` does not exist in the repo. When implementing, create the full directory tree following the exact paths from the upgrade PDF. Do not approximate or reorganise the module structure.

**Why:** The test file (`tests/test_agent_step.py`) and the CLAUDE.md routing table both reference exact paths. Diverging paths break both.
