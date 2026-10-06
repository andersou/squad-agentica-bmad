---
title: 'Story 1.1: Criar e listar tarefas'
type: 'feature'
created: '2026-10-06'
status: 'done'
baseline_commit: '0c5e87b501e5d5b2d174b3a9ea918cd33fe19e07'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-06/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** O repositório só tem planejamento. O dev do time-piloto ainda não consegue recadastrar as tarefas da planilha, inclusive as atrasadas, nem vê-las em ordem de prazo.

**Approach:** Criar o projeto do zero pelo Structural Seed (`uv init --package`) e entregar `POST /tarefas` e `GET /tarefas` nas três camadas (`api → domain ← repo`), com a validação do AD-6 e a persistência em SQLite do AD-8.

## Boundaries & Constraints

**Always:** seguir AD-1 a AD-9 do spine e as convenções do AGENTS.md. O JSON da tarefa é `{"id", "titulo", "prazo": "YYYY-MM-DD", "tags": [], "concluida": false}`. Toda listagem usa `ORDER BY prazo ASC, id ASC`. `criar` roda em `with conn:`. Rotas `def`, sem autenticação. As versões vêm do spine.

**Never:** campo `tags` no POST (é da 1.2), tabela `tarefa_tag`, `PATCH`/`DELETE`, `GET /tarefas/{id}`, paginação, `janela`, `api.agora`/`domain.hoje` (são do Épico 2), README com conteúdo (é da 2.3), ORM, `Strict()` no `prazo`, `date.today()`/`datetime.now()`, outro `TestClient` além da fixture.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Criar com prazo passado | `{"titulo": "Migrar planilha", "prazo": "2026-10-01"}` | 201, `{"id": int, "titulo": "Migrar planilha", "prazo": "2026-10-01", "tags": [], "concluida": false}` | N/A |
| Título aparado | `{"titulo": "  x  ", "prazo": "2026-10-06"}` | 201, `titulo` = `"x"`, gravado assim | N/A |
| Corpo inválido | sem `titulo`; sem `prazo`; `titulo` `""` ou `"   "`; `titulo` com 201 caracteres após strip; `prazo` `"06/10/2026"`, `"2026-02-30"`, `"2026-10-06T00:00:00"` ou `20261006`; com `concluida`; com campo desconhecido | 422 `{"detail": ...}` | nada é gravado |
| Listar | tarefas criadas fora de ordem, duas com o mesmo prazo | 200, array sem envelope, ordenado por `prazo ASC, id ASC` | N/A |
| Persistência | tarefa criada via `client` | `repo.listar(sqlite3.connect(os.environ["TAREFAS_DB"]))` a devolve | N/A |

</frozen-after-approval>

## Code Map

Repositório sem código: só `AGENTS.md`, `CLAUDE.md`, `_bmad/`, `.claude/` e `_bmad-output/`. Não tocar em `_bmad/` nem em `.claude/`. `uv 0.12.23` e CPython 3.14 estão instalados.

- `pyproject.toml` -- novo, via `uv init --package --name tarefas --python 3.14`
- `src/tarefas/domain.py` -- novo: dataclass `Tarefa`
- `src/tarefas/repo.py` -- novo: `criar_schema`, `criar`, `listar`
- `src/tarefas/api.py` -- novo: `app`, `conexao`, schema `TarefaCriar`, rotas
- `tests/conftest.py`, `tests/test_tarefas.py` -- novos

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml` -- `uv init --package --name tarefas --python 3.14`; `uv add fastapi==0.142.2 uvicorn==0.54.0 tzdata==2026.5`; `uv add --dev pytest==9.1.1 httpx==0.28.1 ruff==0.16.10`; `[tool.ruff]` com `target-version = "py314"` e, por decisão do Anderson, `extend-exclude = ["_bmad", ".claude"]`; remover o `main()` e o `[project.scripts]` gerados -- Structural Seed; o lock deve resolver Pydantic 2.13.5
- [x] `.gitignore` -- ignorar `.venv/`, `__pycache__/`, `*.db` -- não versionar ambiente nem banco
- [x] `src/tarefas/domain.py` -- `@dataclass Tarefa(id: int, titulo: str, prazo: date, tags: list[str], concluida: bool)`, sem imports externos -- AD-1, AD-9
- [x] `src/tarefas/repo.py` -- `criar_schema(conn)` com `CREATE TABLE IF NOT EXISTS tarefa(id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, prazo TEXT NOT NULL, concluida INTEGER NOT NULL DEFAULT 0)`; `criar(conn, titulo, prazo, tags) -> Tarefa` em `with conn:`; `listar(conn) -> list[Tarefa]` com `ORDER BY prazo ASC, id ASC` -- AD-4, AD-8, AD-9
- [x] `src/tarefas/api.py` -- `conexao()` com `yield` (lê `TAREFAS_DB`, padrão `tarefas.db`, a cada abertura; `check_same_thread=False`; `PRAGMA foreign_keys=ON`; `criar_schema`; fecha no fim); `TarefaCriar` com `extra="forbid"`, `titulo` strip 1–200, `prazo` via `BeforeValidator`; `POST /tarefas` 201 e `GET /tarefas` 200 -- AD-6, AD-7, AD-8
- [x] `tests/conftest.py` -- fixture `client`: `monkeypatch.setenv("TAREFAS_DB", str(tmp_path / "tarefas.db"))` e `TestClient(app)` -- banco novo por teste
- [x] `tests/test_tarefas.py` -- um teste por linha da I/O Matrix (inválidos parametrizados) e um teste de AD-1 que lê os imports de `domain.py` e `repo.py` -- cobre a matriz e as camadas

**Acceptance Criteria:**
- Given o projeto criado, when rodo `uv run pytest`, `uv run ruff check` e `uv run ruff format --check`, then os três passam.
- Given `domain.py` e `repo.py`, when inspeciono os imports, then `domain` só importa stdlib e `repo` não importa `api`.
- Given a API rodando com `TAREFAS_DB` absoluto, when crio uma tarefa, reinicio a API e chamo `GET /tarefas`, then a tarefa continua lá.

### Review Findings

Code review de 2026-10-06 (`0c5e87b..f9cc065`; camadas blind-hunter, edge-case-hunter, verification-gap e acceptance-auditor).

- [x] [Review][Decision] Surrogate UTF-16 solto no corpo dá 500 — `{"titulo": "a\ud800b", ...}` estoura `UnicodeEncodeError` no `INSERT` do sqlite. `{"prazo": "\ud800"}` também dá 500, porque o 422 repete o `input` e o `JSONResponse` não consegue codificá-lo. Um validator no `titulo` não resolve, porque o 500 só muda para a renderização do 422. A correção completa pede um handler de `RequestValidationError` que serialize com `ensure_ascii`, mais a rejeição do surrogate nos campos `str`. Nada é gravado em nenhum dos casos. **Decisão do Anderson (2026-10-06): rejeitado.** Só acontece com entrada fabricada numa API interna, não perde dados, e segue o mesmo critério do achado #16.
- [x] [Review][Patch] O desempate `id ASC` (AD-4) ficou sem teste, adiado com a premissa falsa de que não dava para provocar a falha [tests/test_tarefas.py:75] — o teste cria o índice `(prazo, id DESC)` antes do GET. Sem o `id ASC` ele falha (confirmado por mutação). O `deferred-work.md` foi removido.
- [x] [Review][Patch] Nenhum teste cobre o fallback de `TAREFAS_DB=""` [tests/test_tarefas.py:68] — `test_tarefas_db_vazio_usa_padrao`. Ele falha com `os.environ.get("TAREFAS_DB", "tarefas.db")` (confirmado por mutação).
- [x] [Review][Patch] `test_criar_com_tags_falha_ate_story_1_2` vazava a conexão quando a asserção falhava e não usava a fixture `client` [tests/test_tarefas.py:142] — agora fecha num `try/finally` e usa o banco da fixture.
- [x] [Review][Patch] O teste de 200 caracteres não conferia o título gravado [tests/test_tarefas.py:60] — passa a verificar que volta `"a" * 200`.
- [x] [Review][Patch] O sprint-status estava em `review` com a spec em `done` [sprint-status.yaml] — os dois estão em `done` depois da decisão acima.

AC 3 conferido à mão: POST, reinício do uvicorn com `TAREFAS_DB` absoluto e GET devolve a tarefa. `uv tree --package pydantic` mostra 2.13.5.

**Rejected:**
- `listar(conn)` mais estreito que o AD-9 e fixture sem `api.agora`, sem registro no spine — false: o spine descreve o estado final, e o `epic-1-context.md` (Cross-Story Dependencies) já diz que o Épico 2 estende `listar` e acrescenta `api.agora`. Não há divergência a registrar.
- Spec Change Log vazio e `review_loop_iteration: 0` — rejeitado: a correção edita a spec sob revisão.
- Faltam testes de `titulo` 123/`null`, `prazo` `null`/`" 2026-10-06"`/`"2026-1-6"` e corpo não JSON — false: o comportamento está certo (422), e a matriz da spec está coberta. O regex já é protegido pelos casos `06/10/2026` e `T00:00:00`.
- Falta guarda automática contra `date.today()` e SQL fora do `repo` — false: não há violação no diff.
- `uv tree --depth 1` na Verification — false: ele mostra as versões das dependências diretas, e o Pydantic tem o próprio comando.
- `test_camadas` não usa `client` — false: é análise estática, sem banco nem relógio, e nenhum dano foi apontado.

## Implementation Notes

- ruff 0.16 habilita por padrão muitas regras e, sem `exclude`, `uv run ruff check`/`ruff format` sem argumentos varrem `_bmad/` e `.claude/` (55 achados no check; o format reescreveu 24 arquivos lá, revertidos com `git checkout`). `uv run ruff check src tests` e `uv run ruff format --check src tests` passam. Decisão do Anderson (2026-10-06): acrescentar `extend-exclude = ["_bmad", ".claude"]` ao `[tool.ruff]`. **Desvio do spine:** a convenção Estilo pede "sem config extra além de `target-version`". O exclude não muda regras, só tira da varredura as pastas instaladas pelo BMAD, e assim `uv run ruff check`/`format` sem argumentos funcionam como diz o AGENTS.md.

## Spec Change Log

## Review Triage Log

Passada 1 (blind-hunter, edge-case-hunter, verification-gap):

| # | Achado | Veredito | Evidência | Rota |
|---|---|---|---|---|
| 1 | `test_camadas` não pega `from tarefas import api`, `from . import api` nem `from .api import x` em `repo.py` | low | O `ast` grava `module` = `tarefas`/`None`/`api`, e nenhum desses casa com `tarefas.api`. A violação do AD-1 passaria no teste | patch |
| 2 | `test_camadas` aceita `sqlite3` em `domain.py` | low | `sqlite3` está em `sys.stdlib_module_names`, e o AGENTS.md proíbe esse import no domain | patch |
| 3 | `repo.criar` descarta `tags` em silêncio | low | Real: o único chamador passa `[]`, mas um chamador novo perderia as tags sem erro. A correção é clara, e a política do AGENTS.md manda corrigir os baixos | patch: `NotImplementedError` com tags não vazias |
| 4 | O regex `\d` aceita dígitos não ASCII no `prazo` | false | `"٢٠٢٦-١٠-٠٦"` e `"２０２６-10-06"` dão 422, porque o parse de `date` rejeita | — |
| 5 | Faltam testes de tipo e de corpo (`titulo` 123/`null`, `[]`, `"x"`, corpo não JSON) | false | Todos testados à mão: 422 e nada gravado | — |
| 6 | O sprint-status está em `in-progress` e a spec em `in-review` | false | O workflow só sincroniza `in-progress` e `done`. A story vai para `done` no fechamento | — |
| 7 | `uv tree --depth 1` não mostra o Pydantic | low | Real: o Pydantic é transitivo | patch na spec: Verification passa a usar `uv tree --package pydantic` |
| 8 | O desvio do ruff não foi levado ao spine, e o TODO do AGENTS.md ficou desatualizado | low | Real. Mexer no spine (`status: final`) e no AGENTS.md vai além do que foi decidido ("anotar na spec") | pergunta para o Anderson |
| 9a | `description` é o placeholder do `uv init` | low | Texto "Add your description here" no `pyproject.toml` | patch |
| 9b | O e-mail em `authors` é pessoal e não bate com a identidade da conta | false | É o mesmo e-mail do `git config` do autor, que já assina os commits | — |
| 10 | `uv.lock` fora do diff | false | Foi excluído só do arquivo de revisão. Entra no commit | — |
| 11 | `response_model=` repete a anotação de retorno | low | São duas fontes do mesmo modelo, que podem divergir | patch |
| 12 | A fixture não troca `api.agora` nem limpa `dependency_overrides` | false | `api.agora` ainda não existe (Épico 2), não há override para vazar, e o AC da fixture na 1.1 só pede `TAREFAS_DB` | — |
| 13 | Com `TAREFAS_DB=""`, o `sqlite3.connect("")` abre um banco temporário e as escritas somem | low | `os.environ.get` devolve `""` quando a variável existe vazia | patch |
| 14 | `OperationalError` do sqlite (diretório inexistente, lock) vira 500 | low | Não aparece no uso normal, e a correção acrescenta tratamento. O lock está no Deferred do spine. Rejeitado | — |
| 15 | Falta CHECK de `prazo`/`concluida` no schema | false | Só o repo grava, sempre com `isoformat()` e o padrão 0 | — |
| 16 | Título só com caracteres invisíveis (`​`) é aceito | low | Fora da regra do PRD, que fala em vazio ou só espaços, e a correção acrescenta validador. Rejeitado | — |
| 17 | A task diz "`[tool.ruff]` só com `target-version`", mas o pyproject tem exclude | low | Real: o texto da task ficou desatualizado | patch na spec: a task cita o `extend-exclude` decidido |
| 18 | O teste de desempate passa sem `id ASC` (gap) | medium | A ordem do scan por rowid coincide com a do id. Não dá para provocar a falha na 1.1 | defer → patch na code review (2026-10-06): a premissa era falsa |

Achado 8 resolvido depois do commit da story: o Anderson aprovou registrar o desvio na convenção Estilo do spine e tirar o TODO do AGENTS.md.

Conferência dos AD contra o diff:
- **AD-1:** `domain` importa só `dataclasses`/`datetime`, e `repo` só `sqlite3`/`datetime`/`tarefas.domain`.
- **AD-2:** nenhuma leitura de relógio.
- **AD-3:** não se aplica, porque não há janela.
- **AD-4:** `ORDER BY prazo ASC, id ASC` e `AUTOINCREMENT`.
- **AD-5:** não se aplica, porque não há tags nem `lower`/`casefold`.
- **AD-6:** `extra="forbid"`, título com strip e de 1 a 200 caracteres, e `prazo` com `BeforeValidator` e o regex, sem `Strict()`.
- **AD-7:** POST devolve 201, GET devolve 200 com array, os erros vêm em `{"detail"}` e não há autenticação.
- **AD-8:** dependência com `yield`, `check_same_thread=False`, `foreign_keys=ON`, `TAREFAS_DB` lido por request, `criar_schema` na dependência e `with conn:` em `criar`.
- **AD-9:** o repo devolve só `Tarefa`, e `criar(conn, titulo, prazo, tags)` segue a assinatura. `listar(conn)` nasce sem os filtros, que o Épico 2 acrescenta (ver Design Notes).

## Design Notes

- `api.agora` e a troca de relógio na fixture ficam para a Story 2.2, que é a primeira a ler o relógio. Criar a dependência agora seria código sem uso.
- Na 1.1 a api chama `repo.criar(conn, titulo, prazo, [])`, e `criar` devolve `tags=[]`. A 1.2 grava as tags. `listar` nasce só com `conn`. O Épico 2 acrescenta `pendentes/de/ate/tag` como keyword-only, com padrão que mantém a listagem geral, e assim nenhum chamador muda. Aceitar os filtros já agora e ignorá-los mascararia erro.
- `prazo`:
  ```python
  def _prazo_iso(v):
      if not isinstance(v, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
          raise ValueError("prazo deve ser YYYY-MM-DD")
      return v


  Prazo = Annotated[date, BeforeValidator(_prazo_iso)]
  ```

## Verification

**Commands:**
- `uv run pytest` -- expected: todos passam
- `uv run ruff check` e `uv run ruff format --check` -- expected: sem achados
- `uv tree --depth 1` e `uv tree --package pydantic` -- expected: versões do spine e Pydantic 2.13.5

**Manual checks:**
- `TAREFAS_DB=/tmp/t11.db uv run uvicorn tarefas.api:app`, `curl` POST e GET, reiniciar e repetir o GET.
