# Review (currency / reality-check) - ARCHITECTURE-SPINE.md - 2026-10-06

Verdict: PASS with one real finding (httpx deprecation in the pinned test stack) and minor notes. All pinned versions match PyPI today; all behavioral claims reproduced.

## PyPI check (curl pypi.org/pypi/<pkg>/json, 2026-10-06)
| Pkg | Pinned | PyPI latest | requires_python | 3.14 classifier |
|---|---|---|---|---|
| fastapi | 0.142.2 | 0.142.2 | >=3.10 | yes |
| uvicorn | 0.54.0 | 0.54.0 | >=3.10 | yes |
| pydantic | 2.13.5 | 2.13.5 | >=3.9 | yes (pydantic-core 2.46.5) |
| tzdata | 2026.5 | 2026.5 | >=2 | none declared (pure data, works; IANA 2026e) |
| pytest | 9.1.1 | 9.1.1 | >=3.10 | yes |
| httpx | 0.28.1 | 0.28.1 | >=3.8 | none declared (installs/runs on 3.14) |
| ruff | 0.16.10 | 0.16.10 | >=3.7 | yes |

fastapi 0.142.2 requires pydantic>=2.9.0, starlette>=0.46 (resolved 1.7.0), opentelemetry-api>=1.44 as a base dep (new; not in memlog).

## Experiments (uv run --python 3.14 --with fastapi==0.142.2 --with httpx==0.28.1, /tmp/uvx)
- TestClient works with httpx 0.28.1 without fastapi[standard]: YES. Without any httpx it fails and tells you to install httpx2.
- `list[str] = Query(None)` receives repeated ?tag=a&tag=b -> ['a','b']; absent -> None. CONFIRMED. `tag: str|None` keeps only the last value ('b'), silently. CONFIRMED. Note: FastAPI does not reject >1 itself; AD-6's "mais de um valor é 422" needs explicit code (len check raising 422/RequestValidationError). Spine implies it; implementer must not assume it is automatic.
- Sync endpoint + sync yield dependency thread: same thread in 30 sequential requests (setup, endpoint, teardown). Both run in the anyio worker pool, so under concurrent load they can differ; check_same_thread=False remains the right, cheap guard. Claim is conservative-correct.
- TestClient without `with` does not run lifespan/startup: CONFIRMED (list empty; filled inside `with`). AD-8 rationale holds.
- Pydantic 2.13.5 lax `date` accepts "2026-10-06T00:00:00" from both python dict and JSON: CONFIRMED. `Field(strict=True)` rejects it via JSON and accepts "2026-10-06". Caveat: strict date on a python dict with str input is rejected, so tests must send via TestClient json= (goes through JSON; fine).
- zoneinfo + tzdata package resolves America/Sao_Paulo on 3.14: YES; 01:00 UTC -> 22:00-03:00 previous day. tzdata 2026.5 = IANA 2026e.
- `uv init --package` (uv 0.12.23): creates src/<name>/__init__.py, pyproject with `requires-python = ">=3.14"` (from local interpreter), `[project.scripts] name = "name:main"`, build-backend uv_build, `.python-version`, README.md. Layout claim CONFIRMED. Notes: generated `main` stub in __init__.py and scripts entry must be removed/adjusted since there is no CLI; the seed's `deps: ...` are not generated, they come from `uv add`.
- ruff 0.16.10 runs; `target-version = "py314"` valid.

## Findings
1. [Medium] Stack pins httpx 0.28.1 for TestClient, but the pinned Starlette (1.7.0) emits StarletteDeprecationWarning: "Using httpx with starlette.testclient is deprecated; install httpx2 instead". httpx2 2.13.1 exists on PyPI and works with fastapi.testclient. Spine/memlog never checked this. Decide: pin httpx2 (preferred, no warning) or keep httpx and accept the warning; also if pytest runs with -W error it will fail. Convention row "pytest + fastapi.testclient (httpx)" and Stack row would change.
2. [Low] AD-6 relies on `list[str]` for tag but no auto-422 for multiple values; spec should state the explicit check (reality: FastAPI returns the list).
3. [Low] `uv init --package` boilerplate (`main` stub, script entry, `requires-python >=3.14` pin) should be cleaned; seed comment implies deps are generated.
4. [Info] memlog does not record that fastapi now pulls opentelemetry-api as a base dependency (verified in PyPI metadata); harmless for the demo, noteworthy for "sem [standard]" minimalism.
5. [Info] tzdata and httpx declare no 3.14 classifier; both verified working on 3.14.

Nothing named in the spine is dead or replaced, except httpx's status as the TestClient backend (finding 1).
