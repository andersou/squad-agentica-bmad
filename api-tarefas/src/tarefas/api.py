import os
import re
import sqlite3
from collections.abc import Iterator
from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel, BeforeValidator, ConfigDict, StringConstraints

from tarefas import repo
from tarefas.domain import Tarefa

app = FastAPI(title="api-tarefas")


def conexao() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(
        os.environ.get("TAREFAS_DB") or "tarefas.db", check_same_thread=False
    )
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        repo.criar_schema(conn)
        yield conn
    finally:
        conn.close()


Conexao = Annotated[sqlite3.Connection, Depends(conexao)]


def _prazo_iso(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        raise ValueError("prazo deve ser YYYY-MM-DD")
    return v


Prazo = Annotated[date, BeforeValidator(_prazo_iso)]
Titulo = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class TarefaCriar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: Titulo
    prazo: Prazo


@app.post("/tarefas", status_code=201)
def criar_tarefa(dados: TarefaCriar, conn: Conexao) -> Tarefa:
    return repo.criar(conn, dados.titulo, dados.prazo, [])


@app.get("/tarefas")
def listar_tarefas(conn: Conexao) -> list[Tarefa]:
    return repo.listar(conn)
