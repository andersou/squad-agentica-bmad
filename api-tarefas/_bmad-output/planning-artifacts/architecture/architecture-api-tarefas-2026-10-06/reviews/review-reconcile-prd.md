# Reconciliacao PRD x ARCHITECTURE-SPINE (api-tarefas)

Veredito: **aprovado com 3 lacunas parciais, 0 contradicoes**. 50 itens do PRD: 45 cobertos, 3 parciais, 2 fora do escopo da arquitetura (SM-3 ilustrativa, SM-4 processo). Cobertura sobre 48 aplicaveis: 45 coberto / 3 parcial.

## Lacunas parciais (duas pessoas poderiam implementar diferente)

1. **Tag vazia na query (FR-6 "422 para tag vazia"; FR-5).** AD-6 declara `tag` como `list[str]` e rejeita so mais de um valor. Nao fixa `min_length`/strip-vazio na query. AD-5 so converte tag vazia em 422 no schema do corpo. `?tag=` ou `?tag=%20` pode virar `norm_tag("") == ""`, casar nada e devolver 200 `[]`. Fixar: tag de query vazia apos strip = 422, via a mesma funcao de AD-5.
2. **`concluida` no POST (FR-1 "nasce pendente", glossario Concluida).** AD-6 usa `extra="forbid"` e lista `concluida` como campo, sem separar os schemas de criacao e edicao. Nao esta pinado se `POST {"concluida": true}` e 422 (forbid) ou aceito. Fixar: schema de criacao nao tem `concluida` (422), nasce `0`.
3. **Persistencia (NFR-5).** `TAREFAS_DB` tem padrao `tarefas.db`, caminho relativo ao cwd. Subir o uvicorn de outro diretorio cria um banco vazio em silencio e "as tarefas sumiram" no reinicio. Fixar caminho absoluto/padrao estavel, ou exigir cwd na secao Execucao.

## Observacoes menores (delegaveis, risco baixo)

- PATCH `{}` (corpo vazio): 200 sem mudanca ou 422? Nao pinado.
- Precedencia 404 x 422 em PATCH com id inexistente e corpo invalido: nao pinada.
- "Lista" nas respostas de listagem: array JSON nu ou envelope? Convencao mostra so o JSON da tarefa. Pinar "array nu".
- `titulo` "1 a 200 caracteres": confirmar que a contagem e apos strip (AD-6 diz "strip, 1 a 200", ordem implicita).
- Tags: sem limite de quantidade por tarefa; `casefold` junta `ss` e `ß` (aceitavel, so registrar).
- Parametros de query desconhecidos (ex. `?concluida=`) sao ignorados em silencio; o PRD nao exige 422.
- AD-2 liga FR-1 ao relogio, mas criar nao le o relogio (inofensivo).

## Matriz

### FR-1 Criar
| Consequencia | Cobertura |
|---|---|
| 422 sem titulo/prazo | AD-6 (campos obrigatorios implicitos no POST) - coberto |
| Titulo vazio/espacos 422 | AD-6 strip + min 1 - coberto |
| Prazo invalido / 2026-02-30 422 | AD-6 `date` strict - coberto |
| Prazo passado aceito | sem restricao no AD-6, AD-3 - coberto |
| Nasce pendente | **parcial** (lacuna 2) |
| Resposta com id | AD-7 201 + JSON da tarefa - coberto |

### FR-2 Editar
Parcial/omitido mantem: AD-6 - coberto. Mesmas validacoes: AD-6 - coberto. Concluida liga/desliga e janelas: AD-3 `concluida = 0` - coberto. 404: AD-7 - coberto.

### FR-3 Excluir
Definitiva e some das listas: AD-7 204, AD-8 cascade - coberto. 404: AD-7 - coberto.

### FR-4 Listagem
Ordem por prazo: AD-4 (desempate id, resolve §8.1) - coberto. Sem paginacao: Deferred - coberto. Sem filtro de concluida: AD-3 aplica `concluida=0` so com janela - coberto.

### FR-5 Tags
Vazia 422 (corpo): AD-5/AD-6 - coberto. Trim: AD-5 - coberto. Case-insensitive: AD-5 casefold + `nome_norm` - coberto. Duplicada, primeira grafia: AD-5 + UNIQUE - coberto. Edicao substitui/omite mantem: AD-6, AD-8 - coberto. Uma tag no filtro: AD-6 - coberto. Filtro em geral e janelas: AD-7 `?janela=&tag=` - coberto. (Tag vazia na query: lacuna 1.)

### FR-6 Janelas
Tabela de regras: AD-3 (`intervalo`) - coberto. Casos ontem/hoje/amanha/+7/+8: AD-3 + convencao de testes - coberto. Concluida fora das janelas: AD-3 - coberto. Caso 22h SP: AD-2 - coberto. Mesma ordenacao: AD-4 - coberto. 422 janela desconhecida e >1 tag: AD-6 - coberto. 422 tag vazia: **parcial** (lacuna 1).

### NFR
NFR-1: AD-2, `domain.hoje`, tzdata - coberto. NFR-2: AD-7 sem auth, `--host <ip-interno>` - coberto. NFR-3: AD-2, `test_janelas.py` - coberto. NFR-4: convencao Documentacao (README com curl cobrindo SM-2) - coberto. NFR-5: AD-8 - **parcial** (lacuna 3).

### Glossario
Tarefa, Titulo, Prazo (ISO sem hora, passado), Tag (sem cadastro, case-insensitive), Concluida (bool estrito), Hoje (fuso fixo), Janela (3 janelas sem sobreposicao: limites disjuntos em AD-3), Listagem geral: todos cobertos. Nenhuma tabela de tags cadastradas, coerente.

### Metricas
SM-1: AD-3 + testes - coberto. SM-2: README - coberto (o exemplo deve usar prazo passado para listar vencidas). SM-3: n/a (ilustrativa). SM-4: n/a (processo BMad). SM-C1: Deferred mantem escopo pequeno - coberto.

### §8 Questoes em aberto
1. Desempate: AD-4. 2. Codigos de sucesso: AD-7. 3. Limites de tamanho e concluida nao booleana: AD-6 (200, 50, StrictBool). 4. Relogio nos testes: AD-2. Todas decididas.

## Contradicoes
Nenhuma. O spine nao viola regra do PRD; so deixa as tres lacunas acima.
