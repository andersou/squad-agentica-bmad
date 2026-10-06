# api-tarefas

API REST interna de tarefas com prazo e tags. Ela responde em uma chamada o que está vencido, o que vence hoje e o que vence nos próximos 7 dias, opcionalmente recortado por uma tag.

## Executar

Requer [uv](https://docs.astral.sh/uv/) 0.12 e Python 3.14 (o `uv sync` baixa o Python se faltar).

```sh
uv sync
TAREFAS_DB=/caminho/absoluto/tarefas.db uv run uvicorn tarefas.api:app --host 0.0.0.0 --port 8000
```

- Use caminho **absoluto** em `TAREFAS_DB`. Com caminho relativo, subir a API de outro diretório abre um banco novo e vazio. Sem `TAREFAS_DB`, o banco é `tarefas.db` no diretório atual.
- A API **não tem autenticação**. Rode-a só na rede interna do time. O `--host 0.0.0.0` escuta em todas as interfaces da máquina; para usar só na própria máquina, troque por `--host 127.0.0.1`.
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

No POST, `titulo` tem de 1 a 200 caracteres e cada tag de 1 a 50, contados depois de remover os espaços nas pontas, que não são gravados. `titulo` ou tag vazios ou só com espaços dão 422. `prazo` é uma data válida em `YYYY-MM-DD` (`2026-02-30` dá 422). Campo desconhecido no corpo dá 422, no POST e no PATCH. Tags iguais sem diferenciar maiúsculas (por `casefold`) nem espaços nas pontas são gravadas uma vez só, com a grafia da primeira, e as tarefas voltam sempre com a grafia gravada.

## Exemplos

Os exemplos usam a tarefa criada acima, com `id` 1 num banco novo. Em outro banco, troque o 1 pelo `id` que o POST devolveu.

### Listar

```sh
# Todas as tarefas, concluídas ou não → 200
curl http://localhost:8000/tarefas

# Filtro por tag, concluídas ou não → 200
curl 'http://localhost:8000/tarefas?tag=Backend'
```

A tag é comparada sem diferenciar maiúsculas (por `casefold`, então `Straße` casa `strasse`) nem espaços nas pontas. Sem `janela`, o filtro por tag traz também as concluídas; para só as pendentes, combine com uma janela. Uma tag só por chamada: mais de uma `tag` na query (`?tag=a&tag=b`), tag vazia ou com mais de 50 caracteres dá 422. Tag que nenhuma tarefa tem dá 200 com `[]`.

### Janelas de prazo

As janelas trazem só tarefas pendentes, e "hoje" é a data em America/Sao_Paulo.

```sh
# Prazo antes de hoje → 200
curl 'http://localhost:8000/tarefas?janela=vencidas'

# Prazo igual a hoje → 200
curl 'http://localhost:8000/tarefas?janela=hoje'

# Prazo de amanhã até hoje + 7 dias → 200
curl 'http://localhost:8000/tarefas?janela=proximos-7-dias'

# Janela desconhecida → 422
curl 'http://localhost:8000/tarefas?janela=amanha'

# Mais de uma janela por chamada → 422
curl 'http://localhost:8000/tarefas?janela=hoje&janela=vencidas'
```

O valor de `janela` é exato, em minúsculas e sem espaços: `Hoje` ou `hoje ` dão 422. Qualquer janela aceita também uma tag, como em `?janela=vencidas&tag=backend`. Com só a tarefa do exemplo no banco, `vencidas` a devolve e `hoje` e `proximos-7-dias` devolvem `[]`.

### Concluir

```sh
# Marca como concluída; campos omitidos ficam como estão → 200 + tarefa
curl -X PATCH http://localhost:8000/tarefas/1 \
  -H 'Content-Type: application/json' \
  -d '{"concluida": true}'
```

O PATCH também edita `titulo`, `prazo` (`YYYY-MM-DD`) e `tags` (a lista enviada substitui a anterior). `{"concluida": false}` reabre a tarefa; `concluida` é booleano JSON, e `"true"` ou `1` dá 422. `"tags": []` limpa as tags, `{}` devolve a tarefa sem mudança e `null` em qualquer campo dá 422.

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
| 422 | corpo, query ou `id` inválidos (por exemplo `prazo` fora de `YYYY-MM-DD`, `titulo` ou tag vazios, campo desconhecido como `concluida` no POST, janela desconhecida, `id` que não é inteiro de 64 bits) |

A validação vem antes da busca: um corpo inválido num `id` inexistente dá 422, não 404. Os erros vêm no formato `{"detail": ...}` do FastAPI: no 404, `detail` é o texto `"tarefa não encontrada"`; no 422, é uma lista de erros com `loc`, `msg` e `input`.

## Desenvolvimento

```sh
uv run pytest
uv run ruff check
uv run ruff format --check
```
