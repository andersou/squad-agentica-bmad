---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/prd.md
  - _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/ARCHITECTURE-SPINE.md
---

# api-tarefas - Epic Breakdown

## Overview

Este documento quebra em épicos e stories implementáveis os requisitos do PRD e as decisões da arquitetura da API de Tarefas. Não há documento de UX porque a API não tem interface.

## Requirements Inventory

### Functional Requirements

- **FR1:** O dev cria uma tarefa com título, prazo e tags opcionais.
  - Sucesso: 201 com o identificador.
  - Título ausente ou vazio, prazo ausente ou fora de ISO 8601 → 422.
  - Prazo no passado é aceito.
  - A tarefa nasce não concluída.
- **FR2:** O dev lista todas as tarefas ou consulta uma tarefa pelo identificador.
  - A listagem não tem paginação e vem ordenada por prazo crescente.
  - Cada tarefa traz identificador, título, prazo, tags e marca de conclusão.
  - Identificador inexistente → 404.
- **FR3:** O dev edita título, prazo e tags e marca ou desmarca a tarefa como concluída.
  - Campo omitido mantém o valor.
  - Valem as validações do FR1.
  - Tarefa inexistente → 404.
  - Uma tarefa concluída sai de todas as janelas de prazo.
- **FR4:** O dev exclui uma tarefa.
  - Depois da exclusão, a tarefa dá 404 e some das listagens.
  - Tarefa inexistente → 404.
- **FR5:** O dev atribui zero ou mais tags na criação ou na edição.
  - A tag nasce no uso e é normalizada (`strip` + não diferencia maiúsculas).
  - Tags repetidas são guardadas uma única vez.
  - Tag vazia → 422.
  - Na edição, uma lista enviada substitui a anterior; tags omitidas não mudam.
- **FR6:** O dev filtra por tag, com a mesma regra de comparação. Tag sem uso devolve lista vazia.
- **FR7:** O dev filtra por janela de prazo, com "hoje" em `America/Sao_Paulo`:
  - vencidas: prazo antes de hoje;
  - hoje: prazo igual a hoje;
  - próximos 7 dias: de amanhã até hoje + 7.

  Tarefas concluídas nunca aparecem. Janela inexistente → 422.
- **FR8:** O dev combina tag e janela de prazo na mesma chamada. O resultado é a interseção dos dois filtros.

### NonFunctional Requirements

- **NFR1:** a documentação traz exemplos `curl` de criar uma tarefa com tag e prazo e de listar as vencidas.
- **NFR2:** testes automatizados cobrem as três janelas e a combinação com tag, incluindo os limites (ontem, hoje, amanhã, hoje + 7, hoje + 8) e a virada do dia em `America/Sao_Paulo` com o servidor em UTC.
- **NFR3:** toda resposta de erro (404, 422) tem o mesmo formato e indica o campo ou parâmetro que causou o erro.
- **NFR4:** as tarefas sobrevivem ao reinício do serviço.
- **NFR5:** a API, que não tem autenticação, só fica acessível na rede interna do time.

### Additional Requirements

**Setup do projeto, story 1.1** (não há template inicial):
- Criar o projeto com `uv init`, Python 3.14 (`requires-python >= 3.14`).
- Dependências de runtime: `fastapi` 0.142.2, `uvicorn` 0.54.0 e `tzdata` 2026.4.
- Dependências de desenvolvimento: `pytest` 9.1.1, `httpx` 0.28.1 e `ruff` 0.16.10.
- Não usar `fastapi[standard]` nem ORM (AD-1).

**Arquitetura:**
- Estrutura em camadas: `app/api.py` → `app/domain.py` ← `app/repo.py`, mais `app/main.py`. `domain` não faz IO e não importa as outras camadas.
- AD-2: o instante atual só vem de `domain.now()`, em UTC. "Hoje" só vem de `domain.today(now)`, convertido para `America/Sao_Paulo`. `date.today()` e `datetime.now()` ficam proibidos fora de `now()`.
- AD-3: `domain.window_bounds(janela, hoje)` devolve limites inclusivos:
  - `overdue` = (None, hoje − 1);
  - `today` = (hoje, hoje);
  - `next7` = (hoje + 1, hoje + 7).

  O `repo` usa `>=` e `<=` e sempre `done = 0`.
- AD-4: tipos compartilhados nos schemas:
  - `DueDate`: só `YYYY-MM-DD` e data válida;
  - `Title`: `strip`, não vazio;
  - `done`: booleano estrito;
  - `due`: enum `overdue | today | next7`.

  Os schemas usam `extra="forbid"`. O `POST` não aceita `done`. No `PATCH`, `null` dá 422 e `tags: []` limpa as tags.
- AD-5: o esquema SQL completo (`tasks` e `task_tags` com `ON DELETE CASCADE`) é criado inteiro na story 1.1.
- AD-6, contrato:
  - `POST /tasks` 201;
  - `GET /tasks?tag=&due=`;
  - `GET /tasks/{id}`;
  - `PATCH /tasks/{id}` parcial;
  - `DELETE /tasks/{id}` 204.

  A tarefa tem a forma `{id, title, due_date, tags, done}`, com `tags` presente desde a 1.1. A ordem é `due_date` crescente e depois `id` crescente.
- AD-7, envelope de erro `{"error": {code, field, message}}`:
  - handlers para `RequestValidationError`, o `HTTPException` do Starlette e `Exception`;
  - códigos `validation_error`, `not_found`, `method_not_allowed` e `internal_error`;
  - `field` é o `loc` do primeiro erro sem o prefixo; o 404 de tarefa usa `field: "id"`;
  - `message` em português;
  - os testes conferem só `code` e `field`.
- AD-8: as fixtures `client` (banco em `tmp_path` via `TASKS_DB_PATH`) e `set_now(instante_utc)` ficam em `tests/conftest.py`, criadas na story 1.1. Os testes das janelas incluem `2026-10-03T01:00Z`.
- AD-9, tags:
  - `domain.normalize_tags` faz `strip` + `casefold`, rejeita tag vazia, remove repetidas e ordena;
  - `repo.replace_tags` e `repo.load_tags` são os únicos caminhos de escrita e leitura;
  - o filtro usa `EXISTS`.
- AD-10, conexão:
  - `repo.connect()` lê `TASKS_DB_PATH` a cada chamada, ativa `foreign_keys` e garante o esquema;
  - `get_db()` com `yield` abre uma conexão por requisição;
  - as rotas são `def`;
  - escritas que tocam mais de uma linha rodam em `with conn:`.
- Convenções: nomes em inglês e `snake_case`; mensagens e documentação em português; `ruff check`/`ruff format`; `uv run pytest` passando antes de cada commit; README com `curl` (NFR1).
- Deploy: `uvicorn app.main:app --host <IP interno>`, um processo, sem Docker nem CI (NFR5).

### UX Design Requirements

Não se aplica: a API não tem interface gráfica.

### FR Coverage Map

- FR1: Épico 1 — criar tarefa
- FR2: Épico 1 — listar e consultar tarefas
- FR3: Épico 1 — editar e concluir tarefa
- FR4: Épico 1 — excluir tarefa
- FR5: Épico 2 — etiquetar tarefa
- FR6: Épico 2 — filtrar por tag
- FR7: Épico 2 — filtrar por janela de prazo
- FR8: Épico 2 — combinar tag e janela de prazo

Requisitos não funcionais: NFR3 e NFR4 entram na story 1.1. O NFR1 começa no README da 1.1 e o épico 2 completa com o `curl` das vencidas. O NFR2 fica no épico 2. O NFR5 entra no README de deploy (1.1).

A importação da planilha (§8 do PRD) fica fora dos épicos: a migração é manual ou por um script descartável, fora do escopo da v1.

## Epic List

### Épico 1: Registrar e manter tarefas
O time troca a planilha pela API para guardar tarefas: cria, lista, consulta, edita, conclui e exclui. As tarefas passam a estar num lugar que scripts conseguem consultar.
**FRs cobertos:** FR1, FR2, FR3, FR4

### Épico 2: Saber o que venceu e o que vence
O time etiqueta tarefas e pergunta, em uma chamada, o que está vencido, o que vence hoje e o que vence nos próximos 7 dias, por tag ou não. É o valor central do produto e só depende do épico 1.
**FRs cobertos:** FR5, FR6, FR7, FR8

## Épico 1: Registrar e manter tarefas

O time troca a planilha pela API para guardar tarefas: cria, lista, consulta, edita, conclui e exclui. As tarefas passam a estar num lugar que scripts conseguem consultar.

### Story 1.1: Criar, listar e consultar tarefas

Como dev do time-piloto,
quero criar uma tarefa com título e prazo e depois listá-la ou consultá-la,
para que as tarefas deixem a planilha e passem a estar num lugar que scripts conseguem consultar.

**Critérios de aceite:**

**Given** o repositório sem código
**When** a story é implementada
**Then** existe um projeto `uv` com Python 3.14 e só as dependências do AD-1 (`fastapi`, `uvicorn`, `tzdata`; dev: `pytest`, `httpx`, `ruff`)
**And** o código segue a árvore do spine (`app/main.py`, `api.py`, `domain.py`, `repo.py`; `tests/conftest.py`)
**And** `uv run ruff check`, `uv run ruff format --check` e `uv run pytest` passam

**Given** a API no ar
**When** o dev faz `POST /tasks` com `{"title": "Revisar PR", "due_date": "2026-10-10"}`
**Then** recebe 201 com `{"id": <int>, "title": "Revisar PR", "due_date": "2026-10-10", "tags": [], "done": false}` (FR1, AD-6)

**Given** um `POST /tasks` sem `title`, com `title` vazio ou com `title` só de espaços
**When** a requisição é processada
**Then** recebe 422 com `{"error": {"code": "validation_error", "field": "title", "message": <texto em português>}}`
**And** nenhuma tarefa é criada (FR1, NFR3, AD-4, AD-7)

**Given** um `POST /tasks` sem `due_date` ou com `due_date` igual a `"2026-02-30"`, `"2026-10-02T00:00:00Z"`, `"02/10/2026"` ou `1790899200`
**When** a requisição é processada
**Then** recebe 422 com `code: "validation_error"` e `field: "due_date"` (FR1, AD-4)

**Given** um `POST /tasks` com prazo no passado
**When** a requisição é processada
**Then** recebe 201, e a tarefa nasce com `done: false` (FR1)

**Given** um `POST /tasks` com um campo fora do schema, como `done` ou `tags`
**When** a requisição é processada
**Then** recebe 422 com `code: "validation_error"` (AD-4; as tags chegam na story 2.1)

**Given** tarefas criadas com prazos fora de ordem e duas com o mesmo prazo
**When** o dev faz `GET /tasks`
**Then** recebe 200 com todas as tarefas, sem paginação, ordenadas por `due_date` crescente e, em empate, por `id` crescente (FR2, AD-6)
**And** sem nenhuma tarefa, recebe `[]`

**Given** uma tarefa existente
**When** o dev faz `GET /tasks/{id}`
**Then** recebe 200 com a tarefa
**And** com um `id` que não existe, recebe 404 com `code: "not_found"` e `field: "id"` (FR2, AD-7)

**Given** uma rota que não existe ou um método não suportado
**When** a requisição é processada
**Then** recebe 404 `not_found` ou 405 `method_not_allowed`, com `field: null`, no envelope do AD-7, nunca `{"detail": ...}`

**Given** uma tarefa criada
**When** o serviço é reiniciado com o mesmo `TASKS_DB_PATH`
**Then** a tarefa continua lá (NFR4, AD-10)
**And** `repo.connect()` cria o esquema completo do AD-5 (`tasks` e `task_tags`) quando o banco não existe

**Given** a suíte de testes
**When** um teste usa a fixture `client` de `tests/conftest.py`
**Then** ele roda contra um banco novo em `tmp_path`, e a fixture `set_now` já existe para os épicos seguintes (AD-8)

**Given** o `README.md`
**When** um dev novo o lê
**Then** encontra como instalar, rodar (`uvicorn app.main:app --host <IP interno>`, NFR5) e exemplos `curl` de criar e listar tarefas (NFR1)

### Story 1.2: Editar e concluir tarefa

Como dev do time-piloto,
quero corrigir título ou prazo de uma tarefa e marcá-la como concluída,
para que a lista reflita o estado real do trabalho.

**Critérios de aceite:**

**Given** uma tarefa existente
**When** o dev faz `PATCH /tasks/{id}` com `{"title": "Novo título"}`
**Then** recebe 200 com a tarefa completa e só o título alterado; `due_date`, `tags` e `done` não mudam (FR3, AD-6)

**Given** uma tarefa não concluída
**When** o dev faz `PATCH /tasks/{id}` com `{"done": true}`
**Then** recebe 200 com `done: true`
**And** um novo `PATCH` com `{"done": false}` a desmarca

**Given** um `PATCH` com corpo `{}`
**When** a requisição é processada
**Then** recebe 200 com a tarefa inalterada

**Given** um `PATCH` com `title` vazio ou só de espaços, `due_date` inválido (mesmos casos da 1.1), `done` que não seja booleano JSON (como `"true"` ou `1`) ou `null` em qualquer campo
**When** a requisição é processada
**Then** recebe 422 com `code: "validation_error"` e o `field` correspondente
**And** a tarefa não muda (FR3, AD-4)

**Given** um `PATCH` com um campo fora do schema, como `tags` ou `id`
**When** a requisição é processada
**Then** recebe 422 (AD-4; as tags chegam na story 2.1)

**Given** um `id` que não existe
**When** o dev faz `PATCH /tasks/{id}`
**Then** recebe 404 com `code: "not_found"` e `field: "id"` (FR3, AD-7)

**Given** a implementação
**When** o código é revisado
**Then** o `PATCH` usa os mesmos tipos `Title` e `DueDate` do `POST` e aplica só os campos enviados (`exclude_unset`), dentro de `with conn:` (AD-4, AD-10)

### Story 1.3: Excluir tarefa

Como dev do time-piloto,
quero excluir uma tarefa registrada por engano ou que não vale mais,
para que ela não polua as listagens.

**Critérios de aceite:**

**Given** uma tarefa existente
**When** o dev faz `DELETE /tasks/{id}`
**Then** recebe 204, sem corpo (FR4, AD-6)
**And** `GET /tasks/{id}` passa a dar 404, e a tarefa não aparece em `GET /tasks`

**Given** um `id` que não existe, inclusive o de uma tarefa já excluída
**When** o dev faz `DELETE /tasks/{id}`
**Then** recebe 404 com `code: "not_found"` e `field: "id"` (FR4, AD-7)

## Épico 2: Saber o que venceu e o que vence

O time etiqueta tarefas e pergunta, em uma chamada, o que está vencido, o que vence hoje e o que vence nos próximos 7 dias, por tag ou não. É o valor central do produto e só depende do épico 1.

### Story 2.1: Etiquetar tarefas e filtrar por tag

Como dev do time-piloto,
quero etiquetar tarefas com tags e listar as de uma tag,
para separar o trabalho por assunto, como `backend` ou `infra`.

**Critérios de aceite:**

**Given** a API do épico 1
**When** o dev faz `POST /tasks` com `"tags": ["backend", " Backend ", "API"]`
**Then** recebe 201 com `"tags": ["api", "backend"]`, normalizadas, sem repetição e em ordem alfabética (FR5, AD-9)
**And** sem `tags` no corpo, a tarefa nasce com `"tags": []`

**Given** um `POST` ou `PATCH` com uma tag vazia ou só de espaços na posição N, `tags: null` ou `tags` que não seja uma lista de textos
**When** a requisição é processada
**Then** recebe 422 com `code: "validation_error"` e `field` igual a `tags.N` ou `tags`
**And** nada é gravado (FR5, AD-4, AD-7)

**Given** uma tarefa com as tags `["api", "backend"]`
**When** o dev faz `PATCH /tasks/{id}` com `"tags": ["infra"]`
**Then** as tags passam a ser exatamente `["infra"]`
**And** com `"tags": []`, a tarefa fica sem tags
**And** com um `PATCH` que não envia `tags`, as tags não mudam (FR5)

**Given** tarefas com tags variadas
**When** o dev faz `GET /tasks?tag=Backend`
**Then** recebe só as tarefas que têm a tag `backend`, cada uma com **todas** as suas tags, na ordem do AD-6 (FR6, AD-9)
**And** uma tag que nenhuma tarefa usa devolve `[]`
**And** `?tag=` vazio ou só de espaços devolve 422 com `field: "tag"`

**Given** uma tarefa com tags
**When** ela é excluída
**Then** as linhas dela em `task_tags` também somem (`ON DELETE CASCADE`, AD-5)

**Given** a implementação
**When** o código é revisado
**Then** toda tag passa por `domain.normalize_tags`, inclusive o `?tag=`
**And** `repo.replace_tags` e `repo.load_tags` são os únicos caminhos de escrita e leitura de tags
**And** o filtro usa `EXISTS`
**And** a tarefa e suas tags são gravadas na mesma transação (AD-9, AD-10)

### Story 2.2: Filtrar por janela de prazo e combinar com tag

Como dev do time-piloto,
quero perguntar em uma chamada o que está vencido, o que vence hoje e o que vence nos próximos 7 dias, inclusive por tag,
para que os prazos deixem de se perder.

**Critérios de aceite:**

**Given** o relógio fixado com `set_now("2026-10-02T15:00Z")`, ou seja, hoje é 2026-10-02 em São Paulo
**And** tarefas com prazo em 10-01, 10-02, 10-03, 10-09 e 10-10, além de uma tarefa concluída com prazo em 10-01
**When** o dev faz `GET /tasks?due=overdue`
**Then** recebe só a tarefa não concluída de 10-01 (FR7, AD-3)

**Given** o mesmo cenário
**When** o dev faz `GET /tasks?due=today`
**Then** recebe só a tarefa de 10-02

**Given** o mesmo cenário
**When** o dev faz `GET /tasks?due=next7`
**Then** recebe as tarefas de 10-03 e 10-09, nessa ordem
**And** a de 10-02 (hoje) e a de 10-10 (hoje + 8) ficam de fora

**Given** o relógio em `set_now("2026-10-03T01:00Z")`: em UTC já é o dia 3, mas em São Paulo ainda são 22h do dia 2
**When** o dev faz `GET /tasks?due=today`
**Then** a tarefa de 10-02 aparece em `today`, e não em `overdue` (FR7, AD-2, NFR2)

**Given** uma tarefa que aparece em uma janela
**When** ela é marcada com `done: true`
**Then** some de todas as janelas
**And** volta a aparecer quando é desmarcada (FR3, FR7)

**Given** um valor de `due` fora de `overdue`, `today` e `next7`
**When** o dev faz `GET /tasks?due=semana`
**Then** recebe 422 com `code: "validation_error"` e `field: "due"` (FR7, AD-7)

**Given** tarefas vencidas com e sem a tag `backend`
**When** o dev faz `GET /tasks?tag=backend&due=overdue`
**Then** recebe só as vencidas que têm `backend`, ou seja, a interseção dos dois filtros (FR8)

**Given** a implementação
**When** o código é revisado
**Then** "hoje" só vem de `domain.today(domain.now())`, e não há `date.today()` nem `datetime.now()` fora de `domain.now()` (AD-2)
**And** os limites saem de `domain.window_bounds`, e o `repo` só aplica `>=`, `<=` e `done = 0` (AD-3)

**Given** o `README.md`
**When** um dev novo segue os exemplos
**Then** consegue criar uma tarefa com tag e prazo e listar as vencidas em duas chamadas `curl` (NFR1, SM-2 do PRD)
