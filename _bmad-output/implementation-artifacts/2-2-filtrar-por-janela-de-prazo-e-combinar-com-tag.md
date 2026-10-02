# Story 2.2: Filtrar por janela de prazo e combinar com tag

Status: ready-for-dev

<!-- Nota: a validação é opcional. Rode validate-create-story para um controle de qualidade antes do dev-story. -->

## Story

Como dev do time-piloto,
quero perguntar em uma chamada o que está vencido, o que vence hoje e o que vence nos próximos 7 dias, inclusive por tag,
para que os prazos deixem de se perder.

## Acceptance Criteria

Cenário-base dos ACs 1 a 3: relógio fixado com `set_now("2026-10-02T15:00Z")` (hoje = 2026-10-02 em São Paulo); tarefas não concluídas com prazo em 10-01, 10-02, 10-03, 10-09 e 10-10, mais uma tarefa **concluída** com prazo em 10-01.

1. **overdue:** `GET /tasks?due=overdue` devolve 200 com só a tarefa não concluída de 10-01. A concluída de 10-01 fica de fora (FR7, AD-3).
2. **today:** `GET /tasks?due=today` devolve só a tarefa de 10-02 (FR7, AD-3).
3. **next7:** `GET /tasks?due=next7` devolve as tarefas de 10-03 e 10-09, **nessa ordem**. A de 10-02 (hoje) e a de 10-10 (hoje + 8) ficam de fora (FR7, AD-3, AD-6).
4. **Virada do dia:** com `set_now("2026-10-03T01:00Z")` (em UTC já é dia 3; em São Paulo são 22h do dia 2), a tarefa de 10-02 aparece em `?due=today` e **não** em `?due=overdue` (FR7, AD-2, NFR2).
5. **Concluída sai das janelas:** uma tarefa que aparece numa janela, depois de `PATCH /tasks/{id}` com `{"done": true}`, some de todas as janelas; com `{"done": false}`, volta a aparecer (FR3, FR7).
6. **Janela inválida:** `GET /tasks?due=semana` devolve 422 com `{"error": {"code": "validation_error", "field": "due", ...}}` (FR7, AD-4, AD-7).
7. **Combinação:** com tarefas vencidas com e sem a tag `backend`, `GET /tasks?tag=backend&due=overdue` devolve só as vencidas que têm `backend` (interseção), cada uma com **todas** as suas tags (FR8, AD-9).
8. **Revisão de código, relógio:** "hoje" só vem de `domain.today(now)`, com `now` injetado pela dependência `domain.now`; não há `date.today()`, `datetime.now()` nem similares fora de `domain.now()` (AD-2).
9. **Revisão de código, limites:** os limites saem de `domain.window_bounds`; o `repo` só aplica `>=`, `<=` (omitindo o lado `None`) e `done = 0` (AD-3).
10. **README:** um dev novo cria uma tarefa com tag e prazo e lista as vencidas em duas chamadas `curl` copiadas do `README.md` (NFR1, SM-2).

## Tasks / Subtasks

- [ ] **Task 1: `domain.window_bounds` (AC: 1, 2, 3, 9)**
  - [ ] 1.1 Em `app/domain.py`, implementar `window_bounds(window, today) -> tuple[str | None, str]` com a tabela do AD-3: `overdue` = (None, hoje − 1), `today` = (hoje, hoje), `next7` = (hoje + 1, hoje + 7). Devolver texto `YYYY-MM-DD` (`date.isoformat()`), usando `timedelta`. Sem IO, sem chamar relógio.
  - [ ] 1.2 Conferir que `now()` e `today(now)` (entregues na 1.1, AD-2) existem e que `today` usa `now.astimezone(ZoneInfo("America/Sao_Paulo")).date()`. Se a 1.1 não os entregou, criá-los aqui exatamente como o AD-2 descreve.
- [ ] **Task 2: parâmetro `due` na rota de listagem (AC: 1-4, 6, 8)**
  - [ ] 2.1 Em `app/api.py`, definir (se ainda não existir) o enum `Due(str, Enum)` com `overdue | today | next7` (AD-4).
  - [ ] 2.2 Em `GET /tasks`, adicionar `due: Due | None = None` como query param e `now: datetime = Depends(domain.now)`. Quando `due` vier, calcular `start, end = domain.window_bounds(due, domain.today(now))` e passar ao `repo`. A rota continua `def` (AD-10).
  - [ ] 2.3 Não validar `due` com `if` na rota: o 422 vem do Pydantic, e o handler do AD-7 gera `field: "due"` a partir de `loc = ("query", "due")`.
- [ ] **Task 3: filtro no `repo` combinável com tag (AC: 1-3, 5, 7, 9)**
  - [ ] 3.1 Estender a função de listagem do `repo` (a mesma que a 2.1 usa para `tag`) com `start: str | None` e `end: str | None`, ou um parâmetro que indique janela ativa. Montar o `WHERE` com parâmetros `?`: com janela ativa, sempre `done = 0`, mais `due_date >= ?` se `start` não for `None` e `due_date <= ?` se `end` não for `None`.
  - [ ] 3.2 Manter o filtro de tag da 2.1 (`EXISTS (SELECT 1 FROM task_tags ...)`) e combinar com `AND` na mesma consulta (FR8). Nunca `JOIN` na consulta principal (AD-9).
  - [ ] 3.3 Manter `ORDER BY due_date, id` e carregar as tags por `repo.load_tags` (AD-6, AD-9).
  - [ ] 3.4 Sem `?due=`, a listagem não ganha `done = 0`: `GET /tasks` e `GET /tasks?tag=` continuam trazendo concluídas (regressão de FR2/FR6).
- [ ] **Task 4: testes em `tests/test_filters.py` (AC: 1-7; NFR2)**
  - [ ] 4.1 Usar só as fixtures `client` e `set_now` do `tests/conftest.py` (AD-8). Não criar outra forma de fixar relógio ou banco; não editar o `conftest`, a menos que `set_now` falte (ver Questões).
  - [ ] 4.2 Helper local mínimo para criar tarefas via `POST /tasks` e concluir via `PATCH`; conferir resultados pelos `due_date` (ou ids) e pela ordem.
  - [ ] 4.3 Teste do cenário-base para `overdue`, `today` e `next7` (AC 1-3), cobrindo ontem, hoje, amanhã, hoje + 7, hoje + 8 e a concluída. Pode ser `pytest.mark.parametrize` por janela.
  - [ ] 4.4 Teste da virada com `set_now(datetime(2026, 10, 3, 1, 0, tzinfo=UTC))` (AC 4): 10-02 em `today` e fora de `overdue`.
  - [ ] 4.5 Teste de concluir/desmarcar (AC 5).
  - [ ] 4.6 Teste de `?due=semana` (e `?due=`, vazio) → 422 com `code == "validation_error"` e `field == "due"`; conferir só `code` e `field`, nunca `message` (AC 6, AD-7).
  - [ ] 4.7 Teste de `?tag=backend&due=overdue` (AC 7), com uma tarefa vencida sem `backend`, uma com `backend` + outra tag (conferir que vem com todas as tags) e uma com `backend` fora da janela. Incluir `?tag=Backend` para confirmar que a normalização vale na combinação.
- [ ] **Task 5: README (AC: 10)**
  - [ ] 5.1 Em `README.md`, adicionar dois `curl` copiáveis: criar tarefa com `tags` e `due_date`, e `curl "http://<host>:8000/tasks?due=overdue"`. Opcionalmente o exemplo combinado `?tag=backend&due=overdue` e uma linha explicando as três janelas e o fuso `America/Sao_Paulo`. Texto em português.
- [ ] **Task 6: verificação final (AC: 8, 9)**
  - [ ] 6.1 `grep -rnE "date\.today|datetime\.now|datetime\.utcnow|time\.time" app/` só pode apontar para `domain.now()`.
  - [ ] 6.2 `uv run ruff check`, `uv run ruff format --check` e `uv run pytest` passando (suíte inteira, incluindo épico 1 e 2.1).

## Dev Notes

### Inteligência de stories anteriores

Não disponível: as stories 1.1, 1.2, 1.3 e 2.1 estão sendo criadas em paralelo e ainda não há código (greenfield). As dependências abaixo vêm do `epics.md` e do spine, não de arquivos reais. **Antes de começar, leia `app/` e `tests/conftest.py` como estiverem** e ajuste nomes de função ao que existir; a regra dos ADs prevalece sobre nomes.

O que esta story assume das anteriores:

| Origem | Entrega esperada | Uso aqui |
| --- | --- | --- |
| 1.1 (AD-2) | `domain.now()` (UTC com fuso) e `domain.today(now)` (São Paulo); `api` recebe `now` como `Depends(domain.now)` | "hoje" das janelas |
| 1.1 (AD-8) | `tests/conftest.py` com `client` (banco em `tmp_path` via `TASKS_DB_PATH`) e `set_now(instante_utc)` via `app.dependency_overrides[domain.now]` | todos os testes |
| 1.1 (AD-5, AD-6, AD-7, AD-10) | esquema completo, `GET /tasks` ordenado por `due_date, id`, envelope de erro, `get_db()` | base da rota e do 422 |
| 1.2 | `PATCH` com `done` estrito | AC 5 |
| 2.1 (AD-9) | `domain.normalize_tags`, `repo.load_tags`, filtro `?tag=` com `EXISTS`, 422 em `?tag=` vazio | AC 7 |

### O que muda e o que precisa continuar igual

- **Muda:** `domain.py` ganha `window_bounds`; `api.py` ganha `due` (e `now`, se a 1.1 ainda não o injetou na listagem) em `GET /tasks`; `repo.py` ganha os limites na consulta de listagem; `tests/test_filters.py` ganha os testes; `README.md` ganha os `curl`.
- **Preservar:** `GET /tasks` sem filtro traz todas as tarefas, concluídas inclusive; `?tag=` sozinho também não exclui concluídas (só as janelas excluem, FR7); ordem `due_date, id`; tarefas sempre com todas as tags; envelope de erro do AD-7; nenhum teste do épico 1 ou da 2.1 quebra.

### Guardrails de arquitetura

- **AD-2:** a rota nunca chama o relógio; recebe `now` por `Depends(domain.now)`. Os testes trocam **só** `now` (instante UTC), então a conversão de fuso em `domain.today` sempre roda. Não fazer override de `today`, não usar `freezegun` (dependência nova viola AD-1).
- **AD-3:** limites inclusivos; nenhum `BETWEEN` com semântica diferente, nenhum `<` semiaberto, nenhuma conta de data fora de `window_bounds`. Comparar `due_date` como texto funciona porque é sempre `YYYY-MM-DD` (AD-4, AD-5).
- **AD-4/AD-7:** `due` é enum; valor fora dele dá 422 `validation_error` com `field: "due"` pelo handler global. Nada de `if` na rota gerando 422.
- **AD-6:** `?tag=` e `?due=` aceitam um valor cada e se combinam por interseção.
- **AD-9:** filtro por tag via `EXISTS`; tags lidas só por `load_tags`.
- **AD-10:** rota `def`, conexão por `get_db()`; esta story é só leitura.
- **Camadas:** `domain` não importa `api` nem `repo`. `repo` recebe limites prontos; não calcula datas.

### Esboço da consulta (orientação, não código final)

```sql
SELECT id, title, due_date, done FROM tasks t
WHERE 1=1
  [AND EXISTS (SELECT 1 FROM task_tags tt WHERE tt.task_id = t.id AND tt.tag = ?)]   -- se tag
  [AND t.done = 0]                                                                      -- se due
  [AND t.due_date >= ?]                                                                 -- se start
  [AND t.due_date <= ?]                                                                 -- se end
ORDER BY t.due_date, t.id
```

Sempre placeholders `?`; nunca interpolar valores na string SQL.

### Bibliotecas

Nenhuma dependência nova (AD-1). Só stdlib (`datetime`, `timedelta`, `zoneinfo`, `enum`) + FastAPI/Pydantic já instalados. `tzdata` já está no runtime para o `ZoneInfo` funcionar em qualquer máquina. Versões do spine: Python 3.14, FastAPI 0.142.2, Pydantic 2.13.x, pytest 9.1.1, httpx 0.28.1, Ruff 0.16.10. Pesquisa web não foi feita: as versões foram conferidas pelo arquiteto em 2026-10-02 (Stack do spine).

### Arquivos

- `app/domain.py` (UPDATE): `window_bounds`.
- `app/api.py` (UPDATE): enum `Due` e parâmetro `due` em `GET /tasks`.
- `app/repo.py` (UPDATE): limites na listagem.
- `tests/test_filters.py` (UPDATE, ou NEW se a 2.1 tiver posto os testes de tag em outro lugar): testes de FR7/FR8. Convenção da revisão adversarial H9: FR-1 a FR-5 em `test_tasks.py`, FR-6 a FR-8 em `test_filters.py`.
- `README.md` (UPDATE): `curl`.
- `tests/conftest.py`: **não editar** (AD-8), salvo a exceção nas Questões.

### Testes

- pytest + `TestClient` contra o app real, banco novo por teste (AD-8).
- Instantes como `datetime` UTC com fuso (`datetime(2026, 10, 2, 15, 0, tzinfo=UTC)`); confirmar a assinatura real de `set_now` no `conftest` (pode aceitar `datetime` ou texto ISO).
- Cobrir os limites exigidos pelo NFR2: ontem, hoje, amanhã, hoje + 7, hoje + 8, concluída e `2026-10-03T01:00Z`.
- Conferir só `code` e `field` nos erros.
- Aviso conhecido (review-rubric-versions): a Starlette resolvida pelo FastAPI 0.142.2 emite `StarletteDeprecationWarning` ao usar `httpx` no `TestClient`. Se o `pyproject` da 1.1 usar `-W error`, isso já terá sido tratado lá; não adicionar `httpx2` aqui sem AD.

### Questões em aberto (registradas, sem bloquear)

1. **`?due=` repetido** (`?due=today&due=overdue`): o AD-6 diz "um valor cada", mas não define o erro. O FastAPI pega o último valor sem erro. Comportamento adotado: aceitar o padrão do FastAPI e não testar; decidir se deve dar 422.
2. **`?due=` vazio:** o enum rejeita, então dá 422 `field: "due"`, coerente com `?tag=` vazio da 2.1. Assumido como correto.
3. **`set_now` ausente:** se a 1.1 não entregou `set_now` (o readiness m1 permitia movê-la para a 2.2), criá-la no `conftest` exatamente como o AD-8 descreve e registrar no Completion Notes.
4. **Nome da função de listagem do `repo`** depende da 2.1; adaptar sem criar uma segunda função de listagem.

### Project Structure Notes

- Alinhado à árvore do spine (`app/main.py`, `api.py`, `domain.py`, `repo.py`; `tests/conftest.py`, `test_tasks.py`, `test_filters.py`). Nenhum arquivo novo em `app/`.
- Nenhum conflito detectado com o spine.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2: Filtrar por janela de prazo e combinar com tag]
- [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements] (AD-2, AD-3, AD-8, AD-9)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/ARCHITECTURE-SPINE.md#AD-2, #AD-3, #AD-4, #AD-6, #AD-7, #AD-8, #AD-9, #AD-10]
- [Source: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/prd.md#3. Glossário] (definição das janelas; "hoje" em São Paulo)
- [Source: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/prd.md#FR-7, #FR-8, #NFR-1, #NFR-2, #SM-1, #SM-2]
- [Source: _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/addendum.md#Pistas de contrato da API] (`?tag=backend&due=overdue|today|next7`)
- [Source: _bmad-output/planning-artifacts/implementation-readiness-report-2026-10-02.md] (FR3/FR7/FR8/NFR2 cobertos na 2.2; m1 sobre `set_now`)
- [Source: _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/reviews/review-adversarial.md#H1, #H3, #H9]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- Análise de contexto concluída: guia completo para o dev criado. Inteligência de stories anteriores indisponível (criadas em paralelo, sem código).

### File List
