import json
from datetime import UTC, datetime, timedelta

from experimentlift.analysis import analyze_experiment
from experimentlift.generator import synthetic_two_arm_data
from experimentlift.models import AnalysisConfig, AnalysisReport, ExperimentConfig
from experimentlift.report import as_json, as_markdown


def test_markdown_report_is_ascii_console_safe() -> None:
    now = datetime(2026, 11, 20, tzinfo=UTC)
    config = ExperimentConfig(
        experiment_key="report-test",
        revision=1,
        allocation={"control": 0.5, "treatment": 0.5},
        practical_threshold=0.01,
        started_at=now - timedelta(days=2),
        ends_at=now - timedelta(days=1),
        analysis=AnalysisConfig(),
    )
    assignments, events = synthetic_two_arm_data(
        config,
        n_per_arm=100,
        control_conversion=0.1,
        treatment_conversion=0.2,
        seed=1,
    )
    report = analyze_experiment(config, assignments, events, now=now)
    assert as_markdown(report).encode("cp1252")


def test_json_report_round_trips_through_the_schema() -> None:
    now = datetime(2026, 11, 20, tzinfo=UTC)
    config = ExperimentConfig(
        experiment_key="report-json",
        revision=1,
        allocation={"control": 0.5, "treatment": 0.5},
        practical_threshold=0.01,
        started_at=now - timedelta(days=2),
        ends_at=now - timedelta(days=1),
        analysis=AnalysisConfig(),
    )
    assignments, events = synthetic_two_arm_data(
        config,
        n_per_arm=100,
        control_conversion=0.1,
        treatment_conversion=0.2,
        seed=1,
    )
    report = analyze_experiment(config, assignments, events, now=now)

    payload = json.loads(as_json(report))

    assert payload == report.model_dump(mode="json")
    assert payload["report_version"] == report.report_version
    assert payload["analysis_at"].endswith("Z") or "+00:00" in payload["analysis_at"]
    assert AnalysisReport.model_validate_json(as_json(report)) == report


def test_markdown_marks_a_non_estimable_effect() -> None:
    now = datetime(2026, 11, 20, tzinfo=UTC)
    config = ExperimentConfig(
        experiment_key="report-empty",
        revision=1,
        allocation={"control": 0.5, "treatment": 0.5},
        practical_threshold=0.01,
        started_at=now - timedelta(days=2),
        ends_at=now - timedelta(days=1),
        analysis=AnalysisConfig(),
    )
    report = analyze_experiment(config, [], [], now=now)

    markdown = as_markdown(report)

    assert report.risk_difference is None
    assert "not estimable" in markdown
    assert "no_assignments" in markdown
    assert markdown.encode("cp1252")
    now = datetime(2026, 11, 20, tzinfo=UTC)
    config = ExperimentConfig(
        experiment_key="report-warnings",
        revision=1,
        allocation={"control": 0.5, "treatment": 0.5},
        practical_threshold=0.01,
        started_at=now - timedelta(days=2),
        ends_at=now - timedelta(days=1),
        analysis=AnalysisConfig(),
    )
    assignments, events = synthetic_two_arm_data(
        config,
        n_per_arm=10,
        control_conversion=0.1,
        treatment_conversion=0.2,
        seed=1,
    )
    report = analyze_experiment(
        config,
        assignments,
        [*events[:-1], events[0]],
        now=now,
    )
    markdown = as_markdown(report)
    assert "missing_outcomes" in markdown
    assert "duplicate_events_deduplicated" in markdown
