# API de Tarefas

API HTTP para registrar tarefas com título, prazo e tags, e consultar o que venceu ou vence.

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/) (0.12+)
- Python 3.14 (o `uv` instala se faltar)

## Instalar e testar

```bash
uv sync
uv run pytest
uv run ruff check && uv run ruff format --check
```

## Rodar

O banco é um arquivo SQLite definido por `TASKS_DB_PATH` (padrão `./tasks.db`), criado na primeira requisição.

```bash
TASKS_DB_PATH=./tasks.db uv run uvicorn app.main:app --host <IP interno> --port 8000
```

> **Atenção:** a API não tem autenticação. Use o IP da rede interna em `--host` e **nunca** `0.0.0.0` numa máquina exposta.

A documentação interativa fica em `http://<IP interno>:8000/docs`.

## Exemplos

Criar uma tarefa (`due_date` sempre no formato `YYYY-MM-DD`):

```bash
curl -X POST http://<IP interno>:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Revisar PR", "due_date": "2026-10-10"}'
# 201 {"id": 1, "title": "Revisar PR", "due_date": "2026-10-10", "tags": [], "done": false}
```

Listar todas (ordem: prazo crescente, depois `id`):

```bash
curl http://<IP interno>:8000/tasks
# 200 [{"id": 1, "title": "Revisar PR", "due_date": "2026-10-10", "tags": [], "done": false}]
```

Consultar uma:

```bash
curl http://<IP interno>:8000/tasks/1
# 200 {"id": 1, "title": "Revisar PR", "due_date": "2026-10-10", "tags": [], "done": false}
```

Editar ou concluir (`PATCH` aplica só os campos enviados; `{"done": false}` desmarca):

```bash
curl -X PATCH http://<IP interno>:8000/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"done": true}'
# 200 {"id": 1, "title": "Revisar PR", "due_date": "2026-10-10", "tags": [], "done": true}
```

Erro de validação (todo erro usa o mesmo envelope):

```bash
curl -X POST http://<IP interno>:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "", "due_date": "2026-10-10"}'
# 422 {"error": {"code": "validation_error", "field": "title", "message": "Campo inválido: title"}}
```

Códigos de erro: `validation_error` (422), `not_found` (404), `method_not_allowed` (405), `internal_error` (500).

### Tags e prazos vencidos

Criar uma tarefa com tags e prazo (tags são normalizadas: sem espaços nas pontas e em minúsculas):

```bash
curl -X POST http://<IP interno>:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Corrigir deploy", "due_date": "2026-10-01", "tags": ["Backend"]}'
# 201 {"id": 2, "title": "Corrigir deploy", "due_date": "2026-10-01", "tags": ["backend"], "done": false}
```

Listar as vencidas:

```bash
curl "http://<IP interno>:8000/tasks?due=overdue"
# 200 [{"id": 2, "title": "Corrigir deploy", "due_date": "2026-10-01", "tags": ["backend"], "done": false}]
```

Janelas de `?due=` (só tarefas não concluídas; "hoje" é a data em `America/Sao_Paulo`):

- `overdue`: prazo antes de hoje;
- `today`: prazo hoje;
- `next7`: prazo de amanhã até hoje + 7 dias.

Filtrar por tag (`?tag=backend`) e combinar com uma janela (interseção):

```bash
curl "http://<IP interno>:8000/tasks?tag=backend&due=overdue"
```
