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


def test_tags_normalizadas(client):
    r = client.post(
        "/tarefas",
        json={
            "titulo": "x",
            "prazo": "2026-10-06",
            "tags": ["Backend", " api ", "backend"],
        },
    )
    assert r.status_code == 201
    assert r.json()["tags"] == ["Backend", "api"]
    assert [t["tags"] for t in client.get("/tarefas").json()] == [["Backend", "api"]]


@pytest.mark.parametrize("extra", [{}, {"tags": []}])
def test_sem_tags(client, extra):
    r = client.post("/tarefas", json={"titulo": "x", "prazo": "2026-10-06", **extra})
    assert r.status_code == 201
    assert r.json()["tags"] == []
    assert [t["tags"] for t in client.get("/tarefas").json()] == [[]]


def test_tag_com_50_caracteres_e_aceita(client):
    r = client.post(
        "/tarefas",
        json={"titulo": "x", "prazo": "2026-10-06", "tags": [" " + "a" * 50 + " "]},
    )
    assert r.status_code == 201
    assert r.json()["tags"] == ["a" * 50]
    assert [t["tags"] for t in client.get("/tarefas").json()] == [["a" * 50]]


@pytest.mark.parametrize(
    "tags",
    [[""], ["   "], [" " + "a" * 51 + " "], "backend", [1], [None], None],
)
def test_tags_invalidas(client, tags):
    r = client.post(
        "/tarefas", json={"titulo": "x", "prazo": "2026-10-06", "tags": tags}
    )
    assert r.status_code == 422
    assert "detail" in r.json()
    assert client.get("/tarefas").json() == []


def test_tags_comparadas_com_casefold(client):
    r = client.post(
        "/tarefas",
        json={"titulo": "x", "prazo": "2026-10-06", "tags": ["Straße", "STRASSE"]},
    )
    assert r.status_code == 201
    assert r.json()["tags"] == ["Straße"]
    assert [t["tags"] for t in client.get("/tarefas").json()] == [["Straße"]]


def test_listar_tags_de_varias_tarefas(client):
    ids = {}
    for nome, prazo, tags in [
        ("A", "2026-10-20", ["x"]),
        ("B", "2026-10-01", []),
        ("C", "2026-10-10", ["y", "z"]),
    ]:
        ids[nome] = client.post(
            "/tarefas", json={"titulo": nome, "prazo": prazo, "tags": tags}
        ).json()["id"]
    assert [(t["id"], t["tags"]) for t in client.get("/tarefas").json()] == [
        (ids["B"], []),
        (ids["C"], ["y", "z"]),
        (ids["A"], ["x"]),
    ]


def test_banco_da_story_1_1_ganha_tarefa_tag(client):
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        with conn:
            conn.execute(
                "CREATE TABLE tarefa("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "titulo TEXT NOT NULL, "
                "prazo TEXT NOT NULL, "
                "concluida INTEGER NOT NULL DEFAULT 0)"
            )
            conn.execute(
                "INSERT INTO tarefa(titulo, prazo) VALUES ('antiga', '2026-10-01')"
            )
    finally:
        conn.close()
    r = client.post(
        "/tarefas", json={"titulo": "nova", "prazo": "2026-10-06", "tags": ["a"]}
    )
    assert r.status_code == 201
    assert [t["tags"] for t in client.get("/tarefas").json()] == [[], ["a"]]


def test_criar_atomico_com_tags_colidindo(client):
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        repo.criar_schema(conn)
        with pytest.raises(sqlite3.IntegrityError):
            repo.criar(conn, "x", date(2026, 10, 6), ["a", "A"])
    finally:
        conn.close()
    assert client.get("/tarefas").json() == []


def test_persistencia(client):
    criada = client.post(
        "/tarefas", json={"titulo": "x", "prazo": "2026-10-06", "tags": ["b", "a"]}
    ).json()
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
        ["b", "a"],
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
    for modulo in ("api", "repo"):
        texto = (SRC / f"{modulo}.py").read_text().lower()
        for proibido in ("lower(", "upper(", "casefold", "nocase"):
            assert proibido not in texto, (modulo, proibido)
