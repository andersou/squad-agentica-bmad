---
title: 'Story 1.4: Editar e concluir tarefa'
type: 'feature'
created: '2026-10-06'
status: 'done'
baseline_commit: 'f0709aa77f9fb485a0189f6e10d3f27c2128b1c6'
route: 'dispatch'
review_loop_iteration: 2
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-06/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** O dev não consegue corrigir título, prazo ou tags de uma tarefa nem marcá-la como concluída (FR-2, FR-5), porque a API ainda não tem `PATCH /tarefas/{id}`.

**Approach:** Acrescentar `PATCH /tarefas/{id}` (200 com a tarefa, AD-7) com um schema `TarefaEditar` de campos opcionais que reusa `Titulo`, `Prazo` e `Tags`, mais `concluida: StrictBool` (AD-6). A rota chama `repo.editar(conn, id, dados.model_dump(exclude_unset=True))`, que confere, grava (trocando as tags) e relê numa única transação e devolve `Tarefa | None` (AD-8, AD-9).

## Boundaries & Constraints

**Always:** seguir AD-1 a AD-9 do spine e o AGENTS.md. Edição parcial: campo omitido mantém o valor. `null` em qualquer campo dá 422. `tags` enviado substitui a lista, `tags: []` limpa. A validação (422) vem antes da busca (404). O `id` de path usa `api.Id`. A tarefa que some antes ou durante o PATCH dá 404, nunca 500. Concluir mantém a tarefa na listagem geral.

**Never:** `GET /tarefas/{id}`; filtro por concluída; `PUT`; normalizar tag fora de `domain`; SQL fora de `repo.py`; outro `TestClient`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Concluir | `{"concluida": true}` | 200; só `concluida` muda; continua em `GET /tarefas` | N/A |
| Corpo vazio | `{}` | 200 com a tarefa inalterada | N/A |
| Tags | `{"tags": ["Infra","infra"]}`, depois `{"titulo": "Outro"}`, depois `{"tags": []}` | `["Infra"]`, depois mantidas, depois `[]` | N/A |
| Título e prazo | `{"titulo": " y ", "prazo": "2026-10-01"}` | 200 com `y` e o novo prazo; a listagem reordena | N/A |
| Corpo inválido | `null` em qualquer campo; `concluida` `"true"` ou `1`; campo desconhecido; título/prazo/tags que o POST rejeita | 422 | tarefa inalterada; com id inexistente também 422 |
| Inexistente | id nunca criado ou excluído, corpo válido | 404 `{"detail": "tarefa não encontrada"}` | nada muda |
| Id inválido | `2**63`, `1_0`, `abc` | 422 | nunca 500 |
| Exclusão concorrente | outra conexão tenta excluir durante o `editar` | não consegue entrar no meio; o PATCH termina com 200, ou 404 se a exclusão veio antes | nunca 500 |

</frozen-after-approval>

## Code Map

- `src/tarefas/api.py` -- reusar `Titulo`, `Prazo`, `Tags`, `Id`, `Conexao` e o padrão de `excluir_tarefa` (`responses={404: ...}`, `HTTPException(404, "tarefa não encontrada")`). Importar `StrictBool` de `pydantic`. Não mexer em `conexao`.
- `src/tarefas/repo.py` -- `criar` mostra o `with conn:` e o `executemany` das tags com `norm_tag`; `listar` monta `Tarefa` a partir do `LEFT JOIN`. Extrair essa montagem para um helper privado `_buscar(conn, onde, params)` usado por `listar` e `editar`, sem mudar a assinatura nem o SQL de ordenação de `listar`.
- `tests/test_tarefas.py` -- reusar a fixture `client`, `_linhas_tag` e o padrão `sqlite3.connect(os.environ["TAREFAS_DB"])`. `test_camadas` fica como está.

## Tasks & Acceptance

**Execution:**
- [x] `src/tarefas/repo.py` -- `_buscar` extraído de `listar`; `editar(conn, id, campos) -> Tarefa | None`: em `with conn:`, `BEGIN IMMEDIATE`, confere a existência (devolve `None` se não há), `UPDATE` só das colunas presentes entre `titulo`/`prazo`/`concluida` (ISO e 0/1 aqui), se `"tags" in campos` apaga e reinsere com `norm_tag`, relê com `_buscar` -- AD-8, AD-9
- [x] `src/tarefas/api.py` -- `TarefaEditar` (`extra="forbid"`; `titulo: Titulo = None`, `prazo: Prazo = None`, `tags: Tags = None`, `concluida: StrictBool = None`) e `@app.patch("/tarefas/{id}", responses={404: ...})` `def editar_tarefa(id: Id, dados: TarefaEditar, conn: Conexao) -> Tarefa`; `None` levanta 404 -- AD-6, AD-7
- [x] `tests/test_tarefas.py` -- um teste por linha da I/O Matrix (inválidos parametrizados, conferindo a tarefa intacta); `repo.editar` direto com id inexistente e `tags` devolve `None`; o teste de concorrência usa um proxy de conexão que, depois da conferência, tenta `DELETE` por outra conexão com `timeout=0` e espera `sqlite3.OperationalError`

### Review Findings

Passada 2 (`bmad-code-review`, 2026-10-06; blind-hunter, edge-case-hunter, verification-gap, acceptance-auditor). Revê também os itens rejeitados na passada 1 contra o AGENTS.md.

- [x] [Review][Patch] Nenhum teste provava que a resposta do PATCH é a tarefa editada: em todos, ela já era a primeira da lista. Trocar o read-back por `_buscar(conn, "", ())[0]` mantinha 83 passed (verification-gap). Agora `test_editar_concluir` cria antes uma tarefa com prazo menor, e a mesma mutação faz o teste falhar [tests/test_tarefas.py:316]
- [x] [Review][Patch] `StrictBool` só era testado com valores verdadeiros (`"true"`, `1`), e corpo ausente ou que não é objeto não tinha caso. `test_editar_corpo_invalido` ganhou `{"concluida": 0}`, `{"concluida": "false"}`, sem corpo, `[]` e `"x"`, todos 422 [tests/test_tarefas.py:372]
- [x] [Review][Patch] `test_repo_editar_bloqueia_exclusao_concorrente` conferia só `id`, `tags` e `concluida` da `Tarefa` devolvida, e um `prazo` como `str` ou um `titulo` errado passariam. Agora compara com a `Tarefa` inteira [tests/test_tarefas.py:506]
- [x] [Review][Patch] `review_loop_iteration` ficou em 0 depois da passada 1, o mesmo erro corrigido na 1.3. Agora está em 2 [spec]

**Rejected:**
- `BEGIN IMMEDIATE` com lock preso por mais de 5 s vira 500, contra o "nunca 500" da matriz (blind, edge, acceptance; era o #9 da passada 1) — false quanto à matriz: a linha "Exclusão concorrente" é coberta, porque o `DELETE` do app segura o lock por microssegundos, e o `editar` espera até 5 s. Só um processo de fora com uma transação aberta chega a 5 s. Essa contenção genérica vale para toda escrita e já foi decidida pelo Anderson na Deferred do spine ("Concorrência de escrita"), e a guarda criaria um código HTTP (503) fora do AD-7. Não fica adiado: a decisão já existe.
- A evidência do #1 da passada 1 cita `in-progress`, mas o sprint-status commitado vai de `backlog` para `done` — false como defeito: os estados intermediários não foram commitados, e o log da passada 1 é histórico. O tracking final está consistente.
- `campos: dict` sem tipo das chaves em `repo.editar` — false: a assinatura `editar(conn, id, campos: dict)` é a do AD-9, e o único chamador passa `model_dump(exclude_unset=True)` de `TarefaEditar`.
- Limites aceitos via PATCH (título de 200, tag de 50, prazo passado) — false: o PATCH usa os mesmos aliases `Titulo`, `Tags` e `Prazo` do POST, cujos limites já têm teste, e `test_editar_titulo_e_prazo` grava um prazo passado.

Com os patches, `uv run pytest` dá 88 passed, e `ruff check` e `ruff format --check` passam. Conferência dos AD-1 a AD-9 contra o diff refeita pelo acceptance-auditor e por mim: continua valendo a da passada 1. Os patches só tocam os testes.

**Acceptance Criteria:**
- Given o código da story, when rodo `uv run pytest`, `uv run ruff check` e `uv run ruff format --check`, then os três passam.
- Given um PATCH com tags, when releio pelo banco, then `tarefa_tag` tem só as tags novas da tarefa e `nome_norm` vem de `norm_tag`.

## Implementation Notes

- Arquivos: `repo.py` (`_buscar` extraído de `listar`, e `editar`), `api.py` (`TarefaEditar` e a rota `editar_tarefa`) e `tests/test_tarefas.py`.
- O `UPDATE` monta a lista de colunas com f-string, mas os nomes vêm da tupla fixa `("titulo", "prazo", "concluida")`, nunca da entrada.
- Tirar o `BEGIN IMMEDIATE` faz `test_repo_editar_bloqueia_exclusao_concorrente` falhar (conferido pelo agente de implementação).

## Spec Change Log

## Review Triage Log

Passada 1 (blind-hunter, edge-case-hunter, verification-gap).

| # | Achado | Veredito | Evidência | Rota |
|---|---|---|---|---|
| 1 | Status da spec (`in-review`) diferente do sprint-status (`in-progress`) (blind) | false | O step 5 sincroniza o sprint-status no fechamento, como na 1.3 | — |
| 2 | O PATCH não testa os limites de id que o DELETE testa (`-2**63-1`, `2**63-1`, `-2**63`) (blind) | low | Real: só `2**63`, `1_0` e `abc`. A correção é estender a parametrização | patch |
| 3 | Nenhum teste prova o rollback de um `editar` que falha (AD-8) (blind) | low | Real: a 1.2 tem `test_criar_atomico_com_tags_colidindo`, e a 1.4 não. A correção é um teste com tags colidindo | patch |
| 4 | `_tags_no_banco` duplica `_linhas_tag` (blind) | low | Real: as duas abrem a conexão e consultam `tarefa_tag` por `tarefa_id`. A correção é `_linhas_tag = len(_tags_no_banco(id))` | patch |
| 5 | O OpenAPI de `TarefaEditar` mostra `"default": null` (blind) | false | `app.openapi()` não traz `default` em nenhum campo de `TarefaEditar`, porque o Pydantic omite o default `None` | — |
| 6 | A classe de teste `Conexao` repete o nome de `api.Conexao` (blind) | low | Real e cosmético. A correção é renomear para `ConexaoEspia` | patch |
| 7 | O teste de concorrência não mostra que o lock é liberado depois do `editar` (blind) | low | Real: um lock preso passaria. A correção é excluir por outra conexão depois e conferir a lista vazia. O caminho da rota com tarefa sumida já é coberto por `test_editar_inexistente` | patch |
| 8 | Seções de implementação e triagem vazias (blind) | false | Preenchidas nesta passada | — |
| 9 | Lock esperado por mais de 5 s faz `BEGIN IMMEDIATE` levantar `database is locked` e virar 500, contra o "nunca 500" da matriz (edge, também como claim) | low | Real só sob contenção que o piloto não tem: as outras escritas seguram o lock por microssegundos. A Deferred do spine ("Concorrência de escrita") já decide isso para todas as escritas. A correção acrescenta guarda. Rejeitado | — |
| 10 | `editar` numa conexão já em transação levanta `cannot start a transaction within a transaction` (edge) | false | O único chamador é a rota, com a conexão nova de `api.conexao`, e toda escrita do repo fecha a própria transação com `with conn:` | — |
| 11 | Chaves desconhecidas em `campos` são ignoradas em silêncio (edge) | false | `campos` vem de `TarefaEditar` com `extra="forbid"` (AD-9), então chave desconhecida dá 422 antes do repo | — |
| 12 | O 404 declarado em `responses` do PATCH (e do DELETE) não tem teste (verification-gap) | low | Pré-verificado: tirar `responses=` não quebra nenhum teste. A correção é um teste lendo `/openapi.json` | patch |

Patches 2, 3, 4, 6, 7 e 12 aplicados, todos em `tests/test_tarefas.py`: `uv run pytest` dá 83 passed, e `ruff check` e `ruff format --check` passam.

Conferência dos AD contra o diff:
- **AD-1:** `repo` continua importando só `tarefas.domain`, `domain` não mudou, e `test_camadas` passa.
- **AD-2:** nenhuma leitura de relógio.
- **AD-3:** não se aplica, porque não há janela.
- **AD-4:** `_buscar` mantém `ORDER BY t.prazo ASC, t.id ASC, g.rowid ASC`, e `listar` só delega. `test_listar_ordenado_por_prazo_e_id` passa.
- **AD-5:** as tags do PATCH passam por `Tags` (`normalizar_tags`), e o repo grava `nome_norm` com `norm_tag`. Nenhum `lower`/`casefold` novo (`test_camadas`).
- **AD-6:** `TarefaEditar` com `extra="forbid"`, os mesmos `Titulo`/`Prazo`/`Tags` e `concluida: StrictBool`. `null` dá 422, `{}` dá 200, `tags: []` limpa, e a validação vem antes do 404 (`test_editar_corpo_invalido` com id inexistente). O `id` usa `api.Id`.
- **AD-7:** `PATCH /tarefas/{id}` dá 200 com a tarefa, o inexistente dá 404 via `HTTPException` com `{"detail"}`, e a rota é `def`.
- **AD-8:** `editar` roda num só `with conn:` com `BEGIN IMMEDIATE`. As tags são apagadas e reinseridas na mesma transação, o rollback está testado, e a conexão vem de `api.conexao`.
- **AD-9:** `editar(conn, id, campos) -> Tarefa | None` recebe `model_dump(exclude_unset=True)` e devolve `domain.Tarefa` montada por `_buscar`, com 0/1 e ISO convertidos no repo. O SQL de `tarefa_tag` fica só no repo.

## Design Notes

- **Decisão técnica de baixo risco, tomada pelo agente:** campos do PATCH com default `None` sem `Optional` no tipo. O Pydantic não valida o default, então campo omitido não aparece em `model_dump(exclude_unset=True)`, e `null` enviado é validado contra `Titulo`/`Prazo`/`Tags`/`StrictBool` e dá 422.
- **Decisão técnica de baixo risco, tomada pelo agente:** `BEGIN IMMEDIATE` no início de `editar`. No modo legado do `sqlite3`, o `SELECT` de conferência rodaria fora da transação (o `BEGIN` implícito só vem antes do primeiro DML), e uma exclusão entre a conferência e o `INSERT` das tags viraria `IntegrityError` de FK, ou seja, 500 (a armadilha da v1). Com o lock de escrita pego antes da conferência, ninguém exclui no meio.

## Verification

**Commands:**
- `uv run pytest` -- expected: todos passam
- `uv run ruff check` e `uv run ruff format --check` -- expected: sem achados
