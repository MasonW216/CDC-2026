# Backend Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish and honestly verify the prototype FastAPI backend while isolating production-model work that is blocked on the EDA/data/model gates.

**Architecture:** Keep `stormroute_api` as a transport layer and keep scoring formulas in `stormroute.scoring`. Three independent streams harden the current prototype: response contracts/errors, offline artifact/readiness behavior, and production serving/deployment. A final integration stream resolves the replay semantics decision and runs the complete gates. The trained-model service remains a separate, explicitly blocked milestone.

**Tech Stack:** FastAPI, Pydantic v2, httpx, Uvicorn, pytest, Ruff, mypy, Vite/React.

**Spec:** `docs/build_guide.md` §13 and `docs/issue_backlog.md` issue #18; prototype wire contract `docs/prototype_score_spec.md`.

## Global Constraints

- Do not duplicate scoring formulas in the API layer; use `stormroute.scoring`.
- Cached demo mode must work with network access disabled.
- CORS is an explicit origin allowlist; never use `*`.
- County FIPS remain five-character strings and timestamps remain timezone-aware UTC.
- Never expose secrets or upstream credentials in responses or logs.
- Every change is test-first: observe a focused failing test before implementation.
- Do not claim the calibrated model contract until Milestones 3–4 produce a validated artifact.

## Review Focus

- A configured scenario whose artifact is missing or malformed must not appear as ready, and its health status must agree with the endpoint that actually serves it.
- A `cached_replay` request must have one documented meaning (historical Helene or contemporary saved replay), and tests/docs/frontend must agree.
- OpenAPI must describe the prototype response shapes, not unrestricted `dict[str, Any]` objects.
- Network failure, timeout, malformed cache JSON, and unhandled exceptions must produce bounded, secret-free, consistent JSON errors.
- A production build must serve the frontend and API together without relying on a localhost URL baked into the bundle.

### Task 1: Reconcile prototype replay and readiness artifacts (parallel stream A)

**Files:**
- Modify: `backend/src/stormroute_api/config.py`, `backend/src/stormroute_api/routes/health.py`, `backend/src/stormroute_api/routes/scenarios.py`
- Test: `backend/tests/test_health.py`, `backend/tests/test_demo_scenario.py`, `backend/tests/test_score_contract.py`
- Modify: `configs/demo.yaml`, `docs/demo_runbook.md`, `backend/README.md` only after the contract decision is recorded

**Interfaces:**
- Consumes: the existing Helene artifact and saved-trip replay path.
- Produces: one readiness predicate reused by `/health` and `/api/v1/scenarios`; an explicit `cached_replay` contract.

- [ ] Record the ruling: `cached_replay` means contemporary saved replay, or make it mean the Helene artifact. Update frontend, docs, and tests together; do not silently change one endpoint.
- [ ] Add failing tests for no-network POST replay, corrupt/missing artifacts, and health/list agreement.
- [ ] Implement shared artifact validation and readiness; ensure list endpoints never advertise an artifact that detail cannot serve.
- [ ] Fill runbook expected values and document the offline rehearsal command/result.
- [ ] Run `.venv/bin/pytest -q backend/tests/test_health.py backend/tests/test_demo_scenario.py backend/tests/test_score_contract.py` and the full suite.

### Task 2: Add typed prototype response contracts and error envelope (parallel stream B)

**Files:**
- Modify: `backend/src/stormroute_api/schemas.py`, `backend/src/stormroute_api/routes/score.py`, `backend/src/stormroute_api/routes/scenarios.py`, `backend/src/stormroute_api/routes/methodology.py`, `backend/src/stormroute_api/main.py`
- Test: `backend/tests/test_openapi_contract.py`, `backend/tests/test_score_contract.py`, `backend/tests/test_request_context.py`

**Interfaces:**
- Consumes: `prototype-score/1` payloads emitted by `stormroute.scoring.trip` and `historical_case_study`.
- Produces: Pydantic response models and `response_model=` declarations for the five canonical endpoints; one JSON error shape containing request ID, code, and message.

- [ ] Write failing OpenAPI assertions that score, scenarios, and methodology responses reference named schemas and that 422/502/503 errors share the envelope.
- [ ] Define models that validate the current prototype wire contract without reimplementing score calculations; use nested typed models where stable and constrained fields for evolving factor payloads.
- [ ] Add exception handlers for validation, `HTTPException`, and unhandled errors; sanitize upstream messages and preserve `X-Request-ID`.
- [ ] Add tests proving no URL, token, request body, or provider exception detail leaks into responses/logs.
- [ ] Run targeted tests, `ruff check`, `ruff format --check`, and `mypy`.

### Task 3: Bound live requests and harden cache/provider failure behavior (parallel stream C)

**Files:**
- Modify: `backend/src/stormroute_api/config.py`, `backend/src/stormroute_api/routes/score.py`, `backend/src/stormroute_api/routes/routing.py`, `src/stormroute/routing/client.py`, `src/stormroute/scoring/live_forecast.py`
- Test: `backend/tests/test_routing.py`, `backend/tests/test_score_contract.py`, `tests/routing/test_client.py`, `tests/scoring/test_prototype_real_data.py`

**Interfaces:**
- Consumes: existing per-provider httpx timeouts and cache directories.
- Produces: a configured end-to-end request deadline and deterministic fallback/error behavior for timeout, malformed cache, and provider outage.

- [ ] Add failing tests for a blocked cached replay POST, malformed cached JSON, provider timeout, and request deadline exceeded.
- [ ] Add a settings-driven deadline that is shorter than the frontend abort window; map deadline/provider failures to the shared error envelope.
- [ ] Make cache reads validate JSON/schema before use and distinguish cached provenance from live provenance.
- [ ] Decide whether routing preview is allowed to fail live or must use a cached route, then test that decision.
- [ ] Measure warm cached p50/p95 latency and record the result in the runbook.

### Task 4: Serve the built frontend as one production service (parallel stream D)

**Files:**
- Modify: `backend/src/stormroute_api/main.py`, `frontend/vite.config.ts`, `.env.example`, `Makefile`
- Create/modify: `backend/tests/test_static_serving.py`, deployment documentation, and a production smoke script if needed

**Interfaces:**
- Consumes: `frontend/dist` generated by `npm run build`.
- Produces: `/` and static assets served by FastAPI, API routes remaining ahead of the SPA fallback, and a documented production start command.

- [ ] Add failing smoke tests for `/`, a static asset, and an unknown client-side route after building the frontend.
- [ ] Mount `frontend/dist` only when present; keep API/docs/health routes reachable and return a clear startup/readiness failure when absent.
- [ ] Ensure production builds use same-origin API defaults rather than `.env` localhost values.
- [ ] Add a non-reload production command and run the integrated API/frontend smoke test.

### Task 5: Complete release evidence and decide the model boundary (serial integration gate)

**Files:**
- Modify: `docs/demo_runbook.md`, `backend/README.md`, `README.md`, `scripts/verify_repository.py`, CI/deployment docs as needed
- Review: `artifacts/models/model_manifest.json`, `docs/model_card.md`, `docs/responsible_ai.md`

**Interfaces:**
- Consumes: outputs and test evidence from Tasks 1–4.
- Produces: an honest Milestone 6 status and a separate blocked-work list for model/data services.

- [ ] Run `make lint`, `make test`, `make verify`, frontend build, offline rehearsal, and production smoke test.
- [ ] Fix the known frontend `act` import failure before calling the repository gate green.
- [ ] Implement `make verify` checks for artifact checksums/placeholders or explicitly remove stale claims that it does so.
- [ ] Record which model-dependent requirements remain blocked: trained artifact, model/data versions, calibrated score fields, and model service loading.
- [ ] Request one fresh whole-branch code review; resolve Critical/Important findings and rerun all gates.

## Deliberately Deferred Until Model/Data Gates Close

The following are not efficient parallel prototype tasks because their interfaces depend on Milestones 3–4: `model_service.py`, `weather_service.py` as a production adapter, `route_service.py`/`cache_service.py` as generalized service objects, calibrated model response fields, model checksum verification, and production model/data versioning. Scaffold them only after the feature table, trained artifact, calibration results, and adoption rule exist.
