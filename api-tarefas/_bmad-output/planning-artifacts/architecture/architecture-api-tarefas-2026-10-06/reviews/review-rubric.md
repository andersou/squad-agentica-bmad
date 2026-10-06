# Review (rubrica) — ARCHITECTURE-SPINE api-tarefas

Verdict: sound and right-sized spine that covers FR-1..6 and resolves all four PRD open questions; fix one likely-unimplementable rule (AD-6 strict date) and a few small gaps before epics.

## Findings

1. **HIGH — AD-6 `date` strict probably rejects every valid prazo.** FastAPI (Pydantic v2) validates the already-parsed JSON dict in python mode. In strict python mode a `date` field rejects the string "2026-10-06" (strict date from str only works in JSON mode). The Rule as written may 422 valid input, or the implementer will drop strict and silently accept `2026-10-06T00:00:00`, which is the divergence AD-6 prevents. Fix: state the mechanism, e.g. `prazo: str` with a `mode="before"` validator (regex `^\d{4}-\d{2}-\d{2}$` then `date.fromisoformat`), and make a test for `2026-10-06T00:00:00` and `2026-02-30` mandatory. Verify against the pinned Pydantic before keeping "strict".
2. **MEDIUM — `?tag=` rule is under-specified.** PRD FR-6 requires 422 for empty tag and for >1 tag. AD-6 says `list[str]` and ">1 is 422" but not how (declaring `list[str]` accepts many), and does not say empty `?tag=` is 422 or that the 50-char limit applies. Fix: one sentence: "`tag` is `Query(max_length=1)` list or explicit check; empty after strip = 422; handled by the same function as the body."
3. **MEDIUM — AD-1/AD-2 Rules are enforceable only by reviewer vigilance.** "Respeitar o diagrama" and "única leitura do relógio" have no check. The Estilo convention bans extra ruff config. Fix: either add one test (grep `src/` for `datetime.now|date.today`, and that `domain.py` has no `fastapi|pydantic|sqlite3` import), or allow `ruff` banned-api for those. About 10 lines, makes both ADs verifiable.
4. **MEDIUM — Operational envelope thin and has an unresolved placeholder.** Execução has `--host <ip-interno>` (no port, no default), and NFR-2 (no auth) depends only on that bind. Not decided: DB file location (default `tarefas.db` is cwd-relative, so cwd changes mean "lost" tasks, which breaks NFR-5 in practice), backup of the SQLite file, who restarts the process after reboot. Deferred covers Docker/CI/logging but not these. Fix: fix a default bind (127.0.0.1 unless told) and port, require absolute `TAREFAS_DB` in the run command, and add to Deferred "backup do arquivo e supervisão do processo (systemd etc.)".
5. **LOW — small divergence points.** (a) "Tags voltam na ordem de inserção" but no ORDER BY for tags (add `ORDER BY rowid` to AD-4). (b) Empty PATCH body `{}` not decided (suggest 200 no-op). (c) Who converts domain tag rejection to 422 is vague ("o schema a converte"): say domain raises `ValueError`, schema validator calls it. (d) NFR-2 absent from the capability map.

## Checklist

- Fixes divergence points: yes (tie-break, status codes, limits, strict bool, clock, window logic, tags, conn handling all pinned). Gaps are in finding 5.
- Rules enforceable / prevent stated divergence: AD-2..5, 7, 8 yes. AD-6 see 1 and 2. AD-1 see 3.
- Deferred safe: yes; nothing there lets two units diverge. Add the ops items from 4.
- Named tech verified-current: not verified. FastAPI 0.142.2, uv 0.12, ruff 0.16.10, uvicorn 0.54.0, pytest 9.1.1 post-date my knowledge; the spine gives no verification evidence. Confirm on PyPI before stories pin them. httpx 0.28.1 and Pydantic 2.13.x are plausible.
- Covers spec capabilities: yes, FR-1..6 and NFR-1,3,4,5 mapped; NFR-2 only in AD-7.
- Dimensions decided/deferred: data, API, time, testing, style, docs yes; deployment/ops see 4. Security: none by NFR-2, accepted.
- Form: terse, no template comments, both mermaid diagrams valid. Slight rationale creep in AD-6 and AD-8 ("o modo lax aceitaria...", TestClient/lifespan reasoning). Acceptable, could trim.
- Over-engineering: mostly proportionate. Three modules, one tag table, 8 ADs is on the heavy side for 4 endpoints, but this is a demo of the BMad flow, and each AD pins a real PRD-listed risk. Possible trims: fold AD-4 into AD-7/AD-3, drop `Janela`/`intervalo` indirection only if you accept the tradeoff (no, keep: it's what NFR-3 tests). No change required.
