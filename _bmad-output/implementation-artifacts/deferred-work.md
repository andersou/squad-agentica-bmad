## Deferred from: code review of 1-2-editar-e-concluir-tarefa (2026-10-02)

- `id` de rota fora do intervalo INTEGER do SQLite causa `OverflowError` → 500 (GET e PATCH /tasks/{id}); validar `task_id` com limite (ex.: `Path(le=2**63-1)`) ou tratar como 404.
- `patch_task` lê a tarefa após o update fora da transação; com DELETE (story 1.3) uma exclusão concorrente faria a rota devolver `None` → 500. Tratar `None` como 404.
