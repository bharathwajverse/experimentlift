from datetime import UTC, datetime, timedelta

import pytest

from experimentlift.generator import synthetic_two_arm_data
from experimentlift.models import AnalysisConfig, ExperimentConfig
from experimentlift.simulation import evaluate_operating_characteristics


NOW = datetime(2026, 11, 20, tzinfo=UTC)
CONFIG = ExperimentConfig(
    experiment_key="boundaries",
    revision=1,
    allocation={"control": 0.5, "treatment": 0.5},
    practical_threshold=0.01,
    started_at=NOW - timedelta(days=2),
    ends_at=NOW - timedelta(days=1),
    analysis=AnalysisConfig(),
)


@pytest.mark.parametrize(
    ("n_per_arm", "control", "treatment"),
    [(0, 0.1, 0.2), (10, -0.1, 0.2), (10, 0.1, 1.1)],
)
def test_generator_rejects_invalid_inputs(
    n_per_arm: int, control: float, treatment: float
) -> None:
    with pytest.raises(ValueError):
        synthetic_two_arm_data(
            CONFIG,
            n_per_arm=n_per_arm,
            control_conversion=control,
            treatment_conversion=treatment,
            seed=1,
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"control_conversion": -0.1},
        {"treatment_conversion": 1.1},
        {"practical_threshold": -0.01},
        {"alpha": 1.0},
    ],
)
def test_simulation_rejects_invalid_inputs(changes: dict[str, float]) -> None:
    arguments: dict[str, float | int] = {
        "simulations": 10,
        "n_per_arm": 100,
        "control_conversion": 0.1,
        "treatment_conversion": 0.2,
        "practical_threshold": 0.01,
        "seed": 1,
        "alpha": 0.05,
    }
    arguments.update(changes)
    with pytest.raises(ValueError):
        evaluate_operating_characteristics(**arguments)
