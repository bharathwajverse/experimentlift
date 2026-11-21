"""Local synthetic-scenario runner."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

from .analysis import analyze_experiment
from .generator import synthetic_two_arm_data
from .models import AnalysisConfig, ExperimentConfig
from .report import as_json, as_markdown


def known_effect_config(now: datetime) -> ExperimentConfig:
    return ExperimentConfig(
        experiment_key="synthetic-ab-known-effect",
        revision=1,
        allocation={"control": 0.5, "treatment": 0.5},
        practical_threshold=0.01,
        started_at=now - timedelta(days=14),
        ends_at=now - timedelta(days=1),
        analysis=AnalysisConfig(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a synthetic ExperimentLift scenario.")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--scenario", choices=["ab_known_effect"], default="ab_known_effect")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()
    now = datetime(2026, 11, 20, tzinfo=UTC)
    config = known_effect_config(now)
    assignments, events = synthetic_two_arm_data(
        config,
        n_per_arm=20_000,
        control_conversion=0.10,
        treatment_conversion=0.13,
        seed=20261120,
    )
    report = analyze_experiment(config, assignments, events, now=now)
    print(as_markdown(report) if args.format == "markdown" else as_json(report))


if __name__ == "__main__":
    main()
