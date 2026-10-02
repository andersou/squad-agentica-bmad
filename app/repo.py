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


def insert_task(conn: sqlite3.Connection, title: str, due_date: str) -> int:
    with conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, due_date) VALUES (?, ?)", (title, due_date)
        )
    return cur.lastrowid


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


def list_tasks(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM tasks ORDER BY due_date, id").fetchall()
    return [_to_task(conn, r) for r in rows]
