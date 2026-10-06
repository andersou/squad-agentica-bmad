# PRD Quality Review — PRD: API de Tarefas

## Overall verdict
É um PRD enxuto e bem calibrado para o que se propõe: uma demo de baixo risco com tese clara ("responder em uma chamada o que está vencido") e FRs com consequências testáveis. O ponto alto é o FR-6, com a tabela de regras e os casos-limite fixados. Os riscos são pequenos e localizados: não existe forma de listar só as pendentes com prazo além de 7 dias, a persistência dos dados fica implícita e alguns detalhes de contrato (códigos de sucesso, desempate na ordenação, parâmetros de filtro inválidos) vão ser decididos na arquitetura sem orientação. Nada disso bloqueia a v1.

## Decision-readiness — strong
As decisões aparecem como decisões: concluir é editar, sem operação separada (§4.1); edição parcial (FR-2); "enviar tags substitui a lista inteira" (FR-5); "A lista vem inteira, sem paginação" (FR-4); sem autenticação, com a justificativa explícita de que "só é aceitável por causa dessa exposição limitada" (NFR-2). As renúncias estão no §6, cada uma com destino ("Fica no backlog", "Ficam para a visão").

Há uma renúncia que foi decidida sem que o custo aparecesse. O FR-4 diz que "As janelas de prazo cumprem esse papel" do filtro por pendente, mas as três janelas param em `hoje + 7`.

### Findings
- **[medium]** Sem forma de listar todas as pendentes (§4.1 FR-4, §4.3 FR-6) — "Não há filtro por concluída ou pendente. As janelas de prazo cumprem esse papel" só vale até `hoje + 7`. Uma tarefa pendente com prazo daqui a 30 dias só aparece na listagem geral, misturada com as concluídas. O PRD não registra que abriu mão disso. *Fix:* assumir a renúncia no §6 ("listar pendentes além de 7 dias: fora da v1, use a listagem geral") ou ajustar a frase do FR-4 para não prometer cobertura total.

## Substance over theater — strong
Há uma persona só, fictícia e declarada como tal (§2.2), e ela sustenta decisões concretas: o prazo no passado (UJ-1 → FR-1), o filtro tag + janela (UJ-2 → FR-5/FR-6) e a concluída que sai das janelas (UJ-3 → FR-2). A Visão (§1) é específica do produto, porque nomeia a pergunta que a planilha não responde. Os NFRs têm conteúdo próprio do produto (fuso fixo, rede interna) e não são boilerplate. O SM-3 é marcado honestamente como "ilustrativa" e o SM-4 como "(demo)", sem fingir que são métricas de produto.

### Findings
- **[low]** NFR-3 e SM-1 dizem a mesma coisa (§5, §7) — os dois são "testes automatizados cobrem os casos-limite do FR-6". Como métrica de sucesso, o SM-1 mede se o build passou, não se a tese se confirmou. *Fix:* manter só o NFR-3 ou fazer o SM-1 apenas referenciá-lo. Para uma demo, a duplicação é tolerável.

## Strategic coherence — strong
A tese está no §1: substituir a planilha respondendo em uma chamada o que está vencido, vence hoje e vence em 7 dias. Tudo no PRD segue dela. O CRUD (FR-1–4) é o mínimo necessário, as tags (FR-5) existem para o recorte "vencidas de `backend`", e as janelas (FR-6) são o núcleo. O MVP é do tipo problem-solving, e a lista de fora da v1 combina com isso. O SM-2 valida a tese de verdade: duas chamadas, guiadas só pela documentação.

### Findings
- **[low]** A contramétrica protege o escopo, não as métricas (§7 SM-C1) — "número de funcionalidades" segura a tentação de crescer o escopo, mas não protege contra um efeito colateral de otimizar SM-1/SM-2. Para uma demo, é uma escolha razoável e deliberada. *Fix:* nenhum necessário. Se quiser, renomear para "guarda de escopo".

## Done-ness clarity — adequate
A maior parte dos FRs é testável sem interpretação: os 422 específicos (FR-1, FR-5), os 404 (FR-2, FR-3), a tabela de janelas e os cinco casos-limite enumerados (FR-6), além do caso 22h SP / 01h UTC. Não aparece nenhum "gracefully" ou "performance razoável".

As lacunas estão na borda do contrato e não no comportamento central. O engenheiro vai precisar decidir sozinho os pontos abaixo.

### Findings
- **[medium]** Persistência não especificada (§1, §5) — a API "substitui a planilha", mas nenhum NFR diz que as tarefas sobrevivem a um reinício. Um armazenamento em memória cumpriria todos os FRs e não cumpriria a Visão. *Fix:* acrescentar um NFR curto, algo como "as tarefas persistem entre reinícios da API".
- **[low]** Desempate na ordenação não definido (§4.1 FR-4, §4.3 FR-6) — "ordenada por prazo" deixa a ordem indefinida entre tarefas com o mesmo prazo, o que torna os testes de lista não determinísticos. *Fix:* definir o critério secundário (por exemplo, ordem de criação ou identificador).
- **[low]** Parâmetros de filtro inválidos sem consequência (FR-5, FR-6) — não está definido o que acontece com uma janela inexistente, com uma tag vazia no filtro ou com mais de uma tag ("Cada chamada aceita uma única tag" não diz se a segunda é ignorada ou rejeitada). *Fix:* uma linha cada, por exemplo "valor de janela desconhecido → 422".
- **[low]** Códigos de sucesso e limites ausentes (FR-1, FR-2, FR-3) — só os erros têm código. A criação "devolve a tarefa criada", mas o status (201?) não está definido, nem o retorno da exclusão. Também não há tamanho máximo para título e tag, nem regra para `concluída` não booleana. *Fix:* deixar explícito que esses pontos ficam para a arquitetura ou fixá-los aqui.

## Scope honesty — strong
O §6 faz trabalho de verdade: sete exclusões concretas, cada uma com motivo ou destino, mais o não-objetivo "competir com Jira, Trello". O §8 "Nenhuma questão bloqueia a v1" é crível para os stakes. A densidade de itens em aberto é zero (sem `[ASSUMPTION]`, sem `[NOTE FOR PM]`), o que combina com um escopo fechado e de baixo risco.

A exceção é a persistência (ver Done-ness), que fica como suposição implícita sem tag.

### Findings
- Nenhum além dos já registrados em Decision-readiness e Done-ness.

## Downstream usability — strong
O PRD alimenta arquitetura e épicos/stories (§0) e está pronto para isso. O Glossário (§3) é usado de forma consistente: "janela de prazo", "pendente" e "listagem geral" aparecem com a mesma grafia nos FRs, nas UJs e nas SMs. Os IDs são contíguos (FR-1–6, UJ-1–3, NFR-1–4, SM-1–4 + SM-C1), as referências resolvem e cada UJ tem protagonista nomeado. Cada FR se sustenta sozinho e referencia outros por ID ("mesmas validações do FR-1", "(FR-6)"), não por "ver acima".

### Findings
- **[low]** "Hoje" sobrecarregado (§3, §4.3) — "Hoje" é ao mesmo tempo um termo do glossário (a data corrente em SP) e o nome de uma janela. Frases como "a janela hoje" versus "prazo = hoje" podem confundir na extração de stories. *Fix:* chamar a janela de "vence hoje" ou grafá-la sempre como "janela **hoje**".

## Shape fit — strong
É uma ferramenta interna com uma persona-operadora, e o PRD tem o formato de especificação de capacidades: as UJs são de uma linha (como pretendido), os FRs com consequências carregam o peso e as SMs são operacionais. Não há formalização demais nem de menos para o tamanho de duas páginas.

### Findings
- Nenhum.

## Mechanical notes
- IDs contíguos e únicos, sem referências quebradas. As UJs são citadas nos FRs/funcionalidades (FR-3 e FR-4 não citam UJ, o que é aceitável porque não há jornada de exclusão).
- O §0 referencia o brief e o addendum do brief em `planning-artifacts/briefs/brief-api-tarefas-2026-10-06/`. Os dois existem. A ausência de addendum do PRD é deliberada.
- Não há `[ASSUMPTION]` e, por isso, não há Assumptions Index. Isso é consistente, nada a conciliar.
- Termos de ator fora do glossário: "dev" e "time-piloto". São óbvios no contexto, então a deriva é baixa.
- Frontmatter `status: draft`: lembrar de atualizar quando o PRD for aprovado.
