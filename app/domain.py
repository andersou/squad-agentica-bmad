from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")


def now() -> datetime:
    """Único ponto do código que lê o relógio (AD-2)."""
    return datetime.now(UTC)


def today(now: datetime) -> date:
    return now.astimezone(TZ).date()


def normalize_tags(tags: list[str]) -> list[str]:
    """Único dono da normalização de tags (AD-9): strip + casefold, únicas, ordenadas."""
    out = {t.strip().casefold() for t in tags}
    if "" in out:
        raise ValueError("tag vazia")
    return sorted(out)
