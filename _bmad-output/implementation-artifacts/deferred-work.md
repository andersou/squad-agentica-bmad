# Trabalho adiado

Achados de code review que as stories adiaram. Todos foram fechados em 2026-10-02, no item de ação 3 da retrospectiva da v1 (`epic-2-retro-2026-10-02.md`).

## Da story 1.1 (criar, listar e consultar)

- [x] Um `id` de path acima do INTEGER de 64 bits do SQLite gerava `OverflowError` e devolvia 500. **Corrigido:** `TaskId` usa `Path(alias="id", le=2**63 - 1)`, então o erro sai como 422 `validation_error` com `field: "id"`. Teste: `test_task_id_overflow`.
- [x] O handler de `HTTPException` transformava qualquer status diferente de 404 e 405 em 500. **Corrigido:** agora o status HTTP é mantido, com `code: "http_error"` (AD-7 emendado). Teste: `test_other_http_status_kept`.

## Da story 1.2 (editar e concluir)

- [x] Estouro do `id` de path. É o mesmo item da 1.1, corrigido lá.
- [x] O `patch_task` relia a tarefa fora da transação, e uma exclusão concorrente fazia a rota devolver `None` e dar 500. **Corrigido:** `repo.update_task` confere, grava e relê dentro de uma transação `BEGIN IMMEDIATE` e devolve a tarefa, ou `None`, que vira 404. Teste: `test_patch_deleted_during_update`.

## Da story 1.3 (excluir)

- [x] Estouro do `id` de path em GET, PATCH e DELETE. É o mesmo item da 1.1, corrigido lá.

## Da story 2.1 (tags)

- [x] O `SELECT` que confere se a tarefa existe rodava fora da transação, e um `DELETE` concorrente gerava `IntegrityError` de FK e 500. **Corrigido** pelo mesmo `BEGIN IMMEDIATE` da 1.2.

## Da story 2.2 (janelas de prazo)

- [x] `?due=` repetido valia o último valor em silêncio. **Corrigido:** `?due=` ou `?tag=` repetido dá 422 com `field` igual ao nome do parâmetro (decisão do Anderson na retro; AD-6 emendado). Teste: `test_repeated_query_param`.
- [x] Idioma `(start and start.isoformat())` em `window_bounds`. **Trocado** por `start.isoformat() if start else None`.

## Atalho conhecido (não é dívida aberta)

- `ponytail:` em `app/repo.py`: N+1 em `load_tags`. Basta enquanto não houver paginação e o time for pequeno. Trocar por `SELECT ... WHERE task_id IN (...)` se a lista crescer.
