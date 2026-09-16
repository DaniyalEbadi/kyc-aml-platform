from __future__ import annotations

from pydantic import BaseModel


class KPIOut(BaseModel):
    total_applications: int = 0
    new_applications: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    in_review_count: int = 0
    approval_rate: float = 0
    rejection_rate: float = 0
    human_review_rate: float = 0
    avg_processing_hours: float = 0
    avg_review_hours: float = 0
    high_risk_count: int = 0
    critical_count: int = 0
    total_customers: int = 0
    total_cases: int = 0
    open_cases: int = 0


class ChartDataPoint(BaseModel):
    label: str
    value: float


class TimeseriesPoint(BaseModel):
    date: str
    value: float


class FunnelStep(BaseModel):
    step: str
    count: int
    percentage: float


class AnalyticsOverview(BaseModel):
    kpis: KPIOut
    applications_over_time: list[TimeseriesPoint] = []
    risk_distribution: list[ChartDataPoint] = []
    verification_funnel: list[FunnelStep] = []
    document_type_distribution: list[ChartDataPoint] = []
    reviewer_workload: list[ChartDataPoint] = []
    status_distribution: list[ChartDataPoint] = []
