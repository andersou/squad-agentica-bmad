import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
  id       INTEGER PRIMARY KEY,
  title    TEXT    NOT NULL,
  due_date TEXT    NOT NULL,          -- YYYY-MM-DD
  done     INTEGER NOT NULL DEFAULT 0 -- 0 ou 1
);
CREATE TABLE IF NOT EXISTS task_tags (
  task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  tag     TEXT    NOT NULL,           -- já normalizada (AD-9)
  PRIMARY KEY (task_id, tag)
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(
        os.environ.get("TASKS_DB_PATH", "./tasks.db"), check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def insert_task(
    conn: sqlite3.Connection, title: str, due_date: str, tags: list[str]
) -> int:
    with conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)", (title, due_date)
        )
        replace_tags(conn, cur.lastrowid, tags)
    return cur.lastrowid


_UPDATABLE = ("title", "due_date", "done")


def update_task(conn: sqlite3.Connection, task_id: int, fields: dict) -> dict | None:
    """Aplica só os campos enviados e devolve a tarefa atualizada (None se não existe).

    Checagem, escrita e releitura na mesma transação: um DELETE concorrente não vira 500.
    """
    cols = [
        c for c in _UPDATABLE if c in fields
    ]  # colunas da lista fixa, nunca do corpo
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,))
        if row.fetchone() is None:
            return None
        if cols:
            sets = ", ".join(f"{c} = ?" for c in cols)
            vals = [int(fields[c]) if c == "done" else fields[c] for c in cols]
            conn.execute(f"UPDATE tasks SET {sets} WHERE id = ?", (*vals, task_id))
        if "tags" in fields:
            replace_tags(conn, task_id, fields["tags"])
        return get_task(conn, task_id)


def replace_tags(conn: sqlite3.Connection, task_id: int, tags: list[str]) -> None:
    """Único caminho de escrita de tags (AD-9); quem chama abre o `with conn:`."""
    conn.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
    conn.executemany(
        "INSERT INTO task_tags (task_id, tag) VALUES (?, ?)",
        [(task_id, t) for t in tags],
    )


# ponytail: N+1 em load_tags, trocar por um SELECT ... WHERE task_id IN (...) se a lista crescer
def load_tags(conn: sqlite3.Connection, task_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT tag FROM task_tags WHERE task_id = ? ORDER BY tag", (task_id,)
    )
    return [r["tag"] for r in rows]


def _to_task(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "due_date": row["due_date"],
        "tags": load_tags(conn, row["id"]),
        "done": bool(row["done"]),
    }


def get_task(conn: sqlite3.Connection, task_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _to_task(conn, row) if row else None


def list_tasks(
    conn: sqlite3.Connection,
    tag: str | None = None,
    window: tuple[str | None, str] | None = None,
) -> list[dict]:
    """`window` = limites inclusivos prontos de `domain.window_bounds` (AD-3)."""
    conds, params = [], []
    if tag is not None:
        # EXISTS, nunca JOIN: a tarefa volta uma vez e com todas as tags (AD-9).
        conds.append(
            "EXISTS (SELECT 1 FROM task_tags tt"
            " WHERE tt.task_id = tasks.id AND tt.tag = ?)"
        )
        params.append(tag)
    if window is not None:
        start, end = window
        conds.append("done = 0")
        if start is not None:
            conds.append("due_date >= ?")
            params.append(start)
        conds.append("due_date <= ?")
        params.append(end)
    where = f" WHERE {' AND '.join(conds)}" if conds else ""
    rows = conn.execute(
        f"SELECT * FROM tasks{where} ORDER BY due_date, id", params
    ).fetchall()
    return [_to_task(conn, r) for r in rows]


def delete_task(conn: sqlite3.Connection, task_id: int) -> bool:
    """Exclui a tarefa (tags caem pelo ON DELETE CASCADE); devolve se existia."""
    with conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cur.rowcount == 1
