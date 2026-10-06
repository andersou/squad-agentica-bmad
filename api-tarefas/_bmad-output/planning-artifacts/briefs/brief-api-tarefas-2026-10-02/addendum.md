---
title: "Addendum: API de Tarefas"
created: 2026-10-02
updated: 2026-10-02
---

# Addendum: API de Tarefas

Detalhes que não cabem no brief e pertencem ao PRD ou à arquitetura. Origem: slides `bmad-squad-agentica.html`, onde esta API é o exemplo de ponta a ponta.

## Pistas de contrato da API

- Recursos e campos em inglês: `POST /tasks`, `GET /tasks`, `title`, `due_date`.
- `POST /tasks` retorna 201 com o `id` da tarefa criada.
- `POST /tasks` com `title` vazio retorna 422.
- `due_date` aceita data em ISO 8601.
- `GET /tasks` não pagina na v1 (paginação está no backlog).

## Divisão prevista em épicos

- Épico 1: CRUD de tarefas (stories 1.1 criar, 1.2 editar, 1.3 excluir).
- Épico 2: tags e filtro por prazo.
