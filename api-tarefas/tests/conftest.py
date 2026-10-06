import pytest
from fastapi.testclient import TestClient

from tarefas.api import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TAREFAS_DB", str(tmp_path / "tarefas.db"))
    return TestClient(app)
