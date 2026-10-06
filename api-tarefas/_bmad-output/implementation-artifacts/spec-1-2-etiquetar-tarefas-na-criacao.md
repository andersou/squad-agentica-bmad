---
title: 'Story 1.2: Etiquetar tarefas na criação'
type: 'feature'
created: '2026-10-06'
status: 'done'
baseline_commit: 'f1aa30cba6217933696d42843fe4599799242d63'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-06/ARCHITECTURE-SPINE.md'
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** O `POST /tarefas` ainda rejeita `tags`, e o dev não consegue marcar o assunto de cada tarefa (por exemplo `backend`) ao recadastrá-la da planilha (FR-1, FR-5).

**Approach:** Aceitar `tags` opcional no POST, normalizado só por `domain.normalizar_tags` (AD-5), gravado na nova tabela `tarefa_tag` na mesma transação da tarefa (AD-8) e devolvido pela listagem geral na ordem de inserção.

## Boundaries & Constraints

**Always:** seguir AD-1 a AD-9 do spine e o AGENTS.md. `norm_tag(s)` = `s.strip().casefold()`. `normalizar_tags` apara, levanta `ValueError` para tag vazia e remove duplicadas por `norm_tag`, mantendo grafia e posição da primeira ocorrência. Cada tag tem no máximo 50 caracteres depois do strip. O repo grava `nome_norm` com `norm_tag` e devolve as tags em `ORDER BY rowid`. `tarefa_tag` tem `UNIQUE(tarefa_id, nome_norm)` e FK `ON DELETE CASCADE`.

**Never:** `lower`/`casefold` fora de `domain.py`; SQL de `tarefa_tag` fora de `repo.py`; filtro `?tag=` (Épico 2); `PATCH`/`DELETE` (1.3 e 1.4); cadastro de tags; migrações; outro `TestClient`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Normalizar | `"tags": ["Backend", " api ", "backend"]` | 201 com `"tags": ["Backend", "api"]`; `GET /tarefas` devolve o mesmo | N/A |
| Sem tags | corpo sem `tags`, ou `"tags": []` | 201 com `"tags": []` | N/A |
| Limite | tag com 50 caracteres depois do strip | 201, tag gravada aparada | N/A |
| Tags inválidas | tag `""` ou `"   "`; tag com 51 caracteres depois do strip; `"tags": "backend"`, `[1]`, `[null]` ou `null` | 422 `{"detail": ...}` | nada é gravado |
| Atomicidade | `repo.criar` chamado direto com tags que colidem em `nome_norm` | `sqlite3.IntegrityError` | a tarefa também não é gravada |

</frozen-after-approval>

## Code Map

- `src/tarefas/domain.py` -- só a dataclass `Tarefa`. Acrescentar `norm_tag` e `normalizar_tags`, sem imports novos.
- `src/tarefas/repo.py` -- `criar_schema` cria só `tarefa`; `criar` levanta `NotImplementedError` com tags (remover); `listar` devolve `tags=[]` fixo. Manter `listar(conn)` sem filtros e o `ORDER BY prazo ASC, id ASC`.
- `src/tarefas/api.py` -- `TarefaCriar` (`extra="forbid"`, `Titulo`, `Prazo`); a rota passa `[]` ao repo. Reusar o padrão `Annotated` + `StringConstraints` do `Titulo`.
- `tests/test_tarefas.py` -- `test_criar_com_tags_falha_ate_story_1_2` deixa de valer (remover). `test_camadas` e `_imports` ficam.

## Tasks & Acceptance

**Execution:**
- [x] `src/tarefas/domain.py` -- `norm_tag(s)` e `normalizar_tags(lista)` conforme AD-5 -- regra de tag só no domain
- [x] `src/tarefas/repo.py` -- `criar_schema` cria também `tarefa_tag(tarefa_id INTEGER NOT NULL REFERENCES tarefa(id) ON DELETE CASCADE, nome TEXT NOT NULL, nome_norm TEXT NOT NULL, UNIQUE(tarefa_id, nome_norm))`; `criar` insere tarefa e tags (`nome_norm` = `norm_tag(nome)`) no mesmo `with conn:`; `listar` preenche `tags` com uma consulta `ORDER BY rowid` agrupada por `tarefa_id` -- AD-5, AD-8, AD-9
- [x] `src/tarefas/api.py` -- `tags: Tags = []` em `TarefaCriar`, com `Tags = Annotated[list[Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)]], AfterValidator(normalizar_tags)]`; a rota repassa `dados.tags` -- AD-5, AD-6
- [x] `tests/test_tarefas.py` -- um teste por linha da I/O Matrix (inválidos parametrizados, com GET vazio); `test_persistencia` passa a criar com tags e conferir `repo.listar`; `test_camadas` passa a falhar se `api.py` ou `repo.py` contiverem `lower(` ou `casefold`; remover o teste do `NotImplementedError` -- cobre matriz e AD-5

**Acceptance Criteria:**
- Given o código da story, when rodo `uv run pytest`, `uv run ruff check` e `uv run ruff format --check`, then os três passam.
- Given um `TAREFAS_DB` da 1.1 já existente, when a API sobe e cria uma tarefa com tags, then `tarefa_tag` é criada por `CREATE TABLE IF NOT EXISTS` e as tarefas antigas voltam com `"tags": []`.

## Implementation Notes

- **Decisão técnica de baixo risco, tomada pelo agente na revisão (achado 5):** `listar` passou a usar uma consulta só, com `LEFT JOIN tarefa_tag ... ORDER BY t.prazo, t.id, g.rowid`, no lugar das duas consultas do Design Notes. Uma instrução só lê um snapshot consistente, o que protege a listagem quando o DELETE (1.3) e o PATCH (1.4) chegarem. Os filtros do Épico 2 entram no `WHERE` da mesma consulta.
- Testes novos da revisão: casefold (`Straße`/`STRASSE`), tags com várias tarefas e banco da 1.1 ganhando `tarefa_tag` (AC 2).

## Spec Change Log

## Review Triage Log

Passada 1 (blind-hunter, edge-case-hunter, verification-gap):

| # | Achado | Veredito | Evidência | Rota |
|---|---|---|---|---|
| 1 | `test_camadas` é case-sensitive e deixa passar `LOWER(`, `UPPER(` e `COLLATE NOCASE` no SQL | low | Real: a guarda do AD-5 olha só `lower(` minúsculo. A correção é direta | patch |
| 2 | Nenhum teste prende `casefold` contra `lower` (VG) | medium | Com `lower`, `["Straße", "STRASSE"]` vira duas tags e todos os testes passam | patch |
| 3 | Nenhum teste confere tags com várias tarefas na listagem (VG) | medium | Todos os testes de tag criam uma tarefa só, e um agrupamento errado passaria | patch |
| 4 | O AC 2 (banco da 1.1) não tem teste (VG) | medium | Todo teste parte de banco vazio. Só a checagem manual cobria | patch |
| 5 | `listar` faz duas leituras sem snapshot comum | low | Hoje só a criação concorre, e o comentário trata esse caso. Com o DELETE da 1.3 e o PATCH da 1.4, uma tarefa sairia com tags de outro momento. Uma consulta só com `LEFT JOIN` resolve sem acrescentar guarda | patch |
| 6 | `listar` lê todas as tags da tabela, inclusive de tarefas filtradas no Épico 2 | false | `listar` não tem filtro nesta story, e toda tag lida é usada. O achado 5 troca a consulta por um `JOIN`, que herda os filtros futuros | — |
| 7 | Sem limite de quantidade de tags por tarefa (blind + edge) | low | Real, mas a API é interna, sem cliente hostil no uso normal, e o PRD e o AD-6 não definem limite. A correção acrescenta regra de produto. Rejeitado, como o #14 da 1.1 | — |
| 8 | `normalizar_tags` calcula `norm_tag` duas vezes | low | Real e cosmético. A correção é uma variável local | patch |
| 9 | O teste de atomicidade cria o schema por efeito colateral do `GET` | low | Real: depende da dependência HTTP. A correção é chamar `repo.criar_schema(conn)` | patch |
| 10 | Implementation Notes e Spec Change Log vazios | — | A correção edita a spec desta build. Rejeitado pela regra da triagem | — |
| 11 | Mesma tag em NFC e NFD fica duplicada | low | Real, mas raro (o mesmo cliente manda a mesma forma), e a correção muda o `norm_tag` fixado no AD-5. Rejeitado | — |
| 12 | Tag só com caracteres invisíveis (`U+200B`) é aceita | low | Fora da regra do PRD ("vazia ou só com espaços"), e a correção acrescenta validador. Rejeitado, como o #16 da 1.1 | — |

Patches 1–5, 8 e 9 aplicados: `uv run pytest` dá 33 passed (o único warning é a depreciação do `httpx`, mantido por regra do AGENTS.md), e `ruff check` e `ruff format --check` passam.

Conferência dos AD contra o diff:
- **AD-1:** `domain` não ganhou imports. `repo` importa `tarefas.domain` e não importa `api`.
- **AD-2:** nenhuma leitura de relógio.
- **AD-3:** não se aplica, porque não há janela.
- **AD-4:** `ORDER BY t.prazo ASC, t.id ASC`, e o teste de desempate com o índice `(prazo, id DESC)` continua passando.
- **AD-5:** `norm_tag`/`normalizar_tags` só no `domain`, e o schema chama `normalizar_tags` num `AfterValidator`. O repo grava `nome_norm` com `norm_tag`, as tags voltam por `g.rowid`, e o `test_camadas` barra `lower(`/`upper(`/`casefold`/`nocase` na api e no repo.
- **AD-6:** `extra="forbid"` mantido. Cada tag tem no máximo 50 caracteres depois do strip, e `tags` que não seja lista de strings dá 422.
- **AD-7:** o POST continua 201, e o GET continua 200 com array. Os erros vêm em `{"detail"}`.
- **AD-8:** a tarefa e as tags são gravadas no mesmo `with conn:` (teste de atomicidade), e o schema é criado na dependência com `IF NOT EXISTS`.
- **AD-9:** o repo devolve só `Tarefa`, o SQL de `tarefa_tag` fica só no `repo`, e `criar(conn, titulo, prazo, tags)` mantém a assinatura.

## Design Notes

- O `strip_whitespace` do `StringConstraints` existe só para o limite de 50 valer depois do strip (AD-6). Não é normalização de caixa, e `normalizar_tags` aparar de novo é inofensivo. Decisão técnica de baixo risco, tomada pelo agente.
- O repo confia que as tags chegam normalizadas. Se não chegarem, o `UNIQUE` derruba a transação inteira (linha Atomicidade), e nada fica pela metade.
- `listar` busca as tags numa segunda consulta (`SELECT tarefa_id, nome FROM tarefa_tag ORDER BY rowid`) e agrupa num dict. Sem paginação, isso evita N+1 sem complicar o SQL principal.

## Verification

**Commands:**
- `uv run pytest` -- expected: todos passam
- `uv run ruff check` e `uv run ruff format --check` -- expected: sem achados

**Manual checks:**
- `TAREFAS_DB=/tmp/t12.db uv run uvicorn tarefas.api:app`, `curl` POST com `["Backend", " api ", "backend"]` e GET devolve `["Backend", "api"]`.
