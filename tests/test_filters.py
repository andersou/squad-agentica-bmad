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
