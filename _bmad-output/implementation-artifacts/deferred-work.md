## Deferred from: code review of 1-2-editar-e-concluir-tarefa (2026-10-02)

- `id` de rota fora do intervalo INTEGER do SQLite causa `OverflowError` → 500 (GET e PATCH /tasks/{id}); validar `task_id` com limite (ex.: `Path(le=2**63-1)`) ou tratar como 404.
- `patch_task` lê a tarefa após o update fora da transação; com DELETE (story 1.3) uma exclusão concorrente faria a rota devolver `None` → 500. Tratar `None` como 404.

## Deferred from: code review of 1-3-excluir-tarefa (2026-10-02)

- `id` de path maior que o INTEGER de 64 bits do SQLite gera OverflowError → 500 `internal_error` em GET/PATCH/DELETE `/tasks/{id}`. Correção possível: `Path(alias="id", ge=1, le=2**63-1)` no `TaskId` (vira 422 `field: "id"`).

## Deferred from: code review of 2-1-etiquetar-tarefas-e-filtrar-por-tag (2026-10-02)

- `update_task` confere a existência com `SELECT` fora da transação (o sqlite3 só abre `BEGIN` implícito antes de DML); um `DELETE` concorrente entre a checagem e o `replace_tags` gera `IntegrityError` de FK → 500 em vez de 404. Correção possível: `conn.execute("BEGIN IMMEDIATE")` no início ou tratar `IntegrityError` como 404.
