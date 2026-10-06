# Review adversarial — ARCHITECTURE-SPINE api-tarefas

Lente: duas stories (CRUD, Tags, Janelas) obedecem todos os ADs e ainda assim constroem peças incompatíveis.
Veredito: spine solido nas regras (relogio, janela, normalizacao, contrato HTTP), mas **furado na fronteira repo<->api**: nenhum AD fixa as assinaturas do repo nem a forma do dado que cruza as camadas. Cinco furos realistas abaixo.

## H1 (alta) — Assinatura de `repo.listar` e "quando ha janela"
- Build A (CRUD): `repo.listar(conn)` com `ORDER BY prazo, id`.
- Build B (Janelas): `repo.listar(conn, de, ate)` aplicando `concluida = 0` "quando ha janela". Como o repo "nao conhece os nomes das janelas" e vencidas e `(None, hoje-1)`, nao ha como distinguir "sem janela" de "janela" olhando so `(de, ate)`. B ou filtra pendentes sempre (some concluida da listagem geral, quebra FR-4) ou nunca (FR-6 quebra). Tags (C) acrescenta um terceiro parametro por conta propria.
- Fecha: novo AD (ou AD-3 apertado): uma unica `repo.listar(conn, *, pendentes: bool = False, de: str | None = None, ate: str | None = None, tag_norm: str | None = None) -> list[Tarefa]`; `pendentes=True` iff ha janela; a api passa `de/ate` em ISO str; nenhuma story cria outra funcao de listagem.

## H2 (alta) — Forma do dado que sai do repo (dois donos de "Tarefa")
- Build A: repo devolve `sqlite3.Row`/dict com `concluida` 0/1 e `tags` ausente; a rota monta o JSON.
- Build B: repo devolve dataclass `domain.Tarefa` com `concluida: bool`, `tags: list[str]` carregadas por JOIN (ou N+1).
- Resultado: `concluida: 1` no JSON, ou `tags` faltando na listagem, ou `prazo` como `str` vs `date`. O spine diz so "tipos do dominio" e fixa o JSON, nao o tipo intermediario.
- Fecha: AD de "Tarefa unica": `domain.Tarefa` (dataclass frozen: `id:int, titulo:str, prazo:date, tags:list[str], concluida:bool`) e o unico tipo que o repo devolve e a api serializa; conversao 0/1<->bool e ISO<->date so dentro do repo; `tags` sempre preenchida (ordem de insercao, `ORDER BY rowid`) em toda leitura.

## H3 (alta) — Quem escreve/le `tarefa_tag` e quem normaliza
- Build A (CRUD): `criar`/`editar` gravam tarefa e ignoram tags (tabela vira "problema da story de tags") ou ja gravam tags com `normalizar_tags` no repo.
- Build B (Tags): normaliza no schema Pydantic e repo grava `nome_norm = tag.casefold()` direto; filtro compara `nome_norm = ?` com o valor cru da query sem `norm_tag`, ou o filtro usa `LIKE`/`lower()`.
- Resultado: duas escritas na mesma tabela, `?tag=Backend` nao acha `backend`, ou normalizacao dupla divergente. AD-5 diz "schema, filtro e repo usam essas funcoes" sem dizer quem chama.
- Fecha: AD-5 apertado: a api normaliza (schema valida via `normalizar_tags`; query via `norm_tag`) e entrega ao repo `tags: list[str]` ja limpas; o repo so calcula `nome_norm = domain.norm_tag(nome)` ao inserir e compara `nome_norm = ?` com o valor ja normalizado. Insercao/leitura de `tarefa_tag` mora so em helpers privados do repo chamados por `criar`/`editar`/`listar` (a story CRUD ja os entrega, mesmo vazios de regra).

## H4 (media) — Contrato do PATCH no repo: omitido vs `[]` vs 404
- Build A: `repo.editar(conn, id, **campos)` com `model_dump()` (sem `exclude_unset`), `tags=None` = "manter".
- Build B: `repo.editar(conn, id, tarefa_completa)` com `tags=[]` = "limpar"; le a tarefa antes, mescla na api. Um sinaliza 404 com `None`, o outro levanta excecao capturada em lugar nenhum.
- Resultado: `PATCH {"tags": []}` nao limpa, ou `PATCH {"titulo": "x"}` apaga tags; 404 vira 500; 404 vs 422 em ordem diferente.
- Fecha: AD-6/AD-8: a api passa ao repo apenas `model_dump(exclude_unset=True)`; no repo, chave ausente = manter, `tags: []` = limpar; `editar`/`excluir` devolvem `None`/`False` quando o id nao existe e a rota converte em `HTTPException(404)` (repo nunca importa fastapi). Validacao (422) roda antes do 404.

## H5 (media) — Fixtures de teste duplicadas
- Build A (`test_tarefas.py`) define `client` com `TAREFAS_DB` em `tmp_path` e sem override de `agora`; build B (`test_janelas.py`) define o seu com `agora` fixo, nome de dependencia diferente e sem `TestClient` em `with`.
- Resultado: um relogio real vaza nos testes de CRUD (prazo "amanha" quebra de madrugada em SP) e dois bancos/fixtures com semanticas diferentes; o seed nao lista `conftest.py`.
- Fecha: Convencao de Testes: `tests/conftest.py` unico (dono: primeira story) com fixtures `client` (db em `tmp_path`, `agora` sempre sobrescrito para um instante fixo) e `fixar_agora(instante)`; testes nao definem fixtures proprias de app/banco. Acrescentar `conftest.py` ao Structural Seed e nomear a dependencia de conexao (`api.get_conn`) e a de relogio (`api.agora`) em AD-2/AD-8.

## Observacoes menores (nao viram AD)
- Filtro `?tag=` vazio ou so espacos: AD-6 diz 422 so para >1 valor; incluir "tag de query: strip, 1 a 50" na tabela do AD-6 (PRD FR-6 exige 422).
- Nomes `get_conn`/`agora` em `api.py`: dois devs editam o mesmo arquivo; ordem de merge, nao arquitetura.
