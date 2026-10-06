---
title: "Revisão: reconciliação PRD × Architecture Spine"
created: 2026-10-02
sources:
  - _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/prd.md
  - _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/ARCHITECTURE-SPINE.md
---

# Revisão: reconciliação PRD × Architecture Spine

Objetivo: achar requisitos ou restrições do PRD (FRs, NFRs, glossário, escopo, pistas do addendum, métricas) que o spine não cobre, contradiz ou deixa ambíguos a ponto de duas stories divergirem.

Resultado geral: o spine cobre todos os FRs e NFRs no `binds` e no mapa de capacidades. Não há contradição direta com o PRD. As lacunas estão em pontos de borda que o PRD torna testáveis e que o spine deixa em aberto. Abaixo, em ordem de severidade.

## Alta

### G-1. O envelope de erro (AD-7) não cobre todos os caminhos de erro do NFR-3

- **PRD:** NFR-3 exige que *toda* resposta 404/422 tenha o mesmo formato e diga qual campo ou parâmetro causou o erro.
- **Spine:** AD-7 só fala de `RequestValidationError` → 422 e `HTTPException` → 404.
- **Lacunas:**
  1. **422 vindos do `domain`, não do Pydantic.** A tag vazia depois de `normalize_tag()` (AD-4, FR-5) e, se for o caso, o título só com espaços (G-3) são detectados fora do schema. O spine não diz que exceção levantar nem como ela vira `code`/`field`. Uma story vai usar `HTTPException(422)` (e cair num handler que só conhece `not_found`), outra vai criar uma exceção de domínio, outra vai usar um validador Pydantic.
  2. **404 de rota inexistente e 405.** Esses erros são levantados como `starlette.exceptions.HTTPException`, não como a `fastapi.HTTPException`. Um handler registrado na classe do FastAPI deixa `{"detail": "Not Found"}` passar. O spine não diz em que classe registrar nem o `code` de 405 (e de outros status, como 400).
  3. **Derivação de `field`.** O `loc` do Pydantic vem como `["body", "tags", 2]`, `["query", "due"]` ou `["path", "id"]`. O spine não diz se `field` vira `tags`, `tags[2]` ou `body.tags`, nem qual erro reportar quando há vários. Os testes de stories diferentes vão fixar valores diferentes.
  4. **Mensagens em português** (Convenções) contra as mensagens padrão do Pydantic, que vêm em inglês. O spine não diz se o handler traduz, usa uma mensagem fixa por `code` ou repassa `msg`.
  5. **JSON malformado** no corpo vira 422 `json_invalid` sem campo. O `field` é `null`? Não está dito.
- **Sugestão:** acrescentar ao AD-7 uma exceção de domínio (`ValidationFailed(field, message)`), o registro em `starlette.exceptions.HTTPException`, a regra `field = último elemento string do loc do primeiro erro` (ou equivalente) e a política de mensagem (fixa em português por tipo de erro).

### G-2. "`due_date` só aceita `YYYY-MM-DD`" não diz como validar

- **PRD:** FR-1/FR-3, prazo fora do formato ISO 8601 → 422. O addendum fixa `YYYY-MM-DD`.
- **Spine:** AD-6 diz "`due_date` só aceita `YYYY-MM-DD`", sem mecanismo.
- **Divergência provável:** com o tipo `date` do Pydantic v2 em modo lax, entram também inteiros (timestamp Unix), `"2026-10-02T00:00:00"` e similares. Com `str` + regex, entra `2026-02-30`. Os dois caminhos violam a regra de jeitos diferentes, e o AD-5 depende de o texto gravado estar sempre canônico para a ordenação funcionar.
- **Sugestão:** fixar no AD-6: `date` em modo estrito, recebido como string e validado com `date.fromisoformat` + checagem de comprimento/regex `^\d{4}-\d{2}-\d{2}$`, e gravado com `isoformat()`.

### G-3. A testabilidade da virada do dia (NFR-2) depende de uma assinatura de `today()` que o spine não define

- **PRD:** NFR-2 exige testar a virada do dia em `America/Sao_Paulo` com o servidor em outro fuso, como UTC.
- **Spine:** AD-2 injeta o relógio via `dependency_overrides`. AD-8 pede um caso em que "a data UTC já virou e a de São Paulo ainda não".
- **Problema:** se o teste substitui o relógio inteiro por uma data fixa, o código real de `today()` (o `ZoneInfo`) nunca roda, e o caso da virada não testa nada. Para ser significativo, `today()` precisa aceitar o instante atual injetável (por exemplo, `today(now: datetime | None = None)` ou um `Callable[[], datetime]`), e o teste precisa passar um instante UTC como `2026-10-03T01:30Z` e esperar `2026-10-02`. O spine também não diz se os testes forçam `TZ=UTC` no processo.
- **Sugestão:** definir no AD-2 a assinatura de `today()` com o instante injetável e no AD-8 o teste unitário de `today()` com instante UTC, além do teste HTTP com o relógio fixado.

### G-4. Ciclo de vida da conexão `sqlite3` e commit (NFR-4) não definidos

- **PRD:** NFR-4, as tarefas sobrevivem ao reinício.
- **Spine:** AD-5 exige `PRAGMA foreign_keys = ON` "em toda conexão", mas não diz quando as conexões são abertas.
- **Divergência provável:** conexão global vs. uma por requisição (dependência com `yield`); rotas `def` (threadpool, esbarram em `check_same_thread`) vs. `async def`; commit explícito vs. `with conn:` vs. `autocommit=True` (Python 3.12+). Esquecer o commit no modo legado do `sqlite3` perde dados sem erro, ferindo o NFR-4. A criação da tarefa e das linhas em `task_tags` precisa ser atômica, e o spine também não diz isso.
- **Sugestão:** acrescentar um AD curto: uma conexão por requisição via dependência do FastAPI, rotas `def`, transação por operação com `with conn:`, `PRAGMA foreign_keys = ON` na abertura.

## Média

### G-5. Título "não pode ser vazio": e só com espaços?

- **PRD:** Glossário e FR-1, título obrigatório e não vazio. Para tags, o PRD diz explicitamente que "só com espaços" é vazia. Para título, não diz.
- **Spine:** silencioso. Uma story usa `min_length=1` (aceita `"   "`), outra faz `strip()` e rejeita. Também não diz se o título é gravado com `strip()`.
- **Sugestão:** decidir no AD-6 (recomendação: `strip()` e 422 se o resultado for vazio, igual à tag).

### G-6. Lacunas no contrato de `tags` e `done`

- **`tags: null` no `PATCH`:** AD-6 lista `null` → 422 para `title`, `due_date` e `done`, mas omite `tags`. `null` limpa as tags, mantém as tags ou dá 422?
- **`tags` omitido no `POST`:** presumivelmente `[]`, mas não está escrito.
- **Ordem das tags na resposta:** não definida (ordem de envio, ordem alfabética, ordem do SQLite). Os testes de igualdade de lista vão divergir.
- **Duplicatas no mesmo payload** (`["Backend", "backend"]`): a PK de `task_tags` deduplica, mas um `INSERT` simples estoura `IntegrityError` (500). O spine não diz se a deduplicação acontece no `domain` ou via `INSERT OR IGNORE`.
- **Forma da tag devolvida:** o cliente envia `Backend` e recebe `backend` (casefold). É compatível com o PRD, mas vale explicitar para que nenhuma story tente preservar a grafia original.
- **`done` no `POST`:** o PRD diz que a tarefa nasce não concluída. O spine não diz se `done: true` no `POST` é ignorado, rejeitado ou aceito. Também não diz se campos desconhecidos no corpo são ignorados ou dão 422 (`extra="forbid"`).
- **`PATCH` com corpo vazio `{}`:** 200 sem mudança ou 422? Não está dito.

### G-7. Parâmetros de consulta nas bordas

- `?tag=` vazio ou só com espaços: AD-4 diz "tag vazia depois da normalização → 422" e diz que a normalização vale para `?tag=`, mas não fica claro se a regra do 422 também vale para o parâmetro (pode ser lido como "sem filtro").
- `?tag=a&tag=b` (várias tags): o PRD fala de "uma tag específica"; o spine não diz se vale a última, a primeira ou se é 422.
- `GET /tasks/abc`: o FastAPI devolve 422 (`field: "id"`), enquanto o FR-2 fala de 404 para identificador inexistente. Isso é aceitável, mas precisa estar escrito para os testes de 404 não divergirem.

## Baixa

### G-8. NFR-5 (rede interna) delegado ao deploy sem uma regra concreta

O spine diz "um único processo `fastapi run` em uma máquina da rede interna", mas `fastapi run` escuta em `0.0.0.0` por padrão. Não há regra de `--host` nem menção a firewall. Como a v1 não tem autenticação, convém fixar o bind (por exemplo, o IP da interface interna) ou documentar no README que a exposição fica a cargo da rede.

### G-9. Dependência implícita do banco de fusos

`ZoneInfo("America/Sao_Paulo")` depende do tzdata do sistema. Em Windows ou em imagens mínimas, ele falta, e o AD-1 proíbe dependências além de `fastapi[standard]`. Isso é aceitável enquanto o deploy for uma máquina Linux/macOS, mas vale registrar como `[ASSUMPTION]` ou permitir `tzdata` no AD-1.

### G-10. Questão em aberto §8 (importação da planilha) não ecoa no spine

O PRD pede para rever a questão antes de quebrar os épicos. O spine não a menciona. O FR-1 (prazo passado aceito) e o `POST /tasks` já viabilizam um script descartável, então basta uma linha em *Deferred* dizendo que a importação, se houver, usa a API pública e não toca o SQLite direto.

## Itens verificados sem lacuna

- Janelas de prazo (glossário, FR-7) → AD-3 com uma definição única, `done = 0` e limites calculados no `domain`.
- Normalização de tag (glossário, FR-5, FR-6) → AD-4.
- Ordenação por prazo (FR-2) → AD-6, com desempate por `id`, o que reforça o PRD.
- Conclusão por edição (FR-3, alternativa descartada no addendum) → `PATCH` com `done`, sem endpoint próprio.
- Sem paginação, sem auth, fuso fixo, sem `X-Timezone` (§6.2, addendum) → *Deferred* e AD-2.
- Pistas de contrato do addendum (`/tasks`, `title`, `due_date`, `tags`, `done`, `?tag=&due=overdue|today|next7`, formato de erro) → adotadas no AD-6 e no AD-7.
- NFR-1 / SM-2 → README com `curl`.
- SM-1 / NFR-2 (limites ontem, hoje, amanhã, +7, +8) → AD-8, com a ressalva do G-3.
- SM-4 → `uv run pytest` antes de cada commit de story.
- SM-C1 → o spine não adiciona endpoints além dos cinco necessários.
