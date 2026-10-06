# api-tarefas

API REST interna de tarefas com prazo e tags. Ela responde em uma chamada o que está vencido, o que vence hoje e o que vence nos próximos 7 dias, opcionalmente recortado por uma tag.

## Executar

Requer [uv](https://docs.astral.sh/uv/) 0.12 e Python 3.14 (o `uv sync` baixa o Python se faltar).

```sh
uv sync
TAREFAS_DB=/caminho/absoluto/tarefas.db uv run uvicorn tarefas.api:app --host 0.0.0.0 --port 8000
```

- Use caminho **absoluto** em `TAREFAS_DB`. Com caminho relativo, subir a API de outro diretório abre um banco novo e vazio. Sem `TAREFAS_DB`, o banco é `tarefas.db` no diretório atual.
- A API **não tem autenticação**. Rode-a só na rede interna do time.
- A documentação interativa (OpenAPI) fica em `http://localhost:8000/docs`.

## Em duas chamadas: criar e listar as vencidas

```sh
# Cria uma tarefa com tag e prazo já passado → 201 + tarefa
curl -X POST http://localhost:8000/tarefas \
  -H 'Content-Type: application/json' \
  -d '{"titulo": "Revisar PR do login", "prazo": "2026-01-15", "tags": ["backend"]}'

# Lista as pendentes vencidas com essa tag → 200 + lista
curl 'http://localhost:8000/tarefas?janela=vencidas&tag=backend'
```

A tarefa volta como `{"id": 1, "titulo": "Revisar PR do login", "prazo": "2026-01-15", "tags": ["backend"], "concluida": false}`. Listagens devolvem um array JSON nessa forma, em ordem de prazo e depois de `id`. Para ver o código HTTP de cada chamada, acrescente `-i` ao `curl`.

No POST, `titulo` tem de 1 a 200 caracteres, `prazo` é uma data válida em `YYYY-MM-DD` (`2026-02-30` dá 422) e cada tag tem até 50 caracteres. Tags iguais sem diferenciar maiúsculas são gravadas uma vez só, com a grafia da primeira, e as tarefas voltam sempre com a grafia gravada.

## Exemplos

Os exemplos usam a tarefa criada acima, com `id` 1 num banco novo. Em outro banco, troque o 1 pelo `id` que o POST devolveu.

### Listar

```sh
# Todas as tarefas, concluídas ou não → 200
curl http://localhost:8000/tarefas

# Filtro por tag, sem diferenciar maiúsculas nem espaços nas pontas → 200
curl 'http://localhost:8000/tarefas?tag=Backend'
```

Uma tag só por chamada: mais de uma `tag` na query (`?tag=a&tag=b`), tag vazia ou com mais de 50 caracteres dá 422. Tag que nenhuma tarefa tem dá 200 com `[]`.

### Janelas de prazo

As janelas trazem só tarefas pendentes, e "hoje" é a data em America/Sao_Paulo.

```sh
# Prazo antes de hoje → 200
curl 'http://localhost:8000/tarefas?janela=vencidas'

# Prazo igual a hoje → 200
curl 'http://localhost:8000/tarefas?janela=hoje'

# Prazo de amanhã até hoje + 7 dias → 200
curl 'http://localhost:8000/tarefas?janela=proximos-7-dias'

# Janela desconhecida ou repetida → 422
curl 'http://localhost:8000/tarefas?janela=amanha'
```

Qualquer janela aceita também `&tag=`. Com só a tarefa do exemplo no banco, `vencidas` a devolve e `hoje` e `proximos-7-dias` devolvem `[]`.

### Concluir

```sh
# Marca como concluída; campos omitidos ficam como estão → 200 + tarefa
curl -X PATCH http://localhost:8000/tarefas/1 \
  -H 'Content-Type: application/json' \
  -d '{"concluida": true}'
```

O PATCH também edita `titulo`, `prazo` (`YYYY-MM-DD`) e `tags` (a lista enviada substitui a anterior). `{"concluida": false}` reabre a tarefa. `"tags": []` limpa as tags, `{}` devolve a tarefa sem mudança e `null` em qualquer campo dá 422.

### Excluir

```sh
# Exclui → 204 sem corpo
curl -X DELETE http://localhost:8000/tarefas/1

# Repetir com a tarefa já excluída (id inexistente) → 404
curl -X DELETE http://localhost:8000/tarefas/1
```

### Códigos de resposta

| Código | Quando |
|---|---|
| 201 | `POST /tarefas` criou a tarefa |
| 200 | `GET /tarefas` (com ou sem `janela`/`tag`) e `PATCH /tarefas/{id}` |
| 204 | `DELETE /tarefas/{id}` excluiu |
| 404 | `PATCH` ou `DELETE` de `id` inexistente |
| 422 | corpo, query ou `id` inválidos (por exemplo `prazo` fora de `YYYY-MM-DD`, `titulo` vazio, `concluida` no POST, janela desconhecida, `id` que não é inteiro de 64 bits) |

A validação vem antes da busca: um corpo inválido num `id` inexistente dá 422, não 404. Os erros vêm no formato `{"detail": ...}` do FastAPI.

## Desenvolvimento

```sh
uv run pytest
uv run ruff check
uv run ruff format --check
```
