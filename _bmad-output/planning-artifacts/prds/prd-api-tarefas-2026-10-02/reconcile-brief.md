---
title: "Reconciliação brief x PRD: API de Tarefas"
created: 2026-10-02
inputs:
  - briefs/brief-api-tarefas-2026-10-02/brief.md
  - briefs/brief-api-tarefas-2026-10-02/addendum.md
  - briefs/brief-api-tarefas-2026-10-02/.memlog.md
  - prds/prd-api-tarefas-2026-10-02/prd.md
  - prds/prd-api-tarefas-2026-10-02/addendum.md
---

# Reconciliação brief x PRD: API de Tarefas

Fuso horário do filtro por prazo ficou fora desta análise de propósito (lacuna plantada para a demo, ver memlog).

## Resultado geral

O PRD cobre bem o brief. Escopo dentro e fora, os três critérios de sucesso de produto, o público, as pistas de contrato e a divisão em dois épicos aparecem todos, quase com a mesma redação. A decisão do memlog de deixar status/conclusão "para o PRD descobrir" foi cumprida (glossário, FR-3, alternativas no addendum). Nenhuma contradição direta. Seguem os desvios encontrados, do mais ao menos relevante.

## Lacunas e distorções

### 1. A visão de futuro do brief sumiu como seção (distorção)

- **Brief, Visão:** "Se a v1 der certo no time-piloto, os passos seguintes são a autenticação com suporte a vários times e os lembretes de prazo entregues onde o time já conversa (chat ou e-mail)."
- **PRD §1 "Visão":** a seção virou descrição do produto atual. A visão de futuro só sobra em fragmentos no §6.2 ("ficam para a visão multi-time", "ficam para a visão (chat ou e-mail)"), que citam uma "visão" que o PRD não escreve em lugar nenhum.
- **Perdido:** a condição "se a v1 der certo no time-piloto" (que liga a visão ao SM-3) e a ordem dos próximos passos.
- **Sugestão:** acrescentar ao §1 um parágrafo "Próximos passos" com a frase do brief, ou renomear o §1 e criar uma subseção de visão.

### 2. Peso do critério de demonstração rebaixado (distorção de intenção)

- **Brief:** os quatro critérios de sucesso estão no mesmo nível, e o memlog registra como decisão: "Propósito: artefato de demo da palestra (deve bater com os slides)".
- **PRD §7:** o fluxo BMad completo (SM-4) virou métrica "secundária".
- **Efeito:** para um artefato cujo propósito declarado é a demo, a métrica da demo ficou abaixo das métricas de produto. Também falta qualquer menção a "deve bater com os slides" como restrição.
- **Sugestão:** subir o SM-4 para primária, ou explicar no §0 por que ele é secundário. Registrar "coerência com os slides" como restrição no §0.

### 3. Escopo cresceu além das três capacidades do brief, em tensão com "bater com os slides" e com a SM-C1

- **Brief, A solução / Dentro da v1:** criar, editar, excluir; etiquetar e filtrar por tag; filtrar por prazo.
- **PRD acrescenta:** consulta por id e listagem (FR-2), marca de conclusão (FR-3), combinação tag + janela na mesma chamada (FR-8) e 404 em várias operações.
- A conclusão é defensável (o memlog pediu que o PRD decidisse). Já o FR-8 e a consulta por id não aparecem no brief, nem nas pistas de contrato vindas dos slides. A própria SM-C1 do PRD diz para não crescer o escopo.
- **Divisão em épicos:** o addendum do brief tem a story 1.1 só para "criar". O addendum do PRD põe listagem e consulta (FR-2) dentro da 1.1, e ela fica maior do que nos slides.
- **Sugestão:** marcar FR-8 como `[ASSUMPTION]` ou candidato a corte, e confirmar com os slides se a 1.1 da demo inclui listagem.

### 4. `due_date` "ISO 8601" estreitado para `YYYY-MM-DD` com rejeição 422 (estreitamento de contrato)

- **Addendum do brief:** "`due_date` aceita data em ISO 8601."
- **PRD:** prazo é "só uma data, sem hora" (`[ASSUMPTION]`), o addendum fixa `YYYY-MM-DD`, e o FR-1 manda 422 para "fora do formato de data". Um valor ISO 8601 válido com hora (`2026-10-02T10:00:00`) passa a ser rejeitado.
- A suposição está marcada, então é um desvio consciente. Mesmo assim, ela troca "aceita" por "só aceita". A decisão sobre aceitar e truncar ou rejeitar deve ser explícita.

### 5. "Próximos 7 dias" sem o dia de hoje (suposição a confirmar)

- **Brief:** três janelas: "vencidas, hoje e próximos 7 dias", sem definir limites.
- **PRD §3:** "próximos 7 dias" = de amanhã até hoje + 7, e exclui hoje (`[ASSUMPTION]`).
- É uma leitura razoável e está marcada, mas o uso comum ("o que vence nos próximos 7 dias?") costuma incluir hoje. O NFR-2 já testa esses limites, então basta confirmar a semântica com o usuário antes da arquitetura.

## Pontos menores (sem ação obrigatória)

- **Tom "não é Jira/Trello":** o brief diz explicitamente que o projeto não compete com Jira, Trello ou similares e não tem diferencial de mercado. O PRD guarda o "pequeno de propósito, rigor leve" (§0) e a SM-C1, mas perde a comparação explícita. É aceitável.
- **Inconsistência interna ligada ao SM-3:** o §6.2 põe a importação da planilha fora da v1, mas a questão aberta 1 (§8) ainda lista "uma importação na v1" como opção. O brief não fala do assunto, mas o SM-3 (o time-piloto larga a planilha) depende dessa resposta.
- **§1 do PRD diz "o atraso aparece antes de acontecer":** isso só vale se alguém consultar a API, porque os lembretes estão fora da v1. Não contradiz o brief, mas pode passar a impressão de que há aviso proativo.

## Itens verificados sem desvio

- Fora da v1: usuários e permissões, interface gráfica, paginação, notificações e lembretes, subtarefas e recorrência estão todos presentes.
- Critérios de sucesso de produto: SM-1, SM-2 e SM-3 reproduzem o brief.
- Público e consumidores (scripts, bots, ferramentas internas) estão presentes.
- Pistas de contrato (`POST/GET /tasks`, `title`, `due_date`, 201 com `id`, 422 para `title` vazio, sem paginação) estão presentes.
- "Cabe em dois épicos" (decisão do memlog) foi mantido.
- Termo único "vencido" (polish do memlog) foi respeitado.
