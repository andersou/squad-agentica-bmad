import os
import re
import sqlite3
from collections.abc import Iterator
from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Response
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    StrictBool,
    StringConstraints,
)

from tarefas import repo
from tarefas.domain import Tarefa, normalizar_tags

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


def _aparar(v):
    # str.strip(), o mesmo do domain: o strip_whitespace do Pydantic mantém \x1c-\x1f.
    return v.strip() if isinstance(v, str) else v


Prazo = Annotated[date, BeforeValidator(_prazo_iso)]
Titulo = Annotated[
    str, BeforeValidator(_aparar), StringConstraints(min_length=1, max_length=200)
]
Tags = Annotated[
    list[Annotated[str, BeforeValidator(_aparar), StringConstraints(max_length=50)]],
    AfterValidator(normalizar_tags),
]


def _id_inteiro(v):
    if not isinstance(v, str) or not re.fullmatch(r"-?\d+", v):
        raise ValueError("id deve ser um inteiro")
    return v


# Path antes do BeforeValidator: na ordem inversa o OpenAPI sai com ge/le crus.
Id = Annotated[int, Path(ge=-(2**63), le=2**63 - 1), BeforeValidator(_id_inteiro)]


class TarefaCriar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titulo: Titulo
    prazo: Prazo
    tags: Tags = []


class TarefaEditar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Default None sem Optional: omitido some do exclude_unset, null dá 422.
    titulo: Titulo = None
    prazo: Prazo = None
    tags: Tags = None
    concluida: StrictBool = None


@app.post("/tarefas", status_code=201)
def criar_tarefa(dados: TarefaCriar, conn: Conexao) -> Tarefa:
    return repo.criar(conn, dados.titulo, dados.prazo, dados.tags)


@app.get("/tarefas")
def listar_tarefas(conn: Conexao) -> list[Tarefa]:
    return repo.listar(conn)


@app.patch("/tarefas/{id}", responses={404: {"description": "tarefa não encontrada"}})
def editar_tarefa(id: Id, dados: TarefaEditar, conn: Conexao) -> Tarefa:
    tarefa = repo.editar(conn, id, dados.model_dump(exclude_unset=True))
    if tarefa is None:
        raise HTTPException(404, "tarefa não encontrada")
    return tarefa


@app.delete(
    "/tarefas/{id}",
    status_code=204,
    responses={404: {"description": "tarefa não encontrada"}},
)
def excluir_tarefa(id: Id, conn: Conexao) -> Response:
    if not repo.excluir(conn, id):
        raise HTTPException(404, "tarefa não encontrada")
    return Response(status_code=204)
