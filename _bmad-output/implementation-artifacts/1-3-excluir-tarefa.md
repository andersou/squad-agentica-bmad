# Story 1.3: Excluir tarefa

Status: ready-for-dev

<!-- Nota: a validação é opcional. Rode validate-create-story para checar a qualidade antes do dev-story. -->

## Story

Como dev do time-piloto,
quero excluir uma tarefa registrada por engano ou que não vale mais,
para que ela não polua as listagens.

## Acceptance Criteria

1. **Dado** uma tarefa existente, **quando** o dev faz `DELETE /tasks/{id}`, **então** recebe **204, sem corpo** (corpo vazio, sem `null` nem `{}`). (FR4, AD-6)
2. **E**, depois disso, `GET /tasks/{id}` dá **404** com `{"error": {"code": "not_found", "field": "id", ...}}`, e a tarefa **não aparece** em `GET /tasks`; as outras tarefas continuam lá, na ordem do AD-6. (FR4, AD-6, AD-7)
3. **Dado** um `id` que não existe, inclusive o de uma tarefa já excluída (segundo `DELETE` no mesmo `id`), **quando** o dev faz `DELETE /tasks/{id}`, **então** recebe **404** com `code: "not_found"` e `field: "id"`, no envelope do AD-7. (FR4, NFR3, AD-7)
4. (Derivado do contrato existente, não é AC novo do épico) `DELETE /tasks/abc` (id não inteiro) dá 422 com `code: "validation_error"` e `field: "id"`, pelo mesmo caminho de validação do `GET /tasks/{id}` da 1.1. (AD-7)
5. `uv run ruff check`, `uv run ruff format --check` e `uv run pytest` passam, incluindo toda a suíte das stories 1.1 e 1.2. (Convenções de qualidade)

## Tasks / Subtasks

- [ ] **Task 1: `repo.delete_task` (AC: 1, 3)**
  - [ ] 1.1 Em `app/repo.py`, criar `delete_task(conn, task_id) -> bool` que executa `DELETE FROM tasks WHERE id = ?` dentro de `with conn:` e devolve `cursor.rowcount == 1`.
  - [ ] 1.2 Não apagar `task_tags` à mão: o `ON DELETE CASCADE` do AD-5 faz isso, desde que a conexão venha de `repo.connect()` (que ativa `PRAGMA foreign_keys = ON`, AD-10).
- [ ] **Task 2: rota `DELETE /tasks/{id}` (AC: 1, 3, 4)**
  - [ ] 2.1 Em `app/api.py`, adicionar a rota `def` (não `async def`) `DELETE /tasks/{task_id}` com `status_code=204`, recebendo a conexão por `Depends(get_db)`, com o mesmo nome/tipo de parâmetro de path usado no `GET`/`PATCH /tasks/{id}` (para o `field` sair `"id"`).
  - [ ] 2.2 Se `delete_task` devolver `False`, levantar o 404 de tarefa **pelo mesmo helper/mecanismo** que o `GET /tasks/{id}` da 1.1 usa (o que produz `field: "id"`). Não criar outro.
  - [ ] 2.3 No sucesso, devolver `Response(status_code=204)` (ou equivalente que garanta corpo vazio). Não declarar `response_model`.
- [ ] **Task 3: testes em `tests/test_tasks.py` (AC: 1, 2, 3, 4)**
  - [ ] 3.1 Teste: cria duas tarefas, exclui uma → 204 e `response.content == b""`; `GET /tasks/{id}` → 404 `not_found`/`id`; `GET /tasks` traz só a outra.
  - [ ] 3.2 Teste: `DELETE` em `id` inexistente (ex.: 999) → 404 `not_found`/`id`; segundo `DELETE` no mesmo `id` já excluído → 404 `not_found`/`id`.
  - [ ] 3.3 Teste: `DELETE /tasks/abc` → 422 `validation_error`/`id`.
  - [ ] 3.4 Usar só a fixture `client` de `tests/conftest.py`; conferir `code` e `field`, nunca o texto de `message` (AD-7, AD-8).
- [ ] **Task 4: regressão e qualidade (AC: 5)**
  - [ ] 4.1 Procurar nos testes da 1.1 algum caso que use `DELETE /tasks/{id}` como exemplo de 405; se existir, trocar por outro método não suportado (ex.: `PUT /tasks/{id}` ou `DELETE /tasks`) para manter a cobertura do 405.
  - [ ] 4.2 Rodar `uv run ruff check`, `uv run ruff format --check` e `uv run pytest`.

## Dev Notes

### Contexto e dependências

- Esta story só **acrescenta** uma rota e uma função de repo. Tudo o mais vem da Story 1.1: projeto `uv`, `app/main.py` com os três handlers do AD-7, `app/api.py` com `get_db()`, `app/repo.py` com `connect()` e o esquema completo do AD-5 (`tasks` + `task_tags` com `ON DELETE CASCADE`), e `tests/conftest.py` com a fixture `client`. [Fonte: epics.md#Story 1.1; ARCHITECTURE-SPINE.md#AD-5, #AD-8, #AD-10]
- Não depende da 1.2 (o relatório de prontidão confirma: "A 1.2 não depende da 1.3"). Se a 1.2 já tiver sido implementada, reaproveitar também o padrão de 404 dela. [Fonte: implementation-readiness-report-2026-10-02.md#Dependências]
- **Inteligência da story anterior indisponível:** as stories 1.1 e 1.2 estão sendo criadas em paralelo e ainda não há código no repositório (greenfield). Antes de começar, o dev deve **ler o código real** de `app/api.py`, `app/repo.py`, `app/main.py` e `tests/conftest.py` e seguir os nomes e helpers que existirem (nome do parâmetro de path, helper de 404, nome de `get_db`).

### Arquivos a tocar (todos UPDATE, nenhum NEW)

| Arquivo | Estado esperado após a 1.1/1.2 | O que esta story muda | O que preservar |
| --- | --- | --- | --- |
| `app/repo.py` | `connect()`, esquema, `create`/`list`/`get` (+ `update` da 1.2) | adiciona `delete_task` | `connect()` intacto; nenhum `DELETE` fora daqui |
| `app/api.py` | rotas `POST`, `GET` (lista e item), `PATCH`; `get_db()` | adiciona a rota `DELETE` | rotas e schemas existentes |
| `tests/test_tasks.py` | testes da 1.1/1.2 | adiciona os testes da exclusão | testes existentes (só ajustar o caso de 405, se usar `DELETE`) |

`app/main.py` e `tests/conftest.py` **não** devem mudar. `app/domain.py` não participa (exclusão não tem regra de domínio).

### Guardrails técnicos

- **Camadas (spine):** `api → repo`; o SQL fica só em `repo`, a rota não monta SQL. [Fonte: ARCHITECTURE-SPINE.md#Design Paradigm]
- **Uma instrução, sem SELECT antes:** `DELETE ... WHERE id = ?` + `rowcount` decide 204 ou 404 de forma atômica. Não fazer `get` e depois `delete` (corrida e consulta a mais).
- **Transação (AD-10):** a exclusão toca mais de uma linha quando há tags (cascata em `task_tags`), então roda dentro de `with conn:`. Além disso, no modo de transação padrão do `sqlite3` (legado), sem `with conn:`/`commit()` o `DELETE` **não é persistido** ao fechar a conexão.
- **Cascata depende do PRAGMA:** `ON DELETE CASCADE` só funciona com `PRAGMA foreign_keys = ON`, ativado em `repo.connect()`. Nunca abrir conexão por outro caminho. A verificação da cascata com tags é critério da Story 2.1, não desta. [Fonte: epics.md#Story 2.1; implementation-readiness-report#FR4]
- **204 sem corpo:** no FastAPI 0.142, devolver `Response(status_code=204)` é o jeito explícito de garantir corpo vazio. Não retornar `{}` nem a tarefa excluída.
- **Erros (AD-7):** o 404 de tarefa sai com `field: "id"`; o 422 de path vem do handler de `RequestValidationError` com `loc` `["path", "<nome do parâmetro>"]` → `field` sem o prefixo. Para dar `"id"`, o parâmetro de path precisa se chamar `id` ou ter `alias="id"`, conforme a 1.1 definiu. Nenhum `{"detail": ...}`.
- **Rota síncrona:** `def`, não `async def` (AD-10).
- **Sem dependências novas** (AD-1). Sem soft delete, sem campo `deleted_at`: a exclusão é física (FR4: 404 depois).

### Testes

- pytest + `TestClient` pela fixture `client` (banco novo em `tmp_path` via `TASKS_DB_PATH`). Não redefinir fixtures. [Fonte: ARCHITECTURE-SPINE.md#AD-8]
- Conferir só `code` e `field` do envelope; `message` é livre (em português).
- Não precisa de `set_now`: a exclusão não depende do relógio.

### Project Structure Notes

- Estrutura conforme o Structural Seed do spine: `app/{main,api,domain,repo}.py`, `tests/{conftest,test_tasks,test_filters}.py`. Os testes desta story vão em `tests/test_tasks.py`.
- Nenhum conflito detectado entre epics, PRD e spine para esta story.

### Questões em aberto (registradas sem bloquear)

1. O nome do parâmetro de path (`id` ou `task_id` com `alias="id"`) e o helper de 404 são definidos na 1.1; esta story assume que existem e devem ser reutilizados.
2. O AC 4 (422 para `id` não inteiro) é derivado do AD-7, não está escrito no épico. Se a 1.1 tiver escolhido outro comportamento para `GET /tasks/abc`, seguir o mesmo e ajustar o teste 3.3.
3. Excluir uma tarefa concluída ou com prazo vencido não tem regra especial no PRD; assume-se que qualquer tarefa pode ser excluída.

### References

- [Fonte: _bmad-output/planning-artifacts/epics.md#Story 1.3: Excluir tarefa]
- [Fonte: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/prd.md#FR-4: Excluir tarefa]
- [Fonte: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/addendum.md#Divisão prevista em épicos]
- [Fonte: _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/ARCHITECTURE-SPINE.md#AD-5, #AD-6, #AD-7, #AD-8, #AD-10]
- [Fonte: _bmad-output/planning-artifacts/implementation-readiness-report-2026-10-02.md#Cobertura (FR4: cascata das tags em 2.1)]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

- Análise de contexto concluída: guia de implementação criado pelo create-story (inteligência de story anterior e de git indisponível: greenfield, stories 1.1/1.2 em criação paralela).

### File List
