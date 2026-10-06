---
status: final
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-06/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-06/ARCHITECTURE-SPINE.md
---

# api-tarefas - Epic Breakdown

## Overview

Este documento quebra em épicos e stories os requisitos do PRD e as decisões do ARCHITECTURE-SPINE da api-tarefas. Não há documento de UX: a API não tem interface gráfica (PRD §6).

## Requirements Inventory

### Functional Requirements

FR-1: Criar tarefa. O dev cria uma tarefa com título e prazo, com tags opcionais. Sem título ou sem prazo dá 422. Título vazio ou só com espaços dá 422. Prazo fora de `YYYY-MM-DD` ou data inexistente (`2026-02-30`) dá 422. Prazo no passado é aceito e a tarefa já nasce vencida. A tarefa nasce pendente. A resposta devolve a tarefa criada com seu identificador.
FR-2: Editar tarefa. O dev altera título, prazo, tags e a marca de concluída de uma tarefa existente. A edição é parcial (campo omitido mantém o valor). Os campos enviados passam pelas validações do FR-1. Ligar concluída tira a tarefa de todas as janelas, e desligar a devolve. Editar tarefa inexistente dá 404.
FR-3: Excluir tarefa. A exclusão é definitiva, e a tarefa some da listagem geral e das janelas. Excluir tarefa inexistente dá 404.
FR-4: Listagem geral. Lista todas as tarefas, concluídas ou não, ordenadas por prazo do mais antigo ao mais distante, inteira, sem paginação e sem filtro por concluída.
FR-5: Etiquetar tarefa e filtrar por tag. Tag vazia ou só com espaços dá 422. A tag é aparada nas pontas. A comparação não diferencia maiúsculas de minúsculas. Tag repetida na mesma tarefa é guardada uma vez, com a grafia da primeira ocorrência. Na edição, enviar tags substitui a lista, e omitir mantém. O filtro aceita uma única tag e funciona na listagem geral e em qualquer janela.
FR-6: Filtrar pendentes por janela de prazo. Vencidas: `prazo < hoje`. Hoje: `prazo = hoje`. Próximos 7 dias: `hoje + 1 <= prazo <= hoje + 7`. Ontem, hoje, amanhã, hoje + 7 e hoje + 8 caem em vencidas, hoje, próximos 7 dias, próximos 7 dias e nenhuma janela. Concluída vencida não aparece em janela. Às 22h em SP (01h UTC do dia seguinte), hoje é a data de SP. Mesma ordenação da listagem geral. Janela desconhecida, tag vazia ou mais de uma tag dá 422.

### NonFunctional Requirements

NFR-1: Fuso fixo. O cálculo de hoje usa sempre America/Sao_Paulo, independentemente do fuso do servidor.
NFR-2: Rede interna. A API roda só na rede interna do time, sem autenticação.
NFR-3: Testes dos limites. Testes automatizados cobrem todos os casos-limite do FR-6.
NFR-4: Documentação por exemplos. A documentação traz exemplos de chamadas suficientes para cumprir o SM-2 (criar tarefa com tag e prazo e listar as vencidas em duas chamadas).
NFR-5: Persistência. As tarefas sobrevivem ao reinício da API.

### Additional Requirements

- Sem starter template. O projeto nasce de `uv init --package` com o Structural Seed do spine: `pyproject.toml` (deps fastapi sem `[standard]`, uvicorn, tzdata; dev pytest, httpx, ruff), `src/tarefas/{api,domain,repo}.py`, `tests/conftest.py`, `tests/test_tarefas.py`, `tests/test_janelas.py`, `README.md`. Isso entra na primeira story do Épico 1.
- Stack fixa pelo spine: Python 3.14, uv 0.12, FastAPI 0.142.2, Pydantic 2.13.5, uvicorn 0.54.0, tzdata 2026.5, pytest 9.1.1, httpx 0.28.1, ruff 0.16.10. Ruff só com `target-version = "py314"`.
- AD-1: camadas `api → domain ← repo`. `domain.py` não importa nada externo, `repo.py` nunca importa `api`. Regra de prazo, janela e tag só em `domain.py`.
- AD-2: `api.agora()` (UTC aware) é a única leitura do relógio, injetada via `Depends`. `domain.hoje(agora)` converte para America/Sao_Paulo. Testes usam `app.dependency_overrides`, e o caso das 22h em SP usa o instante 01:00 UTC do dia seguinte.
- AD-3: `domain.Janela` (`StrEnum`: `vencidas`, `hoje`, `proximos-7-dias`) e `domain.intervalo(janela, hoje) -> (de, ate)` inclusivos. O repo só aplica `de`/`ate` e `concluida = 0`.
- AD-4: toda listagem usa `ORDER BY prazo ASC, id ASC`, com `id INTEGER PRIMARY KEY AUTOINCREMENT`.
- AD-5: `domain.norm_tag` (`strip().casefold()`) e `domain.normalizar_tags` (strip, `ValueError` para vazia, dedup pela primeira grafia). O schema chama `normalizar_tags` num validator. O repo grava e filtra por `nome_norm`. Tags voltam em ordem de inserção.
- AD-6: schemas com `extra="forbid"`. `titulo` com strip e 1 a 200 caracteres. `prazo` com `BeforeValidator` e regex `^\d{4}-\d{2}-\d{2}$`, sem `Strict()`. Tags com no máximo 50 caracteres. `concluida` é `StrictBool`. POST não aceita `concluida`. No PATCH tudo é opcional, `null` dá 422, `{}` dá 200 inalterado e `tags: []` limpa. Query `tag` é `list[str]` com checagem na rota (mais de um, vazio ou acima de 50 dá 422). `janela` desconhecida dá 422. A validação (422) vem antes do 404.
- AD-7: `POST /tarefas` 201, `GET /tarefas?janela=&tag=` 200 com array, `PATCH /tarefas/{id}` 200, `DELETE /tarefas/{id}` 204 sem corpo. Inexistente dá 404 via `HTTPException`, erros no formato `{"detail": ...}`.
- AD-8: uma conexão por request na dependência `api.conexao` (`yield`, `check_same_thread=False`, `PRAGMA foreign_keys=ON`). Endpoints `def`. `TAREFAS_DB` (padrão `tarefas.db`) lido ao abrir a conexão. O schema é criado por `repo.criar_schema(conn)` com `CREATE TABLE IF NOT EXISTS`, chamado pela dependência e não pelo lifespan. Cada escrita roda em `with conn:`, e no PATCH as tags são trocadas na mesma transação.
- AD-9: `domain.Tarefa` (dataclass `id, titulo, prazo, tags, concluida`) é o único tipo entre repo e api. O repo expõe só `criar`, `listar(conn, *, pendentes, de, ate, tag)`, `editar(conn, id, campos) -> Tarefa | None` e `excluir(conn, id) -> bool`. `campos` vem de `model_dump(exclude_unset=True)`.
- Schema: `tarefa(id, titulo, prazo TEXT ISO, concluida INTEGER 0/1)` e `tarefa_tag(tarefa_id FK ON DELETE CASCADE, nome, nome_norm, UNIQUE(tarefa_id, nome_norm))`.
- Testes: um único `tests/conftest.py` com a fixture `client`, que sempre fixa `api.agora` e aponta `TAREFAS_DB` para `tmp_path`.
- Armadilhas da v1 anterior (AGENTS.md): `id` de path com `le=2**63-1` (acima disso é 422, não 500). PATCH concorrente com exclusão confere, grava e relê na mesma transação e devolve 404 se a tarefa sumiu. Parâmetro de query repetido dá 422.
- Documentação: README com exemplos de `curl` que cobrem o SM-2, além do `/docs` automático. Execução com `TAREFAS_DB` em caminho absoluto.

### UX Design Requirements

Não se aplica. A API não tem interface gráfica (PRD §6).

### FR Coverage Map

FR-1: Épico 1 - criar tarefa (Story 1.1), com tags (Story 1.2)
FR-2: Épico 1 - editar e concluir tarefa (Story 1.4)
FR-3: Épico 1 - excluir tarefa (Story 1.3)
FR-4: Épico 1 - listagem geral ordenada (Story 1.1)
FR-5: Épico 1 - etiquetar na criação (Story 1.2) e na edição (Story 1.4); Épico 2 - filtrar por tag (Stories 2.1 e 2.2)
FR-6: Épico 2 - janelas de prazo (Story 2.2)
NFR-1: Épico 2 - Story 2.2
NFR-2: Épico 1 - Story 1.1 (sem autenticação); Épico 2 - Story 2.3 (execução na rede interna)
NFR-3: Épico 2 - Story 2.2
NFR-4: Épico 2 - Story 2.3
NFR-5: Épico 1 - Story 1.1

## Epic List

### Épico 1: Cadastrar e manter tarefas
O dev cadastra tarefas com título, prazo e tags, inclusive as atrasadas da planilha, e depois as lista, edita, conclui e exclui. As tarefas sobrevivem ao reinício da API. Realiza UJ-1 e UJ-3.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5 (etiquetar)
**NFRs:** NFR-2, NFR-5

### Épico 2: Consultar prazos por janela e tag
O dev pergunta em uma chamada o que está vencido, o que vence hoje e o que vence nos próximos 7 dias, opcionalmente recortado por uma tag, e encontra no README os exemplos de chamada. Realiza UJ-2. Usa as tarefas do Épico 1 e não altera o contrato delas.
**FRs covered:** FR-5 (filtrar), FR-6
**NFRs:** NFR-1, NFR-3, NFR-4

## Épico 1: Cadastrar e manter tarefas

O dev cadastra tarefas com título, prazo e tags, inclusive as atrasadas da planilha, e depois as lista, edita, conclui e exclui. As tarefas sobrevivem ao reinício da API.

### Story 1.1: Criar e listar tarefas

Como dev do time-piloto,
quero criar uma tarefa com título e prazo e listar todas as tarefas,
para que eu possa recadastrar as tarefas da planilha, inclusive as atrasadas, e vê-las em ordem de prazo.

**Acceptance Criteria:**

**Dado** um repositório sem código
**Quando** o projeto é criado com `uv init --package` seguindo o Structural Seed
**Então** existem `pyproject.toml` (fastapi sem `[standard]`, uvicorn e tzdata; dev: pytest, httpx e ruff, nas versões do spine; ruff só com `target-version = "py314"`), `src/tarefas/{api,domain,repo}.py`, `tests/conftest.py` e `tests/test_tarefas.py`
**E** `uv run pytest`, `uv run ruff check` e `uv run ruff format --check` passam
**E** `domain.py` não importa nada externo e `repo.py` não importa `api` (AD-1)

**Dado** a fixture `client` de `tests/conftest.py`, que aponta `TAREFAS_DB` para `tmp_path` com `monkeypatch.setenv`
**Quando** um teste faz requisições
**Então** ele usa um banco novo, e nenhum teste cria outro `TestClient`

**Dado** um corpo `{"titulo": "Migrar planilha", "prazo": "2026-10-01"}`
**Quando** chamo `POST /tarefas`
**Então** recebo 201 com `{"id": int, "titulo": "Migrar planilha", "prazo": "2026-10-01", "tags": [], "concluida": false}`
**E** o prazo no passado é aceito (FR-1)

**Dado** corpos sem `titulo`, sem `prazo`, com título vazio ou só com espaços, com título acima de 200 caracteres depois do strip, com `prazo` `"06/10/2026"`, `"2026-02-30"`, `"2026-10-06T00:00:00"` ou `20261006`, com `concluida`, ou com um campo desconhecido
**Quando** chamo `POST /tarefas`
**Então** cada um recebe 422 no formato `{"detail": ...}` (AD-6, `extra="forbid"`, `prazo` validado por `BeforeValidator` com o regex `^\d{4}-\d{2}-\d{2}$`, sem `Strict()`)
**E** o título é gravado já aparado

**Dado** tarefas criadas fora de ordem de prazo, duas delas com o mesmo prazo
**Quando** chamo `GET /tarefas`
**Então** recebo 200 com um array JSON sem envelope e sem paginação, ordenado por `prazo ASC, id ASC` (FR-4, AD-4)

**Dado** uma tarefa criada pela fixture `client`
**Quando** o teste abre `sqlite3.connect(os.environ["TAREFAS_DB"])` e chama `repo.listar` nessa conexão, sem criar outro `TestClient`
**Então** a tarefa está gravada em disco (NFR-5)

**E** a conexão é aberta por request na dependência `api.conexao` (`yield`, `check_same_thread=False`, `PRAGMA foreign_keys=ON`), que lê `TAREFAS_DB` (padrão `tarefas.db`) a cada abertura e chama `repo.criar_schema(conn)`, que cria só a tabela `tarefa` (`id INTEGER PRIMARY KEY AUTOINCREMENT`, `titulo`, `prazo` TEXT ISO, `concluida` INTEGER 0/1) com `CREATE TABLE IF NOT EXISTS` (AD-8)
**E** o repo devolve só `domain.Tarefa` e expõe `criar(conn, titulo, prazo, tags)` e `listar(conn)` com as assinaturas do AD-9; `criar` roda em `with conn:`
**E** as rotas são `def` e não há autenticação (NFR-2, AD-7)

### Story 1.2: Etiquetar tarefas na criação

Como dev do time-piloto,
quero informar tags ao criar uma tarefa,
para que eu possa marcar o assunto de cada tarefa, como `backend`.

**Acceptance Criteria:**

**Dado** um corpo com `"tags": ["Backend", " api ", "backend"]`
**Quando** chamo `POST /tarefas`
**Então** recebo 201 com `"tags": ["Backend", "api"]`: pontas aparadas, duplicadas removidas sem diferenciar maiúsculas, mantendo a grafia e a posição da primeira ocorrência (FR-5)
**E** a listagem geral devolve as mesmas tags, na ordem de inserção (`ORDER BY rowid`)

**Dado** um corpo com uma tag vazia, só com espaços, acima de 50 caracteres depois do strip, ou com `tags` que não seja lista de strings
**Quando** chamo `POST /tarefas`
**Então** recebo 422 e nenhuma tarefa é gravada

**E** `domain.norm_tag(s)` = `s.strip().casefold()` e `domain.normalizar_tags(lista)` (strip, `ValueError` para vazia, dedup por `norm_tag`) são as únicas funções que normalizam tags; o schema chama `normalizar_tags` num validator e nenhuma outra camada faz `lower`/`casefold` (AD-5)
**E** `repo.criar_schema` passa a criar `tarefa_tag(tarefa_id, nome, nome_norm)` com `UNIQUE(tarefa_id, nome_norm)` e FK `ON DELETE CASCADE`, e o repo grava `nome_norm` com `norm_tag`
**E** a tarefa e as tags são gravadas na mesma transação (AD-8), e o SQL de `tarefa_tag` fica só no repo (AD-9)
**E** uma tarefa sem `tags` continua sendo criada com `"tags": []`

### Story 1.3: Excluir tarefa

Como dev do time-piloto,
quero excluir uma tarefa,
para que tarefas canceladas ou cadastradas por engano saiam da lista.

**Acceptance Criteria:**

**Dado** uma tarefa existente com tags
**Quando** chamo `DELETE /tarefas/{id}`
**Então** recebo 204 sem corpo
**E** a tarefa some de `GET /tarefas` e as tags dela somem de `tarefa_tag` pelo `ON DELETE CASCADE` (FR-3)

**Dado** um `id` inexistente
**Quando** chamo `DELETE /tarefas/{id}`
**Então** recebo 404 via `HTTPException`, no formato `{"detail": ...}`

**Dado** um `id` igual a `2**63` (acima de `2**63-1`) ou não inteiro
**Quando** chamo `DELETE /tarefas/{id}`
**Então** recebo 422, nunca 500 (`id` declarado com `le=2**63-1`)

**E** `repo.excluir(conn, id) -> bool` roda em `with conn:` e devolve `False` para id inexistente (AD-9)

### Story 1.4: Editar e concluir tarefa

Como dev do time-piloto,
quero editar título, prazo, tags e a marca de concluída de uma tarefa,
para que eu possa corrigir dados e marcar o que terminei.

**Acceptance Criteria:**

**Dado** uma tarefa existente
**Quando** chamo `PATCH /tarefas/{id}` com `{"concluida": true}`
**Então** recebo 200 com a tarefa concluída, e título, prazo e tags inalterados (edição parcial, FR-2)
**E** a tarefa continua em `GET /tarefas`

**Dado** uma tarefa existente
**Quando** envio `{}`
**Então** recebo 200 com a tarefa inalterada

**Dado** uma tarefa com tags
**Quando** envio `{"tags": ["Infra", "infra"]}`, depois `{"titulo": "Outro"}` e depois `{"tags": []}`
**Então** a lista é substituída por `["Infra"]`, depois mantida e depois limpa (FR-5)

**Dado** corpos com `null` em qualquer campo, `concluida` diferente de booleano (`"true"`, `1`), campo desconhecido ou valores que o FR-1 e a Story 1.2 rejeitam
**Quando** chamo `PATCH /tarefas/{id}`
**Então** recebo 422 (AD-6, `concluida` como `StrictBool`)
**E** com `id` inexistente e corpo inválido também recebo 422, porque a validação vem antes do 404

**Dado** um `id` inexistente e um corpo válido
**Quando** chamo `PATCH /tarefas/{id}`
**Então** recebo 404

**Dado** um `id` igual a `2**63`
**Quando** chamo `PATCH /tarefas/{id}`
**Então** recebo 422, nunca 500

**Dado** uma tarefa excluída por outra conexão entre a checagem e a gravação do PATCH
**Quando** o PATCH termina
**Então** recebo 404, nunca 500: `repo.editar` confere, grava e relê na mesma transação e devolve `None` se a tarefa sumiu

**E** `repo.editar(conn, id, campos)` recebe `model_dump(exclude_unset=True)`, roda em `with conn:`, troca as tags na mesma transação da tarefa e devolve `Tarefa | None` (AD-8, AD-9)

## Épico 2: Consultar prazos por janela e tag

O dev pergunta em uma chamada o que está vencido, o que vence hoje e o que vence nos próximos 7 dias, opcionalmente recortado por uma tag, e encontra no README os exemplos de chamada.

### Story 2.1: Filtrar a listagem geral por tag

Como dev do time-piloto,
quero listar só as tarefas com uma tag,
para que eu possa ver as tarefas de um assunto, como `backend`.

**Acceptance Criteria:**

**Dado** tarefas com as tags `Backend`, `backend-legado` e `frontend`, e uma sem tag
**Quando** chamo `GET /tarefas?tag=BACKEND` ou `GET /tarefas?tag=%20backend%20`
**Então** recebo só a tarefa com `Backend`, concluída ou não, na ordem `prazo ASC, id ASC` (FR-5, FR-4)
**E** as tags da tarefa voltam completas, não só a que casou

**Dado** uma tag que nenhuma tarefa tem
**Quando** filtro por ela
**Então** recebo 200 com `[]`

**Dado** `?tag=a&tag=b`, `?tag=` vazio ou só com espaços, ou uma tag acima de 50 caracteres
**Quando** chamo `GET /tarefas`
**Então** recebo 422; `tag` é declarado como `list[str]` e a checagem é feita na rota (AD-6)

**E** `repo.listar` ganha o argumento `tag=None` e filtra por `nome_norm = norm_tag(tag)` (AD-5, AD-9)

### Story 2.2: Consultar pendentes por janela de prazo

Como dev do time-piloto,
quero listar as tarefas pendentes vencidas, de hoje ou dos próximos 7 dias, opcionalmente com uma tag,
para que meu script publique toda manhã no chat o que está atrasado.

**Acceptance Criteria:**

**Dado** a dependência `api.agora() -> datetime` (UTC aware), única leitura do relógio, e `domain.hoje(agora)`, que converte para `ZoneInfo("America/Sao_Paulo")` e pega `.date()` (AD-2, NFR-1)
**Quando** os testes rodam
**Então** a fixture `client` sempre substitui `agora` por um instante fixo via `app.dependency_overrides`, ajustável pelo teste
**E** nenhum código chama `date.today()` ou `datetime.now()`

**Dado** hoje fixado e tarefas pendentes com prazo em ontem, hoje, amanhã, hoje + 7 e hoje + 8
**Quando** chamo `GET /tarefas?janela=vencidas`, `?janela=hoje` e `?janela=proximos-7-dias`
**Então** ontem cai em vencidas, hoje em hoje, amanhã e hoje + 7 em próximos 7 dias, e hoje + 8 em nenhuma janela (FR-6)
**E** cada caso-limite tem um teste próprio em `tests/test_janelas.py` (NFR-3)

**Dado** uma tarefa concluída com prazo vencido
**Quando** chamo `?janela=vencidas`
**Então** ela não aparece; depois de `PATCH` com `{"concluida": false}`, ela volta a aparecer (FR-2)

**Dado** o instante `01:00 UTC` do dia seguinte (22h em São Paulo) e uma tarefa com prazo na data de São Paulo
**Quando** chamo `?janela=hoje` e `?janela=vencidas`
**Então** ela aparece em hoje e não em vencidas

**Dado** tarefas pendentes vencidas com as tags `backend` e `frontend`
**Quando** chamo `GET /tarefas?janela=vencidas&tag=Backend`
**Então** recebo só as vencidas com `backend`, na ordem `prazo ASC, id ASC` (FR-5, AD-4)

**Dado** `?janela=amanha`, `?janela=` ou `?janela=hoje&janela=vencidas`
**Quando** chamo `GET /tarefas`
**Então** recebo 422; a repetição de `janela` é checada na rota, porque o FastAPI pegaria o último valor sem avisar

**E** `domain.Janela` é um `StrEnum` (`vencidas`, `hoje`, `proximos-7-dias`) e só `domain.intervalo(janela, hoje)` converte a janela em limites inclusivos `(de, ate)` (AD-3)
**E** `repo.listar(conn, *, pendentes=False, de=None, ate=None, tag=None)` aplica `concluida = 0`, `prazo >= de` e `prazo <= ate`, sem conhecer os nomes das janelas; a api passa `pendentes=True` se e só se houver janela (AD-9)
**E** sem `janela`, `GET /tarefas` continua sendo a listagem geral da Story 1.1, sem usar o relógio para filtrar

### Story 2.3: Documentar as chamadas no README

Como dev do time que nunca usou a API,
quero exemplos de chamadas prontos no README,
para que eu crie uma tarefa e liste as vencidas sem ler o código.

**Acceptance Criteria:**

**Dado** o `README.md`
**Quando** um dev segue só os exemplos
**Então** ele cria uma tarefa com tag e prazo e lista as vencidas com essa tag em duas chamadas `curl` (SM-2, NFR-4)
**E** há exemplos de `curl` para listagem geral, filtro por tag, as três janelas, PATCH para concluir e DELETE, com os códigos de resposta do AD-7

**Dado** a seção de execução do README
**Quando** um dev sobe a API
**Então** o comando é `TAREFAS_DB=/caminho/absoluto/tarefas.db uv run uvicorn tarefas.api:app --host 0.0.0.0 --port 8000`, com o aviso de que caminho relativo abre um banco novo ao subir de outro diretório
**E** o README diz que a API não tem autenticação e deve rodar só na rede interna do time (NFR-2)
**E** cita o `/docs` automático do FastAPI e os comandos `uv run pytest` e `uv run ruff check`

**E** os exemplos são conferidos contra a API rodando, e cada `curl` devolve o código documentado
