# Epic 1 Context: Cadastrar e manter tarefas

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Dar ao dev do time-piloto o CRUD completo de tarefas: criar com título, prazo e tags (inclusive tarefas já atrasadas, recadastradas da planilha), listar todas em ordem de prazo, editar, concluir e excluir, com as tarefas sobrevivendo ao reinício da API. O épico também cria o projeto do zero (Structural Seed) e fixa as camadas, o contrato HTTP, a validação e as assinaturas do repo que o Épico 2 (janelas de prazo e filtro por tag) vai reutilizar sem alterar.

## Stories

- Story 1.1: Criar e listar tarefas
- Story 1.2: Etiquetar tarefas na criação
- Story 1.3: Excluir tarefa
- Story 1.4: Editar e concluir tarefa

## Requirements & Constraints

- **Criar:** `titulo` e `prazo` são obrigatórios e `tags` é opcional. Título vazio ou só com espaços dá 422. `prazo` fora de `YYYY-MM-DD` ou com data inexistente (`2026-02-30`) dá 422. Prazo no passado é aceito, e a tarefa já nasce vencida. A tarefa nasce pendente, e a resposta traz a tarefa criada com `id`.
- **Editar:** a edição é parcial, e campo omitido mantém o valor. Os campos enviados passam pelas mesmas validações da criação. Ligar `concluida` mantém a tarefa na listagem geral. Tarefa inexistente dá 404.
- **Excluir:** a exclusão é definitiva e remove a tarefa e as tags dela. Tarefa inexistente dá 404.
- **Listagem geral:** traz todas as tarefas, concluídas ou não, inteiras, sem paginação, sem filtro por concluída e ordenadas por prazo.
- **Tags:** tag vazia ou só com espaços dá 422. A tag é aparada nas pontas, e a comparação não diferencia maiúsculas de minúsculas. Tag repetida na mesma tarefa é guardada uma vez, com a grafia e a posição da primeira ocorrência. No PATCH, enviar `tags` substitui a lista e omitir mantém. O filtro por tag é do Épico 2.
- **Persistência:** as tarefas sobrevivem ao reinício da API.
- **Rede interna:** a API não tem autenticação.
- **Escopo:** nada além de FR-1 a FR-6. Ficam de fora paginação, `GET /tarefas/{id}`, filtro por várias tags, autenticação, migrações, Docker e CI.
- **Armadilhas da v1 anterior:** `id` de path acima de `2**63-1` deve dar 422, nunca 500. Um PATCH concorrente com uma exclusão deve dar 404, nunca 500.

## Technical Decisions

- **Stack:** Python 3.14, uv 0.12, FastAPI 0.142.2 sem `[standard]`, Pydantic 2.13.5, uvicorn 0.54.0 e tzdata 2026.5. Em dev, pytest 9.1.1, httpx 0.28.1 (não `httpx2`) e ruff 0.16.10, com ruff configurado só com `target-version = "py314"` e `extend-exclude = ["_bmad", ".claude"]`. O projeto nasce de `uv init --package`, com `src/tarefas/{api,domain,repo}.py`, `tests/conftest.py` e `tests/test_tarefas.py`.
- **Camadas:** a direção é `api → domain ← repo`. `domain.py` não importa nada externo (nem FastAPI, nem Pydantic, nem sqlite3), e `repo.py` nunca importa `api`. Regra de prazo, janela e tag fica só em `domain.py`.
- **Contrato HTTP:**
  - `POST /tarefas` devolve 201 com a tarefa.
  - `GET /tarefas` devolve 200 com um array JSON, sem envelope.
  - `PATCH /tarefas/{id}` devolve 200 com a tarefa.
  - `DELETE /tarefas/{id}` devolve 204 sem corpo.
  - Tarefa inexistente dá 404 via `HTTPException`. Os erros seguem o formato `{"detail": ...}`.
  - As rotas são `def` (síncronas).
- **JSON da tarefa:** `{"id": int, "titulo": str, "prazo": "YYYY-MM-DD", "tags": [str], "concluida": bool}`.
- **Validação:**
  - Os schemas usam `extra="forbid"`.
  - `titulo` passa por strip e tem de 1 a 200 caracteres.
  - `prazo` é `Annotated[date, BeforeValidator(...)]`, que exige uma `str` casando `^\d{4}-\d{2}-\d{2}$`. Não use `Strict()`, porque no corpo do FastAPI ele rejeita até `"2026-10-06"`.
  - Cada tag tem no máximo 50 caracteres depois do strip.
  - `concluida` é `StrictBool`.
  - O POST não aceita `concluida`.
  - No PATCH, todo campo é opcional e `null` dá 422. `{}` devolve 200 com a tarefa inalterada, e `tags: []` limpa a lista.
  - A validação (422) vem antes da busca do id (404).
  - O `id` de path é declarado com `le=2**63-1`.
- **Tags:** `domain.norm_tag(s)` = `s.strip().casefold()`. `domain.normalizar_tags(lista)` apara, levanta `ValueError` para tag vazia e remove duplicadas por `norm_tag`, mantendo a primeira grafia. O schema chama `normalizar_tags` num validator. O repo grava `nome_norm` com `norm_tag`. Nenhuma outra camada faz `lower` ou `casefold`. As tags voltam em ordem de inserção (`ORDER BY rowid`).
- **Tipo entre camadas:** `domain.Tarefa` é uma dataclass (`id: int, titulo: str, prazo: date, tags: list[str], concluida: bool`) e o único tipo que o repo devolve. O repo nunca devolve `sqlite3.Row` nem dict. As conversões 0/1 e ISO ficam dentro do repo.
- **Assinaturas do repo:** toda função recebe `conn` como primeiro argumento.
  - `criar(conn, titulo, prazo, tags) -> Tarefa`
  - `listar(conn, *, pendentes=False, de=None, ate=None, tag=None) -> list[Tarefa]`. No Épico 1, só a listagem geral é usada.
  - `editar(conn, id, campos: dict) -> Tarefa | None`, com `campos` vindo de `model_dump(exclude_unset=True)`.
  - `excluir(conn, id) -> bool`.
  - `None` ou `False` significa id inexistente, e a rota levanta 404.
- **Ordenação:** toda listagem usa `ORDER BY prazo ASC, id ASC`.
- **Schema:**
  - `tarefa(id INTEGER PRIMARY KEY AUTOINCREMENT, titulo, prazo TEXT ISO, concluida INTEGER 0/1)`.
  - `tarefa_tag(tarefa_id FK ON DELETE CASCADE, nome, nome_norm, UNIQUE(tarefa_id, nome_norm))`.
  - O schema é criado por `repo.criar_schema(conn)` com `CREATE TABLE IF NOT EXISTS`, sem migrações. O SQL fica só em `repo.py`, com sqlite3 puro, sem ORM.
- **Conexão:**
  - Há uma conexão por request, aberta na dependência `api.conexao` (com `yield`, `check_same_thread=False` e `PRAGMA foreign_keys=ON`).
  - `TAREFAS_DB` (padrão `tarefas.db`) é lido a cada abertura da conexão, nunca na importação.
  - `criar_schema` é chamado pela dependência, não pelo lifespan.
- **Transações:** cada escrita roda em `with conn:`. A tarefa e as tags são gravadas na mesma transação. No PATCH, `editar` confere, grava (apagando e reinserindo as tags) e relê na mesma transação, e devolve `None` se a tarefa sumiu.
- **Relógio:** o Épico 1 não filtra por data, mas nunca use `date.today()` nem `datetime.now()`. A única leitura do relógio será `api.agora()`.
- **Testes:**
  - Há um único `tests/conftest.py`, com a fixture `client`, que fixa `api.agora` via `app.dependency_overrides` e aponta `TAREFAS_DB` para `tmp_path` com `monkeypatch.setenv`.
  - Nenhum teste cria outro `TestClient`.
  - A persistência é verificada abrindo `sqlite3.connect(os.environ["TAREFAS_DB"])` e chamando `repo.listar`.
  - Os comandos são `uv run pytest`, `uv run ruff check` e `uv run ruff format`.
- **Nomes:** identificadores em português, sem acento (`titulo`, `prazo`, `concluida`, `tags`).

## Cross-Story Dependencies

- A 1.1 cria o projeto, a fixture `client`, a dependência `api.conexao`, a tabela `tarefa` e as funções `repo.criar` e `repo.listar`. Todas as outras stories dependem dela.
- A 1.2 acrescenta a tabela `tarefa_tag` e `domain.norm_tag`/`normalizar_tags`. A 1.3 (cascade das tags) e a 1.4 (substituição de tags) dependem da 1.2.
- A 1.4 reutiliza as validações da 1.1 e da 1.2 no PATCH.
- O Épico 2 estende `repo.listar` (`tag`, `pendentes`, `de`, `ate`) e acrescenta `api.agora`, `domain.hoje`, `Janela` e `intervalo`, sem alterar o contrato fixado aqui.
