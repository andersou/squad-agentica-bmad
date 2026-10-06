- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-criar-e-listar-tarefas.md`
  summary: Nenhum teste falha se o desempate `id ASC` do `ORDER BY prazo ASC, id ASC` (AD-4) for removido.
  evidence: Na 1.1, o SQLite varre `tarefa` em ordem de rowid, que é igual à do id, e por isso a ordem dos empates não muda sem o `id ASC`. Acrescentar a asserção quando o Épico 2 mudar o plano da consulta (filtros `de`/`ate`/`tag` ou índice em `prazo`), com prazos empatados.
