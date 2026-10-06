---
title: 'Story 1.3: Excluir tarefa'
type: 'feature'
created: '2026-10-06'
status: 'done'
baseline_commit: '4263204d8ff0de143a4a8245252ad3f5b75658cb'
route: 'dispatch'
review_loop_iteration: 2
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-06/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** O dev não consegue tirar da lista uma tarefa cancelada ou cadastrada por engano (FR-3), porque a API ainda não tem `DELETE /tarefas/{id}`.

**Approach:** Acrescentar `DELETE /tarefas/{id}` (204 sem corpo, AD-7), apoiado em `repo.excluir(conn, id) -> bool` num `with conn:` (AD-8, AD-9). As tags somem pelo `ON DELETE CASCADE` de `tarefa_tag`, que depende do `PRAGMA foreign_keys=ON` já ligado em `api.conexao`.

## Boundaries & Constraints

**Always:** seguir AD-1 a AD-9 do spine e o AGENTS.md. A exclusão é definitiva. Id inexistente dá 404 via `HTTPException` (`{"detail": ...}`). O `id` de path é `int` com `le=2**63-1` e `ge=-2**63`, e fora disso (ou não inteiro) dá 422, nunca 500. O SQL fica só em `repo.py`, e `excluir` devolve `False` quando nenhuma linha foi apagada.

**Never:** apagar as tags com SQL explícito (o cascade cuida); exclusão lógica ou lixeira; `GET /tarefas/{id}`; `PATCH` (1.4); outro `TestClient`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Excluir | tarefa existente com tags, mais outra tarefa | 204 sem corpo; `GET /tarefas` traz só a outra; `tarefa_tag` não tem linha da excluída | N/A |
| Inexistente | id nunca criado, ou já excluído (segundo `DELETE`) | 404 `{"detail": ...}` | nada muda |
| Id fora do INTEGER | `2**63`, `-2**63-1` | 422 | nunca 500 |
| Id não inteiro | `abc`, `1.5` | 422 | nunca 500 |
| Limite | `2**63-1`, `-2**63` | 404 | N/A |

</frozen-after-approval>

## Code Map

- `src/tarefas/repo.py` -- `criar_schema` já cria `tarefa_tag` com `ON DELETE CASCADE`. Acrescentar `excluir(conn, id) -> bool` ao lado de `criar`, com o mesmo padrão `with conn:`.
- `src/tarefas/api.py` -- `conexao` já liga `PRAGMA foreign_keys=ON` (não mexer). Acrescentar a rota `def` e um alias `Id = Annotated[int, Path(ge=-2**63, le=2**63-1)]` no padrão de `Prazo`/`Titulo`, para a 1.4 reusar. Importar `HTTPException`, `Path` e `Response` de `fastapi`.
- `tests/test_tarefas.py` -- reusar a fixture `client` e o padrão `sqlite3.connect(os.environ["TAREFAS_DB"])` de `test_persistencia`. `test_camadas` fica como está.

## Tasks & Acceptance

**Execution:**
- [x] `src/tarefas/repo.py` -- `excluir(conn, id) -> bool`: `DELETE FROM tarefa WHERE id = ?` em `with conn:`, devolve `rowcount > 0` -- AD-8, AD-9
- [x] `src/tarefas/api.py` -- `@app.delete("/tarefas/{id}", status_code=204)`, `def excluir_tarefa(id: Id, conn: Conexao) -> Response`; `False` levanta `HTTPException(404, "tarefa não encontrada")`; devolve `Response(status_code=204)` -- AD-7
- [x] `tests/test_tarefas.py` -- um teste por linha da I/O Matrix (ids inválidos e limites parametrizados); o teste de exclusão confere `tarefa_tag` vazia para o id direto no banco -- cobre a matriz e o cascade

### Review Findings

Passada 2 (`bmad-code-review`, 2026-10-06; blind-hunter, edge-case-hunter, verification-gap, acceptance-auditor). Revê também os itens rejeitados ou adiados na passada 1, que o AGENTS.md não permite (achado com correção clara é corrigido, e nada é adiado).

- [x] [Review][Patch] `id` não canônico apaga a tarefa errada: `DELETE /tarefas/1_0` apagava a tarefa 10, e `1.0`, `+1` e `%201` também davam 204 (era o #13 da passada 1). `api.Id` ganhou o `BeforeValidator(_id_inteiro)` com `^-?\d+$`, no padrão de `_prazo_iso`, e `test_excluir_id_nao_canonico` confere 422 e a lista intacta. Isso também prova a precedência 422 antes de 404 com um id que existe (AD-6) [src/tarefas/api.py:54]
- [x] [Review][Patch] Nos casos-limite de 404, `test_excluir_id_limites` só conferia `"detail" in r.json()`, e um 404 de rota não casada também passaria. Agora confere `{"detail": "tarefa não encontrada"}` [tests/test_tarefas.py]
- [x] [Review][Patch] O 404 não aparecia no OpenAPI (era o #8 da passada 1): `responses={404: ...}` no decorator [src/tarefas/api.py]
- [x] [Review][Patch] O pitfall do `id` estava em deferred-work, o que fere o AGENTS.md (era o #6 da passada 1). O pitfall do AGENTS.md passa a citar `api.Id` com `ge`, `le` e só dígitos. O `epic-1-context.md` cita a regra de dígitos, e o item saiu do `deferred-work.md` [AGENTS.md]
- [x] [Review][Patch] O tracking estava inconsistente: a spec dizia `done`, o sprint-status dizia `review`, e `review_loop_iteration` estava em 0. Os dois agora dizem `done`, a iteração está em 2 e `last_updated` tem o horário real do fechamento [sprint-status.yaml]

**Rejected:**
- `repo.excluir` deixa tags órfãs sem `PRAGMA foreign_keys=ON` (#5 da passada 1) — false: o único chamador é a rota, com a conexão de `api.conexao` (AD-8), e `test_excluir` quebra se o pragma sumir. Pôr uma guarda no repo duplicaria o dono da configuração da conexão.
- `Response(status_code=204)` redundante com o decorator (#7 da passada 1) — false: nenhum dano. O decorator documenta o 204 no OpenAPI, o retorno é a assinatura fixada nas Tasks, e o corpo sai vazio (`test_excluir`).
- `ge=-2**63` dentro do bloco congelado sem aval humano — false: a spec foi aprovada como estava pela regra da sessão ("aprovar e continuar"), e a decisão está nas Design Notes.
- `test_excluir` não confere no banco a tag de `outra` — false: `GET /tarefas == [outra]` inclui `tags: ["a"]`, e o `LEFT JOIN` perderia a tag se a linha sumisse.
- AD-8 sem prova de conexão por request com pragma — false: o mesmo `test_excluir` cobre isso.
- `last_updated` recuou, e o log da passada 1 cita 12:34 em vez de 12:37 — low: é só o registro histórico da passada 1. O valor foi corrigido no fechamento desta passada.

**Acceptance Criteria:**
- Given o código da story, when rodo `uv run pytest`, `uv run ruff check` e `uv run ruff format --check`, then os três passam.
- Given `repo.excluir` chamado direto com um id inexistente, when retorna, then devolve `False` e nenhuma tarefa é afetada.

## Implementation Notes

- Arquivos: `repo.py` (`excluir`), `api.py` (alias `Id` com `_id_inteiro` e rota `excluir_tarefa`) e `tests/test_tarefas.py` (5 testes, mais o helper `_linhas_tag`).
- Sem o `PRAGMA foreign_keys=ON`, a linha de `tarefa_tag` sobra, e `test_excluir` falha. O GET sozinho não pegaria, porque o `LEFT JOIN` parte de `tarefa`.

## Spec Change Log

## Review Triage Log

Passada 1 (blind-hunter, edge-case-hunter, verification-gap). O verification-gap não achou lacunas.

| # | Achado | Veredito | Evidência | Rota |
|---|---|---|---|---|
| 1 | `last_updated` do sprint-status voltou de 12:45 para 12:34 (blind + edge) | false | 12:34 é o relógio real da máquina. O 12:45 anterior estava adiantado, e gravar um horário futuro seria inventar | — |
| 2 | Sprint-status em `in-progress` com a spec em `in-review` | false | O step 5 sincroniza o sprint-status no fechamento | — |
| 3 | O teste do cascade passa mesmo se as tags nunca forem gravadas | low | Real: só conferia 0 linhas depois. A correção é um `assert` antes do DELETE | patch |
| 4 | A tarefa sobrevivente não tinha tags, então um DELETE de tags amplo demais passaria | low | Real. A correção é dar tags a `outra` | patch |
| 5 | `repo.excluir` deixa tags órfãs numa conexão sem `PRAGMA foreign_keys=ON` | low | Real fora da API, mas o único chamador é a rota, com a conexão de `api.conexao` (AD-8). A correção acrescenta guarda no repo. Rejeitado | — |
| 6 | `ge=-2**63` decidido pelo agente sem constar no spine | low | O spine não fixa nenhum limite de id. A decisão é técnica (regra da sessão) e está no Design Notes. Patch: `epic-1-context.md` passa a citar `ge` e `le`. O AGENTS.md também só cita `le`, e editar contexto de agente vai para deferred-work | patch + defer |
| 7 | `Response(status_code=204)` redundante com o `status_code=204` do decorator | low | Real e cosmético, mas a assinatura `-> Response` está nas Tasks desta spec. Rejeitado porque a correção edita a spec da build | — |
| 8 | O 404 não aparece no OpenAPI | low | Real, mas nenhuma rota declara `responses`, e a correção acrescenta parâmetro. Rejeitado | — |
| 9 | Nenhum teste fixa a mensagem do 404 | low | Real: um 404 de rota não casada passaria. A correção é trocar o `assert` | patch |
| 10 | A exclusão concorrente (204 e 404) não tem teste | false | O segundo `DELETE` de `test_excluir_inexistente` exercita a mesma sequência, e o `DELETE` é uma instrução só | — |
| 11 | Seções de revisão vazias e AD não conferidos | false | Preenchidos nesta passada (abaixo) | — |
| 12 | Caminhos inconsistentes no diff | false | Artefato do arquivo temporário da revisão, não do repositório | — |
| 13 | `DELETE /tarefas/1.0` (ou `+1`, `" 1"`) exclui a tarefa 1 em vez de 422 (edge) | low | Confirmado com o TestClient: `1.0` dá 204. Mas `1.0` tem valor inteiro e aponta a tarefa 1, ninguém digita isso no uso normal, e a correção acrescenta `pattern` ao `Id`. Rejeitado | — |

Patches 3, 4, 6 e 9 aplicados: `uv run pytest` dá 42 passed, e `ruff check` e `ruff format --check` passam.

Conferência dos AD contra o diff:
- **AD-1:** `repo` importa só `tarefas.domain`, `domain` não mudou, e `test_camadas` passa.
- **AD-2:** nenhuma leitura de relógio.
- **AD-3:** não se aplica, porque não há janela.
- **AD-4:** `listar` não mudou.
- **AD-5:** nenhuma normalização de tag nova, e o cascade apaga as tags sem SQL de tag fora do repo.
- **AD-6:** `id` com `le=2**63-1` (e `ge=-2**63`). A validação (422) vem antes da busca (404), como mostra `test_excluir_id_limites`.
- **AD-7:** `DELETE /tarefas/{id}` dá 204 sem corpo, o inexistente dá 404 via `HTTPException` com `{"detail"}`, e a rota é `def`.
- **AD-8:** `excluir` roda em `with conn:`, e o cascade depende do `PRAGMA foreign_keys=ON` de `api.conexao`, testado direto em `tarefa_tag`.
- **AD-9:** `excluir(conn, id) -> bool`, `False` para inexistente, e o SQL fica só no `repo`.

## Design Notes

- **Decisão técnica de baixo risco, tomada pelo agente:** o AD-6 fixa só `le=2**63-1`, mas `-2**63-1` estoura o INTEGER do SQLite do mesmo jeito (a armadilha da v1, pelo outro lado). `ge=-2**63` fecha o buraco sem mudar a regra "id inexistente dá 404": todo inteiro que cabe no SQLite e não existe continua 404.
- **Decisão técnica de baixo risco, tomada na code review (passada 2):** `api.Id` aceita só `^-?\d+$` antes da conversão para `int`. O `int` padrão do Pydantic aceita `1.0`, `+1`, `" 1"` e `1_0` (este último vira 10), e num DELETE isso apaga a tarefa errada. Zero à esquerda (`05`) continua valendo, porque é um inteiro em dígitos.
- O `DELETE` é uma instrução só, então não há janela entre conferir e apagar. Exclusão concorrente da mesma tarefa: uma recebe 204 e a outra 404.

## Verification

**Commands:**
- `uv run pytest` -- expected: todos passam
- `uv run ruff check` e `uv run ruff format --check` -- expected: sem achados
