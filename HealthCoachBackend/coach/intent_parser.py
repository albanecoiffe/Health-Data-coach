from enum import Enum


class Intent(str, Enum):
    SUMMARY = "summary"
    STATS = "stats"
    COMPARE = "compare"
    UNKNOWN = "unknown"


SUMMARY_KEYWORDS = ["résume", "resume", "bilan", "récap", "recap"]

STATS_KEYWORDS = ["combien", "distance", "km", "kilomètre", "kilometre"]

COMPARE_KEYWORDS = ["compare", "comparé", "progression", "évolution", "vs"]


def detect_intent(message: str) -> Intent:
    msg = message.lower()

    if any(k in msg for k in SUMMARY_KEYWORDS):
        return Intent.SUMMARY

    if any(k in msg for k in STATS_KEYWORDS):
        return Intent.STATS

    if any(k in msg for k in COMPARE_KEYWORDS):
        return Intent.COMPARE

    return Intent.UNKNOWN
