from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from tarefas import api
from tarefas.api import app

# 12h em São Paulo de 2026-10-06. Ajustável no teste por dependency_overrides.
AGORA = datetime(2026, 10, 6, 15, 0, tzinfo=UTC)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TAREFAS_DB", str(tmp_path / "tarefas.db"))
    app.dependency_overrides[api.agora] = lambda: AGORA
    yield TestClient(app)
    app.dependency_overrides.clear()
