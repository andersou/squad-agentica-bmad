---
title: "Product Brief: API de Tarefas"
status: final
created: 2026-10-06
updated: 2026-10-06
---

# Product Brief: API de Tarefas

## Resumo executivo

A API de Tarefas é uma API REST para times pequenos registrarem tarefas, etiquetá-las com tags, marcá-las como concluídas e filtrá-las por prazo. Ela substitui a planilha compartilhada em que hoje os prazos se perdem.

O escopo é pequeno de propósito. Este projeto serve de demonstração do BMad Method de ponta a ponta, do brief ao primeiro commit, e não pretende competir com Jira, Trello ou similares. Não há diferencial de mercado a defender. O valor está em resolver um problema real e bem delimitado, que cabe em dois épicos.

## O problema

Devs de times pequenos controlam tarefas e prazos em planilha e acabam perdendo prazos. A planilha não responde sozinha à pergunta que importa: o que está vencido e o que vence nos próximos 7 dias? Para saber, alguém precisa abrir o arquivo, ordenar e conferir linha a linha. Ninguém faz isso todo dia, então o atraso só aparece depois que já aconteceu.

A planilha também não pode ser consultada por outras ferramentas do time, como scripts, bots e painéis. Isso impede qualquer automação em cima dos prazos.

## A solução

A solução é uma API REST, sem interface gráfica, com três capacidades:

- **Tarefas:** criar, editar e excluir tarefas, cada uma com título e prazo. Marcar uma tarefa como concluída é uma edição como outra qualquer, sem operação separada.
- **Tags:** etiquetar tarefas e filtrar por tag.
- **Prazos:** filtrar as tarefas pendentes em três janelas que não se sobrepõem: vencidas, hoje e próximos 7 dias. Tarefas concluídas não aparecem em nenhuma dessas janelas.

Com isso, a pergunta "o que está vencido?" passa a ser respondida com uma chamada.

O prazo é uma data, sem hora. "Hoje" é calculado sempre no fuso America/Sao_Paulo, e não no fuso do servidor, para que a resposta não mude conforme o lugar em que a API roda. A API aceita prazo no passado: a tarefa já nasce vencida. É assim que o time traz para a API os atrasos que hoje estão na planilha.

## Para quem

O público são **devs de times pequenos** que hoje dividem uma planilha de tarefas. Eles se sentem à vontade chamando uma API por `curl` ou script e não precisam de tela para usá-la.

A API é consumida por scripts, bots e pequenas ferramentas internas escritas pelo próprio time, sempre dentro da rede interna.

## Critérios de sucesso

- Os três filtros de prazo retornam o conjunto correto de tarefas, inclusive nos limites (ontem, hoje, hoje+7 e hoje+8), e deixam de fora as concluídas. Testes automatizados cobrem esses casos.
- Guiado só pelos exemplos da documentação, um dev cria uma tarefa com tag e prazo e lista as vencidas em duas chamadas.
- O time-piloto deixa de abrir a planilha para descobrir o que está vencido. *Este critério é ilustrativo: o time-piloto é fictício, criado para a demonstração.*
- Como demonstração, o fluxo completo roda sem atalhos: brief, PRD, arquitetura, épicos e stories, até o commit da primeira story.

## Escopo

**Dentro da v1**

- Criar, editar e excluir tarefas, com prazo no passado aceito
- Marcar tarefas como concluídas, via edição
- Etiquetar tarefas (zero ou mais tags por tarefa) e filtrar por tag, inclusive combinando tag e janela de prazo na mesma chamada
- Filtrar tarefas pendentes por prazo (vencidas, hoje, próximos 7 dias)
- Rodar apenas na rede interna do time

**Fora da v1**

- Autenticação, usuários e permissões
- Interface gráfica
- Importação da planilha (o time recadastra as tarefas à mão)
- Paginação da listagem (vai para o backlog)
- Notificações e lembretes de prazo
- Subtarefas e tarefas recorrentes

## Visão

Se a v1 der certo no time-piloto, os próximos passos são autenticação com suporte a vários times e lembretes de prazo entregues onde o time já conversa, seja no chat, seja por e-mail.
