---
title: "Addendum: PRD API de Tarefas"
created: 2026-10-02
updated: 2026-10-02
---

# Addendum: PRD API de Tarefas

Detalhes para a arquitetura e as stories que não cabem no corpo do PRD. Origem: addendum do brief (slides `bmad-squad-agentica.html`) e decisões tomadas durante o PRD.

## Pistas de contrato da API

- Recursos e campos em inglês: `POST /tasks`, `GET /tasks`, `title`, `due_date`.
- `POST /tasks` retorna 201 com o `id` da tarefa criada (FR-1).
- `POST /tasks` com `title` vazio retorna 422 (FR-1).
- `due_date` aceita datas no formato ISO 8601 (`YYYY-MM-DD`).
- `GET /tasks` não pagina na v1 (FR-2).
- "Hoje" é calculado no servidor com fuso fixo `America/Sao_Paulo`, independentemente do fuso da máquina.
- Sugestões, a confirmar na arquitetura: campo `tags` (lista de strings), campo `done` (booleano) para a conclusão, filtros por query string em `GET /tasks` (`?tag=backend&due=overdue|today|next7`).
- Formato de erro sugerido para o NFR-3, a confirmar na arquitetura: `{"error": {"code": "validation_error", "field": "title", "message": "..."}}`.

## Divisão prevista em épicos

- **Épico 1: CRUD de tarefas** — stories 1.1 criar (FR-1), 1.2 editar (FR-3, inclui marcar como concluída), 1.3 excluir (FR-4). A listagem e a consulta (FR-2) entram junto com a 1.1.
- **Épico 2: tags e filtro por prazo** — FR-5 a FR-8.

## Alternativas consideradas

- **Conclusão da tarefa:** um endpoint próprio (`POST /tasks/{id}/complete`) ou um status com vários valores (a fazer, em andamento, feita) foram descartados. Marcar a tarefa como concluída pela edição basta para tirá-la das janelas de prazo e cabe na story 1.2, sem exigir uma story nova.
- **Fuso horário:** um header `X-Timezone` por requisição (a solução mostrada nos slides após o readiness check) foi descartado na v1. Com um único time-piloto, basta um fuso fixo (`America/Sao_Paulo`). O header volta a fazer sentido com vários times.
