---
title: "PRD: API de Tarefas"
status: final
created: 2026-10-06
updated: 2026-10-06
---

# PRD: API de Tarefas

## 0. Propósito do documento

Este PRD orienta a arquitetura e a quebra em épicos e stories da API de Tarefas. Ele parte do brief e do addendum do brief, ambos em `planning-artifacts/briefs/brief-api-tarefas-2026-10-06/`, e não repete o que lá já está justificado. Os termos do domínio estão definidos no Glossário (§3) e são usados sempre com a mesma grafia. Os requisitos funcionais (FR) ficam agrupados por funcionalidade e numerados de forma contínua.

O projeto é uma demonstração do BMad Method para slides. Os riscos são baixos e o escopo é pequeno de propósito.

## 1. Visão

A API de Tarefas é uma API REST interna que substitui a planilha em que um time pequeno controla tarefas e prazos. Cada tarefa tem título, prazo, tags e a marca de concluída. A API responde em uma chamada à pergunta que a planilha não responde: o que está vencido, o que vence hoje e o que vence nos próximos 7 dias.

Como é uma API, scripts, bots e painéis do próprio time podem consultar os prazos. Isso abre espaço para automação, o que a planilha impede.

Se a v1 der certo no time-piloto, os próximos passos são autenticação com suporte a vários times e lembretes de prazo entregues no chat ou por e-mail. Nada disso entra na v1.

## 2. Usuário

### 2.1 Jobs To Be Done

- Saber, sem abrir planilha nem conferir linha a linha, quais tarefas pendentes estão vencidas ou vencem em breve.
- Recortar essa visão por assunto (tag), por exemplo "vencidas de `backend`".
- Alimentar scripts e bots do time com a lista de prazos.

### 2.2 Jornadas principais

- **UJ-1. Rafa migra os atrasos da planilha.** Rafa, dev do time-piloto, recadastra à mão as tarefas da planilha, inclusive as que já venceram. Usa prazo no passado e a tag `backend`, e cada tarefa atrasada já nasce vencida.
- **UJ-2. Rafa consulta o que está vencido.** Toda manhã, um script de Rafa pede as tarefas vencidas com a tag `backend` e publica a lista no chat do time.
- **UJ-3. Rafa conclui uma tarefa.** Ao terminar uma tarefa, Rafa a edita e liga a marca de concluída. A tarefa sai das janelas de prazo, mas continua na listagem geral.

*O time-piloto e Rafa são fictícios, criados para a demonstração.*

## 3. Glossário

- **Tarefa** — Item de trabalho do time. Tem um título, um prazo, zero ou mais tags e a marca de concluída.
- **Título** — Texto obrigatório que descreve a tarefa.
- **Prazo** — Data obrigatória, sem hora, no formato ISO `YYYY-MM-DD`. Pode estar no passado.
- **Tag** — Texto livre que etiqueta uma tarefa. Não existe cadastro de tags. A comparação entre tags não diferencia maiúsculas de minúsculas.
- **Concluída** — Marca booleana da tarefa. Uma tarefa não concluída é **pendente**.
- **Hoje** — Data corrente no fuso fixo America/Sao_Paulo, independentemente do fuso do servidor.
- **Janela de prazo** — Recorte das tarefas pendentes pelo prazo em relação a hoje. Há três janelas que não se sobrepõem: **vencidas**, **hoje** e **próximos 7 dias**.
- **Listagem geral** — Lista de todas as tarefas, concluídas ou não.

## 4. Funcionalidades

### 4.1 Tarefas

**Descrição:** o dev cria, edita, exclui e lista tarefas. Concluir uma tarefa é uma edição como outra qualquer: basta ligar a marca de concluída. Não há operação separada para isso. Realiza UJ-1 e UJ-3.

#### FR-1: Criar tarefa

O dev pode criar uma tarefa informando título e prazo, com tags opcionais. Realiza UJ-1.

**Consequências (testáveis):**
- Sem título ou sem prazo, a API rejeita a criação com 422.
- Título vazio ou só com espaços é rejeitado com 422.
- Um prazo fora do formato `YYYY-MM-DD`, ou uma data inexistente como `2026-02-30`, é rejeitado com 422.
- Um prazo no passado é aceito. A tarefa entra na janela vencidas logo na criação.
- A tarefa nasce pendente.
- A resposta devolve a tarefa criada com seu identificador.

#### FR-2: Editar tarefa

O dev pode alterar título, prazo, tags e a marca de concluída de uma tarefa existente. Realiza UJ-3.

**Consequências (testáveis):**
- A edição é parcial: um campo omitido mantém o valor anterior.
- Os campos enviados passam pelas mesmas validações do FR-1.
- Ao ligar a marca de concluída, a tarefa sai de todas as janelas de prazo (FR-6). Ao desligá-la, a tarefa volta às janelas.
- Editar uma tarefa que não existe retorna 404.

#### FR-3: Excluir tarefa

O dev pode excluir uma tarefa.

**Consequências (testáveis):**
- A exclusão é definitiva. A tarefa some da listagem geral e das janelas de prazo.
- Excluir uma tarefa que não existe retorna 404.

#### FR-4: Listagem geral

O dev pode listar todas as tarefas, concluídas ou não.

**Consequências (testáveis):**
- A lista é ordenada por prazo, do mais antigo ao mais distante.
- A lista vem inteira, sem paginação.
- Não há filtro por concluída ou pendente. As janelas de prazo cumprem esse papel. Uma tarefa pendente com prazo depois de hoje + 7 só aparece na listagem geral, ao lado das concluídas. Esse custo foi aceito para a v1.

### 4.2 Tags

**Descrição:** cada tarefa tem zero ou mais tags de texto livre, sem cadastro prévio. O filtro por tag funciona na listagem geral e combinado com uma janela de prazo. Realiza UJ-1 e UJ-2.

#### FR-5: Etiquetar tarefa e filtrar por tag

O dev pode atribuir tags a uma tarefa e filtrar tarefas por uma tag.

**Consequências (testáveis):**
- Tag vazia ou só com espaços é rejeitada com 422.
- Os espaços no início e no fim da tag são removidos.
- A comparação não diferencia maiúsculas de minúsculas: `Backend` e `backend` são a mesma tag.
- Uma tag repetida na mesma tarefa é guardada uma vez só, com a grafia da primeira ocorrência.
- Na edição, enviar tags substitui a lista inteira, e omitir tags mantém a lista atual.
- Cada chamada aceita uma única tag no filtro.
- O filtro por tag funciona na listagem geral (FR-4) e em qualquer janela de prazo (FR-6). Exemplo: vencidas com a tag `backend`.

### 4.3 Janelas de prazo

**Descrição:** responde em uma chamada a "o que está vencido?", "o que vence hoje?" e "o que vence nos próximos 7 dias?". Considera só tarefas pendentes. Realiza UJ-2.

#### FR-6: Filtrar pendentes por janela de prazo

O dev pode listar as tarefas pendentes de uma janela de prazo.

**Consequências (testáveis):**

| Janela | Regra |
|---|---|
| Vencidas | `prazo < hoje` |
| Hoje | `prazo = hoje` |
| Próximos 7 dias | `hoje + 1 <= prazo <= hoje + 7` |

- Com hoje fixado, os prazos de ontem, hoje, amanhã, hoje + 7 e hoje + 8 caem respectivamente em vencidas, hoje, próximos 7 dias, próximos 7 dias e nenhuma janela.
- Uma tarefa concluída com prazo vencido não aparece em nenhuma janela.
- Às 22h em São Paulo, quando já são 01h UTC do dia seguinte, hoje continua sendo a data de São Paulo. Uma tarefa com prazo nessa data aparece em hoje, e não em vencidas.
- O resultado segue a mesma ordenação da listagem geral.
- A API rejeita com 422 uma janela desconhecida, uma tag vazia ou mais de uma tag no filtro.

## 5. Requisitos não funcionais

- **NFR-1. Fuso fixo:** o cálculo de hoje usa sempre America/Sao_Paulo e independe do fuso configurado no servidor.
- **NFR-2. Rede interna:** a API roda só na rede interna do time, sem autenticação. A falta de controle de acesso só é aceitável por causa dessa exposição limitada.
- **NFR-3. Testes dos limites:** testes automatizados cobrem todos os casos-limite do FR-6.
- **NFR-4. Documentação por exemplos:** a documentação traz exemplos de chamadas suficientes para cumprir o SM-2.
- **NFR-5. Persistência:** as tarefas sobrevivem ao reinício da API. Sem isso, a API não substitui a planilha.

## 6. Escopo e não-objetivos

**Dentro da v1:** FR-1 a FR-6.

**Fora da v1:**
- Autenticação, usuários e permissões. Ficam para a visão (§1), junto com o suporte a vários times.
- Interface gráfica. Os usuários são devs que usam `curl` e scripts.
- Importação da planilha. O time recadastra à mão, com prazo no passado quando preciso.
- Paginação. Fica no backlog.
- Notificações e lembretes de prazo. Ficam para a visão (§1).
- Subtarefas, tarefas recorrentes e campos além de título, prazo, tags e concluída.
- Filtro por várias tags na mesma chamada.

**Não-objetivo:** competir com Jira, Trello ou similares.

## 7. Métricas de sucesso

- **SM-1:** as três janelas devolvem o conjunto correto em todos os casos-limite do FR-6, verificado por testes automatizados. Valida FR-6.
- **SM-2:** guiado só pelos exemplos da documentação, um dev cria uma tarefa com tag e prazo e lista as vencidas em duas chamadas. Valida FR-1, FR-5 e FR-6.
- **SM-3:** o time-piloto deixa de abrir a planilha para saber o que está vencido. *Métrica ilustrativa, porque o time-piloto é fictício.*
- **SM-4 (demo):** o fluxo do BMad roda sem atalhos: brief, PRD, arquitetura, épicos e stories, até o commit da primeira story.

**Contramétrica**

- **SM-C1:** número de funcionalidades. Não otimizar: o escopo pequeno é proposital e precisa caber em dois épicos. Contrabalança a tentação de "aproveitar e adicionar" itens da lista de fora da v1.

## 8. Questões em aberto

Nenhuma questão bloqueia a v1. Ficam para a arquitetura (bmad-architecture), que decide e registra:

1. O critério de desempate na ordenação de tarefas com o mesmo prazo, necessário para testes determinísticos.
2. Os códigos de sucesso de cada operação, como 201 na criação.
3. Os limites de tamanho de título e de tag, e a validação de um valor de concluída que não seja booleano.
4. Como os testes fixam o relógio para cobrir os casos-limite do FR-6.
