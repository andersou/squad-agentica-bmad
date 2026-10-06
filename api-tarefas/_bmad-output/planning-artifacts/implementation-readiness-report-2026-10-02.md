---
stepsCompleted: [step-01-document-discovery, step-02-prd-analysis, step-03-epic-coverage-validation, step-04-ux-alignment, step-05-epic-quality-review, step-06-final-assessment]
includedFiles:
  - _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/prd.md
  - _bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-02/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-02/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/epics.md
---

# Implementation Readiness Assessment Report

**Date:** 2026-10-02
**Project:** api-tarefas

## Inventário de documentos

| Tipo | Arquivo | Observação |
| --- | --- | --- |
| PRD | `prds/prd-api-tarefas-2026-10-02/prd.md` + `addendum.md` | final |
| Arquitetura | `architecture/architecture-api-tarefas-2026-10-02/ARCHITECTURE-SPINE.md` | final; `reviews/` excluído |
| Épicos e stories | `epics.md` | 2 épicos, 5 stories |
| UX | — | não se aplica (API sem interface) |

Sem duplicatas e sem documentos obrigatórios faltando.

## Análise do PRD

### Requisitos funcionais

- **FR1:** O dev cria uma tarefa informando título, prazo e, se quiser, tags.
  - Uma criação válida retorna 201 com o identificador.
  - Título ausente ou vazio → 422, e nenhuma tarefa é criada.
  - Prazo ausente ou fora do formato de data ISO 8601 → 422, e nenhuma tarefa é criada.
  - Prazo no passado é aceito, e a tarefa já nasce vencida.
  - A tarefa nasce não concluída.
- **FR2:** O dev lista todas as tarefas ou consulta uma pelo identificador.
  - A listagem sem filtros traz todas as tarefas, concluídas ou não, sem paginação.
  - Toda listagem, com ou sem filtros, vem ordenada por prazo, do mais antigo ao mais distante.
  - Cada tarefa traz identificador, título, prazo, tags e marca de conclusão.
  - Identificador inexistente → 404.
- **FR3:** O dev altera título, prazo e tags e marca ou desmarca a tarefa como concluída.
  - Só os campos enviados mudam.
  - Valem as validações do FR1.
  - Tarefa inexistente → 404.
  - Uma tarefa concluída sai de todas as janelas de prazo.
- **FR4:** O dev exclui uma tarefa.
  - Depois disso, consultar dá 404 e ela não aparece em nenhuma listagem.
  - Tarefa inexistente → 404.
- **FR5:** O dev atribui zero ou mais tags na criação ou na edição.
  - A tag passa a existir no primeiro uso.
  - Espaços nas pontas são removidos e maiúsculas e minúsculas não se distinguem.
  - Repetições são guardadas uma vez.
  - Tag vazia ou só com espaços → 422.
  - Uma lista enviada na edição substitui a anterior; se a edição não envia tags, elas não mudam.
- **FR6:** O dev filtra por tag, pela regra de comparação do Glossário. Tag sem uso → lista vazia, não erro.
- **FR7:** O dev filtra por janela de prazo (vencidas, hoje, próximos 7 dias).
  - Cada janela retorna exatamente o que o Glossário define, com "hoje" em `America/Sao_Paulo`.
  - Tarefas concluídas nunca aparecem.
  - Janela inexistente → 422.
- **FR8:** O dev combina tag e janela de prazo na mesma chamada. O resultado é a interseção.

**Total de FRs: 8**

### Requisitos não funcionais

- **NFR1. Documentação por exemplos:** exemplos (como `curl`) de criar uma tarefa com tag e prazo e de listar as vencidas.
- **NFR2. Testes dos filtros:** testes automatizados das três janelas e da combinação com tag, com os limites (ontem, hoje, amanhã, hoje + 7, hoje + 8) e a virada do dia em `America/Sao_Paulo` com o servidor em outro fuso.
- **NFR3. Erros previsíveis:** toda resposta de erro (404, 422) tem o mesmo formato e diz qual campo ou parâmetro causou o erro.
- **NFR4. Persistência:** as tarefas sobrevivem ao reinício do serviço.
- **NFR5. Rede interna:** sem autenticação, a API só fica acessível na rede interna do time.

**Total de NFRs: 5**

### Requisitos adicionais

**Glossário:**
- Prazo é só data, sem hora.
- As três janelas não se sobrepõem: próximos 7 dias vai de amanhã a hoje + 7.
- Tarefa concluída continua existindo.

**Escopo fora da v1:** autenticação, interface, paginação, lembretes, fuso por time ou requisição, subtarefas, recorrência, importação da planilha e competir com Jira ou Trello.

**Métricas:**
- SM-1: filtros corretos com testes.
- SM-2: duas chamadas guiadas pela documentação.
- SM-3: 4 semanas sem abrir a planilha.
- SM-4: o fluxo BMad completo.
- Contramétrica SM-C1: número de funcionalidades e endpoints.

**Addendum:**
- Contrato `POST /tasks` 201/422.
- Campos `title`, `due_date`.
- `GET /tasks` sem paginação.
- Fuso fixo no servidor.
- Épicos previstos.

### Avaliação de completude do PRD

O PRD está completo e claro para a v1:
- Todo FR tem consequências testáveis.
- O Glossário fixa os termos que os filtros dependem.
- As janelas têm definição exata e o fuso foi decidido.

Uma inconsistência pequena: o §8 ainda lista como aberta a questão da importação da planilha. Ela foi resolvida (fica fora dos épicos) no memlog do PRD durante a quebra em épicos, mas o texto do PRD não foi atualizado.

## Validação da cobertura pelos épicos

### Matriz de cobertura

| FR | Requisito do PRD (resumo) | Cobertura | Status |
| --- | --- | --- | --- |
| FR1 | Criar tarefa; 201; 422 em título e prazo; prazo passado aceito; nasce não concluída | Épico 1, Story 1.1 (tags na criação: Story 2.1) | ✓ Coberto |
| FR2 | Listar sem paginação, ordenado por prazo; consultar; 404 | Story 1.1; ordem com filtro em 2.1 e 2.2 | ✓ Coberto |
| FR3 | Edição parcial; validações; 404; concluir e desmarcar; sai das janelas | Story 1.2; tags em 2.1; saída das janelas em 2.2 | ✓ Coberto |
| FR4 | Excluir; 404 depois; 404 se inexistente | Story 1.3; cascata das tags em 2.1 | ✓ Coberto |
| FR5 | Tags no uso, normalizadas, sem repetição; vazia → 422; substituição na edição | Épico 2, Story 2.1 | ✓ Coberto |
| FR6 | Filtro por tag; tag sem uso → `[]` | Story 2.1 | ✓ Coberto |
| FR7 | Três janelas em São Paulo; concluídas fora; janela inválida → 422 | Story 2.2 | ✓ Coberto |
| FR8 | Interseção de tag e janela | Story 2.2 | ✓ Coberto |

| NFR | Cobertura | Status |
| --- | --- | --- |
| NFR1 | README com `curl` em 1.1; "duas chamadas" em 2.2 | ✓ |
| NFR2 | Story 2.2: limites de 10-01 a 10-10 e virada `2026-10-03T01:00Z`; fixtures na 1.1 | ✓ |
| NFR3 | Story 1.1 (envelope do AD-7, inclusive 404 e 405 de rota); `field` conferido em todas as stories | ✓ |
| NFR4 | Story 1.1 (reinício com o mesmo `TASKS_DB_PATH`) | ✓ |
| NFR5 | Story 1.1 (README de deploy com `--host <IP interno>`) | ✓ (só documentação; não é testável automaticamente) |

### Requisitos sem cobertura

Nenhum FR ou NFR ficou sem cobertura. Não há FR nos épicos que não exista no PRD.

As métricas SM-3 (4 semanas sem a planilha) e SM-4 (fluxo BMad completo) são operacionais e não viram story, o que é esperado.

### Estatísticas de cobertura

- Total de FRs no PRD: 8
- FRs cobertos pelos épicos: 8
- Cobertura: 100%

## Alinhamento de UX

### Status do documento de UX

Não encontrado, e não é necessário. O PRD exclui a interface gráfica de forma explícita (§6.2): o público usa `curl` e scripts. Não há componente web nem mobile implícito.

### Problemas de alinhamento

Nenhum. A "experiência" deste produto é a do dev que chama a API, e ela já está coberta pelos outros documentos:
- documentação com exemplos (NFR1, SM-2);
- envelope de erro com `field` e mensagem em português (NFR3, AD-7);
- nomes em inglês e `snake_case` (convenções da arquitetura).

### Alertas

Nenhum.

## Revisão de qualidade dos épicos

### Estrutura dos épicos

| Verificação | Épico 1: Registrar e manter tarefas | Épico 2: Saber o que venceu e o que vence |
| --- | --- | --- |
| Entrega valor ao usuário | ✓ guardar tarefas fora da planilha, consultáveis por script | ✓ a pergunta central do produto |
| Funciona sozinho | ✓ | ✓ depende só do Épico 1 |
| Stories com tamanho adequado | ⚠️ a 1.1 é grande (ver M1) | ✓ |
| Sem dependências futuras | ✓ | ✓ |
| Tabelas criadas quando necessárias | ⚠️ desvio aceito (ver M2) | ✓ |
| Critérios de aceite claros (Given/When/Then) | ✓ | ✓ |
| Rastreabilidade a FRs | ✓ | ✓ |

**Dependências:**
- **Dentro do Épico 1:** a 1.2 e a 1.3 usam só o que a 1.1 entrega. A 1.2 não depende da 1.3.
- **Dentro do Épico 2:** a 2.2 usa a normalização e o filtro por tag da 2.1 para cumprir o FR8.
- **Nenhuma referência à frente:** o FR3 diz que uma tarefa concluída "sai das janelas", e isso só é verificado na 2.2. Não é dependência futura: a 1.2 grava `done`, e a 2.2 consome esse dado.

### 🔴 Violações críticas

Nenhuma.

### 🟠 Problemas maiores

**M1. A story 1.1 junta muita coisa.** Na mesma story ficam:
- o setup do projeto `uv`;
- `POST`, listagem e consulta;
- os três handlers globais com cinco códigos de erro;
- a persistência;
- as fixtures do `conftest`;
- o README com instruções de deploy.

São 12 critérios de aceite. A story ainda cabe numa sessão de dev, porque cada parte é pequena e está fixada pela arquitetura, mas é a de maior risco de estourar o contexto ou de ser revisada às pressas.
*Recomendação:* manter, mas validar a story com `bmad-create-story` (VS) antes do dev. Se o dev travar, dividir em "1.1a criar e consultar" e "1.1b listar".

**M2. A tabela `task_tags` nasce antes do épico que a usa.** É um desvio da regra "criar cada tabela só quando for necessária". Ele foi aceito de forma explícita: o AD-5 manda criar o esquema inteiro na 1.1, e a forma da tarefa já traz `tags: []` desde a 1.1. São duas tabelas e não há ferramenta de migração, então criar `task_tags` depois exigiria `ALTER` ou recriação.
*Recomendação:* nenhuma ação. O desvio está justificado e documentado.

### 🟡 Pontos menores

**m1. A fixture `set_now` vem antes de ser usada.** A 1.1 cria `set_now` e a dependência `now` por causa do AD-8, mas nada no Épico 1 usa "hoje". É uma estrutura criada com antecedência. É pequena e evita que a 2.2 mexa no `conftest`.
*Recomendação:* aceitar. Se preferir o mínimo, mover `set_now` para a 2.2 e ajustar o texto do AD-8.

**m2. A story 2.1 muda o contrato da 1.1.** No Épico 1, `tags` no corpo dá 422 (`extra="forbid"`); a partir da 2.1, passa a ser aceito. A mudança é intencional e está documentada nas duas stories, mas qualquer script escrito contra o Épico 1 que envie `tags` muda de comportamento.
*Recomendação:* nenhuma ação, porque não há consumidores antes do fim da v1.

**m3. O texto do FR1 diz "ISO 8601", e as stories só aceitam `YYYY-MM-DD`.** As stories rejeitam `2026-10-02T00:00:00Z`, que também é ISO 8601. O Glossário ("prazo é só data") e o addendum (`YYYY-MM-DD`) sustentam a regra mais estrita, mas um leitor do FR1 isolado pode esperar que datas com hora sejam aceitas.
*Recomendação:* no PRD, trocar "formato de data ISO 8601" por "data ISO 8601 `YYYY-MM-DD`".

**m4. O NFR5 (rede interna) só é coberto por documentação.** Ele vira uma instrução de README com `--host <IP interno>`. Não é verificável por teste automático.
*Recomendação:* aceitar. Conferir no deploy do time-piloto.

**m5. Não há CI.** O checklist de projeto do zero espera CI cedo. A arquitetura adiou isso de forma explícita (Deferred: "Docker, CI e backup"), e no lugar dele vale a convenção `uv run pytest` antes de cada commit.
*Recomendação:* aceitar na v1.

**m6. O PRD está desatualizado no §8.** A questão da importação da planilha continua aberta no texto, mas foi resolvida no memlog: fica fora dos épicos.
*Recomendação:* atualizar o §8 do PRD.

## Resumo e recomendações

### Status geral de prontidão

**PRONTO** (PASS com ressalvas menores)

O PRD, a arquitetura e os épicos contam a mesma história:
- os 8 FRs e os 5 NFRs estão cobertos;
- nenhuma story depende de uma story posterior;
- a decisão que nos slides fica em aberto, o fuso horário do filtro por prazo, já foi tomada (`America/Sao_Paulo`, AD-2) e está testada na story 2.2.

### Problemas críticos que exigem ação imediata

Nenhum.

### Próximos passos recomendados

1. **Opcional:** corrigir o PRD. No §8, marcar a importação da planilha como resolvida (m6). No FR1, escrever "data ISO 8601 `YYYY-MM-DD`" (m3).
2. **Antes do dev da 1.1:** rodar `bmad-create-story` e a validação de story (VS). É a story mais carregada (M1).
3. **Seguir para** `bmad-sprint-planning`.

### Nota final

Esta avaliação encontrou 8 pontos em 3 categorias:
- **Qualidade dos épicos:** 2 maiores, os dois aceitos ou mitigáveis, e 5 menores.
- **Completude do PRD:** 1, o mesmo do m6.
- **Cobertura e UX:** nenhum.

Nada bloqueia a implementação. As correções são opcionais, e dá para seguir como está.

*Avaliado em 2026-10-02 pelo workflow `bmad-check-implementation-readiness`.*
