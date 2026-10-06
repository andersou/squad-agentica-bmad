import inspect
import os
import re
import sqlite3
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from tarefas import api, domain, repo
from tarefas.domain import Janela, Tarefa

SRC = Path(__file__).parent.parent / "src" / "tarefas"
JANELAS = [j.value for j in Janela]


def _nova(client, titulo="x", prazo="2026-10-06", tags=("a",)):
    return client.post(
        "/tarefas", json={"titulo": titulo, "prazo": prazo, "tags": list(tags)}
    ).json()


def _janela(client, janela, **params):
    r = client.get("/tarefas", params={"janela": janela, **params})
    assert r.status_code == 200
    return r.json()


@pytest.mark.parametrize(
    "prazo, esperada",
    [
        ("2026-10-05", "vencidas"),
        ("2026-10-06", "hoje"),
        ("2026-10-07", "proximos-7-dias"),
        ("2026-10-13", "proximos-7-dias"),
        ("2026-10-14", None),
    ],
)
def test_limites(client, prazo, esperada):
    t = _nova(client, prazo=prazo)
    for janela in JANELAS:
        assert _janela(client, janela) == ([t] if janela == esperada else []), janela


def test_concluida_fora_das_janelas(client):
    t = _nova(client, prazo="2026-10-05")
    client.patch(f"/tarefas/{t['id']}", json={"concluida": True})
    for janela in JANELAS:
        assert _janela(client, janela) == [], janela
    client.patch(f"/tarefas/{t['id']}", json={"concluida": False})
    assert _janela(client, "vencidas") == [t]


def test_fuso_22h_em_sao_paulo(client):
    # 01:00 UTC de 10-07 ainda é 22h de 10-06 em São Paulo.
    api.app.dependency_overrides[api.agora] = lambda: datetime(
        2026, 10, 7, 1, 0, tzinfo=UTC
    )
    t = _nova(client, prazo="2026-10-06")
    assert _janela(client, "hoje") == [t]
    assert _janela(client, "vencidas") == []


def test_janela_com_tag(client):
    a = _nova(client, "a", "2026-10-03", ["backend"])
    _nova(client, "f", "2026-10-02", ["frontend"])
    b = _nova(client, "b", "2026-10-01", ["Backend", "api"])
    c = _nova(client, "c", "2026-10-03", ["backend"])
    _nova(client, "hoje", "2026-10-06", ["backend"])
    concluida = _nova(client, "z", "2026-10-02", ["backend"])
    client.patch(f"/tarefas/{concluida['id']}", json={"concluida": True})
    assert _janela(client, "vencidas", tag="Backend") == [b, a, c]


def test_sem_janela_traz_concluidas_e_futuras(client):
    vencida = _nova(client, prazo="2026-10-01")
    vencida = client.patch(f"/tarefas/{vencida['id']}", json={"concluida": True}).json()
    futura = _nova(client, prazo="2026-11-05")
    r = client.get("/tarefas")
    assert r.status_code == 200
    assert r.json() == [vencida, futura]


@pytest.mark.parametrize(
    "query",
    [
        "janela=amanha",
        "janela=",
        "janela=hoje&janela=vencidas",
        "janela=hoje&janela=hoje",
    ],
)
def test_janela_invalida(client, query):
    r = client.get(f"/tarefas?{query}")
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert isinstance(detail, list)
    assert [e["loc"] for e in detail] == [["query", "janela"]]


def test_janela_repetida_lista_valores(client):
    r = client.get("/tarefas?janela=amanha&janela=hoje")
    assert r.status_code == 422
    assert r.json()["detail"] == [
        {
            "type": "value_error",
            "loc": ["query", "janela"],
            "msg": "informe uma janela só",
            "input": ["amanha", "hoje"],
        }
    ]


@pytest.mark.parametrize(
    "agora, hoje",
    [
        (datetime(2026, 10, 7, 1, 0, tzinfo=UTC), date(2026, 10, 6)),
        (datetime(2026, 10, 7, 3, 0, tzinfo=UTC), date(2026, 10, 7)),
    ],
)
def test_domain_hoje(agora, hoje):
    assert domain.hoje(agora) == hoje


@pytest.mark.parametrize(
    "janela, esperado",
    [
        (Janela.VENCIDAS, (None, date(2026, 10, 5))),
        (Janela.HOJE, (date(2026, 10, 6), date(2026, 10, 6))),
        (Janela.PROXIMOS_7_DIAS, (date(2026, 10, 7), date(2026, 10, 13))),
    ],
)
def test_domain_intervalo(janela, esperado):
    assert domain.intervalo(janela, date(2026, 10, 6)) == esperado


def test_repo_listar_de_ate_sem_pendentes(client):
    _nova(client, "antes", "2026-10-04")
    t = _nova(client, "dentro", "2026-10-05")
    client.patch(f"/tarefas/{t['id']}", json={"concluida": True})
    _nova(client, "depois", "2026-10-07")
    conn = sqlite3.connect(os.environ["TAREFAS_DB"])
    try:
        tarefas = repo.listar(conn, de=date(2026, 10, 5), ate=date(2026, 10, 6))
    finally:
        conn.close()
    assert tarefas == [Tarefa(t["id"], "dentro", date(2026, 10, 5), ["a"], True)]


def test_openapi_documenta_janela(client):
    doc = client.get("/openapi.json").json()
    params = doc["paths"]["/tarefas"]["get"]["parameters"]
    janela = next(p for p in params if p["name"] == "janela")
    assert janela["in"] == "query"
    assert janela["required"] is False
    assert "uma janela por chamada" in janela["description"]
    assert doc["components"]["schemas"]["Janela"]["enum"] == JANELAS


RELOGIO = re.compile(r"\b(today|now|utcnow|localtime|gmtime)\b|time\.time")


def test_relogio_lido_so_em_api_agora():
    leituras = [
        (a.name, m.group())
        for a in SRC.glob("*.py")
        for m in RELOGIO.finditer(a.read_text())
    ]
    assert leituras == [("api.py", "now")]
    assert RELOGIO.search(inspect.getsource(api.agora))


def test_agora_utc_aware():
    agora = api.agora()
    assert agora.tzinfo is not None
    assert agora.utcoffset() == timedelta(0)
