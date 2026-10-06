import sqlite3
from datetime import date

from tarefas.domain import Tarefa


def criar_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tarefa("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "titulo TEXT NOT NULL, "
        "prazo TEXT NOT NULL, "
        "concluida INTEGER NOT NULL DEFAULT 0)"
    )


def criar(
    conn: sqlite3.Connection, titulo: str, prazo: date, tags: list[str]
) -> Tarefa:
    if tags:
        raise NotImplementedError("tags são gravadas a partir da Story 1.2")
    with conn:
        cur = conn.execute(
            "INSERT INTO tarefa(titulo, prazo) VALUES (?, ?)",
            (titulo, prazo.isoformat()),
        )
    return Tarefa(cur.lastrowid, titulo, prazo, [], False)


def listar(conn: sqlite3.Connection) -> list[Tarefa]:
    rows = conn.execute(
        "SELECT id, titulo, prazo, concluida FROM tarefa ORDER BY prazo ASC, id ASC"
    )
    return [
        Tarefa(id, titulo, date.fromisoformat(prazo), [], bool(concluida))
        for id, titulo, prazo, concluida in rows
    ]
