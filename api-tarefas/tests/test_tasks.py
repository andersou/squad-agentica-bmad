import sqlite3
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from app import domain
from app.main import app


def create(client, title="Revisar PR", due_date="2026-10-10"):
    return client.post("/tasks", json={"title": title, "due_date": due_date})


def assert_error(resp, status, code, field):
    assert resp.status_code == status
    body = resp.json()
    assert "detail" not in body
    assert body["error"]["code"] == code
    assert body["error"]["field"] == field
    assert body["error"]["message"]


def test_create_task(client):
    resp = create(client)
    assert resp.status_code == 201
    body = resp.json()
    assert isinstance(body.pop("id"), int)
    assert body == {
        "title": "Revisar PR",
        "due_date": "2026-10-10",
        "tags": [],
        "done": False,
    }


@pytest.mark.parametrize("payload", [{}, {"title": ""}, {"title": "   "}])
def test_create_invalid_title(client, payload):
    resp = client.post("/tasks", json={**payload, "due_date": "2026-10-10"})
    assert_error(resp, 422, "validation_error", "title")
    assert client.get("/tasks").json() == []


@pytest.mark.parametrize(
    "due_date",
    [None, "2026-02-30", "2026-10-02T00:00:00Z", "02/10/2026", 1790899200, "20261002"],
)
def test_create_invalid_due_date(client, due_date):
    payload = {"title": "x"} | ({} if due_date is None else {"due_date": due_date})
    assert_error(
        client.post("/tasks", json=payload), 422, "validation_error", "due_date"
    )
    assert client.get("/tasks").json() == []


def test_create_past_due_date(client):
    resp = create(client, due_date="2020-01-01")
    assert resp.status_code == 201
    assert resp.json()["done"] is False


@pytest.mark.parametrize("extra", [{"done": True}, {"priority": 1}])
def test_create_extra_field(client, extra):
    payload = {"title": "x", "due_date": "2026-10-10"} | extra
    assert_error(
        client.post("/tasks", json=payload), 422, "validation_error", next(iter(extra))
    )
    assert client.get("/tasks").json() == []


def test_create_invalid_body(client):
    resp = client.post(
        "/tasks", content="[", headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_list_empty(client):
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_order(client):
    ids = [
        create(client, t, d).json()["id"]
        for t, d in [
            ("c", "2026-12-01"),
            ("a", "2026-10-05"),
            ("b", "2026-10-05"),
            ("z", "2026-01-01"),
        ]
    ]
    got = [t["id"] for t in client.get("/tasks").json()]
    assert got == [ids[3], ids[1], ids[2], ids[0]]


def test_get_task(client):
    task = create(client).json()
    resp = client.get(f"/tasks/{task['id']}")
    assert resp.status_code == 200
    assert resp.json() == task


def test_get_task_not_found(client):
    assert_error(client.get("/tasks/999"), 404, "not_found", "id")


def test_unknown_route(client):
    assert_error(client.get("/nada"), 404, "not_found", None)


def test_method_not_allowed(client):
    resp = client.put("/tasks")
    assert_error(resp, 405, "method_not_allowed", None)
    assert "allow" in resp.headers


def test_internal_error(client, monkeypatch):
    def boom(conn):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.repo.list_tasks", boom)
    with TestClient(app, raise_server_exceptions=False) as c:
        assert_error(c.get("/tasks"), 500, "internal_error", None)


def test_persistence_and_schema(client, tmp_path):
    task = create(client).json()
    with TestClient(app) as other:
        assert other.get(f"/tasks/{task['id']}").json() == task
    conn = sqlite3.connect(tmp_path / "tasks.db")
    names = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()
    assert {"tasks", "task_tags"} <= names


def test_today_uses_sao_paulo():
    assert domain.today(datetime.fromisoformat("2026-10-03T01:00Z")) == date(
        2026, 10, 2
    )


def test_set_now_overrides_clock(set_now):
    set_now("2026-10-02T15:00Z")
    assert app.dependency_overrides[domain.now]() == datetime.fromisoformat(
        "2026-10-02T15:00Z"
    )


# --- FR-3: editar e concluir (story 1.2) ---


def test_patch_title_only(client):
    task = create(client).json()
    resp = client.patch(f"/tasks/{task['id']}", json={"title": "  Novo  "})
    assert resp.status_code == 200
    assert resp.json() == task | {"title": "Novo"}
    assert client.get(f"/tasks/{task['id']}").json() == task | {"title": "Novo"}


def test_patch_due_date_reorders(client):
    a = create(client, "a", "2026-10-10").json()
    b = create(client, "b", "2026-10-11").json()
    resp = client.patch(f"/tasks/{a['id']}", json={"due_date": "2026-10-12"})
    assert resp.json()["due_date"] == "2026-10-12"
    assert [t["id"] for t in client.get("/tasks").json()] == [b["id"], a["id"]]


def test_patch_done_toggle(client):
    tid = create(client).json()["id"]
    resp = client.patch(f"/tasks/{tid}", json={"done": True})
    assert resp.status_code == 200
    assert resp.json()["done"] is True
    resp = client.patch(f"/tasks/{tid}", json={"done": False})
    assert resp.status_code == 200
    assert resp.json()["done"] is False


def test_patch_empty_body(client):
    task = create(client).json()
    resp = client.patch(f"/tasks/{task['id']}", json={})
    assert resp.status_code == 200
    assert resp.json() == task


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"title": ""}, "title"),
        ({"title": "   "}, "title"),
        ({"title": None}, "title"),
        ({"due_date": "2026-02-30"}, "due_date"),
        ({"due_date": "2026-10-02T00:00:00Z"}, "due_date"),
        ({"due_date": "02/10/2026"}, "due_date"),
        ({"due_date": 1790899200}, "due_date"),
        ({"due_date": None}, "due_date"),
        ({"done": "true"}, "done"),
        ({"done": 1}, "done"),
        ({"done": None}, "done"),
        ({"priority": 1}, "priority"),
        ({"id": 99}, "id"),
    ],
)
def test_patch_invalid(client, payload, field):
    task = create(client).json()
    resp = client.patch(f"/tasks/{task['id']}", json=payload)
    assert_error(resp, 422, "validation_error", field)
    assert client.get(f"/tasks/{task['id']}").json() == task


def test_patch_not_found(client):
    assert_error(
        client.patch("/tasks/999", json={"done": True}), 404, "not_found", "id"
    )


def test_delete_task(client):
    gone = create(client, title="Engano").json()
    kept = create(client, title="Fica").json()
    resp = client.delete(f"/tasks/{gone['id']}")
    assert resp.status_code == 204
    assert resp.content == b""
    assert_error(client.get(f"/tasks/{gone['id']}"), 404, "not_found", "id")
    assert client.get("/tasks").json() == [kept]


def test_delete_not_found(client):
    assert_error(client.delete("/tasks/999"), 404, "not_found", "id")
    task = create(client).json()
    assert client.delete(f"/tasks/{task['id']}").status_code == 204
    assert_error(client.delete(f"/tasks/{task['id']}"), 404, "not_found", "id")


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_invalid_task_id(client, method):
    kwargs = {"json": {"done": True}} if method == "patch" else {}
    resp = getattr(client, method)("/tasks/abc", **kwargs)
    assert_error(resp, 422, "validation_error", "id")


# Story 2.1: tags


def test_normalize_tags():
    assert domain.normalize_tags(["backend", " Backend ", "API"]) == ["api", "backend"]
    assert domain.normalize_tags([]) == []
    with pytest.raises(ValueError):
        domain.normalize_tags([" "])


def test_create_with_tags(client):
    payload = {"title": "x", "due_date": "2026-10-10"}
    resp = client.post(
        "/tasks", json=payload | {"tags": ["backend", " Backend ", "API"]}
    )
    assert resp.status_code == 201
    task = resp.json()
    assert task["tags"] == ["api", "backend"]
    assert client.get(f"/tasks/{task['id']}").json() == task
    assert client.post("/tasks", json=payload).json()["tags"] == []


INVALID_TAGS = [
    (["ok", "  "], "tags.1"),
    ([""], "tags.0"),
    ([1], "tags.0"),
    (None, "tags"),
    ("backend", "tags"),
]


@pytest.mark.parametrize(("tags", "field"), INVALID_TAGS)
def test_create_invalid_tags(client, tags, field):
    payload = {"title": "x", "due_date": "2026-10-10", "tags": tags}
    assert_error(client.post("/tasks", json=payload), 422, "validation_error", field)
    assert client.get("/tasks").json() == []


@pytest.mark.parametrize(("tags", "field"), INVALID_TAGS)
def test_patch_invalid_tags(client, tags, field):
    task = client.post(
        "/tasks", json={"title": "x", "due_date": "2026-10-10", "tags": ["api"]}
    ).json()
    resp = client.patch(f"/tasks/{task['id']}", json={"title": "novo", "tags": tags})
    assert_error(resp, 422, "validation_error", field)
    assert client.get(f"/tasks/{task['id']}").json() == task


def test_patch_tags(client):
    task = client.post(
        "/tasks",
        json={"title": "x", "due_date": "2026-10-10", "tags": ["api", "backend"]},
    ).json()
    url = f"/tasks/{task['id']}"
    assert client.patch(url, json={"title": "y"}).json()["tags"] == ["api", "backend"]
    assert client.patch(url, json={"done": True}).json()["tags"] == ["api", "backend"]
    assert client.patch(url, json={"tags": ["infra"]}).json()["tags"] == ["infra"]
    assert client.patch(url, json={"tags": []}).json()["tags"] == []
    assert client.get(url).json()["tags"] == []


def test_patch_tags_not_found(client):
    resp = client.patch("/tasks/999", json={"tags": ["a"]})
    assert_error(resp, 404, "not_found", "id")


def test_delete_cascades_tags(client):
    from app import repo

    task = client.post(
        "/tasks", json={"title": "x", "due_date": "2026-10-10", "tags": ["a", "b"]}
    ).json()
    assert client.delete(f"/tasks/{task['id']}").status_code == 204
    conn = repo.connect()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM task_tags WHERE task_id = ?", (task["id"],)
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 0


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_task_id_overflow(client, method):
    kwargs = {"json": {"done": True}} if method == "patch" else {}
    resp = getattr(client, method)(f"/tasks/{2**63}", **kwargs)
    assert_error(resp, 422, "validation_error", "id")


def test_patch_deleted_during_update(client, monkeypatch):
    """Exclusão concorrente entre a checagem e a releitura vira 404, não 500."""
    from app import repo

    task = create(client).json()
    real_replace = repo.replace_tags

    def delete_then_replace(conn, task_id, tags):
        other = sqlite3.connect(conn.execute("PRAGMA database_list").fetchone()[2])
        other.execute("PRAGMA busy_timeout = 0")
        try:
            # BEGIN IMMEDIATE segura o lock: o DELETE concorrente não entra no meio.
            with pytest.raises(sqlite3.OperationalError):
                other.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        finally:
            other.close()
        real_replace(conn, task_id, tags)

    monkeypatch.setattr(repo, "replace_tags", delete_then_replace)
    resp = client.patch(f"/tasks/{task['id']}", json={"tags": ["a"]})
    assert resp.status_code == 200
    assert resp.json()["tags"] == ["a"]


def test_other_http_status_kept():
    from starlette.exceptions import HTTPException

    from app.main import _http

    resp = _http(None, HTTPException(409))
    assert resp.status_code == 409
    assert b'"code":"http_error"' in resp.body
