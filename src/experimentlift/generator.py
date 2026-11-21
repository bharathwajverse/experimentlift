"""Seeded synthetic data only; never use for customer or campaign claims."""

from __future__ import annotations

from datetime import timedelta

import numpy as np

from .models import Assignment, ExperimentConfig, OutcomeEvent, OutcomeStatus


def synthetic_two_arm_data(
    config: ExperimentConfig,
    *,
    n_per_arm: int,
    control_conversion: float,
    treatment_conversion: float,
    seed: int,
) -> tuple[list[Assignment], list[OutcomeEvent]]:
    if n_per_arm < 1:
        raise ValueError("n_per_arm must be at least 1")
    if not 0 <= control_conversion <= 1 or not 0 <= treatment_conversion <= 1:
        raise ValueError("Conversion rates must be between 0 and 1")
    rng = np.random.default_rng(seed)
    assignments: list[Assignment] = []
    events: list[OutcomeEvent] = []
    for arm, conversion_rate in (
        ("control", control_conversion),
        ("treatment", treatment_conversion),
    ):
        outcomes = rng.random(n_per_arm) < conversion_rate
        for index, converted in enumerate(outcomes):
            participant_id = f"{arm}-{index}"
            assignments.append(
                Assignment(
                    experiment_key=config.experiment_key,
                    experiment_revision=config.revision,
                    participant_id=participant_id,
                    variant=arm,
                    assignment_id=(
                        f"{config.experiment_key}:{config.revision}:{participant_id}"
                    ),
                    assigned_at=config.started_at,
                )
            )
            events.append(
                OutcomeEvent(
                    experiment_key=config.experiment_key,
                    experiment_revision=config.revision,
                    idempotency_key=(
                        f"{config.experiment_key}:{config.revision}:outcome:{participant_id}"
                    ),
                    participant_id=participant_id,
                    status=OutcomeStatus.CONVERTED if converted else OutcomeStatus.NOT_CONVERTED,
                    occurred_at=config.started_at + timedelta(days=1),
                )
            )
    return assignments, events
