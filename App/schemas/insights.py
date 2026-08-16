from pydantic import BaseModel
from typing import List


class CategoryBreakdown(BaseModel):
    category: str
    count: int
    percent: float


class ReportsOverTimePoint(BaseModel):
    date: str
    count: int


class InsightsResponse(BaseModel):
    total_reports: int
    resolved: int
    in_progress: int
    pending_verification: int
    category_breakdown: List[CategoryBreakdown]
    reports_over_time: List[ReportsOverTimePoint]
