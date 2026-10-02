## Deferred from: code review of 1-2-editar-e-concluir-tarefa (2026-10-02)

- `id` de rota fora do intervalo INTEGER do SQLite causa `OverflowError` → 500 (GET e PATCH /tasks/{id}); validar `task_id` com limite (ex.: `Path(le=2**63-1)`) ou tratar como 404.
- `patch_task` lê a tarefa após o update fora da transação; com DELETE (story 1.3) uma exclusão concorrente faria a rota devolver `None` → 500. Tratar `None` como 404.

## Deferred from: code review of 1-3-excluir-tarefa (2026-10-02)

- `id` de path maior que o INTEGER de 64 bits do SQLite gera OverflowError → 500 `internal_error` em GET/PATCH/DELETE `/tasks/{id}`. Correção possível: `Path(alias="id", ge=1, le=2**63-1)` no `TaskId` (vira 422 `field: "id"`).
