from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")


def now() -> datetime:
    """Único ponto do código que lê o relógio (AD-2)."""
    return datetime.now(UTC)


def today(now: datetime) -> date:
    return now.astimezone(TZ).date()
