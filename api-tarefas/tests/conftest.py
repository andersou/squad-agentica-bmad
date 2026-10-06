from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import domain
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TASKS_DB_PATH", str(tmp_path / "tasks.db"))
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def set_now(client):
    """Fixa o relógio (AD-2/AD-8): substitui só `domain.now`, nunca `today`."""

    def _set(instant_utc: str) -> None:
        app.dependency_overrides[domain.now] = lambda: datetime.fromisoformat(
            instant_utc
        )

    return _set
