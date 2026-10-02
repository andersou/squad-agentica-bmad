import pytest


def create(client, title, due_date, tags=None):
    payload = {"title": title, "due_date": due_date}
    if tags is not None:
        payload["tags"] = tags
    resp = client.post("/tasks", json=payload)
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def tagged(client):
    a = create(client, "A", "2026-10-10", ["backend", "api"])
    b = create(client, "B", "2026-10-05", ["infra"])
    c = create(client, "C", "2026-10-05", ["backend"])
    d = create(client, "D", "2026-10-01")
    return a, b, c, d


@pytest.mark.parametrize("tag", ["Backend", " BACKEND "])
def test_filter_by_tag(client, tagged, tag):
    a, _, c, _ = tagged
    resp = client.get("/tasks", params={"tag": tag})
    assert resp.status_code == 200
    assert resp.json() == [c, a]
    assert resp.json()[1]["tags"] == ["api", "backend"]


def test_filter_unknown_tag(client, tagged):
    resp = client.get("/tasks", params={"tag": "nada"})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.parametrize("tag", ["", "  "])
def test_filter_empty_tag(client, tag):
    resp = client.get("/tasks", params={"tag": tag})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"
    assert resp.json()["error"]["field"] == "tag"


def test_filter_includes_done(client, tagged):
    a = tagged[0]
    done = client.patch(f"/tasks/{a['id']}", json={"done": True}).json()
    assert done in client.get("/tasks", params={"tag": "api"}).json()


# Janelas de prazo (FR7/FR8). "Hoje" = 2026-10-02 em São Paulo.
BASE_NOW = "2026-10-02T15:00Z"


@pytest.fixture
def windowed(client, set_now):
    set_now(BASE_NOW)
    tasks = {
        d: create(client, d, f"2026-10-{d}") for d in ("01", "02", "03", "09", "10")
    }
    done = create(client, "feita", "2026-10-01")
    client.patch(f"/tasks/{done['id']}", json={"done": True})
    return tasks


def due(client, window, **params):
    resp = client.get("/tasks", params={"due": window, **params})
    assert resp.status_code == 200
    return resp.json()


@pytest.mark.parametrize(
    ("window", "expected"),
    [("overdue", ["01"]), ("today", ["02"]), ("next7", ["03", "09"])],
)
def test_due_windows(client, windowed, window, expected):
    assert due(client, window) == [windowed[d] for d in expected]


def test_due_day_turn_uses_sao_paulo(client, windowed, set_now):
    set_now("2026-10-03T01:00Z")  # UTC já é dia 3; São Paulo ainda é dia 2, 22h
    assert due(client, "today") == [windowed["02"]]
    assert windowed["02"] not in due(client, "overdue")


def test_due_done_leaves_and_returns(client, windowed):
    task = windowed["02"]
    client.patch(f"/tasks/{task['id']}", json={"done": True})
    for window in ("overdue", "today", "next7"):
        assert all(t["id"] != task["id"] for t in due(client, window))
    client.patch(f"/tasks/{task['id']}", json={"done": False})
    assert due(client, "today") == [task]


@pytest.mark.parametrize("value", ["semana", ""])
def test_due_invalid(client, value):
    resp = client.get("/tasks", params={"due": value})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"
    assert resp.json()["error"]["field"] == "due"


@pytest.mark.parametrize("tag", ["backend", "Backend"])
def test_tag_and_due_intersect(client, set_now, tag):
    set_now(BASE_NOW)
    create(client, "sem tag", "2026-09-30", ["infra"])
    hit = create(client, "com tag", "2026-10-01", ["backend", "api"])
    create(client, "fora da janela", "2026-10-05", ["backend"])
    assert due(client, "overdue", tag=tag) == [hit]
    assert hit["tags"] == ["api", "backend"]
