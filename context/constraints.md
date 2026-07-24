# Constraints — AIS / FGSGR

## Hardware

| Constraint | Detail |
|-----------|--------|
| Target platform | NVIDIA Jetson Orin Nano — this is the only deployment target for FGSGR |
| VRAM budget | Strictly limited. No large feed-forward layer depths, no parallel routing matrices, no ops that saturate memory bandwidth |
| CPU | ARM-based. No x86-specific optimisations |
| Network | Must operate fully offline. No cloud API calls in any FGSGR module |

## Software dependencies

| Constraint | Detail |
|-----------|--------|
| Allowed | `torch`, `numpy`, standard Python math (math, cmath, statistics) |
| Not allowed | Any cloud SDK, any external inference API, any library that requires internet at runtime |
| Python | 3.8+ |
| Torch mode | `torch.no_grad()` must wrap all `forward()` calls — no live backpropagation during inference |

## Architecture constraints

| Constraint | Detail |
|-----------|--------|
| Spike firing rule | SFEC: a neuron fires if and only if the spike reduces the VAE-KL divergence. Sign-check on gradient — not a threshold |
| Abstention | Lagrange MLF: `validity_mask = 0.0` must be a hard mathematical failure that terminates execution. No soft penalties |
| Recursion depth | STARS: `max_recursion_depth` must be dynamic (convergence-based). No fixed upper bound |
| Async | All AIS component methods are async. No synchronous blocking calls in `process()` or `initialize()` |

## Time and scope

| Constraint | Detail |
|-----------|--------|
| Upgrade phases | Three phases in order: SFEC → STARS → Lagrange MLF |
| Test coverage | `tests/test_agent_step.py` must be updated for Phase 3 (`test_batch_level_isolation`, `test_ldt_explicit_abstention_override`) |
| Regressions | All existing AIS tests must continue to pass after each phase |

## What we won't compromise on

- Mathematical correctness of the spike firing condition (SFEC)
- The hard-failure nature of Lagrange abstention — this is a physical safety guarantee
- VRAM efficiency — the Jetson has no headroom for bloat
- Log injection protection — `sanitize_log_input()` on all user-controlled log data
- Timezone-aware datetimes — `datetime.now(timezone.utc)` everywhere

## What we will compromise on

- GUI polish — the PyQt6 interface is functional, not beautiful
- AIS API completeness — the five components cover the current scope; no new endpoints needed
- Documentation depth for the AIS layer — it's stable; focus is FGSGR
