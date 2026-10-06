---
title: "Addendum: API de Tarefas"
created: 2026-10-06
updated: 2026-10-06
---

# Addendum: API de Tarefas

Este documento reúne detalhes que servem de entrada para o PRD e para a arquitetura, mas que não cabem no brief.

## Semântica das janelas de prazo

- O prazo é só uma data (dia), sem hora.
- "Hoje" é a data corrente no fuso fixo **America/Sao_Paulo**, independentemente do fuso do servidor.
- As janelas não se sobrepõem e consideram apenas tarefas **não concluídas**:

| Janela | Regra |
|---|---|
| Vencidas | `prazo < hoje` |
| Hoje | `prazo = hoje` |
| Próximos 7 dias | `hoje + 1 <= prazo <= hoje + 7` |

Casos-limite que os testes devem cobrir:

- prazo = ontem, hoje, amanhã, hoje + 7 e hoje + 8;
- tarefa concluída com prazo vencido;
- horário em que o dia já virou em UTC, mas ainda não em São Paulo (ex.: 22h em São Paulo = 01h UTC do dia seguinte).

### Prazo no passado

A API aceita criar tarefas com prazo no passado, e elas já nascem vencidas. Isso viabiliza o recadastro manual das tarefas atrasadas da planilha, já que a importação ficou fora da v1.

## Tarefas concluídas

- A marca de concluída é um atributo da tarefa, alterado pela operação de edição, como os demais atributos. Não existe endpoint separado para concluir uma tarefa.
- Tarefas concluídas continuam existindo e podem ser listadas, mas não aparecem nas janelas de prazo.

## Tags

- Cada tarefa tem zero ou mais tags.
- O filtro por tag pode ser combinado com uma janela de prazo na mesma chamada. Exemplo: tarefas vencidas com a tag `backend`.

## Implantação

A v1 roda apenas na rede interna do time, sem autenticação. A falta de controle de acesso é aceitável só porque a exposição é limitada a essa rede.
