# Deferred Work

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-excluir-tarefa.md`
  summary: Acrescentar ao pitfall de id do AGENTS.md o limite inferior `ge=-2**63` (alias `api.Id`), além do `le=2**63-1`.
  evidence: `DELETE /tarefas/-9223372036854775809` estouraria o INTEGER do SQLite como na v1; a 1.3 fechou com `ge=-2**63`, mas o AGENTS.md só cita o `le`. A correção edita arquivo de contexto de agente, então fica para o Anderson (ou `bmad-project-context`).
