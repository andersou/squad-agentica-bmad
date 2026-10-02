---
baseline_commit: 717a2ab94c68618ad7b767c881619d7e93817971
---

# Story 1.2: Editar e concluir tarefa

Status: done

<!-- Nota: a validação é opcional. Rode validate-create-story para checar a qualidade antes do dev-story. -->

## Story

Como dev do time-piloto,
quero corrigir título ou prazo de uma tarefa e marcá-la como concluída,
para que a lista reflita o estado real do trabalho.

## Acceptance Criteria

1. **Edição parcial de título.** Dada uma tarefa existente, quando o dev faz `PATCH /tasks/{id}` com `{"title": "Novo título"}`, então recebe 200 com a tarefa completa (`{id, title, due_date, tags, done}`) e só o título alterado; `due_date`, `tags` e `done` não mudam. (FR3, AD-6)
2. **Concluir e desmarcar.** Dada uma tarefa não concluída, quando o dev faz `PATCH /tasks/{id}` com `{"done": true}`, então recebe 200 com `done: true`; um novo `PATCH` com `{"done": false}` a desmarca (200, `done: false`). (FR3)
3. **Corpo vazio.** Um `PATCH` com corpo `{}` devolve 200 com a tarefa inalterada.
4. **Validação.** Um `PATCH` com `title` vazio ou só de espaços, `due_date` inválido (mesmos casos da 1.1: `"2026-02-30"`, `"2026-10-02T00:00:00Z"`, `"02/10/2026"`, `1790899200`), `done` que não seja booleano JSON (como `"true"` ou `1`) ou `null` em qualquer campo devolve 422 com `code: "validation_error"` e o `field` correspondente (`title`, `due_date` ou `done`), e a tarefa não muda. (FR3, AD-4, AD-7)
5. **Campo fora do schema.** Um `PATCH` com um campo fora do schema, como `tags` ou `id`, devolve 422 com `code: "validation_error"`. (AD-4; as tags no `PATCH` chegam na story 2.1)
6. **Tarefa inexistente.** Com um `id` que não existe, `PATCH /tasks/{id}` devolve 404 com `code: "not_found"` e `field: "id"`. (FR3, AD-7)
7. **Revisão de código.** O `PATCH` usa os mesmos tipos `Title` e `DueDate` do `POST` e aplica só os campos enviados (`model_dump(exclude_unset=True)`), dentro de `with conn:`. (AD-4, AD-10)

## Tasks / Subtasks

- [x] Tarefa 1: Schema de entrada `TaskUpdate` em `app/api.py` (AC: 4, 5, 7)
  - [x] 1.1 Declarar `TaskUpdate` com `model_config = ConfigDict(extra="forbid")`, reaproveitando os tipos `Title` e `DueDate` que a 1.1 já definiu em `app/api.py` (não redefinir, não copiar).
  - [x] 1.2 Campos opcionais sem `Optional`: `title: Title = None`, `due_date: DueDate = None`, `done: StrictBool = None` (ou o tipo `done` estrito que a 1.1 já tiver). Assim omitir é permitido e `null` explícito dá 422.
  - [x] 1.3 Não declarar `tags` nem `id` em `TaskUpdate` (o `extra="forbid"` rejeita). A 2.1 acrescenta `tags`.
- [x] Tarefa 2: Função de escrita em `app/repo.py` (AC: 1, 2, 3, 6, 7)
  - [x] 2.1 Criar `update_task(conn, task_id, fields: dict) -> bool` (ou nome equivalente seguindo o padrão da 1.1) que, dentro de `with conn:`, monta `UPDATE tasks SET <col> = ? ...` só com as chaves recebidas e devolve se a tarefa existe.
  - [x] 2.2 As colunas vêm de uma lista fixa (`title`, `due_date`, `done`), nunca do texto da requisição; valores sempre por parâmetro `?`.
  - [x] 2.3 Gravar `done` como `0`/`1` (`int(done)`).
  - [x] 2.4 `fields` vazio (corpo `{}`): não executar `UPDATE`; só verificar se a tarefa existe.
  - [x] 2.5 Ler a tarefa atualizada pelo mesmo caminho de leitura do `GET /tasks/{id}` da 1.1 (inclui `tags` via `load_tags`, se a 1.1 já o criou), sem caminho novo de leitura.
- [x] Tarefa 3: Rota `PATCH /tasks/{id}` em `app/api.py` (AC: 1–7)
  - [x] 3.1 `def patch_task(id: int, body: TaskUpdate, conn = Depends(get_db))` — rota `def`, não `async def` (AD-10); `response_model` igual ao das outras rotas (a tarefa `Task` da 1.1).
  - [x] 3.2 `fields = body.model_dump(exclude_unset=True)` e repassar ao `repo`.
  - [x] 3.3 Tarefa inexistente: levantar o mesmo 404 que o `GET /tasks/{id}` da 1.1 levanta (`field: "id"`), reaproveitando o helper/exceção existente.
  - [x] 3.4 Nenhum `if` de validação na rota: toda regra de 422 fica nos tipos Pydantic (AD-7).
- [x] Tarefa 4: Testes em `tests/test_tasks.py` (AC: 1–6)
  - [x] 4.1 Edição de título: só o título muda; `due_date`, `tags` e `done` iguais; `GET /tasks/{id}` confirma a persistência.
  - [x] 4.2 Edição de `due_date` e reordenação: após mudar o prazo, `GET /tasks` reflete a nova ordem (`due_date`, depois `id`).
  - [x] 4.3 `done: true` → `done: false`, conferindo o tipo booleano JSON na resposta (`is True`/`is False`, não `1`/`0`).
  - [x] 4.4 Corpo `{}` → 200 e tarefa igual à anterior.
  - [x] 4.5 422 parametrizado: `title` `""` e `"   "`; `due_date` nos quatro casos da 1.1; `done` `"true"` e `1`; `null` em `title`, `due_date` e `done`. Conferir `code` e `field` (nunca `message`) e que um `GET` depois mostra a tarefa inalterada.
  - [x] 4.6 Campo extra: `{"tags": ["x"]}` e `{"id": 99}` → 422 `validation_error`.
  - [x] 4.7 `PATCH` em `id` inexistente → 404, `code: "not_found"`, `field: "id"`.
  - [x] 4.8 Título com espaços nas pontas (`"  Novo  "`) é gravado sem eles (`"Novo"`), igual ao `POST`.
- [x] Tarefa 5: Qualidade e docs (AC: todos)
  - [x] 5.1 `uv run ruff check`, `uv run ruff format --check` e `uv run pytest` passando (toda a suíte da 1.1 continua verde).
  - [x] 5.2 Acrescentar ao `README.md` um exemplo `curl` de concluir uma tarefa (`PATCH` com `{"done": true}`), em português.

### Review Findings

Revisão de código (bmad-code-review, 2026-10-02): todos os ACs 1–7 atendidos; `uv run pytest` 42 passed; ruff limpo. Nenhum achado alto ou médio.

- [x] [Review][Defer] `id` fora do intervalo INTEGER do SQLite (ex.: `PATCH /tasks/99999999999999999999`) gera `OverflowError` → 500 em vez de 404/422 [app/repo.py:47] — deferred, pre-existing (o `GET /tasks/{id}` da 1.1 tem o mesmo comportamento)
- [x] [Review][Defer] Corrida entre `update_task` e `get_task` (tarefa excluída entre as duas chamadas, possível após a 1.3) faria `patch_task` devolver `None` → 500 de validação de resposta [app/api.py:89] — deferred, inalcançável hoje (não há DELETE); reavaliar na 1.3

## Dev Notes

### Contexto e dependências

- **Depende só da Story 1.1**, que entrega (segundo o epics.md e o spine): projeto `uv` com Python 3.14; `app/main.py` com os três handlers do AD-7; `app/api.py` com `Title`, `DueDate`, `TaskCreate`, o modelo de saída da tarefa, `get_db()` e as rotas `POST /tasks`, `GET /tasks`, `GET /tasks/{id}`; `app/domain.py` com `now()`/`today()`; `app/repo.py` com `connect()` e o esquema completo do AD-5 (`tasks` e `task_tags`); `tests/conftest.py` com as fixtures `client` e `set_now`.
- **Não depende da 1.3** e roda em paralelo com ela (readiness report). A 1.3 vai mexer nas mesmas `api.py`, `repo.py` e `test_tasks.py`: mantenha as mudanças localizadas (uma rota, uma função de repo, um bloco de testes) para facilitar o merge.
- **O que a 1.2 não faz:** tags no `PATCH` (story 2.1: substituição da lista, `tags: []` limpa, `tags: null` → 422, `replace_tags` na mesma transação); filtro por janela e a saída das tarefas concluídas das janelas (story 2.2 consome o `done` gravado aqui). Não antecipe esse código.
- **Inteligência da story anterior:** indisponível. O arquivo da Story 1.1 está sendo criado em paralelo e ainda não existe código (greenfield). Antes de começar, leia o código e o arquivo da 1.1 que já estiverem no repositório e siga os nomes que ela escolheu (nome do modelo de saída, da exceção/helper de 404, das funções do `repo`). Os nomes nesta story são sugestões; os da 1.1 prevalecem.

### Guardrails de arquitetura

- **Camadas (spine):** `api` → `domain` ← `repo`. A rota só valida (Pydantic), chama o `repo` e devolve; SQL só no `repo`; `domain` não é tocado por esta story.
- **AD-4 — tipos compartilhados:** `PATCH` e `POST` usam os **mesmos** `Title` e `DueDate`. Se você se pegar escrevendo um regex ou `strip` novo para o `PATCH`, pare: reuse o tipo da 1.1. `done` é booleano estrito (`StrictBool`): `"true"`, `1`, `0` e `"yes"` dão 422.
- **AD-4 — `null` dá 422:** o padrão verificado na revisão de arquitetura (Pydantic 2.13) é declarar o campo com o tipo não opcional e default `None`, por exemplo `title: Title = None`. O default não é validado (omitir funciona) e o `null` explícito falha na validação do tipo. **Não** use `Title | None = None`: aí `{"title": null}` passaria e gravaria `NULL` numa coluna `NOT NULL` (500). Fonte: `reviews/review-rubric-versions.md`, A7.
- **AD-4 — `extra="forbid"`:** `tags` e `id` no corpo dão 422. O `loc` do erro é `("body", "tags")`, então `field` sai `"tags"` pelo handler do AD-7, sem código extra.
- **AD-6 — contrato:** `PATCH /tasks/{id}` → 200 + tarefa completa; erros 404 e 422. A resposta sai pelo mesmo modelo de saída das outras rotas, com `done` como `bool` JSON e `tags` presente (vazio nesta fase).
- **AD-7 — erros:** não crie handler nem formato novo; os handlers da 1.1 já cobrem 422 e 404. O 404 de tarefa usa `field: "id"`. Os testes conferem só `code` e `field`.
- **AD-10 — conexão e transação:** use a conexão de `get_db()`; não abra conexão própria nem guarde conexão global. A escrita roda em `with conn:` (commit ou rollback). Isso prepara o terreno para a 2.1, que vai acrescentar `replace_tags` na mesma transação do `PATCH` (evita `PATCH` meio aplicado, `reviews/review-adversarial.md`, H8).
- **Ordem de validação:** o FastAPI valida o corpo antes de a rota rodar. Logo, `PATCH` com corpo inválido num `id` inexistente dá 422, não 404. Isso é esperado; não tente inverter.
- **`id` não inteiro** (`PATCH /tasks/abc`) dá 422 com `field: "id"` pelo `loc` `("path", "id")`. Comportamento herdado da 1.1, sem código novo.

### Esboço de referência (não é código final)

```python
# app/api.py
class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Title = None        # sem Optional: null -> 422
    due_date: DueDate = None
    done: StrictBool = None

@router.patch("/tasks/{id}", response_model=Task)
def patch_task(id: int, body: TaskUpdate, conn=Depends(get_db)):
    if not repo.update_task(conn, id, body.model_dump(exclude_unset=True)):
        raise <404 de tarefa da 1.1>
    return <mesma leitura do GET /tasks/{id}>
```

```python
# app/repo.py
_UPDATABLE = ("title", "due_date", "done")

def update_task(conn, task_id, fields):
    cols = [c for c in _UPDATABLE if c in fields]
    with conn:
        if cols:
            sets = ", ".join(f"{c} = ?" for c in cols)
            vals = [int(fields[c]) if c == "done" else fields[c] for c in cols]
            cur = conn.execute(f"UPDATE tasks SET {sets} WHERE id = ?", (*vals, task_id))
            return cur.rowcount > 0
        return conn.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone() is not None
```

O `rowcount` do SQLite conta as linhas casadas pelo `WHERE`, mesmo quando o valor gravado é igual ao anterior; não há falso 404 em `PATCH` idempotente.

### Requisitos de bibliotecas

- Nenhuma dependência nova (AD-1). Use `pydantic` (`BaseModel`, `ConfigDict`, `StrictBool`) que já vem com o `fastapi` 0.142.2 (Pydantic 2.13.x) e o `sqlite3` da stdlib.
- Versões conferidas no spine em 2026-10-02 (PyPI e python.org); não houve pesquisa web adicional nesta story, porque nada novo entra na stack.

### Estrutura de arquivos

| Arquivo | Ação | Mudança |
| --- | --- | --- |
| `app/api.py` | ATUALIZAR | `TaskUpdate` + rota `PATCH /tasks/{id}` |
| `app/repo.py` | ATUALIZAR | `update_task` (ou nome no padrão da 1.1) |
| `tests/test_tasks.py` | ATUALIZAR | testes do FR3 (o spine põe FR-1 a FR-5 neste arquivo) |
| `README.md` | ATUALIZAR | `curl` de concluir tarefa |
| `app/main.py`, `app/domain.py`, `tests/conftest.py` | NÃO TOCAR | handlers, relógio e fixtures já vêm da 1.1 |

Arquivos a ATUALIZAR ainda não existem (greenfield; a 1.1 os cria). Antes de mexer, leia cada um por inteiro e preserve: as rotas `POST`/`GET` e seus testes, os handlers do AD-7, o `connect()` lendo `TASKS_DB_PATH` a cada chamada e as fixtures do AD-8 (nenhuma fixture nova; não redefina `client`).

### Testes

- pytest + `TestClient` via fixture `client` do `tests/conftest.py` (banco novo em `tmp_path`). `set_now` não é necessário nesta story.
- Crie as tarefas pelo `POST /tasks` (o contrato público), não por SQL direto.
- Para "a tarefa não muda" nos 422, faça `GET /tasks/{id}` depois e compare com o estado anterior.
- Confira `code` e `field`, nunca `message` (AD-7).
- Use `pytest.mark.parametrize` para os casos de 422.

### Project Structure Notes

- Alinhado à árvore do spine (`app/api.py`, `app/repo.py`, `tests/test_tasks.py`). Nenhum arquivo novo.
- Nomes em inglês e `snake_case` no código; mensagens, README e commits em português.
- Sem conflito detectado com o spine.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2: Editar e concluir tarefa]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1: Criar, listar e consultar tarefas]
- [Source: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/prd.md#FR-3: Editar tarefa]
- [Source: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/addendum.md] (conclusão por edição; endpoint `/complete` descartado)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/ARCHITECTURE-SPINE.md#AD-4, #AD-6, #AD-7, #AD-10, #Structural Seed]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/reviews/review-rubric-versions.md#A6, #A7]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/reviews/review-adversarial.md#H6, #H8]
- [Source: _bmad-output/planning-artifacts/implementation-readiness-report-2026-10-02.md] (1.2 depende só da 1.1; `done` consumido pela 2.2)

### Questões em aberto

- O nome do modelo de saída, do helper/exceção de 404 e da função de leitura do `repo` depende do que a 1.1 implementar; esta story usa nomes sugeridos (`Task`, `update_task`).
- O `PATCH` com corpo inválido em `id` inexistente devolve 422 (validação antes da rota). Os artefatos não dizem nada; assumido como aceitável.
- O exemplo `curl` de concluir tarefa no README não é exigido pelo NFR1; foi incluído por ser barato. Remover se o time preferir o README mínimo.

## Dev Agent Record

### Agent Model Used

Claude Opus 5.5 (claude-opus-5-5)

### Debug Log References

### Completion Notes List

- Análise de contexto concluída: guia completo para o dev criado (create-story, 2026-10-02).
- Nomes seguidos da 1.1 (código real): modelo de saída `Task`, alias `Db` para `get_db`, parâmetro de rota `task_id` (não `id`), 404 via `HTTPException(404, detail="task_not_found")` que o handler do AD-7 traduz em `field: "id"`, leitura via `repo.get_task` (já inclui `load_tags`).
- `TaskUpdate` em `app/api.py` com `extra="forbid"`, reaproveitando `Title` e `DueDate`; `done: StrictBool = None` (sem `Optional`: `null` explícito dá 422).
- `repo.update_task(conn, task_id, fields) -> bool`: colunas de lista fixa `_UPDATABLE`, valores por `?`, `done` gravado como `int`, corpo `{}` só verifica existência; tudo dentro de `with conn:`.
- Rota `PATCH /tasks/{task_id}` síncrona (`def`), sem `if` de validação; `body.model_dump(exclude_unset=True)` repassado ao repo.
- Testes (TDD: 18 falhando antes, todos verdes depois): edição de título com strip, reordenação por prazo, `done` true/false como booleano JSON, corpo vazio, 13 casos de 422 parametrizados (inclui `tags`/`id` extras e `null`) conferindo que a tarefa não muda, 404 com `field: "id"`.
- Validação: `uv run pytest` 42 passed; `ruff check` e `ruff format --check` limpos. O aviso `StarletteDeprecationWarning` (httpx) já existia antes desta story.
- Decisão: README ganhou o `curl` de concluir tarefa, como pedia a tarefa 5.2.

### File List

- app/api.py
- app/repo.py
- tests/test_tasks.py
- README.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- _bmad-output/implementation-artifacts/1-2-editar-e-concluir-tarefa.md

### Change Log

- 2026-10-02: implementado `PATCH /tasks/{task_id}` (editar título/prazo, concluir/desmarcar), `repo.update_task`, testes do FR3 e exemplo no README. Status → review.
