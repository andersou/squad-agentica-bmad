<!-- bmad:context -->
<!-- Verificado 2026-10-06 contra 80625b6. Gerido por bmad-project-context; edições dentro deste bloco são substituídas no refresh. Mantenha fora dos marcadores o que quiser preservar. -->

## api-tarefas

API REST interna de tarefas com janelas de prazo (vencidas, hoje, próximos 7 dias), feita como demo do BMad Method. Python 3.14, FastAPI, sqlite3 da stdlib, uv. O planejamento (brief, PRD, arquitetura) fica em `_bmad-output/planning-artifacts/`, e stories e sprint ficam em `_bmad-output/implementation-artifacts/`.

## Policy

- Escreva as mensagens de commit em português, no formato `[BMAD 6.12.1] tipo: descrição`. O `bmad-build` pode commitar sozinho ao fechar uma story. Fora isso, só commite quando o Anderson pedir.
- Nunca edite à mão `_bmad/` nem `.claude/skills/`, que são instalados pelo BMAD. Para personalizar, use `bmad-customize`.
- Não adicione funcionalidade fora de FR-1 a FR-6. O que ficou de fora está no PRD §6 e no Deferred do spine.
- Uma story só vai para `done` sem nenhum `[ ]` aberto. Corrija na própria story todo achado de revisão que tenha correção clara, inclusive os de severidade baixa.
- Achado que exige decisão vira pergunta para o Anderson, nunca item adiado.
- A revisão só aprova depois de conferir cada AD do spine contra o diff. "Nenhum achado alto ou médio" não basta.

## Where things are

- Antes de implementar ou revisar uma story, leia `_bmad-output/planning-artifacts/architecture/architecture-api-tarefas-2026-10-06/ARCHITECTURE-SPINE.md`. Os AD-1 a AD-9 fixam rotas, códigos HTTP, validação e assinaturas do repo.
- Os termos do domínio estão no Glossário (§3) de `_bmad-output/planning-artifacts/prds/prd-api-tarefas-2026-10-06/prd.md`.

## Running and verifying

- Use `uv run pytest`, `uv run ruff check` e `uv run ruff format` (ou `--check`), sem argumentos. O `[tool.ruff]` exclui `_bmad/` e `.claude/`. Não chame `pytest` ou `ruff` sozinhos, porque rodam fora do ambiente do projeto.
- Para subir a API, use `TAREFAS_DB=/caminho/absoluto/tarefas.db uv run uvicorn tarefas.api:app`. Com caminho relativo, subir de outro diretório abre um banco novo e vazio.
- As versões (Python 3.14, uv 0.12) vêm do spine e do `pyproject.toml`, nunca do ambiente da sessão.

## Conventions that differ from defaults

- `domain.py` não importa nada (nem FastAPI, nem Pydantic, nem sqlite3), e `repo.py` nunca importa `api`. Regra de prazo, janela ou tag mora só em `domain.py`.
- Nunca chame `date.today()` nem `datetime.now()`. O relógio é lido só pela dependência `api.agora()` (UTC aware) e convertido por `domain.hoje(agora)` para America/Sao_Paulo. Nos testes, substitua `agora` por `app.dependency_overrides`.
- Só `domain.intervalo` converte a janela em limites. O repo recebe `de`/`ate` e não conhece os nomes das janelas.
- Normalize tags só com `domain.norm_tag`. Nenhuma outra camada faz `lower` ou `casefold`.
- SQL fica só em `repo.py`, com sqlite3 puro, sem ORM. O repo devolve só `domain.Tarefa`, nunca `sqlite3.Row` nem dict. Toda listagem usa `ORDER BY prazo ASC, id ASC`.
- Leia `TAREFAS_DB` ao abrir a conexão, nunca na importação. Crie o schema na dependência `api.conexao`, não no lifespan, porque `TestClient` usado fora de `with` não roda o lifespan.
- Valide `prazo` com `BeforeValidator` e o regex `^\d{4}-\d{2}-\d{2}$`, não com `Strict()`, que no corpo do FastAPI rejeita até `"2026-10-06"`.
- Escreva identificadores em português, sem acento, com os termos do Glossário (`titulo`, `prazo`, `concluida`, `janela`).
- Todo teste usa a fixture `client` de `tests/conftest.py` (relógio fixo e banco em `tmp_path`). Não crie outro `TestClient`.
- Instale o FastAPI sem `[standard]` e mantenha `httpx`, não `httpx2`, no TestClient.

## Known pitfalls

- Na v1 anterior, um `id` de path acima de 2⁶³−1 estourava o INTEGER do SQLite e virava 500, e três revisões seguidas adiaram a correção. Declare o `id` com o alias `api.Id` (`ge=-2**63`, `le=2**63-1` e só dígitos) para que dê 422. O `int` solto também aceita `1_0` como 10 e apagaria a tarefa errada.
- Na v1 anterior, um PATCH concorrente com uma exclusão virava 500. Confira, grave e releia na mesma transação, e trate a tarefa que sumiu como 404.
- Parâmetro de query repetido (`?janela=` ou `?tag=`) dá 422. Para escalares, o FastAPI pega o último valor sem avisar, então a rota precisa checar a repetição.

<!-- /bmad:context -->
