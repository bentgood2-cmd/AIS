# Decision 0001 — Use FastAPI as the AIS Web Layer

**Date:** 2026 (initial build)  
**Status:** Decided — in production

## Decision

FastAPI serves as the web framework for the AIS system API (`app.py`).

## Alternatives considered

- Flask — synchronous by default; AIS components are all async; would require workarounds
- Django — too heavy; AIS is a pure API with no ORM or template needs
- Raw ASGI (Starlette) — FastAPI is Starlette with automatic schema generation added; no reason to drop down

## Why FastAPI

- Native async/await support matches AIS's async component lifecycle
- Automatic OpenAPI docs at `/docs` without extra work
- Pydantic v2 integration for request/response validation
- Lifespan context manager handles component startup/shutdown cleanly

## Consequences

- All route handlers are async functions
- Request/response models are Pydantic `BaseModel` subclasses
- The `lifespan` parameter on the `FastAPI()` constructor manages startup/shutdown (not the deprecated `app.router.lifespan_context`)
- Uvicorn is the ASGI server; configured via `AIS_HOST`, `AIS_PORT`, `AIS_LOG_LEVEL` env vars
