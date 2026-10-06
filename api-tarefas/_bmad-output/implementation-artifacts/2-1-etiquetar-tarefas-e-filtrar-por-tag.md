---
baseline_commit: 2c30eec64598709e00af749db836a027d8696b06
---

# Story 2.1: Etiquetar tarefas e filtrar por tag

Status: done

<!-- Nota: a validação é opcional. Rode validate-create-story para checar a qualidade antes do dev-story. -->

## Story

Como dev do time-piloto,
quero etiquetar tarefas com tags e listar as de uma tag,
para separar o trabalho por assunto, como `backend` ou `infra`.

## Acceptance Criteria

1. **Tags na criação (FR5, AD-9).** `POST /tasks` com `"tags": ["backend", " Backend ", "API"]` responde 201 com `"tags": ["api", "backend"]`: normalizadas (`strip` + `casefold`), sem repetição e em ordem alfabética. Sem `tags` no corpo, a tarefa nasce com `"tags": []`.
2. **Tags inválidas (FR5, AD-4, AD-7).** Em `POST` ou `PATCH`, uma tag vazia ou só de espaços na posição N, `tags: null` ou `tags` que não seja lista de textos (por exemplo, `"backend"` ou `[1]`) responde 422 com `code: "validation_error"` e `field` igual a `tags.N` (erro em um item) ou `tags` (erro na lista). Nada é gravado: nem a tarefa (no `POST`), nem qualquer campo dela (no `PATCH`).
3. **Tags na edição (FR5, FR3).** Para uma tarefa com `["api", "backend"]`: `PATCH` com `"tags": ["infra"]` deixa exatamente `["infra"]`; `PATCH` com `"tags": []` deixa a tarefa sem tags; `PATCH` sem `tags` (por exemplo, só `title` ou `done`) não muda as tags.
4. **Filtro por tag (FR6, AD-6, AD-9).** `GET /tasks?tag=Backend` devolve só as tarefas que têm a tag `backend`, cada uma com **todas** as suas tags, ordenadas por `due_date` crescente e, em empate, por `id` crescente. Uma tag que nenhuma tarefa usa devolve `200 []`. `?tag=` vazio ou só de espaços devolve 422 com `code: "validation_error"` e `field: "tag"`.
5. **Cascata na exclusão (AD-5).** Ao excluir uma tarefa com tags (`DELETE /tasks/{id}`), as linhas dela em `task_tags` também somem.
6. **Guardrails de implementação (AD-9, AD-10).** Toda tag de entrada (corpo e `?tag=`) passa por `domain.normalize_tags`; `repo.replace_tags` é o único caminho de escrita e `repo.load_tags` o único de leitura de tags; o filtro usa `EXISTS`, nunca `JOIN` na consulta principal; a tarefa e as suas tags são gravadas na mesma transação (`with conn:`).
7. **Regressão do épico 1.** Os testes das stories 1.1, 1.2 e 1.3 continuam passando, exceto os que afirmavam que `tags` no corpo dava 422: esses passam a afirmar o novo comportamento (ver "Mudança de contrato"). `uv run ruff check`, `uv run ruff format --check` e `uv run pytest` passam.

## Tasks / Subtasks

- [x] **Tarefa 1: `domain.normalize_tags` (AC: 1, 2, 6)**
  - [x] 1.1 Em `app/domain.py`, criar `normalize_tags(tags: list[str]) -> list[str]`: `strip()` + `casefold()` em cada item, `ValueError` (mensagem curta) se algum item ficar vazio, remover repetidas e devolver `sorted(set(...))`. Função pura, sem IO, sem importar `api` nem `repo`.
  - [x] 1.2 Teste unitário direto em `tests/test_tasks.py` (ou `tests/test_domain.py` se já existir): `["backend", " Backend ", "API"]` → `["api", "backend"]`; `[]` → `[]`; `[" "]` → `ValueError`.
- [x] **Tarefa 2: tipos de tag nos schemas (AC: 1, 2, 4, 6)**
  - [x] 2.1 Em `app/api.py`, junto de `Title` e `DueDate`, definir o tipo de item `Tag` que rejeita tag vazia **no item** (para o `loc` sair como `("body", "tags", N)`): `Annotated[str, AfterValidator(...)]` cujo validador chama `domain.normalize_tags([v])[0]` (o `ValueError` vira 422 do Pydantic).
  - [x] 2.2 Definir `Tags = Annotated[list[Tag], AfterValidator(domain.normalize_tags)]` para a deduplicação e a ordenação da lista inteira.
  - [x] 2.3 Schema do `POST`: adicionar `tags: Tags = []` (não opcional: `null` → 422 `field: "tags"`). Manter `extra="forbid"` e continuar sem `done`.
  - [x] 2.4 Schema do `PATCH`: adicionar `tags` no mesmo padrão que a story 1.2 usou para `title`/`due_date`/`done` (campo omitível, `null` → 422, aplicado via `exclude_unset`). Não tornar `tags` `Optional`.
  - [x] 2.5 Parâmetro de query `tag` em `GET /tasks`: `Annotated[TagQuery | None, Query()] = None`, em que `TagQuery` é o mesmo `Tag` (normalizado por `domain.normalize_tags`). `?tag=` vazio ou só de espaços → 422 com `field: "tag"` vindo do validador, nunca de `if` na rota (AD-7).
- [x] **Tarefa 3: `repo` — escrita, leitura e filtro de tags (AC: 1, 3, 4, 5, 6)**
  - [x] 3.1 Em `app/repo.py`, criar `replace_tags(conn, task_id, tags)`: `DELETE FROM task_tags WHERE task_id = ?` seguido de `executemany("INSERT INTO task_tags (task_id, tag) VALUES (?, ?)", ...)`. Não abre transação própria: quem chama está dentro de `with conn:`.
  - [x] 3.2 Reutilizar o `load_tags(conn, task_id) -> list[str]` (`ORDER BY tag`) que a 1.1 já cria; não criar outra função. Só se ele não existir no código, criá-lo aqui. Garantir que consultar, listar, criar e editar devolvem as tags reais via `load_tags`.
  - [x] 3.3 Criação: inserir a tarefa e chamar `replace_tags` dentro do mesmo `with conn:` (se ainda não estiver, mover o `INSERT` da 1.1 para dentro do bloco).
  - [x] 3.4 Edição: quando `tags` estiver entre os campos enviados, chamar `replace_tags` no mesmo `with conn:` que já aplica os outros campos (1.2). O 404 continua sendo decidido antes de qualquer escrita.
  - [x] 3.5 Listagem: acrescentar ao `list_tasks` (nome que a 1.1 tiver dado) o argumento `tag: str | None = None`; quando presente, `WHERE EXISTS (SELECT 1 FROM task_tags tt WHERE tt.task_id = tasks.id AND tt.tag = ?)`. Manter `ORDER BY due_date, id`. Montar o `WHERE` a partir de uma lista de condições para a story 2.2 só acrescentar as de prazo.
- [x] **Tarefa 4: rotas (AC: 1, 3, 4)**
  - [x] 4.1 `POST /tasks` e `PATCH /tasks/{id}` repassam as tags já normalizadas ao `repo`; nenhuma normalização ou validação de tag dentro da rota.
  - [x] 4.2 `GET /tasks` repassa `tag` ao `repo`. Rotas continuam `def` e com a conexão de `get_db()` (AD-10).
- [x] **Tarefa 5: testes de tags na criação e na edição (AC: 1, 2, 3, 5) — `tests/test_tasks.py`**
  - [x] 5.1 `POST` com `["backend", " Backend ", "API"]` → 201 e `["api", "backend"]`; `GET /tasks/{id}` devolve as mesmas tags; `POST` sem `tags` → `[]`.
  - [x] 5.2 422 parametrizado em `POST` e `PATCH`, conferindo só `code` e `field`: `["ok", "  "]` → `tags.1`; `[""]` → `tags.0`; `[1]` → `tags.0`; `null` → `tags`; `"backend"` → `tags`. Depois de cada caso, `GET /tasks` (no `POST`) segue sem a tarefa e `GET /tasks/{id}` (no `PATCH`) segue igual ao antes.
  - [x] 5.3 `PATCH` com `["infra"]` → `["infra"]`; com `[]` → `[]`; com só `{"title": ...}` ou `{"done": true}` → tags inalteradas; `PATCH` com `tags` em `id` inexistente → 404 `not_found`/`id`.
  - [x] 5.4 Cascata: criar com tags, `DELETE`, e conferir com `repo.connect()` (mesmo `TASKS_DB_PATH` do `client`) que `SELECT COUNT(*) FROM task_tags WHERE task_id = ?` dá 0.
- [x] **Tarefa 6: testes do filtro por tag (AC: 4) — `tests/test_filters.py`**
  - [x] 6.1 Cenário: tarefa A `["backend", "api"]` prazo 10-10, B `["infra"]` prazo 10-05, C `["backend"]` prazo 10-05 (criada depois de B), D sem tags. `GET /tasks?tag=Backend` → `[C, A]` na ordem `due_date`, `id`; A volta com `["api", "backend"]` (todas as tags, não só a buscada).
  - [x] 6.2 `?tag=%20BACKEND%20` dá o mesmo resultado; `?tag=nada` → `200 []`; `?tag=` e `?tag=%20%20` → 422 com `field: "tag"`.
  - [x] 6.3 Uma tarefa concluída com a tag continua aparecendo no filtro por tag (só as janelas da 2.2 excluem concluídas).
- [x] **Tarefa 7: atualizar a regressão do épico 1 e a qualidade (AC: 7)**
  - [x] 7.1 Localizar nos testes das stories 1.1 e 1.2 os casos "campo fora do schema, como `tags`" e trocar `tags` por outro campo extra (por exemplo, `"priority": 1`), mantendo a cobertura de `extra="forbid"`. Não remover o caso de `done` no `POST` nem o de `id` no `PATCH`.
  - [x] 7.2 Rodar `uv run ruff check`, `uv run ruff format --check` e `uv run pytest`; tudo verde antes do commit.

### Review Findings

Revisão de código (2026-10-02, bmad-code-review, modo full): todos os ACs 1–7 atendidos; `uv run pytest` 68 passed; `ruff check` e `ruff format --check` limpos. Nenhum achado high/medium.

- [x] [Review][Defer] Checagem de existência no `update_task` roda antes do `BEGIN` implícito do sqlite3 (o `SELECT` não abre transação); um `DELETE` concorrente entre o `SELECT` e o `INSERT` em `task_tags` gera `IntegrityError` de FK → 500 em vez de 404. Baixo: mesmo padrão da corrida já registrada na 1.2 [app/repo.py:48] — deferred, mesma classe de problema pré-existente

## Dev Notes

### Contexto e dependências

- **Depende do épico 1 inteiro** (1.1, 1.2, 1.3). Segundo o `epics.md` e o spine, quando esta story começar já existem: projeto `uv` com Python 3.14 e só as dependências do AD-1; `app/main.py` com os três handlers do AD-7; `app/api.py` com `Title`, `DueDate`, schemas com `extra="forbid"`, `get_db()` e a dependência `now`; `app/domain.py` com `now()` e `today()`; `app/repo.py` com `connect()` (lê `TASKS_DB_PATH` a cada chamada, `PRAGMA foreign_keys = ON`, esquema completo do AD-5, **incluindo `task_tags` com `ON DELETE CASCADE`**); `tests/conftest.py` com `client` e `set_now`; respostas com `"tags": []` fixo.
- **Não crie tabela nem mexa no esquema.** `task_tags` já nasce na 1.1 (AD-5; readiness M2). Se o esquema da 1.1 divergir do AD-5, corrija para o AD-5 e registre no Completion Notes.
- **Story 2.2 é a próxima e roda depois desta**: ela reaproveita o `?tag=` e o `EXISTS` daqui para a interseção (FR8) e acrescenta `due`. Deixe o `WHERE` do `list_tasks` composto por lista de condições para a 2.2 só somar. Não implemente `due`, `window_bounds` nem nada de janela nesta story.

### Mudança de contrato (readiness m2)

No épico 1, `tags` no corpo do `POST` e do `PATCH` dá 422 por `extra="forbid"`. **A partir desta story, `tags` passa a ser aceito.** É intencional (AC 7 da 1.1/1.2 dizem "as tags chegam na story 2.1"). Consequência prática: os testes da 1.1 e da 1.2 que usam `tags` como exemplo de campo extra vão quebrar e devem ser ajustados (Tarefa 7), não apagados. Não há consumidores externos antes do fim da v1, então não há compatibilidade a manter.

### Regras que o dev precisa seguir

- **AD-9 — dono único:** normalização só em `domain.normalize_tags`; escrita só em `repo.replace_tags`; leitura só em `repo.load_tags`; filtro só por `EXISTS`. Um `JOIN task_tags` na consulta principal devolveria só a tag buscada e duplicaria tarefas — é exatamente o erro que o AD-9 previne.
- **Por que a deduplicação importa:** `PRIMARY KEY (task_id, tag)` faz `["Backend", "backend"]` sem normalização virar `IntegrityError` → 500. A normalização acontece no schema, antes do `repo`.
- **AD-7 — 422 só por Pydantic:** a tag vazia é rejeitada no validador do item (`loc = ("body", "tags", N)` → `field = "tags.N"`). Nunca `if not tag: raise HTTPException(...)` na rota. O handler da 1.1 já transforma o `loc` em `field`; não mexa no handler.
- **AD-4:** `tags: null` dá 422 no `POST` e no `PATCH`; `tags: []` limpa. Não use `list[Tag] | None` (aceitaria `null`). Pydantic v2 não converte `int` em `str` no modo padrão, então `[1]` já dá 422 sem `strict` extra.
- **AD-10:** tarefa + tags em um único `with conn:`. `replace_tags` não faz `commit` sozinho. Rotas `def`, conexão por requisição via `get_db()`.
- **AD-6:** forma da tarefa inalterada `{id, title, due_date, tags, done}`; `tags` sempre em ordem alfabética; lista em `due_date` e depois `id`.
- **Nomes:** código e campos em inglês `snake_case`; `message` de erro em português (já é do handler).

### Arquivos tocados (todos UPDATE; nenhum NEW, exceto se a 1.1 não tiver criado `tests/test_filters.py`)

| Arquivo | Estado esperado ao começar (pela 1.1–1.3) | O que muda | O que preservar |
| --- | --- | --- | --- |
| `app/domain.py` | `now()`, `today()` | + `normalize_tags` | `now`/`today` intocados; sem IO |
| `app/api.py` | `Title`, `DueDate`, schemas `POST`/`PATCH` com `extra="forbid"`, rotas CRUD, `get_db`, `now` | + `Tag`/`Tags`, campo `tags` nos dois schemas, `?tag=` no `GET /tasks` | `extra="forbid"`; `POST` sem `done`; `PATCH` com `exclude_unset` e `null` → 422; 404 com `field: "id"` |
| `app/repo.py` | `connect()`, esquema AD-5, CRUD, `load_tags` (já criado na 1.1) | + `replace_tags`, filtro `EXISTS`; criação/edição gravam tags na mesma transação | ordem `due_date, id`; `foreign_keys = ON`; `TASKS_DB_PATH` lido a cada `connect()` |
| `tests/test_tasks.py` | testes da 1.1–1.3 | + Tarefa 5; ajuste da Tarefa 7 | demais asserções |
| `tests/test_filters.py` | pode não existir | + Tarefa 6 | — |

`app/main.py`, `tests/conftest.py`, `pyproject.toml` e o `README.md` **não** mudam nesta story (o `curl` com tag e as vencidas é da 2.2). Nenhuma dependência nova (AD-1).

### Esboço de referência (não é código final)

```python
# api.py
Tag = Annotated[str, AfterValidator(lambda v: domain.normalize_tags([v])[0])]
Tags = Annotated[list[Tag], AfterValidator(domain.normalize_tags)]

# repo.py
def replace_tags(conn, task_id, tags):
    conn.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
    conn.executemany("INSERT INTO task_tags (task_id, tag) VALUES (?, ?)", [(task_id, t) for t in tags])
```

`load_tags` por tarefa gera N+1 consultas na listagem. Para o volume de um time pequeno (sem paginação, PRD §6.2) isso basta; marque com `# ponytail: N+1 em load_tags, trocar por um SELECT ... WHERE task_id IN (...) se a lista crescer`.

### Testes

- pytest + `TestClient` via fixture `client` do `conftest.py` (AD-8). Não redefina fixtures; esta story não precisa de `set_now`.
- Conferir só `code` e `field` nos erros, nunca `message`.
- Para inspecionar `task_tags` direto, use `repo.connect()`: o `client` já apontou `TASKS_DB_PATH` para o `tmp_path` via `monkeypatch`.

### Project Structure Notes

- Segue a árvore do spine (`app/{main,api,domain,repo}.py`, `tests/{conftest,test_tasks,test_filters}.py`). Dependências entre camadas: `api → domain`, `api → repo`, `repo → domain`; `domain` não importa ninguém.
- Variância possível: os nomes exatos das funções do `repo` e do padrão de "campo omitível" no `PATCH` são definidos pelas stories 1.1/1.2, que ainda não existiam quando esta story foi escrita. Siga o que estiver no código; os nomes `replace_tags`, `load_tags` e `normalize_tags` são fixos (AD-9).

### Inteligência de stories anteriores e git

Indisponível: as stories 1.1–1.3 estavam sendo criadas em paralelo e não havia código no repositório (greenfield; commits recentes só de planejamento). As dependências acima vêm do `epics.md` e do spine. Antes de começar, leia os arquivos de story 1.1–1.3 e o código entregue, e ajuste os nomes.

### Informações técnicas atuais

Versões fixadas no spine, conferidas no PyPI em 2026-10-02: FastAPI 0.142.2, Pydantic 2.13.x, pytest 9.1.1, httpx 0.28.1, Ruff 0.16.10. Nenhuma pesquisa extra foi necessária: a story usa só `Annotated` + `AfterValidator` (Pydantic v2) e `Query` com `Annotated` (FastAPI), ambos estáveis nessas versões.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1: Etiquetar tarefas e filtrar por tag]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1, #Story 1.2] (campo `tags` → 422 até esta story)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/ARCHITECTURE-SPINE.md#AD-4, #AD-5, #AD-6, #AD-7, #AD-9, #AD-10]
- [Source: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/prd.md#FR-5, #FR-6, §3 Glossário (Tag)]
- [Source: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/addendum.md#Pistas de contrato da API]
- [Source: _bmad-output/planning-artifacts/implementation-readiness-report-2026-10-02.md#m2, #M2]

### Questões em aberto (registradas, sem bloquear)

1. **Vários `?tag=` na mesma chamada** (`?tag=a&tag=b`): o AD-6 diz "um valor cada"; com um parâmetro `str`, o FastAPI usa o último valor. Assumido assim, sem 422. Confirmar se deveria ser 422.
2. **Limite de tamanho/quantidade de tags:** nenhum documento define. Nenhum limite implementado.
3. **`casefold` vs. `lower`:** `casefold` (AD-9) transforma `Straße` em `strasse`; a resposta devolve a forma casefold, não a digitada. Assumido como aceitável.
4. **Padrão de campo omitível no `PATCH`:** depende de como a 1.2 implementou (default sem `Optional` + `exclude_unset`). Seguir o padrão existente.

## Dev Agent Record

### Agent Model Used

Claude Opus 5.5 (claude-opus-5-5)

### Debug Log References

- Red: 15 falhas + 4 erros com os testes novos antes da implementação. Green: `uv run pytest` 68 passed; `ruff check` e `ruff format --check` limpos.

### Completion Notes List

- Análise de contexto concluída: guia completo para o dev criado (create-story, 2026-10-02).
- `domain.normalize_tags`: `strip` + `casefold`, `ValueError("tag vazia")`, `sorted(set)`.
- `api.py`: `Tag` (validador de item, 422 com `tags.N`) e `Tags` (deduplica/ordena). `TaskCreate.tags: Tags = []`; `TaskUpdate.tags: Tags = None` seguindo o padrão da 1.2 (omitível, `null` → 422). `GET /tasks` recebe `tag: Annotated[Tag | None, Query()]`; o `TagQuery` sugerido não foi criado, o próprio `Tag` serve.
- `repo.py`: `replace_tags` (DELETE + executemany, sem commit próprio); `insert_task` ganhou `tags` e grava tudo no mesmo `with conn:`; `update_task` agora confere a existência da tarefa **antes** de qualquer escrita (sem isso, `PATCH` com `tags` em id inexistente tentaria inserir em `task_tags` e daria `IntegrityError` → 500); `list_tasks(conn, tag=None)` monta o `WHERE` por lista de condições com `EXISTS` (pronto para a 2.2). `load_tags` da 1.1 reaproveitado, com comentário `ponytail:` do N+1.
- Esquema da 1.1 já estava conforme o AD-5 (`task_tags` com `ON DELETE CASCADE`); nada mudou no esquema.
- Regressão: casos de campo extra `tags` nos testes da 1.1/1.2 trocados por `priority` (Tarefa 7).
- Decisões das questões em aberto: vários `?tag=` usam o último valor (comportamento padrão do FastAPI); sem limite de tamanho/quantidade; `casefold` mantido.
- Teste unitário de `normalize_tags` ficou em `tests/test_tasks.py` (não existe `tests/test_domain.py`). `tests/test_filters.py` foi criado (não existia).

### File List

- app/domain.py
- app/api.py
- app/repo.py
- tests/test_tasks.py
- tests/test_filters.py (novo)

## Change Log

- 2026-10-02: Story 2.1 implementada — tags na criação/edição, filtro `?tag=` por `EXISTS`, testes novos e ajuste da regressão do épico 1. Status → review.
