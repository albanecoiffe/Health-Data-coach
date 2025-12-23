# Rôle : contrat API (entrée)
# Ce fichier définit ce que le frontend a le droit d’envoyer.
# Typiquement : ChatRequest, WeeklySnapshot, PeriodSnapshot, Totals, etc.
# C’est le contrat Swift ↔ Python


from pydantic import BaseModel
from datetime import date
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    snapshot: WeeklySnapshot


class Period(BaseModel):
    start: date
    end: date


class WeeklyTotals(BaseModel):
    distance_km: float
    duration_min: float
    sessions: int
    elevation_m: float
    avg_hr: Optional[float] = None


class WeeklySnapshot(BaseModel):
    week_label: str
    period: Period  # ✅ AJOUT
    totals: WeeklyTotals
    zones_percent: dict[str, float]
    daily_runs: list[dict]  # ou ton modèle existant
    training_load: Optional[dict] = None
    comparison_prev_week: Optional[dict] = None
