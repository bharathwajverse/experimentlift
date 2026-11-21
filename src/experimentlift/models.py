"""Typed domain and report schemas with no model-provider dependencies."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from math import isfinite
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class FrozenDict(dict[str, float]):
    """Serializable dict with mutation disabled after validation."""

    def _immutable(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("FrozenDict is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable


class OutcomeStatus(str, Enum):
    CONVERTED = "converted"
    NOT_CONVERTED = "not_converted"


class AnalysisConfig(FrozenModel):
    alpha: float = Field(default=0.05, gt=0, lt=1)
    srm_alpha: float = Field(default=0.001, gt=0, lt=1)
    srm_min_sample: int = Field(default=1_000, ge=1)
    outcome_absence_means_no_conversion: bool = False


class ExperimentConfig(FrozenModel):
    experiment_key: str = Field(min_length=1, max_length=128)
    revision: int = Field(ge=1)
    allocation: dict[Literal["control", "treatment"], float]
    practical_threshold: float = Field(ge=0)
    started_at: datetime
    ends_at: datetime
    analysis: AnalysisConfig

    @field_validator("allocation")
    @classmethod
    def allocation_is_two_arm_and_sums_to_one(
        cls, allocation: dict[str, float]
    ) -> dict[str, float]:
        if set(allocation) != {"control", "treatment"}:
            raise ValueError("Allocation requires exactly control and treatment arms")
        if any(not isfinite(value) for value in allocation.values()):
            raise ValueError("Each allocation value must be finite")
        if any(value <= 0 for value in allocation.values()):
            raise ValueError("Each allocation value must be positive")
        if abs(sum(allocation.values()) - 1) > 1e-12:
            raise ValueError("Allocation must sum to 1.0")
        return FrozenDict(allocation)

    @model_validator(mode="after")
    def measurement_window_is_valid(self) -> "ExperimentConfig":
        if self.started_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Experiment timestamps must be timezone-aware")
        if self.ends_at <= self.started_at:
            raise ValueError("ends_at must be later than started_at")
        return self


class Assignment(FrozenModel):
    experiment_key: str = Field(min_length=1)
    experiment_revision: int = Field(ge=1)
    participant_id: str = Field(min_length=1)
    variant: Literal["control", "treatment"]
    assignment_id: str = Field(min_length=1)
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("assigned_at")
    @classmethod
    def assigned_at_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("assigned_at must be timezone-aware")
        return value


class Exposure(FrozenModel):
    experiment_key: str = Field(min_length=1)
    experiment_revision: int = Field(ge=1)
    participant_id: str = Field(min_length=1)
    exposure_id: str = Field(min_length=1)
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        return value


class OutcomeEvent(FrozenModel):
    experiment_key: str = Field(min_length=1)
    experiment_revision: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1)
    participant_id: str = Field(min_length=1)
    status: OutcomeStatus
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_is_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        return value


class ArmSummary(FrozenModel):
    assigned: int
    conversions: int
    non_conversions: int
    unknown_outcomes: int
    conversion_rate: float | None
    completeness: float
    exposed: int | None = None
    exposure_rate: float | None = None


class TestResult(FrozenModel):
    method: Literal["score", "fisher_exact"]
    statistic: float | None
    p_value: float


class AnalysisReport(FrozenModel):
    report_version: str = "0.2"
    data_source: Literal["SYNTHETIC"] = "SYNTHETIC"
    experiment_key: str
    experiment_revision: int
    configuration_hash: str
    status: Literal["COMPLETE", "PROVISIONAL", "INVALID"]
    validity: Literal["VALID", "INVALID"]
    verdict: Literal["win", "loss", "inconclusive"]
    arms: dict[Literal["control", "treatment"], ArmSummary]
    risk_difference: float | None
    relative_lift: float | None
    confidence_interval: tuple[float, float] | None
    wald_confidence_interval: tuple[float, float] | None
    primary_test: TestResult | None
    srm_p_value: float
    exposure_rate_difference: float | None = None
    exposure_test: TestResult | None = None
    duplicate_events: int
    ignored_events: int
    ignored_exposures: int = 0
    critical_issues: tuple[str, ...]
    warnings: tuple[str, ...]
    analysis_at: datetime
