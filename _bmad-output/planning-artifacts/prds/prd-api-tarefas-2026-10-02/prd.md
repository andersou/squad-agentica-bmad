---
title: "PRD: API de Tarefas"
status: final
created: 2026-10-02
updated: 2026-10-02
---

# PRD: API de Tarefas

## 0. Propósito do documento

Este PRD orienta a arquitetura, os épicos e as stories da API de Tarefas. Ele parte do brief final em `briefs/brief-api-tarefas-2026-10-02/` e não repete o que já está lá. O vocabulário segue o Glossário (§3). As funcionalidades estão agrupadas, e os requisitos funcionais (FR) têm numeração global. Detalhes de contrato HTTP e a divisão em épicos ficam no `addendum.md`.

O projeto é o exemplo de ponta a ponta do BMad Method usado na palestra (slides `bmad-squad-agentica.html`), e este PRD precisa bater com o que os slides mostram. Por isso, o escopo é pequeno de propósito e o rigor é leve.

## 1. Visão

A API de Tarefas é uma API REST, sem interface gráfica, para times pequenos registrarem tarefas com prazo, etiquetá-las com tags e perguntar, em uma chamada, o que está vencido, o que vence hoje e o que vence nos próximos 7 dias.

Ela substitui a planilha compartilhada em que hoje os prazos se perdem. A planilha não responde sozinha à pergunta que importa (o que está vencido e o que vence em breve) e não pode ser consultada por scripts, bots ou painéis. A API resolve as duas coisas: o atraso aparece antes de acontecer, e o time pode automatizar em cima dos prazos.

Se a v1 der certo no time-piloto, os próximos passos são a autenticação com suporte a vários times e os lembretes de prazo entregues onde o time já conversa (chat ou e-mail).

## 2. Público-alvo

Devs de times pequenos que hoje dividem uma planilha de tarefas e chamam APIs por `curl` ou script sem dificuldade. A v1 é validada com um único **time-piloto** (§3).

### 2.1 Jobs to be done

- Saber o que está vencido e o que vence em breve sem abrir e ordenar uma planilha.
- Registrar uma tarefa com prazo em uma chamada, de onde o dev já está: terminal, script ou bot.
- Separar as tarefas por assunto (tags) e cruzar assunto com prazo.
- Alimentar scripts, bots e painéis do próprio time com os prazos.

### 2.2 Fora do público (v1)

- Pessoas que precisam de tela para usar a ferramenta.
- Times que precisam de contas, permissões ou isolamento entre times.

### 2.3 Jornada principal

- **UJ-1. Rafa descobre o que venceu antes da daily.** Rafa é dev no time-piloto, que tem quatro pessoas e até ontem usava a planilha. Com os exemplos da documentação, cria uma tarefa com `curl`, informando título, prazo e a tag `backend`. Na manhã seguinte, pede as tarefas vencidas e recebe a lista na hora, sem abrir a planilha. Depois, um script do time passa a fazer essa chamada sozinho todo dia.

## 3. Glossário

- **Time-piloto:** o primeiro time a trocar a planilha pela API. É nele que a v1 é validada.
- **Tarefa:** unidade de trabalho registrada na API. Tem um título, um prazo, zero ou mais tags e uma marca de conclusão.
- **Título:** texto que descreve a tarefa. Obrigatório e não pode ser vazio.
- **Prazo:** data (dia, sem hora) até a qual a tarefa deve estar concluída. Obrigatório.
- **Tag:** rótulo de texto livre ligado a uma tarefa. Uma tarefa tem zero ou mais tags. A tag passa a existir quando é usada pela primeira vez; não há cadastro separado. Os espaços nas pontas são removidos e maiúsculas e minúsculas não se distinguem: `Backend` e ` backend ` são a mesma tag.
- **Tarefa concluída:** tarefa que o time marcou como feita. Continua existindo, mas não aparece nas janelas de prazo.
- **Hoje:** a data corrente no fuso `America/Sao_Paulo`. Todas as janelas de prazo partem dela.
- **Janela de prazo:** um dos três recortes por prazo, com significados fixos:
  - **Vencidas:** tarefas não concluídas com prazo anterior a hoje.
  - **Hoje:** tarefas não concluídas com prazo igual a hoje.
  - **Próximos 7 dias:** tarefas não concluídas com prazo entre amanhã e hoje + 7 dias, inclusive. Hoje não entra nesta janela; as três janelas não se sobrepõem.

## 4. Funcionalidades

### 4.1 Tarefas

**Descrição:** o dev cria, consulta, edita e exclui tarefas. Para marcar uma tarefa como concluída, ele a edita; não existe operação separada para isso. Realiza UJ-1.

#### FR-1: Criar tarefa

O dev pode criar uma tarefa informando título, prazo e, se quiser, tags.

**Consequências (testáveis):**
- Uma criação válida retorna 201 com o identificador da tarefa criada.
- Título ausente ou vazio retorna 422, e nenhuma tarefa é criada.
- Prazo ausente ou fora do formato de data ISO 8601 retorna 422, e nenhuma tarefa é criada.
- Um prazo no passado é aceito, e a tarefa já nasce vencida. Isso permite trazer as tarefas atrasadas da planilha.
- A tarefa nasce não concluída.

#### FR-2: Listar e consultar tarefas

O dev pode listar todas as tarefas ou consultar uma tarefa pelo identificador.

**Consequências (testáveis):**
- A listagem sem filtros retorna todas as tarefas, concluídas ou não, sem paginação.
- Toda listagem, com ou sem filtros, vem ordenada por prazo, do mais antigo para o mais distante.
- Cada tarefa retornada traz identificador, título, prazo, tags e a marca de conclusão.
- Consultar um identificador que não existe retorna 404.

#### FR-3: Editar tarefa

O dev pode alterar o título, o prazo e as tags de uma tarefa, e marcá-la ou desmarcá-la como concluída.

**Consequências (testáveis):**
- Só os campos enviados mudam; um campo omitido mantém o valor atual.
- As regras de validação do FR-1 valem para os campos enviados (título vazio → 422, prazo inválido → 422).
- Editar uma tarefa que não existe retorna 404.
- Uma tarefa marcada como concluída deixa de aparecer em todas as janelas de prazo (FR-7).

#### FR-4: Excluir tarefa

O dev pode excluir uma tarefa.

**Consequências (testáveis):**
- Depois da exclusão, consultar a tarefa retorna 404 e ela não aparece em nenhuma listagem.
- Excluir uma tarefa que não existe retorna 404.

### 4.2 Tags

**Descrição:** o dev etiqueta tarefas ao criá-las ou editá-las e depois filtra por tag. Realiza UJ-1.

#### FR-5: Etiquetar tarefa

O dev pode atribuir zero ou mais tags a uma tarefa, na criação (FR-1) ou na edição (FR-3).

**Consequências (testáveis):**
- Uma tag usada pela primeira vez passa a existir sem nenhum passo de cadastro.
- As tags seguem a regra de comparação do Glossário (§3): `Backend` e `backend` contam como a mesma tag, e repetições na mesma tarefa são guardadas uma única vez.
- Uma tag vazia (ou só com espaços) retorna 422.
- Quando a edição envia uma lista de tags, ela substitui a lista anterior por inteiro. Quando a edição não envia tags, elas não mudam (FR-3).

#### FR-6: Filtrar por tag

O dev pode listar só as tarefas que têm uma tag específica.

**Consequências (testáveis):**
- O filtro retorna exatamente as tarefas que têm a tag informada, pela regra de comparação do Glossário (§3).
- Uma tag que nenhuma tarefa usa retorna lista vazia, não erro.

### 4.3 Prazos

**Descrição:** o dev pergunta o que está vencido, o que vence hoje e o que vence nos próximos 7 dias, cada pergunta em uma chamada. Este é o valor central do produto. Realiza UJ-1.

#### FR-7: Filtrar por janela de prazo

O dev pode listar as tarefas de uma janela de prazo: vencidas, hoje ou próximos 7 dias.

**Consequências (testáveis):**
- Cada janela retorna exatamente as tarefas definidas no Glossário (§3), nem mais nem menos, com "hoje" calculado no fuso `America/Sao_Paulo`.
- Tarefas concluídas nunca aparecem em uma janela de prazo.
- Uma janela inexistente retorna 422.

#### FR-8: Combinar tag e janela de prazo

O dev pode combinar o filtro por tag (FR-6) com uma janela de prazo (FR-7) na mesma chamada, por exemplo, as tarefas vencidas com a tag `backend`.

**Consequências (testáveis):**
- O resultado é a interseção dos dois filtros.

## 5. Requisitos não funcionais

- **NFR-1. Documentação por exemplos:** a documentação traz exemplos prontos (por exemplo, `curl`) que cobrem pelo menos criar uma tarefa com tag e prazo e listar as vencidas.
- **NFR-2. Testes dos filtros:** os três filtros de prazo e a combinação com tag (FR-7, FR-8) têm testes automatizados. Os testes cobrem os limites de cada janela (ontem, hoje, amanhã, hoje + 7 e hoje + 8) e a virada do dia em `America/Sao_Paulo` com o servidor rodando em outro fuso, como UTC.
- **NFR-3. Erros previsíveis:** toda resposta de erro (404, 422) tem o mesmo formato e diz qual campo ou parâmetro causou o erro.
- **NFR-4. Persistência:** as tarefas sobrevivem ao reinício do serviço.
- **NFR-5. Rede interna:** como a v1 não tem autenticação, a API só deve ficar acessível na rede interna do time.

## 6. Escopo da v1

### 6.1 Dentro

- Criar, consultar, editar e excluir tarefas, inclusive marcar como concluída (FR-1 a FR-4).
- Etiquetar tarefas e filtrar por tag (FR-5, FR-6).
- Filtrar por janela de prazo e combinar com tag (FR-7, FR-8).

### 6.2 Fora

- **Competir com Jira, Trello ou similares:** a API resolve um problema delimitado, não é uma ferramenta de gestão de projetos.
- **Usuários, autenticação e permissões:** ficam para a visão multi-time (§1).
- **Interface gráfica:** o público usa `curl` e scripts.
- **Paginação da listagem:** vai para o backlog; o volume de um time pequeno não exige.
- **Notificações e lembretes de prazo:** ficam para os próximos passos da visão (§1).
- **Fuso por time ou por requisição:** a v1 usa um fuso fixo (`America/Sao_Paulo`).
- **Subtarefas e tarefas recorrentes.**
- **Importação da planilha:** não está planejada; ver §8.

## 7. Métricas de sucesso

**Primárias**
- **SM-1:** os três filtros de prazo retornam o conjunto correto de tarefas, com os testes do NFR-2 passando. Valida FR-7 e FR-8.
- **SM-2:** um dev cria uma tarefa com tag e prazo e lista as vencidas em duas chamadas, guiado só pelos exemplos da documentação. Valida FR-1, FR-5, FR-7 e NFR-1.
- **SM-3:** depois de 4 semanas de uso, o time-piloto confirma que não abriu a planilha para descobrir o que está vencido. Valida o produto como um todo.

**Secundária**
- **SM-4:** como demonstração, o fluxo completo do BMad roda sem atalhos: brief, PRD, arquitetura, épicos e stories, primeira story com commit.

**Contramétrica (não otimizar)**
- **SM-C1:** número de funcionalidades e endpoints. Aumentar o escopo para parecer completo prejudica a demo e o SM-2. Contrabalança o SM-3: se o time-piloto pedir mais coisas, elas vão para o backlog, não para a v1.

## 8. Questões em aberto

1. Como o time-piloto leva as tarefas atuais da planilha para a API? Manualmente, com um script descartável ou com uma importação na v1? Responsável: Anderson. Rever antes de quebrar os épicos.
