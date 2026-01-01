from datetime import date, timedelta
import calendar


def period_to_dates(key: str):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    if key == "CURRENT_WEEK":
        return week_start, week_start + timedelta(days=7)

    if key == "PREVIOUS_WEEK":
        start = week_start - timedelta(days=7)
        return start, start + timedelta(days=7)

    if key == "CURRENT_MONTH":
        start = date(today.year, today.month, 1)
        end = date(
            today.year, today.month, calendar.monthrange(today.year, today.month)[1]
        )
        return start, end

    if key == "PREVIOUS_MONTH":
        m = today.month - 1 or 12
        y = today.year if today.month > 1 else today.year - 1
        start = date(y, m, 1)
        end = date(y, m, calendar.monthrange(y, m)[1])
        return start, end

    raise ValueError(f"Période inconnue: {key}")
