import sqlite3
from datetime import date

from tarefas.domain import Tarefa, norm_tag


def criar_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tarefa("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "titulo TEXT NOT NULL, "
        "prazo TEXT NOT NULL, "
        "concluida INTEGER NOT NULL DEFAULT 0)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tarefa_tag("
        "tarefa_id INTEGER NOT NULL REFERENCES tarefa(id) ON DELETE CASCADE, "
        "nome TEXT NOT NULL, "
        "nome_norm TEXT NOT NULL, "
        "UNIQUE(tarefa_id, nome_norm))"
    )


def criar(
    conn: sqlite3.Connection, titulo: str, prazo: date, tags: list[str]
) -> Tarefa:
    with conn:
        cur = conn.execute(
            "INSERT INTO tarefa(titulo, prazo) VALUES (?, ?)",
            (titulo, prazo.isoformat()),
        )
        conn.executemany(
            "INSERT INTO tarefa_tag(tarefa_id, nome, nome_norm) VALUES (?, ?, ?)",
            [(cur.lastrowid, nome, norm_tag(nome)) for nome in tags],
        )
    return Tarefa(cur.lastrowid, titulo, prazo, list(tags), False)


def listar(conn: sqlite3.Connection) -> list[Tarefa]:
    tarefas = {}
    for id, titulo, prazo, concluida, nome in conn.execute(
        "SELECT t.id, t.titulo, t.prazo, t.concluida, g.nome FROM tarefa t "
        "LEFT JOIN tarefa_tag g ON g.tarefa_id = t.id "
        "ORDER BY t.prazo ASC, t.id ASC, g.rowid ASC"
    ):
        if id not in tarefas:
            tarefas[id] = Tarefa(
                id, titulo, date.fromisoformat(prazo), [], bool(concluida)
            )
        if nome is not None:
            tarefas[id].tags.append(nome)
    return list(tarefas.values())
