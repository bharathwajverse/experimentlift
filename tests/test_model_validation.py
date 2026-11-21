from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from experimentlift.models import (
    AnalysisConfig,
    Assignment,
    ExperimentConfig,
    Exposure,
    OutcomeEvent,
    OutcomeStatus,
)


NOW = datetime(2026, 11, 20, tzinfo=UTC)


@pytest.mark.parametrize(
    ("model", "values"),
    [
        (
            Assignment,
            {
                "participant_id": "p1",
                "variant": "control",
                "assignment_id": "a1",
                "assigned_at": datetime(2026, 11, 20),
            },
        ),
        (
            Exposure,
            {
                "participant_id": "p1",
                "exposure_id": "x1",
                "occurred_at": datetime(2026, 11, 20),
            },
        ),
        (
            OutcomeEvent,
            {
                "idempotency_key": "e1",
                "participant_id": "p1",
                "status": OutcomeStatus.CONVERTED,
                "occurred_at": datetime(2026, 11, 20),
            },
        ),
    ],
)
def test_event_models_reject_naive_timestamps(model: type, values: dict[str, object]) -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        model(**values)


def test_experiment_serialization_is_stable_and_utc_explicit() -> None:
    config = ExperimentConfig(
        experiment_key="serialization",
        revision=1,
        allocation={"control": 0.5, "treatment": 0.5},
        practical_threshold=0.01,
        started_at=NOW - timedelta(days=2),
        ends_at=NOW - timedelta(days=1),
        analysis=AnalysisConfig(),
    )
    payload = config.model_dump_json()
    assert '"srm_alpha":0.001' in payload
    assert '"srm_min_sample":1000' in payload
    assert "Z" in payload


@pytest.mark.parametrize(
    "allocation",
    [
        {"control": float("nan"), "treatment": float("nan")},
        {"control": float("inf"), "treatment": float("-inf")},
    ],
)
def test_experiment_rejects_non_finite_allocation(
    allocation: dict[str, float],
) -> None:
    with pytest.raises(ValidationError, match="finite"):
        ExperimentConfig(
            experiment_key="invalid-allocation",
            revision=1,
            allocation=allocation,
            practical_threshold=0.01,
            started_at=NOW - timedelta(days=2),
            ends_at=NOW - timedelta(days=1),
            analysis=AnalysisConfig(),
        )


def test_experiment_allocation_is_deeply_immutable() -> None:
    config = ExperimentConfig(
        experiment_key="immutable-allocation",
        revision=1,
        allocation={"control": 0.5, "treatment": 0.5},
        practical_threshold=0.01,
        started_at=NOW - timedelta(days=2),
        ends_at=NOW - timedelta(days=1),
        analysis=AnalysisConfig(),
    )
    with pytest.raises(TypeError):
        config.allocation["control"] = 0.9
