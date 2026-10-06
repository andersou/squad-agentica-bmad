---
title: "Product Brief: API de Tarefas"
status: final
created: 2026-10-02
updated: 2026-10-02
---

# Product Brief: API de Tarefas

## Resumo executivo

A API de Tarefas é uma API REST para times pequenos registrarem tarefas, etiquetá-las com tags e filtrá-las por prazo. Ela substitui a planilha compartilhada em que hoje os prazos se perdem.

O escopo é pequeno de propósito. Este é um primeiro projeto para percorrer o BMad Method de ponta a ponta, do brief ao primeiro commit, e não uma tentativa de competir com Jira, Trello ou similares. Não há diferencial de mercado a defender: o valor está em resolver um problema real, bem delimitado, que cabe em dois épicos.

## O problema

Devs de times pequenos controlam tarefas e prazos em planilha, e perdem prazos. A planilha não responde sozinha à pergunta que importa: o que está vencido e o que vence nos próximos 7 dias? Para saber, alguém precisa abrir o arquivo, ordenar e conferir linha a linha. Ninguém faz isso todo dia, então o atraso só aparece depois que já aconteceu.

A planilha também não é consultável por outras ferramentas do time (scripts, bots, painéis), o que impede qualquer automação em cima dos prazos.

## A solução

Uma API REST, sem interface gráfica, com três capacidades:

- **Tarefas:** criar, editar e excluir tarefas, cada uma com título e prazo.
- **Tags:** etiquetar tarefas e filtrar por tag.
- **Prazos:** filtrar por prazo em três janelas: vencidas, hoje e próximos 7 dias.

A pergunta "o que está vencido?" passa a ser respondida com uma chamada.

## Para quem

**Devs de times pequenos** que hoje dividem uma planilha de tarefas. Eles se sentem à vontade chamando uma API por `curl` ou script e não precisam de tela para tirar valor da API.

Quem consome a API são scripts, bots e pequenas ferramentas internas escritas pelo próprio time.

## Critérios de sucesso

- Os três filtros de prazo retornam o conjunto correto de tarefas, com cobertura de testes automatizados.
- Um dev cria uma tarefa com tag e prazo e lista as vencidas em duas chamadas, guiado só pelos exemplos da documentação.
- O time-piloto deixa de abrir a planilha para descobrir o que está vencido.
- Como demonstração: o fluxo completo roda sem atalhos (brief, PRD, arquitetura, épicos e stories, primeira story com commit).

## Escopo

**Dentro da v1**

- Criar, editar e excluir tarefas
- Etiquetar tarefas e filtrar por tag
- Filtrar por prazo (vencidas, hoje, próximos 7 dias)

**Fora da v1**

- Usuários e permissões
- Interface gráfica
- Paginação da listagem (vai para o backlog)
- Notificações e lembretes de prazo
- Subtarefas e tarefas recorrentes

## Visão

Se a v1 der certo no time-piloto, os passos seguintes são a autenticação com suporte a vários times e os lembretes de prazo entregues onde o time já conversa (chat ou e-mail).
