import sqlite3
from collections.abc import Iterator
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    StrictBool,
    StringConstraints,
)

from app import repo


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


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Title
    due_date: DueDate


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Tipo não opcional com default None: omitir vale, null explícito dá 422 (AD-4).
    title: Title = None
    due_date: DueDate = None
    done: StrictBool = None


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

router = APIRouter()


@router.post("/tasks", status_code=201, response_model=Task)
def create_task(body: TaskCreate, conn: Db):
    return repo.get_task(conn, repo.insert_task(conn, body.title, body.due_date))


@router.get("/tasks", response_model=list[Task])
def list_tasks(conn: Db):
    return repo.list_tasks(conn)


@router.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, conn: Db):
    task = repo.get_task(conn, task_id)
    if task is None:
        raise HTTPException(404, detail="task_not_found")
    return task


@router.patch("/tasks/{task_id}", response_model=Task)
def patch_task(task_id: int, body: TaskUpdate, conn: Db):
    if not repo.update_task(conn, task_id, body.model_dump(exclude_unset=True)):
        raise HTTPException(404, detail="task_not_found")
    return repo.get_task(conn, task_id)
