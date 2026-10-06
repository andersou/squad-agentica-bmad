---
title: 'Story 2.3: Documentar as chamadas no README'
type: 'chore'
created: '2026-10-06'
status: 'done'
baseline_commit: '0098325cfc4eef357146944ef5f1c1f7741ee0f0'
route: 'oneshot'
review_loop_iteration: 2
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-06/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** O `README.md` está vazio, então um dev novo não consegue criar uma tarefa com tag e prazo e listar as vencidas sem ler o código (SM-2, NFR-4).

**Approach:** Escrever o `README.md` com: execução (`TAREFAS_DB=/caminho/absoluto/tarefas.db uv run uvicorn tarefas.api:app --host 0.0.0.0 --port 8000`, aviso sobre caminho relativo, aviso de que não há autenticação e de que a API roda só na rede interna); o fluxo do SM-2 em duas chamadas `curl` (criar com tag e prazo passado, listar `?janela=vencidas&tag=`); exemplos de listagem geral, filtro por tag, as três janelas, PATCH para concluir e DELETE, cada um com o código de resposta do AD-7 (201, 200, 204, 404, 422); o `/docs` automático e os comandos `uv run pytest` e `uv run ruff check`. Cada `curl` é conferido contra a API rodando, e nada além de FR-1 a FR-6 é documentado.

</frozen-after-approval>

## Implementation Notes

- Rota `oneshot`: só o `README.md` muda, sem perguntas em aberto nem nada irreversível. Baseline `0098325cfc4eef357146944ef5f1c1f7741ee0f0`.
- **Decisão técnica de baixo risco, tomada pelo agente:** o exemplo do SM-2 usa prazo fixo no passado (`2026-01-15`), para cair em `vencidas` qualquer que seja o dia em que o dev rode. Os exemplos de PATCH e DELETE usam `id` 1, com o aviso de trocar pelo `id` devolvido em outro banco.
- **Decisão técnica de baixo risco, tomada pelo agente:** a conferência dos `curl` é manual, contra a API rodando (a AC da story pede isso), sem teste automático que leia o README. Seria código novo fora do FR-1 a FR-6.
- Conferência contra a API rodando (`TAREFAS_DB=/tmp/tarefas-readme.db uv run uvicorn tarefas.api:app --host 0.0.0.0 --port 8000`, banco novo): extraí todo `curl` do README e o rodei em ordem. Os códigos foram 201, 200 (vencidas com `backend` devolve a tarefa), 200, 200, 200, 200, 200, 422 (`janela=amanha`), 200 (PATCH), 204 e 404, todos iguais aos documentados. As afirmações acrescentadas na revisão também foram conferidas: `2026-02-30` dá 422, tags `Front`/` front ` viram uma só, `null` no PATCH dá 422, `{}` e `tags: []` dão 200, `id` `abc` ou acima de 2⁶³−1 dá 422, corpo inválido em `id` 999 dá 422, `tag` e `janela` repetidas dão 422.
- `uv run pytest` dá 131 passed, e `uv run ruff check` e `uv run ruff format --check` passam.
- O sprint-status vai para `done` junto com a spec, como nas stories anteriores (o passo oneshot diria `review`; a sincronização é o action item 6 da retro do épico 1, ainda aberto).

Conferência dos AD contra o diff (o diff é só documentação; nenhum código mudou):
- **AD-1:** nada mudou em `src/`. O README não descreve regra fora do que `domain` aplica.
- **AD-2:** o README diz que "hoje" é a data em America/Sao_Paulo; o relógio continua lido só em `api.agora`.
- **AD-3:** as três janelas aparecem com os valores do `StrEnum` (`vencidas`, `hoje`, `proximos-7-dias`), os limites corretos e só pendentes.
- **AD-4:** o README diz "ordem de prazo e depois de `id`".
- **AD-5:** o filtro aparece sem diferenciar maiúsculas nem espaços, e as tags duplicadas por caixa viram uma só, com a grafia da primeira.
- **AD-6:** limites de `titulo` (1 a 200), `prazo` `YYYY-MM-DD` válido, tag até 50, `concluida` no POST dá 422, `null` no PATCH dá 422, `{}` dá 200, `tags: []` limpa, uma `tag` e uma `janela` por chamada, 422 antes de 404.
- **AD-7:** rotas e códigos da tabela (201, 200, 204, 404) e o formato `{"detail": ...}`; sem autenticação, só rede interna.
- **AD-8:** o comando de execução usa `TAREFAS_DB` com caminho absoluto e avisa sobre o relativo e o padrão `tarefas.db`.
- **AD-9:** o JSON da tarefa documentado é `{"id", "titulo", "prazo", "tags", "concluida"}`, e as listagens são array sem envelope.

## Review Triage Log

Passada 1 (blind-hunter; os outros layers não existem na rota oneshot).

| # | Achado | Veredito | Evidência | Rota |
|---|---|---|---|---|
| 1 | A spec termina com marcação de ferramenta solta (`</content>`, `</invoke>`) | low | Real: sobra da geração do arquivo | patch |
| 2 | A spec é só um esqueleto e não registra a conferência dos `curl` | low | A rota oneshot só tem Intent e Implementation Notes, por desenho. Mas as Implementation Notes estavam vazias e a AC "conferido contra a API rodando" não tinha registro | patch |
| 3 | "Tag repetida" é ambíguo com tags duplicadas no corpo (que não dão 422) | low | Real: no corpo, `["a","A"]` dá 201 com uma tag só | patch |
| 4 | Faltam regras do PATCH: `null` dá 422, `tags: []` limpa, `{}` não muda nada | low | Real, conferido na API | patch |
| 5 | A tabela não traz o 422 de `id` inválido nem a precedência 422 antes de 404 | low | Real: `/tarefas/abc` e `id` acima de 2⁶³−1 dão 422; corpo inválido em `id` 999 dá 422 (AD-6) | patch |
| 6 | Faltam limites do corpo: `titulo` 1 a 200, tag até 50 no corpo, data impossível dá 422 | low | Real: `2026-02-30` dá 422 | patch |
| 7 | Sem pré-requisitos (uv, Python 3.14) | low | Real: versões no spine e no `pyproject.toml` | patch |
| 8 | Janelas sem resultado esperado; DELETE não mostra nada sem `-i` | low | Real: `hoje` e `proximos-7-dias` devolvem `[]` no exemplo | patch |
| 9 | O README não diz que a tarefa volta com a grafia gravada da tag | low | Real: `?tag=Backend` devolve `"backend"` | patch |

Passada 2 (`bmad-code-review` sobre `0098325..0618305`: blind-hunter, edge-case-hunter, verification-gap, acceptance-auditor). O verification-gap não achou lacuna. Todos os patches foram aplicados no `README.md`.

| # | Achado | Fonte | Veredito | Evidência | Rota |
|---|---|---|---|---|---|
| 1 | Tag vazia ou só com espaços no corpo dá 422, e o README não dizia | blind+edge+auditor | low | Real: `"tags": [" "]` e `[""]` dão 422 `tag vazia` (`domain.normalizar_tags`) | patch, aplicado |
| 2 | O README não dizia que `titulo` e tags perdem os espaços nas pontas antes do limite, nem que a deduplicação de tags também ignora esses espaços | blind+auditor | low | Real: `"  ok  "` grava `ok`, título só com espaços dá 422, `[" Front ","front","FRONT"]` grava `["Front"]`, e uma tag de 50 caracteres com espaços nas pontas dá 201 | patch, aplicado |
| 3 | O README não dizia que campo desconhecido dá 422 no POST e no PATCH | blind | low | Real: `extra="forbid"`; `descricao` no POST e `concluído` no PATCH dão 422 | patch, aplicado |
| 4 | O README não dizia que `concluida` é booleano JSON estrito | blind | low | Real: `StrictBool`; `"true"` e `1` dão 422 | patch, aplicado |
| 5 | O README não descrevia o formato de `detail` (texto no 404, lista no 422) | blind | low | Real: o 404 devolve `{"detail":"tarefa não encontrada"}` e o 422 devolve uma lista com `loc`, `msg` e `input` | patch, aplicado |
| 6 | O README não explicava que `--host 0.0.0.0` escuta em todas as interfaces | blind+edge | low | Real. O comando da Intent fica como está, e o README só ganhou a nota de usar `127.0.0.1` quando a API rodar só na máquina (NFR-2) | patch, aplicado |
| 7 | O comentário dizia que janela "repetida" dá 422, mas o curl mostrava só a janela desconhecida | blind | low | Real: o curl `?janela=hoje&janela=vencidas` foi acrescentado e dá 422 `informe uma janela só` | patch, aplicado |

**Decisões técnicas de baixo risco, tomadas pelo agente:** a nota sobre o `0.0.0.0` complementa o comando congelado na Intent sem trocá-lo. A janela repetida ganhou um curl próprio, em vez de sumir do comentário. Nenhum achado pediu decisão de escopo ou de produto.

Conferência contra a API rodando (banco novo em `/tmp`): os 11 `curl` do README, rodados em ordem, deram 201, 200, 200, 200, 200, 200, 200, 422, 422, 200, 204 e, ao repetir o DELETE, 404, todos iguais aos documentados. As afirmações novas também foram conferidas (as evidências estão na tabela). `uv run pytest` dá 131 passed, e `uv run ruff check` e `uv run ruff format --check` passam.

Conferência dos AD contra o diff da passada 2 (só o README mudou): o **AD-5** cobre as tags aparadas e deduplicadas por `norm_tag`; o **AD-6** cobre o strip antes dos limites, a tag vazia, `extra="forbid"` e o `StrictBool`; o **AD-7** cobre o formato de `detail` e o NFR-2 da rede interna. Os outros AD (1 a 4, 8 e 9) não mudam, e a conferência da passada 1 continua valendo.

Rejeitados na passada 2:
- Exemplo de PATCH com 404 e de POST com 422 (blind): low e dispensável. Os códigos 404 e 422 já têm exemplo executável, e a tabela cobre PATCH.
- `epic-2` continua `in-progress` no sprint-status (blind): não vem desta story. O `epic-1` está igual, o fechamento do épico fica com a retrospectiva, e a sincronização é o action item 6, ainda aberto.
- Triage Log sem coluna de resultado e AC sem conferência item a item (blind): a correção seria editar a spec revisada (regra da triagem). Mesmo assim, esta tabela já registra o resultado de cada achado.
- "Só o `README.md` muda", mas o diff também mexe na spec e no sprint-status (auditor): a correção seria editar a spec revisada, e a nota seguinte da própria spec já explica o sprint-status.
- O `id` 1 pode não existir num banco reaproveitado (edge): false. O README já diz "com `id` 1 num banco novo" e manda trocar pelo `id` devolvido em outro banco.
- Falta a linha 405 na tabela (edge): low e fora do contrato. Rota não definida é comportamento do framework, não um código do AD-7.

