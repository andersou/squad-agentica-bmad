# Reconciliação: brief x PRD — API de Tarefas

- **Entrada:** `planning-artifacts/briefs/brief-api-tarefas-2026-10-06/brief.md`
- **PRD:** `planning-artifacts/prds/prd-api-tarefas-2026-10-06/prd.md`
- **Data:** 2026-10-06
- **Critério:** o PRD não precisa repetir a justificativa que já está no brief. As decisões tomadas depois pelo usuário (regras de tag, data ISO, edição parcial, exclusão definitiva, sem filtro concluída/pendente) contam como refinamentos, não como conflitos.

Legenda: **Completo** / **Parcial** / **Ausente** / **Contradito**

## Itens

| # | Tipo | Item do brief | PRD | Status | Observação |
|---|---|---|---|---|---|
| 1 | Ideia | API REST para times pequenos registrarem, etiquetarem, concluírem e filtrarem tarefas por prazo | §1 | Completo | |
| 2 | Ideia | Substitui a planilha compartilhada em que os prazos se perdem | §1, §2.1 | Completo | |
| 3 | Intenção | Escopo pequeno de propósito | §0, SM-C1 | Completo | |
| 4 | Intenção | Demonstração do BMad Method de ponta a ponta, do brief ao primeiro commit | §0, SM-4 | Completo | O PRD acrescenta "para slides", o que é um refinamento. |
| 5 | Intenção | Não compete com Jira/Trello, sem diferencial de mercado a defender | §6 (não-objetivo) | Completo | O "sem diferencial de mercado" fica implícito, o que é aceitável. |
| 6 | Restrição | Cabe em dois épicos | SM-C1 | Completo | |
| 7 | Problema | Planilha não responde sozinha ao que está vencido ou vence em 7 dias, e o atraso só aparece depois | §1, §2.1 | Completo | A justificativa fica no brief. |
| 8 | Problema | A planilha não é consultável por scripts, bots e painéis, o que impede automação | §1, §2.1 | Completo | |
| 9 | Requisito | API sem interface gráfica | §6 | Completo | |
| 10 | Requisito | Criar, editar e excluir tarefas com título e prazo | FR-1, FR-2, FR-3 | Completo | Refinamentos: edição parcial e exclusão definitiva. O PRD também acrescenta a listagem geral (FR-4). |
| 11 | Requisito | Concluir é uma edição comum, sem operação separada | §4.1, FR-2, UJ-3 | Completo | |
| 12 | Requisito | Etiquetar tarefas e filtrar por tag | FR-5 | Completo | Regras de tag acrescentadas pelo usuário (refinamento). |
| 13 | Requisito | Zero ou mais tags por tarefa | Glossário, §4.2 | Completo | |
| 14 | Requisito | Combinar tag e janela de prazo na mesma chamada | FR-5 | Completo | O PRD limita o filtro a uma tag por chamada. Refinamento compatível. |
| 15 | Requisito | Três janelas sem sobreposição: vencidas, hoje e próximos 7 dias | Glossário, FR-6 | Completo | As regras estão formalizadas em tabela. |
| 16 | Requisito | Concluídas ficam fora de todas as janelas | FR-2, FR-6 | Completo | |
| 17 | Requisito | Responder "o que está vencido?" em uma chamada | §1, §4.3 | Completo | |
| 18 | Restrição | Prazo é data, sem hora | Glossário | Completo | Refinamento: formato ISO `YYYY-MM-DD`. |
| 19 | Restrição | "Hoje" calculado no fuso America/Sao_Paulo, nunca no do servidor | Glossário, NFR-1, FR-6 | Completo | Inclui o caso das 22h em SP. |
| 20 | Requisito | Prazo no passado aceito, tarefa já nasce vencida | FR-1, UJ-1 | Completo | |
| 21 | Intenção | Prazo no passado serve para migrar os atrasos da planilha | UJ-1, §6 | Completo | |
| 22 | Público | Devs de times pequenos que dividem a planilha | §2, UJ | Completo | |
| 23 | Público | Usam `curl` ou script, sem precisar de tela | §6 | Completo | |
| 24 | Público | Consumida por scripts, bots e ferramentas internas do time | §1, §2.1, UJ-2 | Completo | |
| 25 | Restrição | Só rede interna | NFR-2 | Completo | |
| 26 | Sucesso | Filtros corretos nos limites (ontem, hoje, hoje+7, hoje+8), sem as concluídas, com testes automatizados | FR-6, NFR-3, SM-1 | Completo | O PRD acrescenta o caso "amanhã". |
| 27 | Sucesso | Seguindo só os exemplos da documentação, criar tarefa com tag e prazo e listar as vencidas em duas chamadas | SM-2, NFR-4 | Completo | |
| 28 | Sucesso | Time-piloto deixa de abrir a planilha (critério ilustrativo, time fictício) | SM-3, nota em §2.2 | Completo | O caráter ilustrativo foi mantido. |
| 29 | Sucesso | Fluxo completo sem atalhos: brief, PRD, arquitetura, épicos e stories, até o commit da 1ª story | SM-4 | Parcial | O SM-4 diz só "do brief ao commit da primeira story", sem listar as etapas intermediárias. Diferença mínima. |
| 30 | Fora | Autenticação, usuários e permissões | §6, NFR-2 | Completo | |
| 31 | Fora | Interface gráfica | §6 | Completo | |
| 32 | Fora | Importação da planilha, com recadastro à mão | §6, UJ-1 | Completo | |
| 33 | Fora | Paginação, que vai para o backlog | FR-4, §6 | Completo | |
| 34 | Fora | Notificações e lembretes | §6 | Completo | |
| 35 | Fora | Subtarefas e tarefas recorrentes | §6 | Completo | O PRD acrescenta "campos extras" e "várias tags por filtro" (refinamento). |
| 36 | Visão | Condicional: só se a v1 der certo no time-piloto | — | Ausente | O PRD não registra essa condição. |
| 37 | Visão | Autenticação com suporte a vários times | §6 ("ficam para a visão") | Parcial | Aparece só como remissão dentro do escopo. A §1 "Visão" do PRD descreve o produto atual, não o futuro. |
| 38 | Visão | Lembretes entregues onde o time conversa (chat, e-mail) | §6 ("ficam para a visão") | Parcial | Os canais (chat, e-mail) não aparecem. |

## Refinamentos do usuário (sem conflito)

- **Regras de tag** (FR-5): trim, sem distinção de maiúsculas e minúsculas, deduplicação, rejeição de tag vazia, substituição da lista na edição, uma tag por filtro. Tudo compatível com "zero ou mais tags".
- **Data ISO** `YYYY-MM-DD` e validação de datas inexistentes (FR-1). Compatível com "data sem hora".
- **Edição parcial** (FR-2). Compatível.
- **Exclusão definitiva** (FR-3). Compatível.
- **Sem filtro concluída/pendente** na listagem geral (FR-4). O brief não pedia esse filtro, então não há conflito.
- O PRD acrescenta a listagem geral (FR-4) e a ordenação por prazo. O brief não as citava, mas elas são necessárias para "filtrar por tag" fora das janelas.

## Lacunas

1. **A visão futura ficou só como remissão.** O PRD diz que autenticação e lembretes "ficam para a visão", mas nenhum documento downstream registra essa visão: a condição "se a v1 der certo no time-piloto", o "suporte a vários times" (citado só de passagem) e os canais de lembrete (chat, e-mail). A §1 "Visão" do PRD trata do produto atual. Impacto baixo para a v1, mas o conteúdo só existe no brief.
2. **Referência a um addendum inexistente.** A §0 diz que o PRD "parte do brief e do addendum", mas nenhum addendum existe (por decisão deliberada). Isso não é lacuna de conteúdo, mas a referência fica pendurada e pode confundir a arquitetura.
3. **O SM-4 omite as etapas do fluxo** (PRD, arquitetura, épicos e stories). Diferença mínima, já coberta por "sem atalhos".

Nenhuma contradição encontrada.
