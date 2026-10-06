---
title: "Reconciliação: addendum do brief x PRD"
created: 2026-10-06
input: planning-artifacts/briefs/brief-api-tarefas-2026-10-06/addendum.md
prd: planning-artifacts/prds/prd-api-tarefas-2026-10-06/prd.md
---

# Reconciliação: addendum do brief x PRD

Legenda de cobertura: **completo**, **parcial**, **ausente**, **contradito**.

## Itens extraídos do addendum

| # | Seção do addendum | Item (regra, caso-limite, restrição ou justificativa) | Onde no PRD | Cobertura |
|---|---|---|---|---|
| 1 | Janelas | Prazo é só data (dia), sem hora | §3 Glossário "Prazo" (ISO `YYYY-MM-DD`, sem hora) | completo |
| 2 | Janelas | "Hoje" = data corrente no fuso fixo America/Sao_Paulo | §3 "Hoje"; NFR-1 | completo |
| 3 | Janelas | Independe do fuso do servidor | §3 "Hoje"; NFR-1 | completo |
| 4 | Janelas | As janelas não se sobrepõem | §3 "Janela de prazo" | completo |
| 5 | Janelas | Janelas consideram só tarefas não concluídas | §3 "Janela de prazo" (pendentes); §4.3; FR-6 | completo |
| 6 | Janelas | Vencidas: `prazo < hoje` | FR-6, tabela | completo |
| 7 | Janelas | Hoje: `prazo = hoje` | FR-6, tabela | completo |
| 8 | Janelas | Próximos 7 dias: `hoje + 1 <= prazo <= hoje + 7` | FR-6, tabela | completo |
| 9 | Casos-limite | Testes devem cobrir prazo = ontem | FR-6 (cai em vencidas); NFR-3; SM-1 | completo |
| 10 | Casos-limite | Prazo = hoje | FR-6 (cai em hoje); NFR-3 | completo |
| 11 | Casos-limite | Prazo = amanhã | FR-6 (cai em próximos 7 dias); NFR-3 | completo |
| 12 | Casos-limite | Prazo = hoje + 7 | FR-6 (cai em próximos 7 dias); NFR-3 | completo |
| 13 | Casos-limite | Prazo = hoje + 8 | FR-6 (nenhuma janela); NFR-3 | completo |
| 14 | Casos-limite | Tarefa concluída com prazo vencido | FR-6 (não aparece em nenhuma janela); NFR-3 | completo |
| 15 | Casos-limite | Dia já virou em UTC mas não em SP (22h SP = 01h UTC do dia seguinte) | FR-6 ("hoje continua sendo a data de São Paulo"); NFR-1; NFR-3 | completo (ver observação O1) |
| 16 | Casos-limite | A cobertura desses casos é obrigação dos testes automatizados | NFR-3; SM-1 | completo |
| 17 | Prazo no passado | API aceita criar tarefa com prazo no passado | §3 "Prazo"; FR-1 | completo |
| 18 | Prazo no passado | A tarefa já nasce vencida | FR-1 ("entra na janela vencidas logo na criação"); UJ-1 | completo |
| 19 | Prazo no passado | Justificativa: viabiliza recadastro manual dos atrasos, pois a importação ficou fora da v1 | UJ-1; §6 "Importação da planilha" | completo |
| 20 | Concluídas | Concluída é atributo da tarefa, alterado pela edição | §3 "Concluída"; §4.1; FR-2 | completo |
| 21 | Concluídas | Não existe endpoint separado para concluir | §4.1 ("Não há operação separada para isso") | completo |
| 22 | Concluídas | Concluídas continuam existindo e podem ser listadas | §3 "Listagem geral"; FR-4; UJ-3 | completo |
| 23 | Concluídas | Concluídas não aparecem nas janelas | FR-2; FR-6; UJ-3 | completo |
| 24 | Tags | Cada tarefa tem zero ou mais tags | §3 "Tarefa"; §4.2 | completo |
| 25 | Tags | Filtro por tag combinável com janela na mesma chamada (ex.: vencidas + `backend`) | FR-5; UJ-2 | completo |
| 26 | Implantação | v1 roda só na rede interna do time | NFR-2 | completo |
| 27 | Implantação | Sem autenticação | NFR-2; §6 | completo |
| 28 | Implantação | Justificativa: falta de controle de acesso só é aceitável pela exposição limitada | NFR-2 | completo |

## Lacunas

Nenhuma lacuna relevante. Nenhum item do addendum está ausente ou contradito no PRD.

### Observações menores (não bloqueiam)

- **O1. Caso do fuso sem resultado esperado explícito.** O FR-6 afirma que às 22h em SP "hoje continua sendo a data de São Paulo", mas não diz em que janela cai uma tarefa nesse instante (ex.: prazo = data de SP aparece em "hoje", não em "vencidas"; prazo = data UTC seguinte aparece em "próximos 7 dias", não em "hoje"). O resultado decorre das regras, mas explicitá-lo deixaria o teste tão direto quanto os outros casos-limite.
- **O2. Testabilidade do relógio.** Os casos-limite exigem fixar "hoje" e o instante UTC nos testes. O PRD não precisa dizer como; fica para a arquitetura (relógio injetável ou equivalente).

### Itens do PRD sem origem no addendum (acréscimos, não conflitos)

Validações 422 de título, prazo e tag; data inexistente rejeitada; edição parcial; desligar concluída devolve a tarefa às janelas; tags sem diferenciar maiúsculas, com trim e deduplicação; filtro de uma única tag por chamada; ordenação por prazo; sem paginação; exclusão definitiva e 404. Nenhum contradiz o addendum.
