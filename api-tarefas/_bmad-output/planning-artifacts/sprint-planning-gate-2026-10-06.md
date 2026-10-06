---
title: "Gate do sprint planning (bmad-sprint-planning)"
created: 2026-10-06
verdict: CONCERNS
---

# Gate do sprint planning

Saída da sessão do `/bmad-sprint-planning`, registrada sem edição.

## Veredito

**CONCERNS** (1 achado)

O plano está quase todo amarrado. FR-1 a FR-6 e NFR-1 a NFR-5 aparecem em stories, e cada story remete ao PRD ou ao spine. Nenhuma story depende de uma story posterior: 1.3 e 1.4 usam a 1.2, e a 2.2 usa a 1.4. Não há UX, e isso está certo porque a API não tem interface. As três armadilhas do AGENTS.md estão nos ACs: `le=2**63-1`, PATCH concorrente com exclusão e query repetida.

**Achado: a Story 1.1 contradiz a convenção de testes** (`epics.md:118-120` contra o AGENTS.md e a convenção Testes do spine).

- O AC de persistência (NFR-5) manda fechar o cliente e abrir outro apontando para o mesmo `TAREFAS_DB`.
- Na mesma story, o AC da linha 102 e o AGENTS.md dizem que nenhum teste cria outro `TestClient`.

Quem implementar vai ter que decidir sozinho qual dos dois vale.

**O que eu recomendo:** reescrever o AC para usar só a fixture `client`. O teste cria a tarefa e depois abre `sqlite3.connect(os.environ["TAREFAS_DB"])` e chama `repo.listar`. Isso prova que a tarefa está gravada em disco, não muda a convenção e não precisa de outro `TestClient`. Outra opção seria a própria `conftest.py` oferecer uma segunda fixture que simula o reinício, mas aí a convenção muda.

A correção vale para o `epics.md` (via `bmad-create-epics-and-stories` ou `bmad-correct-course`). Escolha uma opção:

1. Corrijo o AC como recomendei e depois gero o `sprint-status.yaml`.
2. Fica a segunda fixture, e eu ajusto o AC e a convenção.
3. Gero o tracking agora e o achado fica para a Story 1.1 resolver.

## Resolução

Resposta: opção 1 (corrigir o AC e gerar o `sprint-status.yaml`).

Corrigi o AC e gerei o `_bmad-output/implementation-artifacts/sprint-status.yaml`. O script validou o arquivo sem nenhum problema.

**AC corrigido** em `epics.md:118-120`, na Story 1.1. O teste de persistência (NFR-5) agora usa só a fixture `client`. Ele abre `sqlite3.connect(os.environ["TAREFAS_DB"])`, chama `repo.listar` e confere que a tarefa está gravada em disco, sem criar outro `TestClient`. Com isso o achado do gate deixa de existir.

**O que o arquivo tem:**
- **Épico 1:** stories 1.1 a 1.4, todas em `backlog`.
- **Épico 2:** stories 2.1 a 2.3, todas em `backlog`.
- **Retrospectivas:** uma por épico, ambas `optional`.
- **Chave com acento:** a Story 1.2 ficou com a chave `1-2-etiquetar-tarefas-na-criação`, porque o script mantém os acentos do título de propósito. Funciona, mas o nome do arquivo da story vai ter `ç` e `ã`. Se preferir sem acento, mude o título da story no `epics.md` e rode este skill de novo.
- **Avisos do script:** dois títulos não viraram entradas, `# api-tarefas - Epic Breakdown` e `## Epic List`. É o esperado, porque nenhum dos dois é épico.

Não fiz commit. Para começar a implementar, rode o `bmad-build` na Story 1.1, que cria o projeto e a base de testes.
