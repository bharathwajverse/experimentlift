from datetime import UTC, datetime, timedelta

from experimentlift.analysis import analyze_experiment
from experimentlift.models import (
    AnalysisConfig,
    Assignment,
    ExperimentConfig,
    OutcomeEvent,
    OutcomeStatus,
    Exposure,
)
import pytest


NOW = datetime(2026, 11, 20, tzinfo=UTC)


def config(**changes: object) -> ExperimentConfig:
    values: dict[str, object] = {
        "experiment_key": "email-ai-creative-v1",
        "revision": 1,
        "allocation": {"control": 0.5, "treatment": 0.5},
        "practical_threshold": 0.01,
        "started_at": NOW - timedelta(days=14),
        "ends_at": NOW - timedelta(days=1),
        "analysis": AnalysisConfig(),
    }
    values.update(changes)
    return ExperimentConfig(**values)


def assignments(n_per_arm: int) -> list[Assignment]:
    return [
        Assignment(
            experiment_key="email-ai-creative-v1",
            experiment_revision=1,
            participant_id=f"{variant}-{index}",
            variant=variant,
            assignment_id=f"assignment-{variant}-{index}",
            assigned_at=NOW - timedelta(days=13),
        )
        for variant in ("control", "treatment")
        for index in range(n_per_arm)
    ]


def terminal_events(
    n_per_arm: int, control_conversions: int, treatment_conversions: int
) -> list[OutcomeEvent]:
    events: list[OutcomeEvent] = []
    for variant, conversions in (
        ("control", control_conversions),
        ("treatment", treatment_conversions),
    ):
        for index in range(n_per_arm):
            events.append(
                OutcomeEvent(
                    experiment_key="email-ai-creative-v1",
                    experiment_revision=1,
                    idempotency_key=f"outcome-{variant}-{index}",
                    participant_id=f"{variant}-{index}",
                    status=(
                        OutcomeStatus.CONVERTED
                        if index < conversions
                        else OutcomeStatus.NOT_CONVERTED
                    ),
                    occurred_at=NOW - timedelta(days=2),
                )
            )
    return events


def test_known_effect_with_practical_significance_is_a_win() -> None:
    report = analyze_experiment(
        config(),
        assignments(2_000),
        terminal_events(2_000, control_conversions=200, treatment_conversions=300),
        now=NOW,
    )

    assert report.status == "COMPLETE"
    assert report.validity == "VALID"
    assert report.verdict == "win"
    assert report.risk_difference > 0.04
    assert report.confidence_interval[0] > 0.01
    assert report.primary_test.method == "score"


def test_fixed_aa_fixture_is_inconclusive_without_relying_on_random_p_value() -> None:
    report = analyze_experiment(
        config(),
        assignments(2_000),
        terminal_events(2_000, control_conversions=200, treatment_conversions=200),
        now=NOW,
    )

    assert report.status == "COMPLETE"
    assert report.verdict == "inconclusive"
    assert report.risk_difference == 0
    assert report.confidence_interval[0] < 0 < report.confidence_interval[1]


def test_srm_invalidates_a_winner() -> None:
    imbalanced_assignments = [
        *assignments(700)[:700],
        *assignments(700)[700:1_100],
    ]
    events = terminal_events(700, 70, 140)
    report = analyze_experiment(config(), imbalanced_assignments, events, now=NOW)

    assert report.status == "INVALID"
    assert report.validity == "INVALID"
    assert report.verdict == "inconclusive"
    assert "sample_ratio_mismatch" in report.critical_issues


def test_unknown_outcomes_block_actionable_causal_conclusion() -> None:
    assigned = assignments(100)
    observed = terminal_events(60, 6, 18)
    report = analyze_experiment(config(), assigned, observed, now=NOW)

    assert report.status == "INVALID"
    assert report.verdict == "inconclusive"
    assert report.arms["control"].unknown_outcomes == 40
    assert report.arms["control"].conversion_rate == pytest.approx(0.06)
    assert report.risk_difference == pytest.approx(0.12)
    assert "missing_outcomes" in report.critical_issues


def test_duplicate_events_do_not_inflate_conversions() -> None:
    assigned = assignments(100)
    events = terminal_events(100, 10, 20)
    duplicate = events[100].model_copy(update={"idempotency_key": events[100].idempotency_key})
    report = analyze_experiment(config(), assigned, [*events, duplicate], now=NOW)

    assert report.arms["treatment"].conversions == 20
    assert report.duplicate_events == 1


def test_zero_conversions_are_safe_and_relative_lift_is_not_estimable() -> None:
    report = analyze_experiment(
        config(),
        assignments(500),
        terminal_events(500, 0, 0),
        now=NOW,
    )

    assert report.relative_lift is None
    assert report.verdict == "inconclusive"
    assert report.primary_test.statistic is None
    assert '"statistic":null' in report.model_dump_json()


def test_small_counts_use_fisher_exact_fallback() -> None:
    report = analyze_experiment(
        config(),
        assignments(20),
        terminal_events(20, 0, 3),
        now=NOW,
    )

    assert report.primary_test.method == "fisher_exact"


def test_running_experiment_is_provisional() -> None:
    report = analyze_experiment(
        config(ends_at=NOW + timedelta(days=1)),
        assignments(100),
        terminal_events(100, 10, 30),
        now=NOW,
    )

    assert report.status == "PROVISIONAL"
    assert report.verdict == "inconclusive"


def test_conflicting_idempotency_key_is_rejected() -> None:
    assigned = assignments(10)
    events = terminal_events(10, 1, 2)
    conflicting = events[0].model_copy(
        update={"participant_id": "control-1", "status": OutcomeStatus.CONVERTED}
    )
    with pytest.raises(ValueError, match="idempotency"):
        analyze_experiment(config(), assigned, [events[0], conflicting], now=NOW)


def test_conflicting_terminal_outcomes_are_rejected() -> None:
    assigned = assignments(10)
    first = terminal_events(10, 1, 2)[0]
    conflicting = first.model_copy(
        update={
            "idempotency_key": "different-key",
            "status": OutcomeStatus.NOT_CONVERTED,
        }
    )
    with pytest.raises(ValueError, match="terminal outcomes"):
        analyze_experiment(config(), assigned, [first, conflicting], now=NOW)


def test_duplicate_assignment_id_is_rejected() -> None:
    assigned = assignments(2)
    assigned[1] = assigned[1].model_copy(
        update={"assignment_id": assigned[0].assignment_id}
    )
    with pytest.raises(ValueError, match="assignment IDs"):
        analyze_experiment(config(), assigned, [], now=NOW)


def test_assignment_outside_window_invalidates_analysis() -> None:
    assigned = assignments(10)
    assigned[0] = assigned[0].model_copy(
        update={"assigned_at": config().ends_at + timedelta(seconds=1)}
    )
    report = analyze_experiment(
        config(), assigned, terminal_events(10, 1, 2), now=NOW
    )
    assert report.status == "INVALID"
    assert "assignment_outside_measurement_window" in report.critical_issues


def test_outcome_before_assignment_is_ignored() -> None:
    assigned = assignments(10)
    assigned[0] = assigned[0].model_copy(
        update={"assigned_at": NOW - timedelta(days=2)}
    )
    event = terminal_events(10, 1, 2)[0].model_copy(
        update={"occurred_at": NOW - timedelta(days=3)}
    )
    report = analyze_experiment(config(), assigned, [event], now=NOW)
    assert report.arms["control"].conversions == 0
    assert report.ignored_events == 1


def test_future_outcome_is_ignored_in_provisional_analysis() -> None:
    provisional = config(ends_at=NOW + timedelta(days=2))
    event = terminal_events(10, 1, 2)[0].model_copy(
        update={"occurred_at": NOW + timedelta(days=1)}
    )
    report = analyze_experiment(provisional, assignments(10), [event], now=NOW)
    assert report.arms["control"].conversions == 0
    assert report.ignored_events == 1


def test_future_assignment_invalidates_provisional_analysis() -> None:
    provisional = config(ends_at=NOW + timedelta(days=2))
    assigned = assignments(10)
    assigned[0] = assigned[0].model_copy(
        update={"assigned_at": NOW + timedelta(days=1)}
    )
    report = analyze_experiment(provisional, assigned, [], now=NOW)
    assert report.status == "INVALID"
    assert "assignment_outside_measurement_window" in report.critical_issues


def test_foreign_revision_records_are_rejected() -> None:
    assigned = [
        assignment.model_copy(
            update={
                "experiment_key": config().experiment_key,
                "experiment_revision": 1,
            }
        )
        for assignment in assignments(10)
    ]
    with pytest.raises(ValueError, match="experiment revision"):
        analyze_experiment(config(revision=2), assigned, [], now=NOW)


def test_foreign_revision_outcome_and_exposure_are_rejected() -> None:
    foreign_event = terminal_events(10, 1, 2)[0].model_copy(
        update={"experiment_revision": 2}
    )
    with pytest.raises(ValueError, match="experiment revision"):
        analyze_experiment(config(), assignments(10), [foreign_event], now=NOW)

    foreign_exposure = Exposure(
        experiment_key=config().experiment_key,
        experiment_revision=2,
        participant_id="control-0",
        exposure_id="foreign-revision",
        occurred_at=NOW - timedelta(days=2),
    )
    with pytest.raises(ValueError, match="experiment revision"):
        analyze_experiment(
            config(),
            assignments(10),
            [],
            exposures=[foreign_exposure],
            now=NOW,
        )


def test_differential_exposure_is_reported_without_changing_itt() -> None:
    assigned = assignments(100)
    exposures = [
        Exposure(
            experiment_key=config().experiment_key,
            experiment_revision=config().revision,
            participant_id=f"control-{index}",
            exposure_id=f"exposure-control-{index}",
            occurred_at=NOW - timedelta(days=2),
        )
        for index in range(50)
    ] + [
        Exposure(
            experiment_key=config().experiment_key,
            experiment_revision=config().revision,
            participant_id=f"treatment-{index}",
            exposure_id=f"exposure-treatment-{index}",
            occurred_at=NOW - timedelta(days=2),
        )
        for index in range(90)
    ]
    report = analyze_experiment(
        config(),
        assigned,
        terminal_events(100, 10, 20),
        exposures=exposures,
        now=NOW,
    )
    assert report.arms["control"].exposure_rate == pytest.approx(0.5)
    assert report.arms["treatment"].exposure_rate == pytest.approx(0.9)
    assert report.exposure_rate_difference == pytest.approx(0.4)
    assert "differential_exposure" in report.warnings
    assert report.risk_difference == pytest.approx(0.1)


def test_ignored_exposure_is_counted_separately_from_ignored_outcomes() -> None:
    report = analyze_experiment(
        config(),
        assignments(10),
        terminal_events(10, 1, 2),
        exposures=[
            Exposure(
                experiment_key=config().experiment_key,
                experiment_revision=config().revision,
                participant_id="not-assigned",
                exposure_id="ignored-exposure",
                occurred_at=NOW - timedelta(days=2),
            )
        ],
        now=NOW,
    )
    assert report.ignored_exposures == 1
    assert report.ignored_events == 0
    assert "out_of_window_or_unassigned_exposures_ignored" in report.warnings
    assert "out_of_window_or_unassigned_events_ignored" not in report.warnings


def test_ignored_outcome_does_not_inflate_ignored_exposure_count() -> None:
    assigned = assignments(10)
    assigned[0] = assigned[0].model_copy(
        update={"assigned_at": NOW - timedelta(days=2)}
    )
    event = terminal_events(10, 1, 2)[0].model_copy(
        update={"occurred_at": NOW - timedelta(days=3)}
    )
    report = analyze_experiment(
        config(),
        assigned,
        [event],
        exposures=[
            Exposure(
                experiment_key=config().experiment_key,
                experiment_revision=config().revision,
                participant_id="control-1",
                exposure_id="accepted-exposure",
                occurred_at=NOW - timedelta(days=2),
            )
        ],
        now=NOW,
    )
    assert report.ignored_events == 1
    assert report.ignored_exposures == 0
    assert "out_of_window_or_unassigned_events_ignored" in report.warnings
    assert "out_of_window_or_unassigned_exposures_ignored" not in report.warnings


def test_every_exposure_ignored_does_not_claim_an_exposure_test() -> None:
    report = analyze_experiment(
        config(),
        assignments(10),
        terminal_events(10, 1, 2),
        exposures=[
            Exposure(
                experiment_key=config().experiment_key,
                experiment_revision=config().revision,
                participant_id="not-assigned",
                exposure_id=f"ignored-exposure-{index}",
                occurred_at=NOW - timedelta(days=2),
            )
            for index in range(3)
        ],
        now=NOW,
    )
    assert report.ignored_exposures == 3
    assert report.arms["control"].exposed == 0
    assert report.arms["treatment"].exposed == 0
    assert report.exposure_rate_difference == 0
    assert report.exposure_test is not None
    assert "differential_exposure" not in report.warnings


def test_arm_without_assignments_is_invalid_not_silently_valid() -> None:
    control_only = [
        assignment for assignment in assignments(10) if assignment.variant == "control"
    ]
    control_events = [
        event for event in terminal_events(10, 1, 2) if event.participant_id.startswith("control-")
    ]
    report = analyze_experiment(config(), control_only, control_events, now=NOW)

    assert report.status == "INVALID"
    assert report.validity == "INVALID"
    assert report.verdict == "inconclusive"
    assert "arm_without_assignments" in report.critical_issues
    assert report.primary_test is None


def test_srm_check_requires_configured_minimum_sample() -> None:
    population = assignments(600)
    control = [item for item in population if item.variant == "control"]
    treatment = [item for item in population if item.variant == "treatment"]
    analysis = AnalysisConfig(outcome_absence_means_no_conversion=True)

    below_minimum = analyze_experiment(
        config(analysis=analysis),
        [*control, *treatment[:399]],
        [],
        now=NOW,
    )
    at_minimum = analyze_experiment(
        config(analysis=analysis),
        [*control, *treatment[:400]],
        [],
        now=NOW,
    )

    assert below_minimum.srm_p_value < 0.001
    assert "sample_ratio_mismatch" not in below_minimum.critical_issues
    assert below_minimum.status == "COMPLETE"

    assert at_minimum.srm_p_value < 0.001
    assert "sample_ratio_mismatch" in at_minimum.critical_issues
    assert at_minimum.status == "INVALID"


def test_newcombe_failure_is_not_papered_over_with_fabricated_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from experimentlift import analysis

    def explode(*_args: object, **_kwargs: object) -> tuple[float, float]:
        raise ValueError("newcombe unavailable")

    monkeypatch.setattr(analysis, "confint_proportions_2indep", explode)

    with pytest.raises(analysis.StatisticUnavailableError, match="Newcombe"):
        analysis.calculate_proportion_statistics(150, 1_000, 100, 1_000, 0.05)


def test_empty_dataset_is_invalid_without_exception() -> None:
    report = analyze_experiment(config(), [], [], now=NOW)
    assert report.status == "INVALID"
    assert report.primary_test is None
    assert "no_assignments" in report.critical_issues
