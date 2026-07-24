# Feedback Log — AIS / FGSGR

_What we've learned. Each entry makes the next build better._

---

## Entry 001 — 2026-07 — Security review and fixes applied

**What happened:** A security review identified 50+ issues across the AIS codebase.

**What we learned:**
- Log injection (CWE-117) was present in every module that logged user-controlled data. Fix: `sanitize_log_input()` wrapper — now a build rule.
- Naive `datetime.now()` was used throughout. Fix: `datetime.now(timezone.utc)` — now a build rule.
- `python-multipart < 0.0.7` had a ReDoS vulnerability. Fix: pinned to `>=0.0.7`.
- `scikit-learn < 1.5.0` had a data leakage vulnerability. Fix: pinned to `>=1.5.0`.
- The deprecated `app.router.lifespan_context` was in use. Fix: `lifespan` parameter on `FastAPI()` constructor.

**Rules updated:** Rules 5 and 8 in `rules/build-rules.md` encode these permanently.

**Full list of fixes:** See `SECURITY_FIXES.md`.

---

## Entry 002 — 2026-07 — Build Kit scaffold provisioned

**What happened:** CLAUDE.md created using the five-phase Build Kit methodology. Full project scaffold (`context/`, `rules/`, `documentation/`, `verification/`, `feedback/`) provisioned.

**What we learned:**
- The AIS `ais/` directory is generated, not committed. This is a common source of confusion — new AI sessions try to edit non-existent files. CLAUDE.md Phase 1 and Rule 1 now explicitly warn about this.
- The `fgsgr/` directory also doesn't exist yet. Every plan file now has a "not started" status marker so the state is immediately clear.
- The Build Kit's five-phase structure works well for this project: Context captures the Jetson constraints clearly, Rules encode the three non-negotiable FGSGR invariants, Documentation captures the three upgrade plans.

**Next session start:** Read CLAUDE.md routing table first, then the relevant plan file.

---

## Entry 003 — (next session will fill this in)

Template for the next feedback entry:

**What happened:**  
**What we learned:**  
**Rules updated (if any):**  
**Definition of done updated (if any):**
