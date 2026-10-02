import sqlite3
from collections.abc import Iterator
from datetime import date, datetime
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    StrictBool,
    StringConstraints,
)

from app import domain, repo


def _valid_date(v: str) -> str:
    date.fromisoformat(v)
    return v


# Tipos únicos por campo (AD-4); reaproveitar no PATCH.
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
DueDate = Annotated[
    str,
    StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}$"),
    AfterValidator(_valid_date),
]
# Item valida sozinho para o 422 sair com field "tags.N"; a lista deduplica e ordena (AD-9).
Tag = Annotated[str, AfterValidator(lambda v: domain.normalize_tags([v])[0])]
Tags = Annotated[list[Tag], AfterValidator(domain.normalize_tags)]


class Due(str, Enum):
    overdue = "overdue"
    today = "today"
    next7 = "next7"


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Title
    due_date: DueDate
    tags: Tags = []


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Tipo não opcional com default None: omitir vale, null explícito dá 422 (AD-4).
    title: Title = None
    due_date: DueDate = None
    done: StrictBool = None
    tags: Tags = None


class Task(BaseModel):
    id: int
    title: str
    due_date: str
    tags: list[str]
    done: bool


def get_db() -> Iterator[sqlite3.Connection]:
    conn = repo.connect()
    try:
        yield conn
    finally:
        conn.close()


Db = Annotated[sqlite3.Connection, Depends(get_db)]
# Alias "id" faz o 422 de path sair com field "id" (AD-7).
TaskId = Annotated[int, Path(alias="id")]

router = APIRouter()


@router.post("/tasks", status_code=201, response_model=Task)
def create_task(body: TaskCreate, conn: Db):
    task_id = repo.insert_task(conn, body.title, body.due_date, body.tags)
    return repo.get_task(conn, task_id)


@router.get("/tasks", response_model=list[Task])
def list_tasks(
    conn: Db,
    now: Annotated[datetime, Depends(domain.now)],
    tag: Annotated[Tag | None, Query()] = None,
    due: Due | None = None,
):
    if due is None:
        return repo.list_tasks(conn, tag=tag)
    start, end = domain.window_bounds(due.value, domain.today(now))
    return repo.list_tasks(conn, tag=tag, window=(start, end))


@router.get("/tasks/{id}", response_model=Task)
def get_task(task_id: TaskId, conn: Db):
    task = repo.get_task(conn, task_id)
    if task is None:
        raise HTTPException(404, detail="task_not_found")
    return task


@router.patch("/tasks/{id}", response_model=Task)
def patch_task(task_id: TaskId, body: TaskUpdate, conn: Db):
    if not repo.update_task(conn, task_id, body.model_dump(exclude_unset=True)):
        raise HTTPException(404, detail="task_not_found")
    return repo.get_task(conn, task_id)


@router.delete("/tasks/{id}", status_code=204)
def delete_task(task_id: TaskId, conn: Db):
    if not repo.delete_task(conn, task_id):
        raise HTTPException(404, detail="task_not_found")
    return Response(status_code=204)
