---
title: 'Revisão adversarial — Architecture Spine da API de Tarefas'
target: ../ARCHITECTURE-SPINE.md
context: ../../../prds/prd-api-tarefas-2026-10-02/prd.md
date: '2026-10-02'
method: 'pares de stories que obedecem a todos os ADs ao pé da letra e ainda assim saem incompatíveis'
---

# Revisão adversarial — Architecture Spine da API de Tarefas

## Veredito

**Não está pronta para quebrar em stories. Precisa de uma rodada de aperto.** O paradigma, a stack e as decisões de domínio (relógio único, janelas, normalização) estão certos e cortam as divergências óbvias. O problema está nas **costuras entre os épicos**. A spine diz *o que* existe, mas deixa sem dono e sem forma justamente o que duas stories compartilham: o tipo de cada campo da tarefa, o caminho de leitura e escrita das tags, a semântica dos limites das janelas, a derivação do `field` no erro, quem cria o esquema e quando a conexão abre, e o contrato das fixtures de teste. Encontrei 9 pares de stories que obedecem a todos os ADs e quebram uma à outra. Cinco deles são de severidade alta, e um (H1) torna o teste exigido pelo próprio AD-8 impossível de escrever do jeito que o AD-2 manda.

Stories consideradas: **1.1** criar + listar/consultar (FR-1, FR-2), **1.2** editar, incluindo `done` (FR-3), **1.3** excluir (FR-4), **2.x** tags e janelas (FR-5 a FR-8). Quando o Épico 2 precisar de mais de uma story, uso **2.1** para tags (FR-5, FR-6) e **2.2** para janelas (FR-7, FR-8).

## Resumo

| # | Buraco | Pares | Severidade |
| --- | --- | --- | --- |
| H1 | Sobrescrever o relógio apaga o teste da virada UTC × São Paulo | 1.1 × 2.2 (AD-2 × AD-8) | Alta |
| H2 | Tags sem dono: dois caminhos de leitura, lista parcial no filtro e 500 em duplicata | 1.1 × 2.1, 1.2 × 2.1, 2.1 × 2.2 | Alta |
| H3 | Limites da janela sem semântica (aberto ou fechado) | 2.2 (domain) × 2.2 (repo) | Alta |
| H4 | Envelope de erro: `field` sem regra de derivação e handlers que deixam rotas de fora | 1.1 × 1.3, 1.1 × 2.1, 2.2 × qualquer | Alta |
| H5 | Esquema e conexão sem dono: lifespan × TestClient, env lido no import, thread | 1.1 × 2.1, 1.1 × 1.2 | Alta |
| H6 | Forma da tarefa sem tipos (`done` int ou bool, `due_date` permissivo, título só com espaços) | 1.1 × 1.2 | Média |
| H7 | `tags: null` e `?tag=` repetido no PATCH e no GET sem regra | 1.2 × 2.1 | Média |
| H8 | Escrita do PATCH em duas etapas sem transação definida | 1.2 × 2.1 | Média |
| H9 | Contrato das fixtures (`conftest.py`) sem forma | 1.1 × 2.2 | Média |

---

## H1 — Sobrescrever o relógio apaga o teste da virada UTC × São Paulo (Alta)

**Unidades:** 1.1 (escreve o `conftest.py` e o relógio fixado) × 2.2 (escreve os testes das janelas).

**Como cada uma obedece:**
- A 1.1 segue o AD-2 ao pé da letra: `domain.today()` sem argumentos, com `ZoneInfo("America/Sao_Paulo")`. A rota declara `today: date = Depends(domain.today)`, e o `conftest` faz `app.dependency_overrides[domain.today] = lambda: date(2026, 10, 2)`.
- A 2.2 segue o AD-8: precisa de "um caso em que a data UTC já virou e a de São Paulo ainda não".

**O choque:** com o override do AD-2, a função que converte o fuso **nunca roda nos testes**. O override devolve uma `date` pronta, e o caso exigido pelo AD-8 vira tautologia (o teste injeta a data de São Paulo e confere que ela é a data de São Paulo). A 2.2 então tem duas saídas, e as duas violam algum AD: chamar `datetime.now()` com `freezegun` (dependência nova, AD-1, e chamada de relógio fora do `domain`, AD-2) ou testar `domain.today()` direto, sem `TestClient` (contra o "testes contra o app real" do AD-8). Se outra story escolher a outra saída, ficam dois mecanismos de relógio nos testes.

**Correção proposta (reescrever o AD-2):**
> O único ponto que lê o relógio do sistema é `domain.now() -> datetime`, que devolve `datetime.now(UTC)`. A conversão é pura: `domain.today(now: datetime) -> date` faz `now.astimezone(ZoneInfo("America/Sao_Paulo")).date()`. A `api` injeta `now` por `Depends(domain.now)` e chama `domain.today(now)`. Os testes sobrescrevem **apenas** `domain.now`, com um instante UTC *aware* (por exemplo, `2026-10-03T01:30Z`, que em São Paulo ainda é 02/10). É proibido sobrescrever `today`.

## H2 — Tags sem dono: dois caminhos de leitura, lista parcial no filtro e 500 em duplicata (Alta)

O AD-6 obriga a tarefa a ter `tags` **desde a 1.1**, mas o FR-5 é do Épico 2. A spine não diz quem é dono de quê.

**Par A — 1.1 × 2.1 (dois donos da leitura):**
- A 1.1 obedece ao AD-6 devolvendo `"tags": []` fixo, com `SELECT * FROM tasks` e um mapeamento linha → dict na rota. Ou então implementa tags por inteiro, já que o ERD tem `task_tags` e a forma exige o campo, e invade a 2.1.
- A 2.1 precisa reescrever o caminho de leitura de todas as rotas (`GET`, `GET /{id}`, `POST`, `PATCH`). No primeiro caso, a 2.1 mexe em código da 1.1 e da 1.2. No segundo, há dois donos do FR-5.

**Par B — 2.1 × 2.2 (filtro devolve tags parciais):**
- A 2.1 implementa `?tag=` com `JOIN task_tags ... WHERE tag = ?` e monta `tags` com `GROUP_CONCAT(tag)` na mesma consulta. Isso obedece ao AD-4 e ao AD-5.
- Resultado: `GET /tasks?tag=backend` devolve a tarefa com `"tags": ["backend"]`, embora ela também tenha `api`. A 2.2 carrega as tags numa segunda consulta e devolve a lista completa. A mesma tarefa sai com duas formas, dependendo do filtro.

**Par C — 1.2/2.1 × 2.1 (duplicata vira 500):**
- O AD-5 diz que a chave `(task_id, tag)` "deduplica". A 2.1 confia nisso e faz `INSERT INTO task_tags` para cada tag de `["Backend", "backend "]`. Depois da normalização, as duas viram `backend`, e o segundo `INSERT` levanta `IntegrityError` → **500 sem envelope**. Outra story usa `INSERT OR IGNORE` ou deduplica no `domain`. Comportamentos diferentes para a mesma entrada.

**Par D — ordem das tags:** nenhum AD define a ordem de `tags` na resposta. Um teste da 2.1 compara `["backend", "api"]` (ordem de inserção). Um `SELECT` pela chave primária devolve `["api", "backend"]`. Os testes ficam instáveis entre stories.

**Correção proposta (novo AD-9, "Tags: dono e forma"):**
> - `domain.normalize_tags(list[str]) -> list[str]` normaliza cada tag (AD-4), rejeita vazias e devolve a lista **sem repetições e em ordem alfabética**. A resposta sempre traz `tags` nessa ordem.
> - O `repo` tem **uma** função de leitura, `_with_tags(conn, rows)`, que carrega as tags de todos os ids numa só consulta (`WHERE task_id IN (...)`). Todas as rotas passam por ela.
> - O filtro por tag é feito com `EXISTS (SELECT 1 FROM task_tags WHERE task_id = tasks.id AND tag = ?)`. É proibido montar `tags` a partir do `JOIN` do filtro.
> - A escrita de tags é `repo.replace_tags(conn, task_id, tags)`: um `DELETE` seguido de `INSERT`s, sobre uma lista já sem repetições.
> - Dono: a 1.1 cria o esquema completo (ver H5) e a função de leitura, que devolve `[]` enquanto não houver tags. A 2.1 é a única story que aceita `tags` na entrada e chama `replace_tags`.

## H3 — Limites da janela sem semântica (Alta)

**Unidades:** quem escreve a função de janelas no `domain` × quem escreve o SQL no `repo`. Podem ser a mesma story, mas o objetivo da spine é que não dependa de serem.

**Como cada uma obedece:** o AD-3 diz só que a função "devolve os limites de `due_date`" e que o `repo` "filtra no SQL usando esses limites".
- O `domain` devolve intervalos semiabertos `[início, fim)`: `today → (hoje, amanhã)`, `next7 → (amanhã, hoje+8)`, `overdue → (None, hoje)`.
- O `repo` usa `due_date BETWEEN ? AND ?` (fechado).

**O choque:** `today` passa a incluir amanhã, `next7` inclui hoje + 8 e `overdue` inclui hoje. As janelas se sobrepõem, contra o Glossário do PRD. Os testes de limite do AD-8 pegam o erro, mas só depois que as duas metades já foram escritas, e cada lado vai dizer que seguiu o AD-3.

Um problema menor no mesmo ponto: se o `repo` receber objetos `date` como parâmetro, o `sqlite3` usa o adaptador padrão de `date`, que está *deprecated* desde o Python 3.12. Com `filterwarnings = error` no pytest, isso quebra numa story e não na outra.

**Correção proposta (apertar o AD-3):**
> `domain.window_bounds(window, today) -> tuple[str | None, str | None]` devolve um intervalo **fechado nos dois lados**, em texto `YYYY-MM-DD`: `overdue = (None, hoje-1)`, `today = (hoje, hoje)`, `next7 = (hoje+1, hoje+7)`. O `repo` aplica `due_date >= ?` e `due_date <= ?`, omitindo o lado que for `None`, e sempre `AND done = 0`. O `repo` só recebe datas como `str`.

## H4 — Envelope de erro: `field` sem regra de derivação e handlers que deixam rotas de fora (Alta)

**Par A — 1.1 × 2.1 (derivação de `field`):**
- O `RequestValidationError` traz uma lista de erros com `loc`, por exemplo `("body", "title")`, `("body", "tags", 0)`, `("query", "due")` ou `("path", "id")`. O AD-7 pede um único `{"code", "field", "message"}`.
- A 1.1 usa `field = loc[-1]` → `"title"`, e para tags `0`, um inteiro. A 2.1 usa `".".join(map(str, loc))` → `"body.tags.0"`. Ambas obedecem ao AD-7.
- Quando há vários erros (título vazio **e** prazo inválido), uma story usa o primeiro e outra o último. Os testes de cada story assumem formatos diferentes.
- A tag vazia (AD-4) piora o quadro. Se `normalize_tag` rodar dentro de um validador Pydantic, o erro sai como `RequestValidationError` com `loc` de body. Se rodar na rota e a rota levantar `HTTPException(422)`, o AD-7 não diz qual `code` usar, porque o handler de `HTTPException` só mapeia o 404. Se rodar no `domain` levantando `ValueError`, o resultado é 500.

**Par B — 1.1 × 1.3 (`field` no 404):**
- O AD-7 diz "`field` = `null` quando não se aplica". O NFR-3 diz que o erro "diz qual campo **ou parâmetro** causou o erro". A 1.1 devolve `field: null` no 404. A 1.3 lê o NFR-3 e devolve `field: "id"`. As duas têm base.

**Par C — 2.2 × qualquer (handlers que não cobrem tudo):**
- O handler é registrado para `fastapi.HTTPException`. O 404 de **rota inexistente** e o 405 são `starlette.exceptions.HTTPException`, que esse handler não pega, e saem como `{"detail": "Not Found"}`. Quem registrar para a classe do Starlette pega tudo, mas o AD-7 só define `code` para o 404, então o 405 recebe `"not_found"` em uma story e `"method_not_allowed"` em outra.
- Exceções não tratadas, como o `IntegrityError` do H2, saem como 500 em texto puro.
- O AD-7 pede mensagens em português, mas as do Pydantic vêm em inglês. Uma story repassa `msg`, outra traduz, e os testes que conferem `message` divergem.

**Correção proposta (apertar o AD-7):**
> - Os códigos formam um conjunto fechado: `validation_error` (422), `not_found` (404), `method_not_allowed` (405), `internal_error` (500). Um código novo exige alterar o AD.
> - O handler de HTTP é registrado para `starlette.exceptions.HTTPException`. Há também um handler para `Exception` (500, `field: null`).
> - Para `RequestValidationError`, vale **o primeiro erro** da lista. `field` é o `loc` sem o primeiro elemento (`body`, `query` ou `path`), juntado por `.`: `title`, `tags.0`, `due`, `id`. JSON malformado dá `field: null`.
> - No 404 de recurso, `field = "id"`. No 404 de rota, `field = null`.
> - Toda validação de entrada, inclusive a tag vazia, acontece em validadores Pydantic nos modelos de `api`, que chamam `domain.normalize_tags`. Assim todo 422 passa pelo mesmo handler. As rotas nunca levantam `HTTPException(422)`.
> - `message` é texto livre em português. **Os testes conferem só `code` e `field`.**

## H5 — Esquema e conexão sem dono (Alta)

**Par A — 1.1 × 2.1 (onde o esquema é criado):**
- A convenção diz "`CREATE TABLE IF NOT EXISTS` no startup do app". A 1.1 cria só `tasks`, num `lifespan`. A 2.1 acrescenta `task_tags` em outro ponto, por exemplo de forma preguiçosa no `repo`. Ou então a 1.1 cria as tabelas na importação de `main.py`.
- Um `conftest` com `TestClient(app)` **sem** `with` não executa o `lifespan`, e a primeira consulta falha com "no such table". Outro `conftest` com `with TestClient(app)` funciona. Esquema na importação grava em `./tasks.db` antes de o teste definir `TASKS_DB_PATH`, o que suja o repositório e compartilha o banco entre testes (contra o AD-8).
- Se o time-piloto rodar o Épico 1 com dados reais e a 2.x mudar o DDL de `tasks` (um índice ou um `CHECK`), o `IF NOT EXISTS` ignora a mudança em silêncio. A seção *Deferred* aceita isso, mas nenhum AD congela o DDL para impedir.

**Par B — 1.1 × 1.2 (vida da conexão):**
- A 1.1 abre uma conexão global no módulo `repo`, lendo `TASKS_DB_PATH` na importação, e usa rotas `async def`. A 1.2 usa `def` (que roda no threadpool) e reaproveita a conexão global: `ProgrammingError: SQLite objects created in a thread can only be used in that same thread`. Além disso, com o env lido na importação, o `monkeypatch.setenv` de cada teste não tem efeito.
- O `PRAGMA foreign_keys = ON` "em toda conexão" (AD-5) só se cumpre se houver um único ponto que abre conexões.

**Correção proposta (novo AD-10, "Esquema e conexão"):**
> - `repo.connect()` é o **único** ponto que abre conexões. Ele lê `os.environ["TASKS_DB_PATH"]` **na chamada** (nunca na importação), executa `PRAGMA foreign_keys = ON` e define `row_factory = sqlite3.Row`.
> - A `api` obtém a conexão por uma dependência `get_conn` com `yield`: uma conexão por requisição, fechada no fim. As rotas são `def`.
> - `repo.init_schema(conn)` contém o **DDL completo das duas tabelas**, transcrito literalmente na spine. Ele é criado pela 1.1 e chamado pelo `lifespan` de `main.py`. Nenhuma outra story altera o DDL sem um AD.
> - DDL de referência:
>   - `tasks(id INTEGER PRIMARY KEY, title TEXT NOT NULL, due_date TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)))`
>   - `task_tags(task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE, tag TEXT NOT NULL, PRIMARY KEY (task_id, tag))`
> - O `conftest` usa `with TestClient(app)`.

## H6 — Forma da tarefa sem tipos (Média)

**Unidades:** 1.1 (modelo de criação e resposta) × 1.2 (modelo de edição).

**Como cada uma obedece:** o AD-6 fixa os **nomes** `{id, title, due_date, tags, done}`, mas não os **tipos** nem as regras de cada campo.
- **`done`:** a 1.1 devolve a linha do banco direto e responde `"done": 0`. A 1.2 declara um `response_model` com `done: bool` e responde `false`. No PATCH, o `bool` do Pydantic em modo lax aceita `"yes"`, `1` e `"true"`. Uma story usa `StrictBool`, a outra não.
- **`due_date`:** a 1.1 usa o tipo `date` do Pydantic, que em modo lax também aceita, por exemplo, `"2026-10-02T00:00:00"` e timestamps inteiros, contra o "só `YYYY-MM-DD`" do AD-6. A 1.2 usa `str` com regex, que aceita `2026-02-30`.
- **`title`:** a 1.1 usa `min_length=1` e aceita `"   "`. A 1.2 faz `strip` antes de validar e rejeita. O mesmo título passa no POST e falha no PATCH, ou vice-versa. Também não está definido se o título é gravado com ou sem os espaços das pontas.

**Correção proposta (apertar o AD-6):**
> Tipos de saída: `id: int`, `title: str`, `due_date: str` (`YYYY-MM-DD`), `tags: list[str]` (H2), `done: bool`. Um único `response_model` `Task` serve todas as rotas. Na entrada, os tipos são definidos uma vez em `api.py` e reutilizados por `TaskCreate` e `TaskUpdate`:
> - `Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]`, gravado já sem espaços nas pontas;
> - `DueDate`: `date` em modo estrito, que no JSON só aceita `YYYY-MM-DD`;
> - `Done = StrictBool`.

## H7 — `tags: null` e `?tag=` repetido sem regra (Média)

**Unidades:** 1.2 (PATCH) × 2.1 (tags no PATCH e no filtro).

- O AD-6 lista `null` → 422 para `title`, `due_date` e `done`, mas **não para `tags`**. A 1.2 (ou a 2.1) declara `tags: list[str] | None = None`, e `{"tags": null}` passa a significar "limpar". Outra leitura trata `null` como "não mexer", porque o `exclude_unset` só olha a presença do campo. Uma terceira devolve 422 por analogia. Três semânticas para o mesmo corpo.
- `GET /tasks?tag=a&tag=b`: com `tag: str | None`, o FastAPI usa o último valor. Com `tag: list[str]`, a story escolhe entre E e OU. O FR-6 diz "uma tag", mas nada impede a divergência.

**Correção proposta (apertar o AD-6):**
> `tags: null` → 422, como nos outros campos. `tags: []` limpa a lista. Campo ausente mantém a lista. `?tag=` é escalar: se vier repetido, vale o último valor, e isso fica documentado. Uma tag por chamada na v1.

## H8 — Escrita do PATCH em duas etapas sem transação definida (Média)

**Unidades:** 1.2 (`UPDATE tasks`) × 2.1 (`replace_tags` no mesmo PATCH).

- A 1.2 abre a conexão com `autocommit=True` (Python 3.12+) ou `isolation_level=None`, e cada comando confirma sozinho. A 2.1 acrescenta `DELETE` + `INSERT` de tags supondo uma transação implícita. Se um `INSERT` falhar (por exemplo, a duplicata do H2), o título já foi gravado e as tags antigas já foram apagadas: um **PATCH meio aplicado e perda de tags**.
- O mesmo vale para o POST com tags: a tarefa é criada e as tags falham, ou o 500 sai depois do commit.

**Correção proposta (entra no AD-10):**
> Toda operação de escrita do `repo` roda em `with conn:` (uma transação, com commit ou rollback). Uma requisição corresponde a no máximo uma transação. As funções de escrita recebem a tarefa inteira já validada (campos e tags) e fazem tudo dentro dela.

## H9 — Contrato das fixtures sem forma (Média)

**Unidades:** 1.1 (cria o `conftest.py`) × 2.2 (precisa de várias datas por teste).

- A 1.1 obedece ao AD-8 com uma fixture `client` que já vem com o relógio fixado em uma data qualquer, escolhida por ela. A 2.2 precisa (a) mudar o instante dentro de um teste ou por parâmetro, (b) usar um instante UTC específico (H1) e (c) criar tarefas relativas a hoje. Sem um contrato, a 2.2 reescreve o `conftest`, mexe nos testes da 1.x ou cria uma segunda fixture paralela (`client_at`). São duas maneiras de fixar o relógio no mesmo projeto.
- Também não está definido em qual arquivo ficam os testes do FR-5 e do FR-6: `test_tasks.py` ou `test_filters.py`. É um detalhe menor, mas gera conflito de merge entre a 2.1 e a 1.2.

**Correção proposta (apertar o AD-8):**
> O `conftest.py` expõe exatamente duas fixtures: `client` (banco temporário via `tmp_path` + `monkeypatch.setenv("TASKS_DB_PATH")`, `with TestClient(app)`, relógio padrão `2026-10-02T15:00Z`) e `set_now(dt: datetime)`, que troca o override de `domain.now` dentro do teste. Nenhuma story cria outra forma de fixar o relógio ou o banco. Os testes de FR-1 a FR-5 ficam em `test_tasks.py`, e os de FR-6 a FR-8 em `test_filters.py`.

---

## O que já está bom e não deve mudar

- O AD-2 e o AD-3 já impedem as duas divergências mais caras do produto, o fuso e a definição de "próximos 7 dias". Só faltam a forma da injeção (H1) e a semântica dos limites (H3).
- O AD-5 escolhe tabela, e não JSON, para as tags, e o `CASCADE` com `PRAGMA` resolve a exclusão da 1.3 sem que ela precise saber de tags.
- O AD-7 já proíbe que as rotas montem o corpo do erro. Falta apenas fechar a derivação do `field` (H4).

## Ordem sugerida de aplicação

1. H5 (esquema e conexão) e H6 (tipos), porque são pré-requisitos da story 1.1.
2. H1 e H9 (relógio e fixtures), porque a 1.1 cria o `conftest`.
3. H4 (erros), porque a 1.1 registra os handlers.
4. H2, H7 e H8 (tags e transação) antes do Épico 2. H3 antes da story das janelas.
