from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")


def now() -> datetime:
    """Único ponto do código que lê o relógio (AD-2)."""
    return datetime.now(UTC)


def today(now: datetime) -> date:
    return now.astimezone(TZ).date()


def window_bounds(window: str, today: date) -> tuple[str | None, str]:
    """Limites inclusivos (início, fim) em YYYY-MM-DD da janela (AD-3); None = aberto."""
    day = timedelta(days=1)
    start, end = {
        "overdue": (None, today - day),
        "today": (today, today),
        "next7": (today + day, today + 7 * day),
    }[window]
    return (start and start.isoformat()), end.isoformat()


def normalize_tags(tags: list[str]) -> list[str]:
    """Único dono da normalização de tags (AD-9): strip + casefold, únicas, ordenadas."""
    out = {t.strip().casefold() for t in tags}
    if "" in out:
        raise ValueError("tag vazia")
    return sorted(out)
