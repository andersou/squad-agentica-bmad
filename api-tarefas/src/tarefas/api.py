import os
import re
import sqlite3
from collections.abc import Iterator
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    StrictBool,
    StringConstraints,
)

from tarefas import domain, repo
from tarefas.domain import Janela, Tarefa, normalizar_tags

app = FastAPI(title="api-tarefas")


def agora() -> datetime:
    # Única leitura do relógio (AD-2); os testes a substituem por override.
    return datetime.now(UTC)


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


TAG_MAX = 50

Prazo = Annotated[date, BeforeValidator(_prazo_iso)]
Titulo = Annotated[
    str, BeforeValidator(_aparar), StringConstraints(min_length=1, max_length=200)
]
Tags = Annotated[
    list[
        Annotated[str, BeforeValidator(_aparar), StringConstraints(max_length=TAG_MAX)]
    ],
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


def _erro_query(campo, msg, entrada):
    # RequestValidationError mantém o 422 em lista, no formato HTTPValidationError
    # que o OpenAPI anuncia (AD-7).
    raise RequestValidationError(
        [{"type": "value_error", "loc": ("query", campo), "msg": msg, "input": entrada}]
    )


@app.get("/tarefas")
def listar_tarefas(
    conn: Conexao,
    request: Request,
    agora_: Annotated[datetime, Depends(agora)],
    tag: Annotated[
        list[str],
        Query(
            default_factory=list,
            description=(
                "Filtra por tag, sem diferenciar maiúsculas nem espaços nas pontas: "
                f"uma tag por chamada, até {TAG_MAX} caracteres."
            ),
        ),
    ],
    janela: Annotated[
        Janela | None,
        Query(
            description=(
                "Só pendentes com prazo na janela, com hoje em America/Sao_Paulo: "
                "uma janela por chamada."
            )
        ),
    ] = None,
) -> list[Tarefa]:
    # O FastAPI pegaria o último valor repetido sem avisar (AD-6).
    janelas = request.query_params.getlist("janela")
    if len(janelas) > 1:
        _erro_query("janela", "informe uma janela só", janelas)
    valor = None
    if tag:
        # A checagem fica na rota (AD-6).
        motivo, entrada = None, tag
        if len(tag) > 1:
            motivo = "informe uma tag só"
        else:
            entrada = tag[0]
            valor = _aparar(entrada)
            if not valor:
                motivo = "tag vazia"
            elif len(valor) > TAG_MAX:
                motivo = f"tag deve ter até {TAG_MAX} caracteres"
        if motivo:
            _erro_query("tag", motivo, entrada)
    de = ate = None
    if janela is not None:
        de, ate = domain.intervalo(janela, domain.hoje(agora_))
    return repo.listar(conn, pendentes=janela is not None, de=de, ate=ate, tag=valor)


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
