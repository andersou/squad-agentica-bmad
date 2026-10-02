# PRD Quality Review — PRD: API de Tarefas

Calibração: PRD de demonstração (palestra), escopo pequeno e rigor leve declarados no §0. A régua abaixo é a de um PRD curto que alimenta arquitetura e stories, não a de um produto com muitos stakeholders.

## Overall verdict
O PRD é enxuto e coerente: a tese (substituir a planilha pela pergunta "o que está vencido / vence hoje / vence em 7 dias" em uma chamada) organiza as funcionalidades, as métricas e a contramétrica, e as janelas de prazo estão definidas com precisão de limite (§3, NFR-2). Está pronto para seguir para a arquitetura. Os riscos estão em pontos de "done" que as stories vão precisar decidir: semântica da edição (parcial ou substituição, e o que acontece com `tags` omitido) e a regra de comparação de tags. A SM-3 também não tem forma de medição.

## Decision-readiness — strong
As decisões aparecem como decisões, não como "considerações": janelas sem sobreposição (§3, "as três janelas não se sobrepõem"), conclusão por edição em vez de endpoint próprio (FR-3), sem paginação (FR-2, §6.2), sem autenticação compensada por rede interna (NFR-5). O addendum registra a alternativa descartada e o motivo ("Alternativas consideradas": endpoint `/complete` e status com vários valores). A única questão em aberto (§8) é de fato aberta e tem responsável ("Anderson") e prazo ("antes de quebrar os épicos").

Não há callouts `[NOTE FOR PM]`. Para o porte do documento, isso não faz falta.

## Substance over theater — strong
Uma persona (Rafa, UJ-1), e ela orienta decisões reais: `curl`, exemplos na documentação (NFR-1), script diário (FR-7). A Visão (§1) é específica ao problema da planilha e não serviria para outro PRD. Os NFRs têm conteúdo concreto. Exemplo: NFR-2 lista os limites testáveis "ontem, hoje, amanhã, hoje + 7 e hoje + 8". Não há seção de diferenciação nem NFR genérico de "escalável/seguro".

## Strategic coherence — strong
A tese está explícita: o §4.3 diz que as janelas de prazo são "o valor central do produto", e o escopo segue a tese. CRUD e tags existem para alimentar FR-7/FR-8. SM-1 e SM-2 validam a tese, e a SM-C1 é uma contramétrica de verdade, ligada a uma métrica primária ("Contrabalança SM-3"). A SM-4 é uma métrica de meta-demonstração, legítima pelo §0.

### Findings
- **medium** SM-3 sem forma de medição (§7, SM-3) — "o time-piloto deixa de abrir a planilha para descobrir o que está vencido" não tem prazo nem método de verificação, e é a única métrica que valida o produto como um todo. *Fix:* acrescentar critério e janela, por exemplo "após 2 semanas de uso, o time-piloto confirma na retro que a daily usa só a API".
- **low** SM-1 repete o NFR-2 (§7, SM-1) — "testes automatizados passando" é critério de entrega, não resultado. *Fix:* aceitável para a demo. Se quiser diferenciar, deixe a SM-1 só como referência ao NFR-2.

## Done-ness clarity — adequate
Os FRs têm consequências testáveis com códigos HTTP (201/404/422), e as janelas são definidas por limites exatos no Glossário. FR-7 e FR-8 estão bem fechados. As lacunas estão em FR-3/FR-5/FR-6, onde a story vai precisar inventar regras.

### Findings
- **medium** Semântica da edição ambígua (§4.1 FR-3; §4.2 FR-5) — FR-3 fala em "campos alterados" (sugere edição parcial), e FR-5 diz que "a lista de tags enviada substitui a anterior". Não está definido o que acontece quando a edição não envia `tags`: mantém ou apaga? *Fix:* declarar que a edição é parcial e que campo omitido não muda, e que `tags: []` limpa as tags.
- **medium** Regra de comparação de tags indefinida (§3 Tag; FR-5; FR-6) — "texto livre" sem dizer se `Backend` e `backend` são a mesma tag, se espaços são removidos ou se tag vazia é aceita. O FR-6 ("exatamente as tarefas que têm a tag informada") e a deduplicação do FR-5 dependem disso. *Fix:* uma linha no Glossário, por exemplo "comparação sensível a maiúsculas, sem espaços nas pontas, tag vazia → 422", ou a regra que for escolhida.
- **low** Prazo no passado na criação (FR-1) — fica implícito que é aceito (a janela "Vencidas" depende disso), mas isso não está escrito. Uma validação "prazo >= hoje" seria um erro plausível na implementação. *Fix:* acrescentar "prazo no passado é aceito" às consequências do FR-1.
- **low** Ordem dos resultados não especificada (FR-2, FR-7) — scripts e painéis (JTBD §2.1) costumam supor uma ordem. *Fix:* "ordenadas por prazo crescente" ou "ordem não garantida".
- **low (conhecida/intencional)** Fuso horário de "hoje" (§3, Janela de prazo) — "hoje" não diz de qual relógio (servidor, UTC, time). Lacuna plantada de propósito para a verificação de prontidão. Registrada aqui só por completude. *Fix:* nenhum agora.

## Scope honesty — strong
O §6.2 faz trabalho real: cada omissão tem motivo (paginação "o volume de um time pequeno não exige", auth "fica para a visão multi-time"). As suposições estão marcadas no texto e indexadas (§9). A densidade de itens abertos (1 questão + 5 suposições) é baixa e compatível com o porte do PRD. A importação da planilha aparece ao mesmo tempo como fora de escopo (§6.2) e como questão em aberto (§8), e as duas referências se ligam explicitamente ("ver §8").

## Downstream usability — strong
O Glossário está presente e é usado de forma consistente ("janela de prazo", "concluída", "tag"). FR-1..8, NFR-1..5 e SM-1..4 + SM-C1 são contíguos, e as referências cruzadas resolvem. O addendum dá pistas de contrato (`due_date`, `?due=overdue|today|next7`) marcadas como "a confirmar na arquitetura", que é o lugar certo para elas, e uma divisão em épicos que cobre FR-1..8 sem buracos.

### Findings
- **low** NFR-3 sem formato de erro (§5, NFR-3) — "mesmo formato" e "diz qual campo" são suficientes como requisito, mas o addendum não sugere um formato, então a arquitetura vai decidir isso sozinha. *Fix:* opcional, uma pista no addendum (por exemplo `{ "error": ..., "field": ... }`).

## Shape fit — strong
Serviço interno, sem UI e com um tipo de usuário: o formato de spec de capacidades com uma única UJ de protagonista nomeado é o correto. Não há excesso de formalização (nada de várias personas ou jornadas), e a UJ-1 está ligada a todas as funcionalidades ("Realiza UJ-1").

## Mechanical notes
- Roundtrip de suposições ok: 5 tags inline (§3 Prazo, §3 Próximos 7 dias, FR-3, FR-5, NFR-5) ↔ 5 entradas no §9.
- FR-5 e NFR-5 usam `[ASSUMPTION]` sem texto inline. O conteúdo só está no §9. Pequena inconsistência com as outras três tags, que trazem o texto.
- "time-piloto" (SM-3, §8) aparece sem introdução. A UJ-1 fala em "time de quatro pessoas". Vale um termo no Glossário ou uma menção na UJ.
- IDs contíguos e sem duplicatas. Seções obrigatórias presentes para o porte declarado.
