import ast
import os
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pytest

from tarefas import api, repo
from tarefas.domain import Tarefa

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
        {"titulo": "\x1f", "prazo": "2026-10-06"},
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


def _gravar(client, via, campos):
    # Mesmo limite no POST e no PATCH: os dois schemas usam Titulo e Tags.
    if via == "post":
        return client.post(
            "/tarefas", json={"titulo": "x", "prazo": "2026-10-06", **campos}
        )
    t = _nova(client)
    return client.patch(f"/tarefas/{t['id']}", json=campos)


@pytest.mark.parametrize("via", ["post", "patch"])
def test_titulo_com_200_caracteres_e_aceito(client, via):
    # \x1f é espaço para str.strip(), mas não para o strip_whitespace do Pydantic.
    r = _gravar(client, via, {"titulo": " \x1f" + "a" * 200 + "\x1f "})
    assert r.status_code == {"post": 201, "patch": 200}[via]
    assert r.json()["titulo"] == "a" * 200
    assert [t["titulo"] for t in client.get("/tarefas").json()] == ["a" * 200]


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


@pytest.mark.parametrize("via", ["post", "patch"])
def test_tag_com_50_caracteres_e_aceita(client, via):
    r = _gravar(client, via, {"tags": [" \x1f" + "a" * 50 + "\x1f "]})
    assert r.status_code == {"post": 201, "patch": 200}[via]
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


def _tarefas_com_tags(client):
    backend = _nova(client, "b", "2026-10-02", ["api", "Backend", "urgente"])
    backend = client.patch(f"/tarefas/{backend['id']}", json={"concluida": True}).json()
    _nova(client, "l", "2026-10-01", ["backend-legado"])
    _nova(client, "f", "2026-10-03", ["frontend"])
    _nova(client, "s", "2026-10-04", [])
    return backend


@pytest.mark.parametrize("tag", ["BACKEND", " backend "])
def test_filtrar_por_tag(client, tag):
    backend = _tarefas_com_tags(client)
    r = client.get("/tarefas", params={"tag": tag})
    assert r.status_code == 200
    assert r.json() == [backend]
    assert backend["concluida"] is True
    assert backend["tags"] == ["api", "Backend", "urgente"]


def test_filtrar_por_tag_ordenado(client):
    a = _nova(client, "a", "2026-10-10", ["backend"])
    _nova(client, "x", "2026-10-01", ["outra"])
    b = _nova(client, "b", "2026-10-05", ["Backend"])
    c = _nova(client, "c", "2026-10-10", ["backend"])
    r = client.get("/tarefas?tag=backend")
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [b["id"], a["id"], c["id"]]


def test_filtrar_por_tag_sem_match(client):
    _tarefas_com_tags(client)
    r = client.get("/tarefas?tag=inexistente")
    assert r.status_code == 200
    assert r.json() == []


def test_listar_sem_tag_traz_todas(client):
    _tarefas_com_tags(client)
    r = client.get("/tarefas")
    assert r.status_code == 200
    assert [t["titulo"] for t in r.json()] == ["l", "b", "f", "s"]


@pytest.mark.parametrize(
    "query, msg, entrada",
    [
        ("tag=a&tag=b", "informe uma tag só", ["a", "b"]),
        ("tag=a&tag=a", "informe uma tag só", ["a", "a"]),
        ("tag=", "tag vazia", ""),
        ("tag=%20%20", "tag vazia", "  "),
        (
            f"tag=%20{'a' * 51}%20",
            "tag deve ter até 50 caracteres",
            f" {'a' * 51} ",
        ),
    ],
)
def test_filtrar_por_tag_invalida(client, query, msg, entrada):
    r = client.get(f"/tarefas?{query}")
    assert r.status_code == 422
    assert r.json()["detail"] == [
        {"type": "value_error", "loc": ["query", "tag"], "msg": msg, "input": entrada}
    ]


def test_filtrar_por_tag_com_50_caracteres(client):
    t = _nova(client, tags=["a" * 50])
    _nova(client, tags=["b"])
    r = client.get("/tarefas", params={"tag": " " + "A" * 50 + " "})
    assert r.status_code == 200
    assert r.json() == [t]


def test_repo_listar_por_tag(client):
    t = _nova(client, tags=["x", "Straße"])
    _nova(client, tags=["strass"])
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        tarefas = repo.listar(conn, tag="  STRASSE ")
    finally:
        conn.close()
    assert tarefas == [Tarefa(t["id"], "x", date(2026, 10, 6), ["x", "Straße"], False)]


def test_openapi_documenta_tag(client):
    params = client.get("/openapi.json").json()["paths"]["/tarefas"]["get"][
        "parameters"
    ]
    tag = next(p for p in params if p["name"] == "tag")
    assert tag["in"] == "query"
    assert tag["required"] is False
    assert tag["schema"]["type"] == "array"
    assert tag["schema"]["items"] == {"type": "string"}
    assert "uma tag por chamada" in tag["description"]


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


def _tags_no_banco(id):
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        return conn.execute(
            "SELECT nome, nome_norm FROM tarefa_tag WHERE tarefa_id = ? ORDER BY rowid",
            (id,),
        ).fetchall()
    finally:
        conn.close()


def _linhas_tag(id):
    return len(_tags_no_banco(id))


def test_excluir(client):
    excluida = client.post(
        "/tarefas", json={"titulo": "x", "prazo": "2026-10-06", "tags": ["a", "b"]}
    ).json()["id"]
    outra = client.post(
        "/tarefas", json={"titulo": "y", "prazo": "2026-10-07", "tags": ["a"]}
    ).json()
    assert _linhas_tag(excluida) == 2
    r = client.delete(f"/tarefas/{excluida}")
    assert r.status_code == 204
    assert r.content == b""
    assert client.get("/tarefas").json() == [outra]
    assert _linhas_tag(excluida) == 0


def test_excluir_inexistente(client):
    id = client.post("/tarefas", json={"titulo": "x", "prazo": "2026-10-06"}).json()[
        "id"
    ]
    assert client.delete(f"/tarefas/{id}").status_code == 204
    outra = client.post("/tarefas", json={"titulo": "y", "prazo": "2026-10-07"}).json()
    for alvo in (id, 999):
        r = client.delete(f"/tarefas/{alvo}")
        assert r.status_code == 404
        assert r.json() == {"detail": "tarefa não encontrada"}
    assert client.get("/tarefas").json() == [outra]


@pytest.mark.parametrize(
    "id, status",
    [
        (2**63, 422),
        (-(2**63) - 1, 422),
        ("abc", 422),
        ("1.5", 422),
        (2**63 - 1, 404),
        (-(2**63), 404),
    ],
)
def test_excluir_id_limites(client, id, status):
    r = client.delete(f"/tarefas/{id}")
    assert r.status_code == status
    if status == 404:
        assert r.json() == {"detail": "tarefa não encontrada"}
    else:
        assert "detail" in r.json()


@pytest.mark.parametrize("alvo", ["1.0", "+1", "%201", "1_0"])
def test_excluir_id_nao_canonico(client, alvo):
    for i in range(10):
        client.post("/tarefas", json={"titulo": f"t{i}", "prazo": "2026-10-06"})
    antes = client.get("/tarefas").json()
    assert client.delete(f"/tarefas/{alvo}").status_code == 422
    assert client.get("/tarefas").json() == antes


def test_repo_excluir_inexistente(client):
    outra = client.post("/tarefas", json={"titulo": "y", "prazo": "2026-10-07"}).json()
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        assert repo.excluir(conn, outra["id"] + 1) is False
    finally:
        conn.close()
    assert client.get("/tarefas").json() == [outra]


def _nova(client, titulo="x", prazo="2026-10-06", tags=("a",)):
    return client.post(
        "/tarefas", json={"titulo": titulo, "prazo": prazo, "tags": list(tags)}
    ).json()


def test_editar_concluir(client):
    # Outra tarefa antes na ordem: a resposta tem de ser a editada, não a primeira.
    antes = _nova(client, "antes", "2026-10-01")
    t = _nova(client)
    r = client.patch(f"/tarefas/{t['id']}", json={"concluida": True})
    assert r.status_code == 200
    assert r.json() == {**t, "concluida": True}
    assert client.get("/tarefas").json() == [antes, {**t, "concluida": True}]
    r = client.patch(f"/tarefas/{t['id']}", json={"concluida": False})
    assert r.json() == t


def test_editar_corpo_vazio(client):
    t = _nova(client)
    r = client.patch(f"/tarefas/{t['id']}", json={})
    assert r.status_code == 200
    assert r.json() == t
    assert client.get("/tarefas").json() == [t]


def test_editar_tags(client):
    t = _nova(client, tags=["velha", "outra"])
    outra = _nova(client, tags=["Infra"])
    url = f"/tarefas/{t['id']}"
    r = client.patch(url, json={"tags": ["Infra", "infra", " Straße "]})
    assert r.status_code == 200
    assert r.json()["tags"] == ["Infra", "Straße"]
    assert _tags_no_banco(t["id"]) == [("Infra", "infra"), ("Straße", "strasse")]
    r = client.patch(url, json={"titulo": "Outro"})
    assert r.json() == {**t, "titulo": "Outro", "tags": ["Infra", "Straße"]}
    r = client.patch(url, json={"tags": []})
    assert r.json()["tags"] == []
    assert _tags_no_banco(t["id"]) == []
    assert _tags_no_banco(outra["id"]) == [("Infra", "infra")]


def test_editar_titulo_e_prazo(client):
    a = _nova(client, "a", "2026-10-05")
    b = _nova(client, "b", "2026-10-06")
    r = client.patch(
        f"/tarefas/{b['id']}", json={"titulo": " y ", "prazo": "2026-10-01"}
    )
    assert r.status_code == 200
    assert r.json() == {**b, "titulo": "y", "prazo": "2026-10-01"}
    assert [t["id"] for t in client.get("/tarefas").json()] == [b["id"], a["id"]]


@pytest.mark.parametrize(
    "corpo",
    [
        {"titulo": None},
        {"prazo": None},
        {"tags": None},
        {"concluida": None},
        {"concluida": "true"},
        {"concluida": 1},
        {"concluida": 0},
        {"concluida": "false"},
        None,
        [],
        "x",
        {"desconhecido": 1},
        {"id": 99},
        {"titulo": ""},
        {"titulo": "   "},
        {"titulo": "a" * 201},
        {"prazo": "06/10/2026"},
        {"prazo": "2026-02-30"},
        {"prazo": "2026-10-06T00:00:00"},
        {"prazo": 20261006},
        {"tags": [""]},
        {"tags": ["   "]},
        {"tags": ["a" * 51]},
        {"tags": "backend"},
        {"tags": [1]},
        {"tags": [None]},
        {"titulo": "ok", "concluida": "true"},
    ],
)
def test_editar_corpo_invalido(client, corpo):
    t = _nova(client)
    for alvo in (t["id"], t["id"] + 1):
        r = client.patch(f"/tarefas/{alvo}", json=corpo)
        assert r.status_code == 422
        assert "detail" in r.json()
    assert client.get("/tarefas").json() == [t]


def test_editar_inexistente(client):
    excluida = _nova(client)
    assert client.delete(f"/tarefas/{excluida['id']}").status_code == 204
    t = _nova(client)
    for alvo in (excluida["id"], 999):
        r = client.patch(f"/tarefas/{alvo}", json={"titulo": "z", "tags": ["b"]})
        assert r.status_code == 404
        assert r.json() == {"detail": "tarefa não encontrada"}
    assert client.get("/tarefas").json() == [t]
    assert _linhas_tag(excluida["id"]) == 0


@pytest.mark.parametrize(
    "id, status",
    [
        (2**63, 422),
        (-(2**63) - 1, 422),
        ("1_0", 422),
        ("abc", 422),
        (2**63 - 1, 404),
        (-(2**63), 404),
    ],
)
def test_editar_id_limites(client, id, status):
    for i in range(10):
        _nova(client, f"t{i}")
    antes = client.get("/tarefas").json()
    r = client.patch(f"/tarefas/{id}", json={"titulo": "z"})
    assert r.status_code == status
    if status == 404:
        assert r.json() == {"detail": "tarefa não encontrada"}
    else:
        assert "detail" in r.json()
    assert client.get("/tarefas").json() == antes


def test_repo_editar_atomico_com_tags_colidindo(client):
    t = _nova(client, tags=["velha"])
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        with pytest.raises(sqlite3.IntegrityError):
            repo.editar(conn, t["id"], {"titulo": "novo", "tags": ["a", "A"]})
    finally:
        conn.close()
    assert client.get("/tarefas").json() == [t]


def test_openapi_documenta_404(client):
    rota = client.get("/openapi.json").json()["paths"]["/tarefas/{id}"]
    assert "404" in rota["patch"]["responses"]
    assert "404" in rota["delete"]["responses"]


def test_repo_editar_inexistente(client):
    t = _nova(client)
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        assert repo.editar(conn, t["id"] + 1, {"tags": ["b"]}) is None
    finally:
        conn.close()
    assert _linhas_tag(t["id"] + 1) == 0
    assert client.get("/tarefas").json() == [t]


def test_repo_editar_bloqueia_exclusao_concorrente(client):
    t = _nova(client)
    caminho = os.environ["TAREFAS_DB"]
    bloqueios = []

    class ConexaoEspia(sqlite3.Connection):
        def execute(self, sql, *args):
            cur = super().execute(sql, *args)
            if sql.startswith("SELECT") and not bloqueios:
                # Logo depois da conferência, outra conexão tenta excluir.
                outra = sqlite3.connect(caminho, timeout=0)
                try:
                    with pytest.raises(sqlite3.OperationalError):
                        outra.execute("DELETE FROM tarefa WHERE id = ?", (t["id"],))
                    bloqueios.append(sql)
                finally:
                    outra.close()
            return cur

    conn = sqlite3.connect(caminho, factory=ConexaoEspia)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        editada = repo.editar(conn, t["id"], {"tags": ["c"], "concluida": True})
        assert client.get("/tarefas").json() == [
            {**t, "tags": ["c"], "concluida": True}
        ]
        # Com a conexão do editar ainda aberta, o lock já foi liberado.
        nova = sqlite3.connect(caminho, timeout=0)
        try:
            with nova:
                nova.execute("DELETE FROM tarefa WHERE id = ?", (t["id"],))
        finally:
            nova.close()
    finally:
        conn.close()
    assert len(bloqueios) == 1
    assert editada == Tarefa(t["id"], "x", date(2026, 10, 6), ["c"], True)
    assert client.get("/tarefas").json() == []


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
        for proibido in (
            "lower(",
            "upper(",
            "casefold",
            "nocase",
            "title(",
            "swapcase(",
            "normalize(",
            "collate",
        ):
            assert proibido not in texto, (modulo, proibido)


def test_id_no_openapi_com_minimum_e_maximum(client):
    caminho = client.get("/openapi.json").json()["paths"]["/tarefas/{id}"]
    for metodo in ("patch", "delete"):
        schema = caminho[metodo]["parameters"][0]["schema"]
        assert schema["minimum"] == -(2**63), metodo
        assert schema["maximum"] == 2**63 - 1, metodo


def test_conexao_usada_em_outra_thread(client):
    # O FastAPI abre a dependência e roda a rota em threads diferentes do pool.
    # O TestClient não reproduz isso, então sem check_same_thread=False só o
    # uvicorn real quebraria (AD-8).
    gen = api.conexao()
    conn = next(gen)
    try:
        with ThreadPoolExecutor(1) as ex:
            assert ex.submit(lambda: conn.execute("SELECT 1").fetchone()).result() == (
                1,
            )
    finally:
        gen.close()
