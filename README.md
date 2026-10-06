# Squad agêntica com BMAD

Apresentação sobre como usar o [BMAD Method](https://github.com/bmad-code-org/BMAD-METHOD) como squad agêntica, do primeiro comando ao dia a dia, e o projeto de exemplo construído com ela, do brief à retrospectiva.

## Conteúdo

- [`docs/bmad-squad-agentica.html`](docs/bmad-squad-agentica.html): os slides (abra no navegador).
- [`docs/bmad-squad-agentica.pdf`](docs/bmad-squad-agentica.pdf): os mesmos slides em PDF.
- [`api-tarefas/`](api-tarefas/): API REST de tarefas com tags e janelas de prazo (Python 3.14, FastAPI, SQLite), feita pela squad. Veja o [README](api-tarefas/README.md) para instalar, testar e rodar.

## Artefatos gerados pela squad

Tudo o que os agentes produziram está versionado em [`api-tarefas/_bmad-output/`](api-tarefas/_bmad-output/):

| Etapa | Skill | Artefato |
|---|---|---|
| Brief | `bmad-product-brief` | `planning-artifacts/briefs/.../brief.md` |
| PRD | `bmad-prd` | `planning-artifacts/prds/.../prd.md` |
| Arquitetura | `bmad-architecture` | `planning-artifacts/architecture/.../ARCHITECTURE-SPINE.md` |
| Contexto do projeto | `bmad-project-context` | [`api-tarefas/AGENTS.md`](api-tarefas/AGENTS.md) |
| Épicos e stories | `bmad-create-epics-and-stories` | `planning-artifacts/epics.md` |
| Gate e sprint | `bmad-sprint-planning` | `planning-artifacts/sprint-planning-gate-*.md` e `implementation-artifacts/sprint-status.yaml` |
| Implementação | `bmad-build` + `bmad-code-review` | `implementation-artifacts/spec-*.md` (uma por story) |
| Retrospectiva | `bmad-retrospective` | `implementation-artifacts/epic-*-retro-*.md` |

Cada `.memlog.md` registra as decisões tomadas na conversa com o agente, e as pastas `reviews/` guardam as revisões de cada documento.

## Versões do BMAD

O projeto foi feito duas vezes, uma por versão do BMAD. Cada versão tem uma tag:

- [`bmad-v6.10.0`](../../tree/bmad-v6.10.0): primeira rodada (readiness check, create-story e dev-story).
- [`bmad-v6.12.1`](../../tree/bmad-v6.12.1): rodada atual (gate no sprint planning e bmad-build).

Os commits da rodada atual levam o prefixo `[BMAD 6.12.1]`, um por etapa. Para comparar as duas rodadas:

```bash
git diff bmad-v6.10.0 bmad-v6.12.1 -- api-tarefas/
```
