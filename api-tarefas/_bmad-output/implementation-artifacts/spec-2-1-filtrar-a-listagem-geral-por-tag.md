---
title: 'Story 2.1: Filtrar a listagem geral por tag'
type: 'feature'
created: '2026-10-06'
status: 'done'
baseline_commit: '63ce5a3b5f0fb737362f6df23626748764dcc1eb'
route: 'dispatch'
review_loop_iteration: 3
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-06/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** O dev não consegue ver só as tarefas de um assunto, como `backend` (FR-5), porque `GET /tarefas` devolve sempre a lista inteira.

**Approach:** `GET /tarefas` ganha a query `tag`, declarada como `list[str]` e checada na rota (um valor, não vazio depois do strip, até 50 caracteres; senão 422, AD-6). `repo.listar(conn, *, tag=None)` filtra as tarefas que têm alguma tag com `nome_norm = norm_tag(tag)` e devolve cada uma com todas as tags (AD-5, AD-9).

## Boundaries & Constraints

**Always:** seguir AD-1 a AD-9 do spine e o AGENTS.md. Filtro só na listagem geral: concluídas e pendentes entram. Ordem `prazo ASC, id ASC` (AD-4). A tarefa volta com todas as tags, na ordem de inserção. Comparação só via `domain.norm_tag` no repo. Sem `tag`, a resposta é a mesma de hoje.

**Never:** janelas, `pendentes`, `de`/`ate` ou `api.agora` (Story 2.2); filtro por várias tags; `lower`/`casefold` fora de `domain`; SQL fora de `repo.py`; outro `TestClient`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Filtro | tarefas com `Backend` (concluída), `backend-legado`, `frontend` e sem tag; `?tag=BACKEND` ou `?tag=%20backend%20` | 200 só com a de `Backend`, com todas as tags dela | N/A |
| Ordem | duas tarefas com `backend`, a de id maior com prazo menor | 200, `prazo ASC, id ASC` | N/A |
| Sem match | `?tag=inexistente` | 200 `[]` | N/A |
| Sem tag | `GET /tarefas` | igual à listagem geral atual | N/A |
| Inválido | `?tag=a&tag=b`, `?tag=a&tag=a`, `?tag=`, `?tag=%20%20`, tag com 51 caracteres depois do strip | 422 `{"detail": ...}` | nada muda |
| Limite | tag com 50 caracteres (com espaços nas pontas) | 200 | N/A |

</frozen-after-approval>

## Code Map

- `src/tarefas/api.py` -- `listar_tarefas` (hoje sem parâmetros). Reusar `_aparar` (`str.strip()`, o mesmo da escrita). Importar `Query` de `fastapi` e `RequestValidationError` de `fastapi.exceptions`. A checagem da tag fica na rota e levanta `RequestValidationError([{"type": "value_error", "loc": ("query", "tag"), "msg": <motivo>, "input": <valor recebido>}])`, nunca `HTTPException`. Uma única chamada `repo.listar(conn, tag=valor)` no fim, com `valor = None` sem tag (a 2.2 acrescenta a janela nessa mesma chamada).
- `src/tarefas/repo.py` -- `listar` delega para `_buscar(conn, onde, params)`, que monta `Tarefa` a partir do `LEFT JOIN` com `ORDER BY t.prazo, t.id, g.rowid`. Filtrar com subconsulta em `onde` (`WHERE t.id IN (SELECT tarefa_id FROM tarefa_tag WHERE nome_norm = ?)`), para o JOIN continuar trazendo todas as tags. Não mexer em `_buscar` nem em `editar`.
- `tests/test_tarefas.py` -- reusar a fixture `client` e o padrão de `test_listar_ordenado_por_prazo_e_id`/`test_tags_comparadas_com_casefold`. `test_camadas` já barra `lower`/`casefold` em `api` e `repo`.

## Tasks & Acceptance

**Execution:**
- [x] `src/tarefas/repo.py` -- `listar(conn, *, tag=None)`: sem tag, como hoje; com tag, `_buscar` com a subconsulta e `norm_tag(tag)` -- AD-5, AD-9
- [x] `src/tarefas/api.py` -- `listar_tarefas(conn, tag: Annotated[list[str], Query(default_factory=list, description=...)])` (o ruff barra `= []` pela B006; a descrição diz "uma tag por chamada, até 50 caracteres"): mais de um valor, valor vazio depois do `_aparar` ou acima de 50 caracteres dá 422 via `RequestValidationError`; repassa `tag=` ao repo -- AD-6, AD-7
- [x] `tests/test_tarefas.py` -- um teste por linha da I/O Matrix; nos inválidos (parametrizados), conferir `r.json()["detail"][0]["loc"] == ["query", "tag"]` e o `msg` esperado de cada caso, sem comparar a listagem antes e depois (um GET não grava nada); `repo.listar` direto com tag que só difere por caixa e espaços

**Acceptance Criteria:**
- Given o código da story, when rodo `uv run pytest`, `uv run ruff check` e `uv run ruff format --check`, then os três passam.
- Given `/openapi.json`, when leio o parâmetro `tag` de `GET /tarefas`, then ele é um array de strings opcional, com descrição.
- Given um 422 da query `tag`, when leio o corpo, then `detail` é uma lista no formato que o OpenAPI anuncia para o 422 (`HTTPValidationError`), igual ao 422 do corpo.

### Review Findings

Passada 3 (code review pós-fechamento, 2026-10-06; diff `63ce5a3..4aa0bc8`).

- [x] [Review][Patch] O limite de 50 aparecia em três lugares (`Tags`, checagem da rota e `description`); se mudar em `Tags`, a query diverge do corpo. Agora todos usam `api.TAG_MAX` [src/tarefas/api.py:51]
- [x] [Review][Patch] A mesma regra (tag vazia depois do strip) tinha dois textos: `tag vazia` no corpo (`domain.normalizar_tags`) e `tag não pode ser vazia` na query. A query passou a usar `tag vazia` [src/tarefas/api.py:123]
- [x] [Review][Patch] O `description` do `tag` no OpenAPI não dizia que a comparação ignora maiúsculas e espaços nas pontas [src/tarefas/api.py:105]
- [x] [Review][Patch] `test_filtrar_por_tag_ordenado` não conferia `status_code` antes de ler `r.json()` [tests/test_tarefas.py:209]

Rejeitados:
- **false:** o 422 da query não é "igual" ao do corpo por não ter o prefixo `Value error, ` nem `ctx` (blind, acceptance). O AC pede o formato `HTTPValidationError`, em que `ctx` é opcional e `msg` é texto livre. O prefixo é artefato do Pydantic, e o próprio corpo já usa outro `type`/`msg` para 51 caracteres (`string_too_long`).
- **false:** sem índice em `nome_norm` (blind). Com poucas centenas de tarefas no piloto, a varredura de `tarefa_tag` não chega a ser lentidão que alguém perceba. Já era o #8 da passada 1.
- **false:** nenhum teste mistura pendente e concluída no mesmo filtro (blind). Um `concluida = 0` no caminho da tag zera a resposta de `test_filtrar_por_tag`, cujo único match é concluído, e `test_filtrar_por_tag_ordenado` cobre as pendentes.
- **false:** os asserts de `backend` em `test_filtrar_por_tag` seriam código morto (blind). Eles conferem literais (`True`, `["api", "Backend", "urgente"]`) depois de `r.json() == [backend]`, então provam a resposta. Já era o #6 da passada 1.
- **false:** com `repo.listar(conn, tag="")`, o repo filtra por `nome_norm = ""` (acceptance). A rota nunca passa `""`, e a escrita proíbe tag vazia.
- **false:** tag de regra na `api` contra o AD-1 (acceptance). O AD-6 manda explicitamente checar a query na rota. Já era o #2 da passada 1.
- **spec:** a nota da passada 2 #3 diz "levado ao Anderson" sem registrar resposta (blind). A correção seria editar a spec, e o achado foi julgado `false` por escopo (PRD §FR-6), então não há decisão pendente.
- **spec:** a conferência do AD-9 em Implementation Notes parece afirmar a assinatura completa (blind). A correção seria editar a spec, e o subconjunto já está registrado em Design Notes.

## Implementation Notes

- Arquivos: `repo.py` (`listar(conn, *, tag=None)` com a subconsulta em `nome_norm`), `api.py` (query `tag` e a checagem na rota) e `tests/test_tarefas.py` (8 testes novos).
- O default da query é `Query(default_factory=list)`, porque o ruff barra `= []` (B006).
- O `input` do 422 é o valor recebido, sem strip (a lista inteira quando há repetição). O limite de 50 conta depois do `str.strip()`, como no corpo.
- Com os patches da passada 2, `uv run pytest` dá 106 passed, e `ruff check` e `ruff format --check` passam.
- Passada 3: o limite virou `api.TAG_MAX` (usado em `Tags`, na rota e na `description`), e o 422 de tag vazia na query usa o mesmo texto do corpo (`tag vazia`). Continua 106 passed, com `ruff check` e `ruff format --check` limpos.

Conferência dos AD contra o diff:
- **AD-1:** `repo` continua importando só `tarefas.domain`, `domain` não mudou, e `test_camadas` passa.
- **AD-2:** nenhuma leitura de relógio (nem `today` nem `now(` em `src/`).
- **AD-3:** não se aplica: sem janela nesta story.
- **AD-4:** a filtragem usa `_buscar`, com `ORDER BY t.prazo ASC, t.id ASC, g.rowid ASC`; `test_filtrar_por_tag_ordenado` põe o id maior com prazo menor.
- **AD-5:** o filtro compara `nome_norm = norm_tag(tag)` no repo; a rota só apara com `_aparar` (`str.strip()`), sem `lower`/`casefold` (`test_camadas`). As tags voltam na ordem de inserção.
- **AD-6:** `tag` é `list[str]`; mais de um valor, vazio depois do strip ou acima de 50 dá 422, checado na rota.
- **AD-7:** `GET /tarefas?tag=` dá 200 com array sem envelope; o 422 sai no formato padrão do FastAPI (`detail` lista, `HTTPValidationError`).
- **AD-8:** só leitura, pela conexão de `api.conexao`; nada mudou na escrita.
- **AD-9:** `listar(conn, *, tag=None)` segue a assinatura do AD-9 (os demais argumentos entram na 2.2) e devolve `domain.Tarefa` montada por `_buscar`.

## Spec Change Log

- **Passada 1, bad_spec (blind-hunter #1):** a spec mandava `HTTPException(422, "<motivo>")`, que devolve `detail` string, enquanto o OpenAPI da rota anuncia `HTTPValidationError` (`detail` lista) e o 422 do corpo é lista. Emendados Code Map, Tasks, AC e Design Notes para `RequestValidationError` com `loc` `["query", "tag"]`, ainda checado na rota (AD-6), no formato padrão do FastAPI (AD-7). Evita dois formatos de 422 na mesma API e um `/docs` que mente. Também entraram: uma única chamada ao repo na rota (blind #3), `msg`/`loc` conferidos nos testes de inválido no lugar da comparação vazia antes/depois (blind #5) e a descrição da query no OpenAPI (blind #10). **KEEP:** o `repo.listar` com a subconsulta `t.id IN (SELECT tarefa_id FROM tarefa_tag WHERE nome_norm = ?)` sem mexer em `_buscar`; `Query(default_factory=list)`; o conjunto de testes da implementação anterior (`_tarefas_com_tags` com a de `Backend` concluída e com três tags, ordem com id maior e prazo menor, sem match, sem tag, limite de 50 com espaços, `repo.listar` direto com `Straße`/`STRASSE`, OpenAPI do `tag`).

## Review Triage Log

Passada 1 (blind-hunter, edge-case-hunter, verification-gap). Edge-case e verification-gap: nenhum achado.

| # | Achado | Veredito | Evidência | Rota |
|---|---|---|---|---|
| 1 | O 422 da query tem `detail` string, mas o OpenAPI de `GET /tarefas` anuncia `HTTPValidationError` (lista), e o 422 do corpo é lista (blind) | medium | Conferido: `openapi.json` traz `$ref HTTPValidationError` no 422, `?tag=` devolvia `{"detail": "tag deve ter..."}` e `POST {}` devolve lista. O AD-7 pede o formato padrão do FastAPI, então não há decisão a perguntar | bad_spec |
| 2 | O limite 50 e a checagem de vazio repetem a regra de `Tags`/`normalizar_tags` (blind) | low | Real, mas o limite é fixo no PRD, as duas checagens ficam no mesmo arquivo e o AD-6 manda checar a query na rota. Unificar exige um alias novo validado por `TypeAdapter`, mais que uma correção direta. Rejeitado | — |
| 3 | `if not tag: return repo.listar(conn)` duplica a chamada ao repo (blind) | low | Real: a 2.2 teria de pôr a janela em duas chamadas. Correção direta | patch (absorvido no loopback) |
| 4 | Nenhum teste filtra depois de um PATCH que troca as tags (blind) | false | O filtro lê `nome_norm`, e a 1.4 já testa que o PATCH regrava `nome_norm` com `norm_tag` (AC da 1.4). Não há caminho novo | — |
| 5 | Em `test_filtrar_por_tag_invalida`, comparar a listagem antes e depois de um GET não prova nada, e `"detail" in` não confere o motivo (blind) | low | Real: um GET não grava, e o caso `a&a` passaria rejeitado por outro motivo. Correção direta | patch (absorvido no loopback) |
| 6 | Asserts de `test_filtrar_por_tag` conferem a fixture, não a resposta (blind) | false | Vêm depois de `r.json() == [backend]`, então conferir `backend` é conferir a resposta | — |
| 7 | Nenhum teste de `\x1c` na query (blind) | false | A rota usa `_aparar` (`str.strip()`) e o repo filtra por `norm_tag`, que também usa `str.strip()`. Mesmo que a rota regredisse, o repo ainda apararia | — |
| 8 | Sem índice em `nome_norm` (blind) | low | Real, mas o piloto tem poucas centenas de tarefas, e o índice é mudança de schema. Rejeitado | — |
| 9 | Status da spec (`in-review`) diferente do sprint-status (`in-progress`); task fala `= []` e o código usa `default_factory` (blind) | false / spec | O step 5 sincroniza o sprint-status no fechamento, como na 1.3 e na 1.4. O texto da task é edição da spec (rejeitado pela regra), mas foi acertado de carona na emenda do #1 | — |
| 10 | O OpenAPI do `tag` não diz que é um valor só, de até 50 caracteres (blind) | low | Real: o `/docs` (NFR-4) sugere enviar várias. A correção é um `description=` na `Query` | patch (absorvido no loopback) |

Passada 2 (blind-hunter, edge-case-hunter, verification-gap), depois do loopback. Edge-case e verification-gap: nenhum achado.

| # | Achado | Veredito | Evidência | Rota |
|---|---|---|---|---|
| 1 | ~25 linhas de validação à mão que o FastAPI faz nativo com `list[Annotated[str, ..., StringConstraints(min_length=1, max_length=50)]]` e `Query(max_length=1)`; o 50 fica repetido (blind) | false | carried do #2 da passada 1, com evidência nova: a rubric do spine (`reviews/review-rubric.md`, item 2) ofereceu `Query(max_length=1)` ou checagem explícita, e o AD-6 escolheu "checagem feita na rota"; a `review-currency.md` aponta `RequestValidationError`. O código segue a decisão registrada | — |
| 2 | O OpenAPI não publica `maxItems`/`minLength`/`maxLength` do `tag` (blind) | low | carried do #10 da passada 1: o contrato está no `description`, conferido por `test_openapi_documenta_tag`. Publicar como schema depende do #1 | — |
| 3 | `?tags=backend` (typo) é ignorado e devolve a lista inteira (blind) | false | Fora do escopo pela intenção: o PRD (§FR-6, linha 133) lista de forma fechada os 422 da query, e o AGENTS.md proíbe funcionalidade fora de FR-1 a FR-6. O FastAPI já ignorava parâmetro desconhecido em todas as rotas desde a 1.1. Levado ao Anderson no fechamento, sem bloquear | — |
| 4 | `test_filtrar_por_tag_invalida` confere só `loc` e `msg` de `detail[0]`; o AC do formato igual ao 422 do corpo não fica preso (blind) | low | Real: um erro a mais, sem `type` ou com `input` trocado passaria. Correção direta: comparar o `detail` inteiro | patch |
| 5 | `_nova(client, tags=["a"])` sobrou sem uso em `test_filtrar_por_tag_invalida` (blind) | low | Real: servia à comparação antes/depois removida no loopback. Deleção | patch |
| 6 | O ramo de validação é difícil de seguir; extrair `_erro_query` para a 2.2 reusar (blind) | low | Só legibilidade; o helper só tem um chamador hoje. A 2.2 extrai quando tiver o segundo. Rejeitado | — |
| 7 | O comentário de `repo.listar` cita AD-5 para "volta com todas as tags", que é FR-5/AD-9 (blind) | low | Real. Correção direta | patch |
| 8 | Status da spec (`in-review`) diferente do sprint-status (`in-progress`) (blind) | false | carried do #9 da passada 1: o step 5 sincroniza no fechamento | — |
| 9 | `## Implementation Notes` vazio (blind) | false | Correção é editar a spec (rejeitado pela regra); preenchido no fechamento, que é quando a seção é escrita | — |
| 10 | `epic-2-context.md` descreve a fixture `client` com `api.agora` fixo, que ainda não existe (blind) | false | O contexto descreve a convenção do spine, e o próprio arquivo diz em Cross-Story Dependencies que a 2.2 acrescenta `api.agora` | — |
| 11 | Sem teste da precedência entre erros em `?tag=&tag=backend` (blind) | false | A matriz só exige 422 para os dois motivos, e os dois casos dão 422 pelo `len > 1`. Nenhum comportamento fica sem dono | — |

## Design Notes

- **Decisão técnica de baixo risco, tomada pelo agente (revista na passada 1):** o 422 da query vem de `RequestValidationError`, levantado na rota. Assim o `detail` é a lista padrão do FastAPI (AD-7), a mesma do 422 do corpo e a que o OpenAPI anuncia.
- **Decisão técnica de baixo risco, tomada pelo agente:** o limite de 50 caracteres conta depois do strip, como no corpo (AD-6, "depois do strip").
- **Decisão técnica de baixo risco, tomada pelo agente (passada 3):** o limite de tag é a constante `api.TAG_MAX`, e não um alias validado por `TypeAdapter`. Assim o 50 tem uma fonte só, sem mudar o formato do 422 nem a checagem na rota (AD-6).
- **Decisão técnica de baixo risco, tomada pelo agente:** `listar` ganha só `tag` agora; `pendentes`, `de` e `ate` entram na 2.2, que é quem os usa.

## Verification

**Commands:**
- `uv run pytest` -- expected: todos passam
- `uv run ruff check` e `uv run ruff format --check` -- expected: sem achados
