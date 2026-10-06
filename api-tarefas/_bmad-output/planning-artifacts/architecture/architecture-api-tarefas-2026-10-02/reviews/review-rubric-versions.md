---
title: 'Revisão do Architecture Spine: rubrica e versões'
target: ../ARCHITECTURE-SPINE.md
driving-prd: ../../../prds/prd-api-tarefas-2026-10-02/prd.md
reviewed: '2026-10-02'
lenses: ['A: checklist de bom spine', 'B: verificação de versões e tecnologias na realidade']
verdict: 'Aprovado com ressalvas: corrigir os 2 achados altos antes de quebrar épicos e stories'
---

# Revisão do Architecture Spine — API de Tarefas

## Veredito

**Aprovado com ressalvas.** O spine é enxuto, tem a altitude certa e acerta as principais divergências (relógio único, janelas num só lugar, normalização de tag, modelo de dados, contrato HTTP, envelope de erro). Todas as versões da tabela *Stack* conferem com o PyPI e o python.org em 2026-10-02. Porém duas decisões, do jeito que estão escritas, deixam stories divergirem ou tornam um teste exigido pelo PRD inócuo: o ciclo de vida da conexão SQLite (não decidido) e o ponto de substituição do relógio (AD-2/AD-8 testam a data, não o fuso). Há também um conjunto de lacunas médias no contrato (formato de data aceito, mapeamento do envelope de erro, 404/405 do roteador) e uma surpresa recente no `fastapi[standard]` 0.142 (OpenTelemetry nativo).

| Severidade | Quantidade |
| --- | --- |
| Crítica | 0 |
| Alta | 2 |
| Média | 6 |
| Baixa | 8 |
| **Total** | **16** |

---

## Lente A — Checklist de bom spine

### A1. [ALTA] O teste de virada do dia em São Paulo não testa nada se o relógio for substituído no nível da data

AD-2 diz que a `api` recebe o relógio como dependência e que os testes o trocam por `app.dependency_overrides`. AD-8 pede "um caso em que a data UTC já virou e a de São Paulo ainda não". Se a dependência sobrescrita é `domain.today()` (que devolve um `date`), o teste fixa direto a data e o código `ZoneInfo("America/Sao_Paulo")` nunca roda nos testes. O caso de virada vira um teste de nada, e o NFR-2 ("a virada do dia em `America/Sao_Paulo` com o servidor rodando em outro fuso, como UTC") e o SM-1 ficam sem cobertura real.

**Correção sugerida:** separar o *instante* da *data*. Por exemplo, `domain.today(now: datetime) -> date` faz `now.astimezone(ZoneInfo("America/Sao_Paulo")).date()`, e a dependência injetável é o relógio de instante (`now_utc()` → `datetime.now(UTC)`). Os testes sobrescrevem o instante (ex.: `2026-10-03T01:30Z`, que ainda é 02/10 em São Paulo) e a conversão de fuso é exercitada. Escrever isso na Rule de AD-2 e AD-8, porque é exatamente o ponto onde duas stories (Épico 1 e Épico 2) fariam escolhas diferentes.

### A2. [ALTA] Ciclo de vida da conexão SQLite não decidido

AD-5 exige `PRAGMA foreign_keys = ON` "em toda conexão", mas o spine não diz quando as conexões nascem e morrem. É uma divergência real entre stories:

- uma story abre uma conexão global no startup; outra abre uma por requisição;
- com rotas `def` (síncronas), o FastAPI as executa num threadpool; uma conexão global criada em outra thread levanta `sqlite3.ProgrammingError` (o `check_same_thread=True` é o padrão do `sqlite3`), e com `check_same_thread=False` há acesso concorrente sem lock;
- controle de transação (`commit`/`with conn:`) e quem chama `commit` também ficam por conta de cada story.

**Correção sugerida:** um AD curto: "uma conexão por requisição, aberta por uma dependência `get_db()` com `yield` em `repo`, que aplica `PRAGMA foreign_keys = ON`, usa `with conn:` para a transação e fecha no fim; rotas `def` síncronas; nada de conexão global". Isso também resolve A4 (o teste sobrescreve `get_db` ou o caminho).

### A3. [MÉDIA] AD-7 não define como `RequestValidationError` vira `field` e `message`

O envelope tem um único `{code, field, message}`, mas `exc.errors()` devolve uma **lista**, com `loc` do tipo `("body", "title")`, `("query", "due")`, `("body", "tags", 2)` ou `("body", 17)` para JSON malformado (`json_invalid`). Sem regra, cada story escolhe: primeiro erro ou último; `field = "title"` ou `"body.title"`; `"tags"` ou `"tags[2]"`; o que fazer com corpo ausente. Como o NFR-3 diz que o erro "diz qual campo ou parâmetro causou o erro", isso é testável e vai divergir.

**Correção sugerida:** fixar na Rule: usar o primeiro erro; `field` = último elemento textual de `loc` depois de descartar a origem (`body`/`query`/`path`) e índices numéricos; `null` quando não houver (JSON inválido, corpo ausente). Mensagem em português gerada pelo handler (não o `msg` em inglês do Pydantic), o que também precisa estar escrito, já que a convenção diz "mensagens em português".

### A4. [MÉDIA] `TASKS_DB_PATH` por teste e criação de esquema no startup dependem de detalhes não fixados

AD-8 diz que cada teste usa um arquivo temporário "via `TASKS_DB_PATH`", e a convenção diz que o esquema é criado "no startup". Verificado com FastAPI 0.142.2: o startup/lifespan **só roda** quando o `TestClient` é usado como gerenciador de contexto (`with TestClient(app) as c:`); sem isso as tabelas não existem. E, se a variável de ambiente for lida na importação do módulo, trocar a variável por teste não tem efeito. Além disso, `@app.on_event("startup")` ainda existe mas emite `DeprecationWarning`; o caminho atual é `lifespan`.

**Correção sugerida:** "o caminho do banco é lido em tempo de execução (no `lifespan` e em `get_db()`), nunca na importação; esquema criado no `lifespan`; `conftest.py` usa `monkeypatch.setenv` + `with TestClient(app)`". Ou, mais simples, sobrescrever `get_db` em vez de mexer em variável de ambiente.

### A5. [MÉDIA] O handler de 404 precisa ser registrado para o `HTTPException` do Starlette, e 405 não tem `code`

AD-7 cita "`HTTPException` (→ `code: "not_found"` para 404)". A documentação do FastAPI orienta registrar o handler para `starlette.exceptions.HTTPException`; se uma story registrar para `fastapi.HTTPException`, os 404 de rota inexistente e os 405 gerados pelo roteador (que levantam o `HTTPException` do Starlette) escapam com `{"detail": "Not Found"}`, quebrando o NFR-3 ("toda resposta de erro tem o mesmo formato"). Verificado: `GET /nope` → 404 e `POST /tasks/{id}` → 405 vêm do roteador.

**Correção sugerida:** escrever na Rule "handler registrado em `starlette.exceptions.HTTPException`; `code` derivado do status (`404 → not_found`, `405 → method_not_allowed`, demais → `http_error`)". Decidir também se 500 usa o envelope (o PRD só exige 404/422; pode ficar explícito como Deferred).

### A6. [MÉDIA] "`due_date` só aceita `YYYY-MM-DD`" não é garantido pelo tipo `date` do Pydantic

Verificado com Pydantic 2.13.5: um campo `date` aceita `"2026-10-02"`, mas também o inteiro `1790899200` (timestamp Unix), `"2026-10-02T00:00:00"` e `"2026-10-02T00:00:00Z"`. Se a story de criação usar `date` e a de edição usar `str` com regex (ou vice-versa), o contrato diverge entre `POST` e `PATCH`.

**Correção sugerida:** a Rule deve dizer "um único tipo `DueDate` em `api`, usado nos dois schemas". Uma forma simples e explícita é `str` com `pattern=r"^\d{4}-\d{2}-\d{2}$"` mais um validador que chama `date.fromisoformat`. O modo estrito do Pydantic é uma alternativa, mas o comportamento com entrada JSON precisa ser confirmado por teste antes de virar regra.

### A7. [BAIXA] Lacunas menores no contrato que podem gerar diferenças entre stories

- **`tags: null` no `PATCH`:** AD-6 cobre `null` em `title`, `due_date` e `done`, mas não em `tags`. Dizer se é 422 ou "limpa as tags" (sugestão: 422; limpar é `[]`).
- **Título só com espaços:** o PRD diz "não pode ser vazio". `"   "` é vazio? Decidir (`strip()` antes de validar ou não).
- **Ordem das tags na resposta:** não definida; os testes de igualdade de lista vão divergir. Sugestão: ordem alfabética.
- **`?tag=` vazio:** 422 (coerente com AD-4) ou ignorado? AD-4 sugere 422; deixar explícito para query.
- **Como fazer o `null` virar 422 no `PATCH`:** com `exclude_unset`, um `null` explícito é "set" e entra no `model_dump`. Verificado: declarar `title: str = None` (sem `Optional`) rejeita `null` e permite omitir; vale citar o padrão para todas as stories usarem o mesmo.

### A8. [BAIXA] Diagrama de camadas permite `repo → domain`, mas a Rule diz que `repo` recebe tudo pronto

O Design Paradigm mostra `repo --> domain`, mas AD-3 e o texto de `repo` dizem que ele recebe limites e tags já calculados. Se `repo` não precisa importar `domain`, remover a seta deixa a regra mais forte e verificável (`domain` puro, `repo` só SQL).

### A9. [BAIXA] Implantação e ambientes: falta decidir o bind de rede para o NFR-5

O *Deploy* `[ASSUMPTION]` cobre processo e banco, e Docker/CI/backup estão em Deferred com gatilho, o que está correto. Mas `fastapi run` escuta em `0.0.0.0:8000` por padrão. Para o NFR-5 (só rede interna), o spine deveria dizer como isso é garantido: host/porta explícitos (`--host <ip interno>`) ou firewall da máquina. Também não há menção a ambientes (dev com `fastapi dev`, piloto com `fastapi run`); uma linha basta.

### A10. [BAIXA] Questão em aberto do PRD sem destino na arquitetura

PRD §8 (como as tarefas da planilha entram na API) pede revisão "antes de quebrar os épicos". O spine não a menciona. Mesmo que a resposta seja "script descartável usando `POST /tasks`, sem impacto arquitetural", registrar em Deferred ou numa seção de questões em aberto fecha o ciclo.

### Verificação do restante do checklist

- **Cobertura do PRD:** FR-1 a FR-8 e NFR-1 a NFR-5 estão no mapa *Capability → Architecture*. O prazo passado aceito (FR-1), lista sem paginação (FR-2), substituição integral de tags (FR-5), janela inválida → 422 (FR-7) e interseção (FR-8) estão cobertos pelas Rules ou pelo contrato. Ordenação com desempate por `id` é uma boa adição.
- **Deferred:** nada ali permite divergência entre unidades da v1; cada item tem gatilho de revisão. Concorrência está bem amarrada a "um processo".
- **Operações:** logs (uvicorn) e backup (deferido) estão decididos; ver B3 sobre observabilidade, que mudou de fato com o FastAPI 0.142.

---

## Lente B — Versões e tecnologias verificadas na realidade (2026-10-02)

Método: consulta direta à API JSON do PyPI, à API de releases do python.org e à PEP 790; leitura das docs oficiais do FastAPI e do Python 3.14; execução local de scripts com `uv run --python 3.14` contra `fastapi[standard]==0.142.2` e `pydantic==2.13.5`.

| Item no spine | Realidade em 2026-10-02 | Situação |
| --- | --- | --- |
| Python 3.14 | 3.14.8 é a última estável (30/09/2026). 3.15.0 estava previsto para 01/10/2026 (PEP 790), ainda não publicado na API do python.org; só 3.15.0rc2 | Correto; ver B4 |
| uv 0.12.x | 0.12.22 (02/10/2026) | Correto |
| FastAPI 0.142.2 | 0.142.2 é a última (30/09/2026) | Correto; ver B3 |
| Pydantic 2.13.x | 2.13.5 (28/08/2026), resolvido pelo `fastapi[standard]` | Correto |
| pytest 9.1.1 | 9.1.1 é a última (19/06/2026) | Correto |
| Ruff 0.16.10 | 0.16.10 é a última (01/10/2026) | Correto |
| `sqlite3` stdlib | Presente no 3.14 | Correto; ver A2 |
| `zoneinfo` | Presente; depende do banco IANA do sistema ou do pacote `tzdata` | Ver B1 |
| `app.dependency_overrides` | Funciona no 0.142.2 (verificado) | Correto; ver A1 |
| `model_dump(exclude_unset=True)` | Padrão documentado do FastAPI para `PATCH` com Pydantic v2 | Correto; ver A7 |

Nenhuma versão está desatualizada nem foi inventada. O que falta é **evidência de verificação no próprio documento**: o spine não registra fonte nem data de verificação das versões (ver B5).

### B1. [MÉDIA] `zoneinfo` sem `tzdata` pode falhar no host de implantação, e AD-1 proíbe adicioná-lo

A documentação do Python 3.14 diz: "Some systems, including notably Windows systems, do not have an IANA database available, and so for projects targeting cross-platform compatibility that require time zone data, it is recommended to declare a dependency on tzdata. If neither system data nor tzdata are available, all calls to `ZoneInfo` will raise `ZoneInfoNotFoundError`." Verificado: `tzdata` **não** vem no `fastapi[standard]`. O host do piloto ainda é indefinido (Deferred), e imagens Linux mínimas (Debian 12 slim, por exemplo) e Windows não trazem `/usr/share/zoneinfo`. Como AD-1 proíbe qualquer dependência fora do `fastapi[standard]` sem um novo AD, a story que bater nisso fica travada ou improvisa.

**Correção sugerida:** acrescentar `tzdata` (pacote first-party do PyPA/CPython, 2026.4) a AD-1 e à tabela *Stack*. Custo quase zero, e remove a dependência do SO.

### B2. [BAIXA] `TestClient` com Starlette 1.7 emite aviso de depreciação do `httpx`

Verificado: ao importar `fastapi.testclient`, a Starlette 1.7.0 (resolvida pelo FastAPI 0.142.2) emite `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` Funciona, mas se a configuração do pytest usar `-W error` (comum em projetos novos) os testes quebram. Decidir: adicionar `httpx2` como dependência de dev ou filtrar o aviso em `pyproject.toml`. Como AD-1 governa dependências, isso precisa estar escrito.

### B3. [MÉDIA] `fastapi[standard]` 0.142 traz OpenTelemetry nativo, Sentry SDK e o CLI da FastAPI Cloud — "uma dependência" é na prática ~55 pacotes

Verificado com `uv pip compile` para `fastapi[standard]==0.142.2` em Python 3.14: 55 pacotes, entre eles `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http`, `sentry-sdk`, `fastapi-cloud-cli`, `pydantic-settings`, `jinja2`, `email-validator`, `uvloop`, `watchfiles`. O OpenTelemetry nativo entrou no 0.142.0 em 29/09/2026 (há três dias), e o 0.142.2 já corrigiu "Allow startup when automatic OpenTelemetry configuration fails". Segundo a documentação, sem variáveis `OTEL_*` nada é exportado; com `OTEL_EXPORTER_OTLP_ENDPOINT` definido, o FastAPI passa a exportar sozinho. Isso contradiz o *Deferred* "Logs e observabilidade: a v1 usa só o log padrão do uvicorn" e torna o AD-1 menos restritivo do que parece.

**Correção sugerida (escolher uma):**
- manter `fastapi[standard]`, mas fixar `fastapi[standard]~=0.142.2` (ou travar via `uv.lock`, já implícito no projeto `uv`) e escrever em AD-1 que o app nasce com `FastAPI(telemetry={"auto_configure": False})` até a observabilidade sair do Deferred; ou
- trocar por `fastapi` + `uvicorn` como runtime e `httpx` (ou `httpx2`) como dev. Como `fastapi run` vem do `fastapi-cli`, nesse caso o comando de deploy passa a ser `uvicorn app.main:app`.

Para um demo pequeno, a primeira opção é a menor mudança.

### B4. [BAIXA] Python 3.15 é iminente e `requires-python >= 3.14` deixa a versão do interpretador em aberto

O 3.15.0 estava agendado para 01/10/2026 e deve sair a qualquer momento. Com `requires-python >= 3.14` e sem `.python-version`, `uv` pode escolher 3.15 em uma máquina e 3.14 em outra. Sugestão: fixar `.python-version` com `3.14` (o `uv init` já cria) e mencionar no spine. A troca para 3.15 fica para quando `pydantic-core` e demais wheels confirmarem suporte.

### B5. [BAIXA] O spine não registra a verificação das versões

Todas as versões conferem, mas o documento não diz de onde vieram nem quando foram verificadas. Para um spine que vai alimentar stories por semanas, uma linha "versões conferidas no PyPI em 2026-10-02" (e a regra de que o `uv.lock` é a fonte de verdade) evita que alguém troque números por memória.

---

## Resumo das correções, por prioridade

1. **A1 (alta):** injetar o instante, não a data; `today(now)` converte para São Paulo; teste de virada sobrescreve o instante.
2. **A2 (alta):** AD de conexão: `get_db()` por requisição com `yield`, `PRAGMA foreign_keys = ON`, `with conn:`, rotas síncronas.
3. **A3, A5 (média):** completar AD-7: mapeamento de `loc` → `field`, primeiro erro, mensagens em português, handler no `HTTPException` do Starlette, `code` para 405.
4. **A4 (média):** esquema no `lifespan`, caminho lido em runtime, `with TestClient(app)`.
5. **A6 (média):** tipo único `DueDate` com formato estrito.
6. **B1, B3 (média):** `tzdata` em AD-1; decidir sobre o OpenTelemetry automático do `fastapi[standard]` 0.142.
7. Baixas: A7 a A10, B2, B4, B5.

## Fontes

- PyPI JSON API: `fastapi`, `pydantic`, `pytest`, `ruff`, `uv`, `tzdata`, `starlette`, `httpx2` (consultado em 2026-10-02)
- python.org releases API e [PEP 790 — Python 3.15 Release Schedule](https://peps.python.org/pep-0790/)
- [zoneinfo — Python 3.14 docs](https://docs.python.org/3.14/library/zoneinfo.html)
- [FastAPI — Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [FastAPI — Body Updates (PATCH, exclude_unset)](https://fastapi.tiangolo.com/tutorial/body-updates/)
- [FastAPI — OpenTelemetry](https://fastapi.tiangolo.com/advanced/opentelemetry/)
- [FastAPI — Release Notes](https://fastapi.tiangolo.com/release-notes/) e [PR #16403](https://github.com/fastapi/fastapi/pull/16403)
- Execução local (`uv run --python 3.14`) com `fastapi[standard]==0.142.2` e `pydantic==2.13.5`: `dependency_overrides`, lifespan do `TestClient`, 404/405 do roteador, aceitação de formatos por `date`, `null` em campo `str = None`, resolução de dependências.
