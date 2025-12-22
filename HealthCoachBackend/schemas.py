from __future__ import annotations

from datetime import date
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class PeriodSnapshot(BaseModel):
    start: date
    end: date


class WeeklyTotals(BaseModel):
    distance_km: float
    duration_min: float
    sessions: int
    elevation_m: float
    avg_hr: Optional[float] = None


class TrainingLoad(BaseModel):
    load_7d: float = Field(..., alias="load_7d")
    load_28d: float = Field(..., alias="load_28d")
    ratio: float

    class Config:
        populate_by_name = True


class DailyRunSnapshot(BaseModel):
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
    period: PeriodSnapshot
    totals: WeeklyTotals
    zones_percent: Dict[str, float] = {}
    daily_runs: List[DailyRunSnapshot] = []
    training_load: Optional[TrainingLoad] = None
    comparison_prev_week: Optional[Dict[str, float]] = None


class ChatRequest(BaseModel):
    message: str
    snapshot: WeeklySnapshot
