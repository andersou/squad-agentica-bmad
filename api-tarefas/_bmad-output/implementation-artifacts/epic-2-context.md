# Epic 2 Context: Consultar prazos por janela e tag

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Responder em uma chamada à pergunta que a planilha não responde: o que está vencido, o que vence hoje e o que vence nos próximos 7 dias, considerando só tarefas pendentes e opcionalmente recortado por uma tag. É o que alimenta o script matinal do time (vencidas de `backend` publicadas no chat). O épico também filtra a listagem geral por tag e documenta no README as chamadas `curl`, para que um dev novo crie uma tarefa com tag e prazo e liste as vencidas em duas chamadas. Ele usa as tarefas do Épico 1 e não altera o contrato delas.

## Stories

- Story 2.1: Filtrar a listagem geral por tag
- Story 2.2: Consultar pendentes por janela de prazo
- Story 2.3: Documentar as chamadas no README

## Requirements & Constraints

- **Filtro por tag:** uma única tag por chamada. Ele funciona na listagem geral (concluídas ou não) e combinado com qualquer janela. A comparação não diferencia maiúsculas de minúsculas e ignora espaços nas pontas. A tarefa volta com todas as tags, não só a que casou. Tag que ninguém tem dá 200 com `[]`.
- **Janelas** (só pendentes, limites inclusivos):
  - vencidas: `prazo < hoje`
  - hoje: `prazo = hoje`
  - próximos 7 dias: `hoje + 1 <= prazo <= hoje + 7`
  - Com hoje fixado, ontem, hoje, amanhã, hoje + 7 e hoje + 8 caem em vencidas, hoje, próximos 7 dias, próximos 7 dias e nenhuma janela.
- **Concluída:** uma tarefa concluída vencida não aparece em nenhuma janela. Ao desligar `concluida`, ela volta.
- **Fuso:** hoje é sempre a data em America/Sao_Paulo, independentemente do fuso do servidor. Às 22h em SP (01h UTC do dia seguinte), uma tarefa com prazo na data de SP aparece em hoje e não em vencidas.
- **Ordenação:** janelas e filtros seguem a mesma ordem da listagem geral.
- **Erros 422:** janela desconhecida ou vazia, `janela` repetida, tag vazia ou só com espaços, tag acima de 50 caracteres, ou mais de uma tag.
- **Sem janela:** `GET /tarefas` continua sendo a listagem geral, sem usar o relógio para filtrar.
- **Testes dos limites:** cada caso-limite das janelas (incluindo o do fuso) tem um teste próprio.
- **README:** os exemplos `curl` cobrem criar com tag e prazo e listar vencidas com essa tag (duas chamadas), além de listagem geral, filtro por tag, as três janelas, PATCH para concluir e DELETE, com os códigos de resposta. Também traz a execução com `TAREFAS_DB` em caminho absoluto (com o aviso sobre caminho relativo), o aviso de que não há autenticação e de que a API roda só na rede interna, o `/docs` automático e os comandos `uv run pytest` e `uv run ruff check`. Cada `curl` é conferido contra a API rodando.
- **Escopo:** nada além de FR-1 a FR-6. Ficam de fora o filtro por várias tags, a paginação, `GET /tarefas/{id}` e a autenticação.

## Technical Decisions

- **Camadas:** `api → domain ← repo`. Toda regra de prazo, janela e tag fica em `domain.py`, que não importa nada externo. `repo.py` nunca importa `api`.
- **Relógio:** `api.agora() -> datetime` (UTC aware) é a única leitura do relógio, injetada nas rotas via `Depends`. `domain.hoje(agora) -> date` converte para `ZoneInfo("America/Sao_Paulo")` e pega `.date()`, com o fuso vindo do `tzdata`. Nunca use `date.today()` nem `datetime.now()`.
- **Janela:** `domain.Janela` é um `StrEnum` (`vencidas`, `hoje`, `proximos-7-dias`). Só `domain.intervalo(janela, hoje) -> (de, ate)` converte a janela em limites inclusivos, que podem ser `None`:
  - vencidas: `(None, hoje-1)`
  - hoje: `(hoje, hoje)`
  - próximos 7 dias: `(hoje+1, hoje+7)`
- **Repo:** `listar(conn, *, pendentes=False, de=None, ate=None, tag=None) -> list[Tarefa]` continua sendo a única função de listagem. Ela aplica `concluida = 0`, `prazo >= de` e `prazo <= ate` sem conhecer os nomes das janelas, e filtra a tag por `nome_norm = norm_tag(tag)`. A api passa `pendentes=True` se e só se houver janela. O `prazo` é TEXT ISO, então a comparação é feita como texto. Toda listagem usa `ORDER BY prazo ASC, id ASC`.
- **Tags:** só `domain.norm_tag` (`strip().casefold()`) normaliza. Nenhuma outra camada faz `lower` ou `casefold`.
- **Query:**
  - `tag` é declarado como `list[str]`, e a rota checa se há mais de um valor, se o valor fica vazio depois do strip ou se passa de 50 caracteres (422).
  - `janela` é um `Janela`, e valor desconhecido dá 422.
  - A repetição de `janela` é checada na rota, porque o FastAPI pegaria o último valor sem avisar.
- **Contrato:** `GET /tarefas?janela=&tag=` devolve 200 com um array JSON, sem envelope. Os erros seguem o formato `{"detail": ...}`.
- **Testes:**
  - Os casos-limite das janelas e do fuso ficam em `tests/test_janelas.py`.
  - Todo teste usa a fixture `client` de `tests/conftest.py`, que sempre fixa `api.agora` via `app.dependency_overrides` (ajustável pelo teste) e usa um banco em `tmp_path`. Nenhum teste cria outro `TestClient`.
  - O caso das 22h em SP usa o instante `01:00 UTC` do dia seguinte.
- **Nomes:** identificadores em português, sem acento (`janela`, `hoje`, `de`, `ate`, `pendentes`).

## Cross-Story Dependencies

- O épico depende do Épico 1: tabela `tarefa_tag` com `nome_norm`, `domain.norm_tag`, o `PATCH` de `concluida` e a fixture `client`.
- A 2.1 acrescenta o argumento `tag` em `repo.listar` e a checagem da query `tag`. A 2.2 reutiliza esse filtro combinado com a janela.
- A 2.2 acrescenta `pendentes`, `de` e `ate` em `repo.listar`, além de `api.agora`, `domain.hoje`, `Janela` e `intervalo`.
- A 2.3 documenta as rotas da 2.1 e da 2.2 e confere os exemplos contra a API rodando, por isso vem por último.
