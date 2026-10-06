import ast
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pytest

from tarefas import repo

SRC = Path(__file__).parent.parent / "src" / "tarefas"


def test_criar_com_prazo_passado(client):
    r = client.post(
        "/tarefas", json={"titulo": "Migrar planilha", "prazo": "2026-10-01"}
    )
    assert r.status_code == 201
    corpo = r.json()
    assert isinstance(corpo.pop("id"), int)
    assert corpo == {
        "titulo": "Migrar planilha",
        "prazo": "2026-10-01",
        "tags": [],
        "concluida": False,
    }


def test_titulo_aparado(client):
    r = client.post("/tarefas", json={"titulo": "  x  ", "prazo": "2026-10-06"})
    assert r.status_code == 201
    assert r.json()["titulo"] == "x"
    assert [t["titulo"] for t in client.get("/tarefas").json()] == ["x"]


@pytest.mark.parametrize(
    "corpo",
    [
        {"prazo": "2026-10-06"},
        {"titulo": "x"},
        {"titulo": "", "prazo": "2026-10-06"},
        {"titulo": "   ", "prazo": "2026-10-06"},
        {"titulo": " " + "a" * 201 + " ", "prazo": "2026-10-06"},
        {"titulo": "x", "prazo": "06/10/2026"},
        {"titulo": "x", "prazo": "2026-02-30"},
        {"titulo": "x", "prazo": "2026-10-06T00:00:00"},
        {"titulo": "x", "prazo": 20261006},
        {"titulo": "x", "prazo": "2026-10-06", "concluida": False},
        {"titulo": "x", "prazo": "2026-10-06", "desconhecido": 1},
    ],
)
def test_corpo_invalido(client, corpo):
    r = client.post("/tarefas", json=corpo)
    assert r.status_code == 422
    assert "detail" in r.json()
    assert client.get("/tarefas").json() == []


def test_titulo_com_200_caracteres_e_aceito(client):
    r = client.post(
        "/tarefas", json={"titulo": " " + "a" * 200 + " ", "prazo": "2026-10-06"}
    )
    assert r.status_code == 201
    assert r.json()["titulo"] == "a" * 200


def test_tarefas_db_vazio_usa_padrao(client, tmp_path, monkeypatch):
    monkeypatch.setenv("TAREFAS_DB", "")
    monkeypatch.chdir(tmp_path)
    client.post("/tarefas", json={"titulo": "x", "prazo": "2026-10-06"})
    assert [t["titulo"] for t in client.get("/tarefas").json()] == ["x"]


def test_listar_ordenado_por_prazo_e_id(client):
    ids = {}
    for titulo, prazo in [
        ("c", "2026-10-20"),
        ("a", "2026-10-01"),
        ("b1", "2026-10-10"),
        ("b2", "2026-10-10"),
    ]:
        ids[titulo] = client.post(
            "/tarefas", json={"titulo": titulo, "prazo": prazo}
        ).json()["id"]
    # Sem índice, o scan por rowid já sai em ordem de id. Com (prazo, id DESC),
    # os empates só saem certos se o SQL tiver o `id ASC` (AD-4).
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        with conn:
            conn.execute("CREATE INDEX ix_desempate ON tarefa(prazo, id DESC)")
    finally:
        conn.close()
    r = client.get("/tarefas")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert [t["id"] for t in r.json()] == [ids["a"], ids["b1"], ids["b2"], ids["c"]]


def test_persistencia(client):
    criada = client.post("/tarefas", json={"titulo": "x", "prazo": "2026-10-06"}).json()
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        tarefas = repo.listar(conn)
    finally:
        conn.close()
    assert len(tarefas) == 1
    t = tarefas[0]
    assert (t.id, t.titulo, t.prazo, t.tags, t.concluida) == (
        criada["id"],
        "x",
        date(2026, 10, 6),
        [],
        False,
    )


def _imports(modulo):
    arvore = ast.parse((SRC / f"{modulo}.py").read_text())
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes |= {a.name for a in no.names}
        elif isinstance(no, ast.ImportFrom):
            base = no.module or ""
            if no.level:
                base = f"tarefas.{base}" if base else "tarefas"
            nomes.add(base)
            nomes |= {f"{base}.{a.name}" for a in no.names}
    return nomes


def test_camadas():
    domain = _imports("domain")
    assert all(n.split(".")[0] in sys.stdlib_module_names for n in domain), domain
    assert "sqlite3" not in domain
    assert not any(
        n == "tarefas.api" or n.startswith("tarefas.api.") for n in _imports("repo")
    )


def test_criar_com_tags_falha_ate_story_1_2(client):
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        repo.criar_schema(conn)
        with pytest.raises(NotImplementedError):
            repo.criar(conn, "x", date(2026, 10, 6), ["a"])
    finally:
        conn.close()
    assert client.get("/tarefas").json() == []
