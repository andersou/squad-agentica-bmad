# Story 1.1: Criar, listar e consultar tarefas

Status: ready-for-dev

<!-- Nota: a validação é opcional. Rode validate-create-story para checar a qualidade antes do dev-story. -->

## Story

Como dev do time-piloto,
quero criar uma tarefa com título e prazo e depois listá-la ou consultá-la,
para que as tarefas deixem a planilha e passem a estar num lugar que scripts conseguem consultar.

## Acceptance Criteria

1. **Setup.** **Given** o repositório sem código, **When** a story é implementada, **Then** existe um projeto `uv` com Python 3.14 e só as dependências do AD-1 (`fastapi`, `uvicorn`, `tzdata`; dev: `pytest`, `httpx`, `ruff`), **And** o código segue a árvore do spine (`app/main.py`, `app/api.py`, `app/domain.py`, `app/repo.py`; `tests/conftest.py`), **And** `uv run ruff check`, `uv run ruff format --check` e `uv run pytest` passam.
2. **Criar.** **Given** a API no ar, **When** o dev faz `POST /tasks` com `{"title": "Revisar PR", "due_date": "2026-10-10"}`, **Then** recebe 201 com `{"id": <int>, "title": "Revisar PR", "due_date": "2026-10-10", "tags": [], "done": false}` (FR1, AD-6).
3. **Título inválido.** **Given** um `POST /tasks` sem `title`, com `title` vazio ou só de espaços, **When** a requisição é processada, **Then** recebe 422 com `{"error": {"code": "validation_error", "field": "title", "message": <texto em português>}}`, **And** nenhuma tarefa é criada (FR1, NFR3, AD-4, AD-7).
4. **Prazo inválido.** **Given** um `POST /tasks` sem `due_date` ou com `due_date` igual a `"2026-02-30"`, `"2026-10-02T00:00:00Z"`, `"02/10/2026"` ou `1790899200`, **When** a requisição é processada, **Then** recebe 422 com `code: "validation_error"` e `field: "due_date"` (FR1, AD-4).
5. **Prazo no passado.** **Given** um `POST /tasks` com prazo no passado, **When** a requisição é processada, **Then** recebe 201, e a tarefa nasce com `done: false` (FR1).
6. **Campos fora do schema.** **Given** um `POST /tasks` com um campo fora do schema, como `done` ou `tags`, **When** a requisição é processada, **Then** recebe 422 com `code: "validation_error"` (AD-4; as tags chegam na story 2.1).
7. **Listar.** **Given** tarefas criadas com prazos fora de ordem e duas com o mesmo prazo, **When** o dev faz `GET /tasks`, **Then** recebe 200 com todas as tarefas, sem paginação, ordenadas por `due_date` crescente e, em empate, por `id` crescente (FR2, AD-6), **And** sem nenhuma tarefa, recebe `[]`.
8. **Consultar.** **Given** uma tarefa existente, **When** o dev faz `GET /tasks/{id}`, **Then** recebe 200 com a tarefa, **And** com um `id` que não existe, recebe 404 com `code: "not_found"` e `field: "id"` (FR2, AD-7).
9. **Rota/método inexistente.** **Given** uma rota que não existe ou um método não suportado, **When** a requisição é processada, **Then** recebe 404 `not_found` ou 405 `method_not_allowed`, com `field: null`, no envelope do AD-7, nunca `{"detail": ...}`.
10. **Persistência e esquema.** **Given** uma tarefa criada, **When** o serviço é reiniciado com o mesmo `TASKS_DB_PATH`, **Then** a tarefa continua lá (NFR4, AD-10), **And** `repo.connect()` cria o esquema completo do AD-5 (`tasks` e `task_tags`) quando o banco não existe.
11. **Fixtures.** **Given** a suíte de testes, **When** um teste usa a fixture `client` de `tests/conftest.py`, **Then** ele roda contra um banco novo em `tmp_path`, e a fixture `set_now` já existe para os épicos seguintes (AD-8).
12. **README.** **Given** o `README.md`, **When** um dev novo o lê, **Then** encontra como instalar, rodar (`uvicorn app.main:app --host <IP interno>`, NFR5) e exemplos `curl` de criar e listar tarefas (NFR1).

## Tasks / Subtasks

> Ordem pensada para o achado **M1** do readiness (esta é a story mais carregada): cada tarefa deixa algo verificável antes da próxima. Ordem de dependência: setup → `domain` → `repo` → `api` → `main` → testes → README → portão de qualidade. Se o contexto apertar, pare depois da Tarefa 7 com `uv run pytest` verde e registre o ponto nas Completion Notes.

- [ ] **Tarefa 1: Setup do projeto `uv`** (AC: 1)
  - [ ] 1.1 Na raiz do projeto (`api-tarefas/`, a mesma pasta de `_bmad/`), rodar `uv init --app --python 3.14 --vcs none --no-readme` (o repositório git já existe). Apagar o `main.py`/`hello.py` de exemplo que o `uv init` gera na raiz. Conferir `requires-python = ">=3.14"` no `pyproject.toml`.
  - [ ] 1.2 `uv add fastapi==0.142.2 uvicorn==0.54.0 tzdata==2026.4` e `uv add --dev pytest==9.1.1 httpx==0.28.1 ruff==0.16.10`. **Nada além disso** (sem `fastapi[standard]`, sem ORM, sem `pydantic-settings`, sem `python-dotenv`, sem `freezegun`).
  - [ ] 1.3 No `pyproject.toml`: `[tool.pytest.ini_options]` com `testpaths = ["tests"]` e `pythonpath = ["."]`; `[tool.ruff]` com `extend-exclude = [".claude", "_bmad", "_bmad-output", "docs"]` (ver "Armadilhas" 1 e 2).
  - [ ] 1.4 Criar `app/__init__.py` vazio e `tests/` (sem `__init__.py`). Acrescentar `tasks.db`, `.venv/`, `__pycache__/` e `.pytest_cache/`, `.ruff_cache/` ao `.gitignore`. Commitar `uv.lock`.
- [ ] **Tarefa 2: `app/domain.py` — relógio** (AC: 11; base do AD-2)
  - [ ] 2.1 `now() -> datetime`: devolve `datetime.now(UTC)`. É o **único** lugar do código que lê o relógio.
  - [ ] 2.2 `today(now: datetime) -> date`: `now.astimezone(ZoneInfo("America/Sao_Paulo")).date()`. Constante de fuso no módulo, não configurável.
  - [ ] 2.3 Nada de `window_bounds` nem `normalize_tags` aqui: são das stories 2.2 e 2.1. `domain` não importa `api`, `repo`, `fastapi` nem `sqlite3`.
- [ ] **Tarefa 3: `app/repo.py` — conexão, esquema e leitura/escrita** (AC: 2, 7, 8, 10)
  - [ ] 3.1 `connect() -> sqlite3.Connection`: lê `os.environ.get("TASKS_DB_PATH", "./tasks.db")` **a cada chamada**; `sqlite3.connect(path, check_same_thread=False)`; `row_factory = sqlite3.Row`; `PRAGMA foreign_keys = ON`; `executescript(SCHEMA)` com o SQL exato do AD-5 (as duas tabelas, `IF NOT EXISTS`).
  - [ ] 3.2 `insert_task(conn, title, due_date) -> int`: `INSERT INTO tasks (title, due_date) VALUES (?, ?)` dentro de `with conn:`; devolve `lastrowid`. `done` fica no `DEFAULT 0`.
  - [ ] 3.3 `load_tags(conn, task_id) -> list[str]`: `SELECT tag FROM task_tags WHERE task_id = ? ORDER BY tag`. Na 1.1 sempre volta `[]`, mas a resposta já sai daqui (AD-9: único caminho de leitura de tags).
  - [ ] 3.4 `get_task(conn, task_id) -> dict | None` e `list_tasks(conn) -> list[dict]` (`ORDER BY due_date, id`), cada um montando `{"id", "title", "due_date", "tags": load_tags(...), "done": bool(row["done"])}`. Uma função privada `_to_task(conn, row)` evita duplicar a montagem.
  - [ ] 3.5 Só SQL parametrizado (`?`), nunca f-string com valor do usuário. Sem regra de negócio no `repo`.
- [ ] **Tarefa 4: `app/api.py` — tipos, schemas, dependências e rotas** (AC: 2–8)
  - [ ] 4.1 Tipos compartilhados (AD-4), definidos **uma vez** para a 1.2 reaproveitar:
    - `Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]`
    - `DueDate = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}$"), AfterValidator(_valid_date)]`, em que `_valid_date` chama `date.fromisoformat(v)` e devolve `v` (o `ValueError` vira 422 sozinho). Ver "Armadilhas" 3.
  - [ ] 4.2 `TaskCreate(BaseModel)`: `model_config = ConfigDict(extra="forbid")`, campos `title: Title` e `due_date: DueDate`. **Sem** `done` e **sem** `tags` (AC 6).
  - [ ] 4.3 `Task(BaseModel)` de resposta: `id: int`, `title: str`, `due_date: str`, `tags: list[str]`, `done: bool`.
  - [ ] 4.4 `get_db()`: `conn = repo.connect()`; `try: yield conn` / `finally: conn.close()`.
  - [ ] 4.5 `router = APIRouter()` com rotas **`def`** (não `async def`):
    - `POST /tasks` → `status_code=201`, `response_model=Task`; insere e devolve `repo.get_task(...)`.
    - `GET /tasks` → `list[Task]`, sem parâmetros de filtro ainda (`tag`/`due` são da 2.1/2.2).
    - `GET /tasks/{task_id}` → `task_id: int`; se `None`, `raise HTTPException(404, detail=...)` marcado como 404 **de tarefa** (ver 5.3).
  - [ ] 4.6 A dependência `now` **ainda não é usada por nenhuma rota** na 1.1 (nenhuma regra de "hoje" no épico 1). Não criar parâmetro morto; a 2.2 injeta `Depends(domain.now)`. A fixture `set_now` funciona mesmo assim (override é só uma entrada no dicionário).
- [ ] **Tarefa 5: `app/main.py` — app e envelope de erro** (AC: 3, 4, 6, 8, 9)
  - [ ] 5.1 `app = FastAPI(title="API de Tarefas")`; `app.include_router(api.router)`.
  - [ ] 5.2 Uma função `_error(status, code, field) -> JSONResponse` que monta `{"error": {"code", "field", "message"}}`, com `message` em português derivado de `code` + `field` (ex.: `"Campo inválido: title"`, `"Tarefa não encontrada"`, `"Rota não encontrada"`, `"Método não permitido"`, `"Erro interno"`).
  - [ ] 5.3 Handler de `RequestValidationError`: 422, `validation_error`, `field = ".".join(str(p) for p in exc.errors()[0]["loc"][1:]) or None`.
  - [ ] 5.4 Handler de **`starlette.exceptions.HTTPException`** (não o do FastAPI; senão rota inexistente e 405 escapam com `{"detail": ...}`): 404 → `not_found` com `field = "id"` se veio da rota de tarefa, senão `None`; 405 → `method_not_allowed`, `field: None`. Sugestão simples: na rota, `raise HTTPException(404, detail="task_not_found")` e o handler testa `exc.detail == "task_not_found"`. Preservar `exc.headers` (o 405 traz `Allow`).
  - [ ] 5.5 Handler de `Exception`: 500, `internal_error`, `field: None`.
- [ ] **Tarefa 6: `tests/conftest.py` — fixtures do AD-8** (AC: 11)
  - [ ] 6.1 `client(tmp_path, monkeypatch)`: `monkeypatch.setenv("TASKS_DB_PATH", str(tmp_path / "tasks.db"))`; `with TestClient(app) as c: yield c`; no teardown, `app.dependency_overrides.clear()`.
  - [ ] 6.2 `set_now`: fixture que devolve uma função `_set(instante_utc: str)` que faz `app.dependency_overrides[domain.now] = lambda: datetime.fromisoformat(instante_utc)` (aceita `"2026-10-02T15:00Z"`; `fromisoformat` do 3.11+ entende o `Z`). Substitui **só** `now`, nunca `today` (AD-2). Depende de `client` para herdar a limpeza.
  - [ ] 6.3 Só estas duas fixtures moram aqui; as stories seguintes não redefinem fixtures.
- [ ] **Tarefa 7: `tests/test_tasks.py`** (AC: 2–11)
  - [ ] 7.1 POST válido → 201 e corpo exato do AC 2 (exceto o valor de `id`, que é `int`).
  - [ ] 7.2 `@pytest.mark.parametrize` dos títulos inválidos (ausente, `""`, `"   "`) → 422, `code`/`field == "title"`, e `GET /tasks == []` depois.
  - [ ] 7.3 Parametrize dos prazos do AC 4 (ausente, `"2026-02-30"`, `"2026-10-02T00:00:00Z"`, `"02/10/2026"`, `1790899200`) → 422, `field == "due_date"`, nada gravado.
  - [ ] 7.4 Prazo no passado (`"2020-01-01"`) → 201 e `done is False`.
  - [ ] 7.5 Campos extras `done` e `tags` → 422 `validation_error` (conferir `field` igual ao nome do campo extra).
  - [ ] 7.6 Lista vazia `[]`; ordenação com prazos fora de ordem + empate (empate resolvido pelo `id` crescente).
  - [ ] 7.7 `GET /tasks/{id}` existente → 200; inexistente (ex.: `999`) → 404, `not_found`, `field == "id"`.
  - [ ] 7.8 Rota inexistente (`GET /nada`) → 404 `not_found`, `field is None`; método não suportado (ex.: `PUT /tasks`) → 405 `method_not_allowed`, `field is None`; em ambos, `"detail" not in body`.
  - [ ] 7.9 Persistência: criar com `client`, abrir um **segundo** `TestClient(app)` com o mesmo `TASKS_DB_PATH` e achar a tarefa; com `sqlite3` direto no arquivo, conferir que `tasks` e `task_tags` existem (`sqlite_master`).
  - [ ] 7.10 Um teste curto do relógio: `domain.today(datetime.fromisoformat("2026-10-03T01:00Z")) == date(2026, 10, 2)` (garante que `tzdata`/`ZoneInfo` funcionam desde já).
  - [ ] 7.11 Testes conferem `code` e `field`, **nunca** o texto de `message` (AD-7).
- [ ] **Tarefa 8: `README.md` na raiz do projeto** (AC: 12)
  - [ ] 8.1 Em português: pré-requisitos (`uv`, Python 3.14), `uv sync`, `uv run pytest`, `TASKS_DB_PATH` (padrão `./tasks.db`).
  - [ ] 8.2 Rodar: `uv run uvicorn app.main:app --host <IP interno> --port 8000`, com o aviso de **nunca** usar `0.0.0.0` em máquina exposta: a API não tem autenticação (NFR5).
  - [ ] 8.3 `curl` de criar (`-X POST -H 'Content-Type: application/json' -d '{"title": "Revisar PR", "due_date": "2026-10-10"}'`), listar e consultar, com a resposta esperada; um exemplo de erro 422 mostrando o envelope. Deixar um lugar evidente para o `curl` de tags/vencidas que a 2.2 completa.
- [ ] **Tarefa 9: Portão de qualidade** (AC: 1)
  - [ ] 9.1 `uv run ruff format`, `uv run ruff check`, `uv run ruff format --check`, `uv run pytest`, tudo verde.
  - [ ] 9.2 `grep -rn "date.today\|datetime.now" app/` só pode achar `domain.now()` (AD-2).
  - [ ] 9.3 Conferir que `app/domain.py` não importa `api`, `repo`, `fastapi` nem `sqlite3`.

## Dev Notes

### Contexto

- Greenfield: **não há código no repositório**. Nenhum arquivo é UPDATE; todos são NEW. A raiz do repositório git é `api-tarefas/`, que já contém `.claude/`, `_bmad/`, `_bmad-output/` e `docs/` — não mexer nessas pastas.
- Esta story estabelece a base que 1.2, 1.3, 2.1 e 2.2 vão estender. O que nasce aqui e **não pode ser redefinido depois**: os tipos `Title`/`DueDate`, o `get_db()`, os três handlers de erro, o esquema completo, `repo.load_tags`, e as fixtures `client`/`set_now`.
- O que **não** entra aqui (para não invadir as stories paralelas): `PATCH` (1.2), `DELETE` (1.3), tags na entrada, `normalize_tags`, `replace_tags`, `?tag=` (2.1), `window_bounds`, `?due=`, uso de `now` em rota (2.2).

### Requisitos técnicos e guardrails da arquitetura

- **AD-1:** Python 3.14, FastAPI, `sqlite3` da stdlib. Só as 6 dependências listadas. Uma dependência nova precisa de um AD.
- **Camadas:** `api → domain`, `api → repo`, `repo → domain`. Nada mais. `main.py` monta o app e os handlers.
- **AD-2:** só `domain.now()` lê o relógio; "hoje" só via `domain.today(now)`. Proibido `date.today()`/`datetime.now()` em qualquer outro lugar (inclusive nos testes, que usam instantes fixos).
- **AD-4:** schemas de entrada com `extra="forbid"`; `POST` não aceita `done` nem (por enquanto) `tags`. Toda regra que gera 422 mora em validador Pydantic, nunca em `if` na rota (AD-7).
- **AD-5:** o esquema inteiro (inclusive `task_tags` com `ON DELETE CASCADE`) nasce na 1.1 — desvio aceito, achado M2 do readiness.
- **AD-6:** a tarefa é sempre `{"id": int, "title": str, "due_date": "YYYY-MM-DD", "tags": [str], "done": bool}`; o `POST` devolve a **tarefa inteira** (não só o `id`); lista ordenada por `due_date`, depois `id`.
- **AD-7:** envelope `{"error": {"code", "field", "message"}}` com os códigos fechados `validation_error | not_found | method_not_allowed | internal_error`.
- **AD-10:** `repo.connect()` é o único que abre conexão; lê `TASKS_DB_PATH` a cada chamada; uma conexão por requisição via `get_db()` com `yield`; rotas `def`; escrita de várias linhas em `with conn:`.
- Convenções: código e nomes em inglês `snake_case`; `message`, README e commits em português.

### Armadilhas conhecidas (ler antes de codar)

1. **pytest vai coletar testes de `.claude/skills/**/tests/`** se não houver `testpaths = ["tests"]`. E sem `pythonpath = ["."]`, `import app` falha nos testes (o projeto `uv --app` não é instalado como pacote).
2. **ruff vai lintar os scripts Python em `.claude/` e `_bmad/`** e o portão do AC 1 quebra por código que não é nosso. Use `extend-exclude`.
3. **`datetime.date` do Pydantic em modo lax aceita `1790899200` (timestamp) e `"2026-10-02T00:00:00Z"` (datetime com hora zero)** — exatamente os casos que o AC 4 manda rejeitar. Por isso `DueDate` é `str` com `pattern` + `date.fromisoformat`. A ordem importa: o `pattern` vem antes, porque `date.fromisoformat` no Python 3.11+ também aceita formatos como `"20261002"`. Um `int` não passa por `str` (Pydantic v2 não converte número em texto), então o 422 sai com `field: "due_date"`.
4. **`sqlite3` + rotas `def`:** o FastAPI roda a dependência síncrona `get_db` e a rota no threadpool, e podem ser **threads diferentes**. Sem `check_same_thread=False`, aparece `ProgrammingError: SQLite objects created in a thread can only be used in that same thread`. É seguro: cada requisição tem a sua conexão e a usa em sequência.
5. **`with conn:` não fecha a conexão**, só faz commit/rollback. Quem fecha é o `finally` do `get_db()`. Leituras não precisam de `with conn:`.
6. **Handler de `Exception` + `TestClient`:** o `TestClient` relança exceções do servidor por padrão (`raise_server_exceptions=True`). Se quiser testar o 500, use `TestClient(app, raise_server_exceptions=False)` num teste próprio — opcional, não está nos ACs.
7. **Handler de HTTPException:** registrar para `starlette.exceptions.HTTPException`. O `fastapi.HTTPException` é subclasse, então também cai nele.
8. **`field` do 422:** `loc` vem como `("body", "title")`, `("body", "due_date")`, `("body", "done")` (extra), ou só `("body",)` quando o corpo inteiro é inválido (JSON quebrado, lista em vez de objeto). No último caso o join dá `""` → devolver `None`.
9. **Override de dependência no `set_now`:** a chave do `dependency_overrides` tem de ser o objeto `domain.now` exato que a rota usará em `Depends(domain.now)` (na 2.2). Não envolver `now` em outra função.
10. **`uv init`** cria um `main.py` de exemplo na raiz e pode criar `.python-version`: apague o `main.py`; manter `.python-version` com `3.14` é aceitável.

### Bibliotecas e versões (spine, conferidas em 2026-10-02)

| Pacote | Versão | Observação |
| --- | --- | --- |
| Python | 3.14 (`>=3.14`) | 3.14.7 já instalado na máquina (Homebrew e uv) |
| uv | 0.12.22 no spine | a máquina tem 0.12.19; funciona igual para esta story |
| fastapi | 0.142.2 | traz Pydantic 2.13.x e Starlette |
| uvicorn | 0.54.0 | sem extras `[standard]` |
| tzdata | 2026.4 | garante `ZoneInfo("America/Sao_Paulo")` em qualquer SO |
| pytest | 9.1.1 | dev |
| httpx | 0.28.1 | dev, exigido pelo `TestClient` |
| ruff | 0.16.10 | dev |

APIs a usar: `typing.Annotated`, `pydantic.StringConstraints`, `pydantic.AfterValidator`, `pydantic.ConfigDict(extra="forbid")`, `fastapi.exceptions.RequestValidationError`, `starlette.exceptions.HTTPException`, `fastapi.testclient.TestClient`, `datetime.UTC`, `zoneinfo.ZoneInfo`.

### Estrutura de arquivos (todos NEW)

```text
api-tarefas/
  pyproject.toml   uv.lock   .gitignore   README.md
  app/__init__.py
  app/main.py      # app + 3 handlers (AD-7)
  app/api.py       # Title, DueDate, TaskCreate, Task, get_db, router (AD-4, AD-6)
  app/domain.py    # now(), today() (AD-2)
  app/repo.py      # SCHEMA, connect(), insert_task, get_task, list_tasks, load_tags (AD-5, AD-9, AD-10)
  tests/conftest.py
  tests/test_tasks.py
```

`tests/test_filters.py` é da story 2.2; não criar.

### Testes

- pytest + `TestClient` contra o app real; banco descartável por teste via fixture `client` (AD-8).
- Conferir `code` e `field`, nunca `message`.
- Preferir `@pytest.mark.parametrize` para os casos de 422 em vez de um teste por caso.
- `uv run pytest` verde é condição para o commit da story.

### Inteligência de stories anteriores

Não se aplica: é a primeira story. As stories 1.2, 1.3, 2.1 e 2.2 estão sendo criadas em paralelo, então não houve leitura de outros arquivos de story nem análise de commits de código (o git só tem commits de planejamento).

### Pesquisa de versões

Não foi refeita: o spine registra as versões conferidas no PyPI/python.org em 2026-10-02 (hoje). As armadilhas 3, 4, 6 e 7 descrevem comportamento de Pydantic v2/FastAPI/Starlette relevante para essas versões.

### Project Structure Notes

- Alinhado à Structural Seed do spine. Única variação: `app/__init__.py`, necessário para `app.main:app` ser importável de forma explícita.
- `repo.load_tags` nasce na 1.1 (antes da 2.1) para que a resposta já leia `tags` pelo caminho único do AD-9. A 2.1 acrescenta `replace_tags` e o filtro, sem reescrever `load_tags`.
- Não existe `project-context.md` no projeto.

### Perguntas em aberto (registradas, não bloqueiam)

1. **`field` quando o corpo inteiro é inválido** (`loc == ("body",)`): o AD-7 não diz; esta story adota `null`. Confirmar com o arquiteto.
2. **`set_now` antes de uso (m1 do readiness):** mantido conforme AD-8; nenhuma rota da 1.1 depende de `now`.
3. **Divisão da story (M1):** se o dev travar, o readiness sugere "1.1a criar e consultar" / "1.1b listar". A ordem das tarefas já permite parar após a Tarefa 7.
4. **`repo.load_tags` na 1.1:** decisão desta story para cumprir o AD-9 desde já; a story 2.1 (criada em paralelo) deve reutilizá-lo, não recriá-lo. Conferir consistência quando as cinco stories estiverem prontas.
5. **Marcação do 404 de tarefa:** sugerido `detail="task_not_found"`; qualquer mecanismo serve, desde que o 404 de rota continue com `field: null`.
6. **FR1 diz "ISO 8601"** e a story aceita só `YYYY-MM-DD` (m3 do readiness); a story segue o AD-4 e o addendum.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1: Criar, listar e consultar tarefas]
- [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- [Source: _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/ARCHITECTURE-SPINE.md#AD-1 a AD-10, Consistency Conventions, Stack, Structural Seed]
- [Source: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/prd.md#FR-1, FR-2, NFR-1, NFR-3, NFR-4, NFR-5]
- [Source: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/addendum.md#Pistas de contrato da API]
- [Source: _bmad-output/planning-artifacts/implementation-readiness-report-2026-10-02.md#M1, M2, m1, m3, m4, m5]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- Análise de contexto concluída: guia completo do desenvolvedor criado (bmad-create-story, 2026-10-02).

### File List
