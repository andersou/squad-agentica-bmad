from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")


@dataclass
class Tarefa:
    id: int
    titulo: str
    prazo: date
    tags: list[str]
    concluida: bool


def norm_tag(s: str) -> str:
    return s.strip().casefold()


def normalizar_tags(lista: list[str]) -> list[str]:
    tags, vistas = [], set()
    for tag in lista:
        tag = tag.strip()
        if not tag:
            raise ValueError("tag vazia")
        norm = norm_tag(tag)
        if norm not in vistas:
            vistas.add(norm)
            tags.append(tag)
    return tags


class Janela(StrEnum):
    VENCIDAS = "vencidas"
    HOJE = "hoje"
    PROXIMOS_7_DIAS = "proximos-7-dias"


def hoje(agora: datetime) -> date:
    return agora.astimezone(FUSO).date()


def intervalo(janela: Janela, hoje: date) -> tuple[date | None, date | None]:
    """Limites inclusivos de prazo da janela; None é sem limite."""
    um_dia = timedelta(days=1)
    match janela:
        case Janela.VENCIDAS:
            return None, hoje - um_dia
        case Janela.HOJE:
            return hoje, hoje
        case Janela.PROXIMOS_7_DIAS:
            return hoje + um_dia, hoje + 7 * um_dia
