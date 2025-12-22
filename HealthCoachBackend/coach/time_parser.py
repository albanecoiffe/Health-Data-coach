from dataclasses import dataclass
from datetime import date
import re
from datetime import date, timedelta
from calendar import monthrange


@dataclass
class TimeQuery:
    type: str  # "week", "month", "year", "custom", "relative"
    offset: int | None = None
    start_date: date | None = None
    end_date: date | None = None


def parse_time_query(message: str) -> TimeQuery:
    msg = message.lower()

    # --- SEMAINE ---
    if "cette semaine" in msg:
        return TimeQuery(type="week", offset=0)

    if "semaine dernière" in msg:
        return TimeQuery(type="week", offset=-1)

    match = re.search(r"il y a (\d+) semaines?", msg)
    if match:
        return TimeQuery(type="week", offset=-int(match.group(1)))

    # --- MOIS ---
    if "ce mois" in msg:
        return TimeQuery(type="month", offset=0)

    if "mois dernier" in msg:
        return TimeQuery(type="month", offset=-1)

    # --- ANNÉE ---
    if "cette année" in msg:
        return TimeQuery(type="year", offset=0)

    # --- PÉRIODE PERSONNALISÉE ---
    match = re.search(r"du (\d{1,2}) au (\d{1,2})", msg)
    if match:
        start_day = int(match.group(1))
        end_day = int(match.group(2))
        today = date.today()
        return TimeQuery(
            type="custom",
            start_date=date(today.year, today.month, start_day),
            end_date=date(today.year, today.month, end_day),
        )

    # --- DÉFAUT ---
    return TimeQuery(type="week", offset=0)


def resolve_time_query(tq: TimeQuery) -> tuple[date, date]:
    today = date.today()

    if tq.type == "week":
        start = today - timedelta(days=today.weekday())
        start += timedelta(weeks=tq.offset)
        end = start + timedelta(days=6)
        return start, end

    if tq.type == "month":
        year = today.year
        month = today.month + tq.offset
        if month < 1:
            month += 12
            year -= 1
        if month > 12:
            month -= 12
            year += 1

        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
        return start, end

    if tq.type == "year":
        return date(today.year, 1, 1), date(today.year, 12, 31)

    if tq.type == "custom":
        return tq.start_date, tq.end_date

    # fallback
    return today, today
