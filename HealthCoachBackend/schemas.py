from typing import Optional, Dict, List
from pydantic import BaseModel


class Period(BaseModel):
    start: str
    end: str


class WeeklyTotals(BaseModel):
    distance_km: float
    duration_min: float
    sessions: int
    elevation_m: float
    avg_hr: Optional[float] = None


class TrainingLoad(BaseModel):
    load_7d: float
    load_28d: float
    ratio: float


class DailyRun(BaseModel):
    date: str
    distance_km: float
    duration_min: float
    elevation_m: float
    avg_hr: float
    z1: float
    z2: float
    z3: float
    z4: float
    z5: float


class WeeklySnapshot(BaseModel):
    week_label: str
    period: Period
    totals: WeeklyTotals
    zones_percent: Dict[str, float]
    daily_runs: List[DailyRun]
    training_load: Optional[TrainingLoad] = None
    comparison_prev_week: Optional[Dict[str, float]] = None


class ChatRequest(BaseModel):
    message: str
    snapshot: WeeklySnapshot
