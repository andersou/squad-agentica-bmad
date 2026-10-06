---
title: 'Story 2.2: Consultar pendentes por janela de prazo'
type: 'feature'
created: '2026-10-06'
status: 'done'
baseline_commit: '1796fa3c51e1d6753514cbd4e0055fc2aa015636'
route: 'dispatch'
review_loop_iteration: 2
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-06/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** O script matinal do time não consegue perguntar à API o que está vencido, o que vence hoje e o que vence nos próximos 7 dias (FR-6), porque `GET /tarefas` só lista tudo ou filtra por tag.

**Approach:** `GET /tarefas` ganha a query `janela` (`vencidas`, `hoje`, `proximos-7-dias`). A rota lê o relógio só por `api.agora()` (UTC aware), `domain.hoje` converte para America/Sao_Paulo, `domain.intervalo` devolve `(de, ate)` e `repo.listar(conn, *, pendentes=False, de=None, ate=None, tag=None)` aplica `concluida = 0` e os limites, combinável com `tag` (AD-2, AD-3, AD-9).

## Boundaries & Constraints

**Always:** seguir AD-1 a AD-9 do spine e o AGENTS.md. Só pendentes nas janelas, limites inclusivos. `pendentes=True` se e só se houver janela. Ordem `prazo ASC, id ASC` (AD-4). Sem `janela`, a resposta é a listagem geral atual (com ou sem `tag`). A fixture `client` sempre fixa `api.agora` via `app.dependency_overrides`, ajustável pelo teste. Casos-limite em `tests/test_janelas.py`, um teste cada.

**Never:** `date.today()` ou `datetime.now()` sem fuso fora de `api.agora`; nomes de janela no repo; regra de janela fora de `domain.py`; SQL fora de `repo.py`; outro `TestClient`; várias janelas ou várias tags por chamada; nada da Story 2.3 (README).

## I/O & Edge-Case Matrix

Hoje fixado em 2026-10-06 (SP).

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Limites | pendentes com prazo 10-05, 10-06, 10-07, 10-13, 10-14 | 10-05 só em `vencidas`; 10-06 só em `hoje`; 10-07 e 10-13 só em `proximos-7-dias`; 10-14 em nenhuma | N/A |
| Concluída | concluída com prazo 10-05 | fora de `vencidas`; após `PATCH {"concluida": false}`, volta | N/A |
| Fuso | `agora` = 2026-10-07 01:00 UTC (22h SP de 10-06), prazo 10-06 | aparece em `hoje`, não em `vencidas` | N/A |
| Com tag | vencidas com `backend` (id maior com prazo menor) e `frontend`; `?janela=vencidas&tag=Backend` | só as de `backend`, `prazo ASC, id ASC` | N/A |
| Sem janela | concluída vencida e pendente em hoje + 30 | ambas na listagem geral | N/A |
| Inválido | `?janela=amanha`, `?janela=`, `?janela=hoje&janela=vencidas`, `?janela=hoje&janela=hoje` | 422 `{"detail": [...]}` com `loc` `["query", "janela"]` | nada muda |

</frozen-after-approval>

## Code Map

- `src/tarefas/domain.py` -- acrescentar `Janela(StrEnum)`, `hoje(agora) -> date` (`agora.astimezone(ZoneInfo("America/Sao_Paulo")).date()`) e `intervalo(janela, hoje) -> tuple[date | None, date | None]`. Só stdlib (`enum`, `datetime`, `zoneinfo`); `test_camadas` confere.
- `src/tarefas/repo.py` -- `listar(conn, *, tag=None)` vira `listar(conn, *, pendentes=False, de=None, ate=None, tag=None)`, montando a lista de condições (`t.concluida = 0`, `t.prazo >= ?`, `t.prazo <= ?` com `isoformat()`, e a subconsulta de tag existente) unidas por `AND` em `onde`. Não mexer em `_buscar`.
- `src/tarefas/api.py` -- `agora() -> datetime` = `datetime.now(UTC)`. `listar_tarefas` recebe `janela: Janela | None` (com `description`), `request: Request` para `request.query_params.getlist("janela")` e `agora_: Annotated[datetime, Depends(agora)]`. Extrair `_erro_query(campo, msg, entrada)` que levanta o `RequestValidationError` da 2.1 (segundo chamador, como previsto na passada 2 #6). Uma única chamada `repo.listar(conn, pendentes=..., de=..., ate=..., tag=valor)`.
- `tests/conftest.py` -- `client` vira fixture com `yield`: põe `app.dependency_overrides[api.agora] = lambda: AGORA` (2026-10-06 15:00 UTC) e limpa os overrides no teardown.
- `tests/test_janelas.py` -- novo. Reusar o padrão de `_nova` de `tests/test_tarefas.py` (copiar o helper; ele é local àquele módulo).

## Tasks & Acceptance

**Execution:**
- [x] `src/tarefas/domain.py` -- `Janela`, `hoje`, `intervalo` -- AD-2, AD-3
- [x] `src/tarefas/repo.py` -- `listar` com `pendentes`, `de`, `ate`, `tag` -- AD-3, AD-9
- [x] `src/tarefas/api.py` -- `agora`, query `janela`, checagem de repetição na rota, `_erro_query`, chamada única ao repo -- AD-2, AD-6, AD-7
- [x] `tests/conftest.py` -- override de `agora` e limpeza -- AD-2
- [x] `tests/test_janelas.py` -- um teste por linha da matriz (Limites parametrizado por prazo, um caso por limite); `domain.hoje` e `domain.intervalo` diretos; `repo.listar` direto com `de`/`ate` sem `pendentes`; `janela` no OpenAPI com o enum; relógio lido só em `api.agora` -- NFR-3

**Acceptance Criteria:**
- Given o código da story, when rodo `uv run pytest`, `uv run ruff check` e `uv run ruff format --check`, then os três passam.
- Given `src/`, when procuro leituras do relógio, then `today(` não aparece e `now(` aparece uma vez só, em `api.agora`.
- Given um 422 da query `janela`, when leio o corpo, then `detail` é uma lista no formato `HTTPValidationError`, como o 422 da `tag`.

## Spec Change Log

## Review Triage Log

Passada 1 (blind-hunter, edge-case-hunter, verification-gap).

| # | Achado | Veredito | Evidência | Rota |
|---|---|---|---|---|
| 1 | `domain.intervalo` sem `case _`: um membro novo de `Janela` devolveria `None` e daria 500 (blind, edge) | false | `Janela` é fechado em três valores pelo AD-3 e os três têm `case`; o membro novo é hipotético, e o `TypeError` falha alto, não em silêncio | — |
| 2 | `domain.hoje` aceita datetime naive e usaria o fuso do host (blind, edge) | false | Nenhum chamador passa naive: `api.agora` devolve `datetime.now(UTC)` e o override da fixture é aware. O risco real (o `agora` de produção mudar) é o #13 | — |
| 3 | A guarda do relógio só pega `today(`/`now(` com parêntese; `date.today` sem chamada, `utcnow`, `time.time()` e `localtime` escapam (blind, edge) | low | Real: `Field(default_factory=date.today)` passaria. Correção direta no regex do teste | patch |
| 4 | O último assert de `test_relogio_lido_so_em_api_agora` repete o anterior, que está preso à indentação exata da linha (blind) | low | Real: um reformat quebra o teste sem mudar o comportamento. Correção direta, junto com o #3 | patch |
| 5 | `?janela=hoje&janela=amanha` dá o 422 do enum (só `amanha`), não "informe uma janela só"; a mensagem depende da ordem (blind, edge) | low | Real, mas os dois casos dão 422 com `loc` `["query", "janela"]` (a matriz pede só isso) e o erro do enum é verdadeiro. A correção é declarar `list[Janela]`, que muda o OpenAPI decidido em Design Notes. Rejeitado | — |
| 6 | Com `janela` e `tag` inválidas, o 422 só traz o erro da `janela` (blind, edge) | low | Real, mas raro (dois erros na mesma chamada) e a correção é juntar os erros numa lista, mais que correção direta. A mesma rota já parava no primeiro erro da `tag` na 2.1. Rejeitado | — |
| 7 | `_erro_query` sem anotações nem `NoReturn`, ao contrário dos outros helpers (blind) | false | Os helpers do módulo (`_prazo_iso`, `_aparar`, `_id_inteiro`) também não têm anotação | — |
| 8 | O parâmetro `hoje` de `intervalo` esconde a função `domain.hoje` (blind) | false | O AD-3 fixa a assinatura `intervalo(janela, hoje)`; o dano é hipotético (uma edição futura chamar `hoje(...)` ali) | — |
| 9 | Nenhum teste combina janela, tag e tarefa concluída (blind) | low | Real: um `pendentes` perdido só no caminho com tag passaria. Correção direta: uma concluída `backend` vencida em `test_janela_com_tag` | patch |
| 10 | Falta teste HTTP à meia-noite de SP (03:00 UTC) (blind) | false | `test_domain_hoje` cobre 03:00 UTC, e a rota só repassa `agora` a `domain.hoje`; o caso de fuso do FR-6 (22h) já tem teste HTTP | — |
| 11 | `repo.listar` direto só com `ate` e `pendentes` sem teste (blind) | false | É o formato de `vencidas`, exercido pela rota em `test_limites` e `test_concluida_fora_das_janelas` | — |
| 12 | Em `test_janela_invalida`, conferir a listagem depois de um GET não prova nada (blind) | low | Real, como o #5 da passada 1 da 2.1. Deleção; de carona, `status_code` em `test_janela_repetida_lista_valores` | patch |
| 13 | Nenhum teste chama o `api.agora()` real; um `agora` naive passaria com a suíte verde (verification-gap) | low | Pré-verificado: todo teste HTTP usa o override. Correção direta: `test_agora_utc_aware` | patch |

Passada 2 (blind-hunter, edge-case-hunter, verification-gap, acceptance-auditor). Reabre o #5 e o #6 da passada 1, cuja rejeição contrariava o AGENTS.md (achado com correção clara se corrige; decisão vira pergunta ou, nesta sessão, decisão técnica registrada).

| # | Achado | Veredito | Evidência | Rota |
|---|---|---|---|---|
| 1 | `?janela=hoje&janela=amanha` dá o 422 do enum, e `?janela=amanha&janela=hoje` dá "informe uma janela só": a mensagem depende da ordem e contraria a Design Note (blind, edge, auditor) | low | Real: o FastAPI valida o último valor antes do corpo da rota. Há correção sem mudar o OpenAPI: a checagem vira a dependência `_janela_unica` em `dependencies=[...]` da rota, que roda antes da validação da query. O teste novo falha contra o `api.py` anterior | patch |
| 2 | Com `janela` e `tag` inválidas, o 422 só traz o primeiro erro (blind, auditor) | low | Real. Juntar os dois exige levar a checagem da `tag` para validator de `Query`, o que muda `msg`/`type` do 422 da 2.1. Virou decisão técnica de baixo risco (Design Notes) | decisão registrada |
| 3 | `review_loop_iteration: 0` com uma passada feita (blind, edge, auditor) | low | Real, o mesmo defeito do action item 5 da retro do épico 1. Corrigido para 2 com esta passada | patch |
| 4 | `test_openapi_documenta_janela` compara o enum com `JANELAS` derivado de `Janela`, e os laços de `test_limites` encolhem em silêncio se um membro sumir (blind) | low | Real: o teste compara o código com ele mesmo. `JANELAS` passa a ser a lista literal do AD-3 | patch |
| 5 | A guarda do relógio não pega `from time import time; time()` nem `fromtimestamp`, e `glob` não desce em subpacotes (blind, edge) | low | Real. `RELOGIO` passa a casar `\btime\b` e `fromtimestamp`, com `rglob`; `src/` não tem a palavra `time` hoje | patch |
| 6 | Nenhum teste fixa que `janela` diferencia maiúsculas (`?janela=Hoje` → 422), ao contrário da `tag` (blind) | low | Real como lacuna: um `_missing_` em `Janela` passaria. Um caso a mais em `test_janela_invalida` | patch |
| 7 | `domain.hoje` aceita datetime naive (edge) | false | Já julgado na passada 1 (#2); `test_agora_utc_aware` agora trava o `agora` real, e o override é aware | — |
| 8 | Nenhum teste prova que `vencidas` não tem limite inferior (blind) | false | `test_domain_intervalo` fixa `(None, 10-05)` e `repo.listar` só acrescenta `prazo >= ?` com `de is not None` | — |
| 9 | O "nada muda" da linha Inválido ficou sem teste depois do patch #12 da passada 1 (auditor) | false | A rota é um GET só de leitura, pela conexão de `api.conexao`; não há escrita que um 422 pudesse deixar pela metade | — |
| 10 | A guarda do relógio acusaria `now`/`today` em comentário (blind) | false | Falha alta e visível, não esconde leitura; nenhum comentário em `src/` tem essas palavras | — |

### Review Findings

- [x] [Review][Patch] Repetição de `janela` dependia da ordem dos valores [src/tarefas/api.py:111]
- [x] [Review][Patch] `review_loop_iteration` zerado com passada feita [spec frontmatter]
- [x] [Review][Patch] `JANELAS` derivado da implementação [tests/test_janelas.py:14]
- [x] [Review][Patch] Guarda do relógio sem `time`/`fromtimestamp` e sem `rglob` [tests/test_janelas.py:162]
- [x] [Review][Patch] Caixa da `janela` sem teste [tests/test_janelas.py:89]

Rejected: #7 false (`test_agora_utc_aware` e override aware); #8 false (`intervalo` fixa `None` e o repo não aplica limite com `None`); #9 false (GET só lê); #10 false (falha alta, sem ocorrência em `src/`).

## Design Notes

- **Decisão técnica de baixo risco, tomada pelo agente:** `janela` é declarada escalar (`Janela | None`), e a repetição é checada com `request.query_params.getlist("janela")` na dependência `_janela_unica`, em `dependencies=[...]` da rota (passada 2 #1), que roda antes da validação do enum. Assim o OpenAPI publica um enum único (o AD-6 diz "`janela` é um `Janela`"), e valor desconhecido ou vazio dá o 422 nativo do enum. Repetição dá `msg` `informe uma janela só` com `input` igual à lista recebida, no padrão da `tag`.
- **Decisão técnica de baixo risco, tomada pelo agente:** `api.agora` usa `datetime.now(UTC)`. O AGENTS.md proíbe ler o relógio fora de `agora`; dentro dela, a chamada com fuso é a própria leitura permitida. O teste do AC trava isso.
- **Decisão técnica de baixo risco, tomada pelo agente (passada 2 #2):** com mais de um parâmetro inválido, o 422 traz só o primeiro erro (enum da `janela`, repetição da `janela`, depois a `tag`). Juntar todos exigiria trocar a checagem da `tag` da 2.1 por validator de `Query`, que muda `type`/`msg` do 422 já testado. O formato continua `HTTPValidationError` (AD-7) e cada erro sozinho é exato.
- **Decisão técnica de baixo risco, tomada pelo agente:** `agora` é resolvida em toda chamada de `GET /tarefas` (o `Depends` não é condicional), mas só é usada quando há `janela`.

## Implementation Notes

- Arquivos: `domain.py` (`Janela`, `hoje`, `intervalo`), `repo.py` (`listar` com `pendentes`, `de`, `ate`, `tag`), `api.py` (`agora`, query `janela`, `_erro_query` reusado pela `tag`), `tests/conftest.py` (override de `agora` com `yield` e limpeza) e `tests/test_janelas.py` (novo).
- `janela` vem depois de `tag` na assinatura da rota, porque tem default `None` e `tag` não.
- Com os patches da passada 1, `uv run pytest` dá 129 passed, e `ruff check` e `ruff format --check` passam. Com os da passada 2, 131 passed, e os dois `ruff` passam.
- O sprint-status vai para `done` junto com a spec, como nas stories anteriores (o step 5 diria `review`; a sincronização é o action item 6 da retro do épico 1, ainda aberto).

Conferência dos AD contra o diff:
- **AD-1:** `domain` importa só stdlib (`enum`, `datetime`, `zoneinfo`); `repo` importa só `tarefas.domain`; a regra de janela está só em `domain.intervalo`. `test_camadas` passa.
- **AD-2:** `api.agora` devolve `datetime.now(UTC)` e entra na rota por `Depends`; `domain.hoje` converte para `ZoneInfo("America/Sao_Paulo")`. `test_relogio_lido_so_em_api_agora` acha uma leitura só, dentro de `agora`; a fixture sempre faz o override; o caso das 22h usa 01:00 UTC de 10-07.
- **AD-3:** `Janela` é `StrEnum` com os três valores; `intervalo` devolve `(None, hoje-1)`, `(hoje, hoje)` e `(hoje+1, hoje+7)`. O repo aplica `concluida = 0`, `prazo >= de` e `prazo <= ate` sem conhecer nomes de janela.
- **AD-4:** `listar` continua em `_buscar`, com `ORDER BY t.prazo ASC, t.id ASC, g.rowid ASC`; `test_janela_com_tag` põe o id maior com prazo menor.
- **AD-5:** o filtro de tag segue em `nome_norm = norm_tag(tag)` no repo; nenhuma camada nova faz `lower`/`casefold`.
- **AD-6:** `janela` é um `Janela` (valor desconhecido, vazio ou com outra caixa dá 422 nativo); a repetição é checada por `getlist` na dependência `_janela_unica` da rota, em qualquer ordem dos valores. A checagem da `tag` não mudou.
- **AD-7:** `GET /tarefas?janela=&tag=` dá 200 com array sem envelope; os 422 de query saem em lista (`HTTPValidationError`) por `_erro_query`.
- **AD-8:** só leitura, pela conexão de `api.conexao`; nada mudou na escrita.
- **AD-9:** `listar(conn, *, pendentes=False, de=None, ate=None, tag=None)` segue a assinatura completa; a rota passa `pendentes=janela is not None` numa chamada única e o repo devolve `domain.Tarefa`.

## Verification

**Commands:**
- `uv run pytest` -- expected: todos passam
- `uv run ruff check` e `uv run ruff format --check` -- expected: sem achados
