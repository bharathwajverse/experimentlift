"""Fixed-horizon two-arm binary-outcome analysis."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from math import isfinite, sqrt

from scipy.stats import chisquare, fisher_exact, norm
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    test_proportions_2indep,
)

from .models import (
    AnalysisReport,
    ArmSummary,
    Assignment,
    Exposure,
    ExperimentConfig,
    OutcomeEvent,
    OutcomeStatus,
    TestResult,
)


@dataclass(frozen=True)
class ProportionStatistics:
    test: TestResult
    confidence_interval: tuple[float, float]
    wald_confidence_interval: tuple[float, float]


class StatisticUnavailableError(RuntimeError):
    """Raised when a requested statistic cannot be computed for the given data."""


def configuration_hash(config: ExperimentConfig) -> str:
    payload = json.dumps(config.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def analyze_experiment(
    config: ExperimentConfig,
    assignments: list[Assignment],
    events: list[OutcomeEvent],
    *,
    exposures: list[Exposure] | None = None,
    now: datetime,
) -> AnalysisReport:
    """Analyze one frozen experiment revision using assigned-population ITT."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    by_participant: dict[str, Assignment] = {}
    assignment_ids: set[str] = set()
    for assignment in assignments:
        if (
            assignment.experiment_key != config.experiment_key
            or assignment.experiment_revision != config.revision
        ):
            raise ValueError("Assignment belongs to a different experiment revision")
        if assignment.participant_id in by_participant:
            raise ValueError("Assignment input has duplicate participant IDs")
        if assignment.assignment_id in assignment_ids:
            raise ValueError("Assignment input has duplicate assignment IDs")
        by_participant[assignment.participant_id] = assignment
        assignment_ids.add(assignment.assignment_id)

    accepted: dict[str, OutcomeEvent] = {}
    seen_events: dict[str, OutcomeEvent] = {}
    duplicate_events = 0
    ignored_events = 0
    ignored_exposures = 0
    observation_cutoff = min(now, config.ends_at)
    for event in events:
        if (
            event.experiment_key != config.experiment_key
            or event.experiment_revision != config.revision
        ):
            raise ValueError("Outcome belongs to a different experiment revision")
        if event.idempotency_key in seen_events:
            if event != seen_events[event.idempotency_key]:
                raise ValueError("Conflicting payload for idempotency key")
            duplicate_events += 1
            continue
        seen_events[event.idempotency_key] = event
        if event.participant_id not in by_participant:
            ignored_events += 1
            continue
        assignment = by_participant[event.participant_id]
        if not (
            assignment.assigned_at <= event.occurred_at <= observation_cutoff
        ):
            ignored_events += 1
            continue
        accepted[event.idempotency_key] = event

    participant_outcomes: dict[str, OutcomeStatus] = {}
    for event in accepted.values():
        prior = participant_outcomes.get(event.participant_id)
        if prior is not None and prior != event.status:
            raise ValueError("Conflicting terminal outcomes for participant")
        participant_outcomes[event.participant_id] = event.status

    assigned_ids = defaultdict(list)
    for assignment in by_participant.values():
        assigned_ids[assignment.variant].append(assignment.participant_id)

    arm_summaries: dict[str, ArmSummary] = {}
    for arm in ("control", "treatment"):
        ids = assigned_ids[arm]
        converted = sum(
            participant_outcomes.get(participant_id) == OutcomeStatus.CONVERTED
            for participant_id in ids
        )
        observed_non_conversion = sum(
            participant_outcomes.get(participant_id) == OutcomeStatus.NOT_CONVERTED
            for participant_id in ids
        )
        unknown = len(ids) - converted - observed_non_conversion
        if config.analysis.outcome_absence_means_no_conversion:
            non_conversions = observed_non_conversion + unknown
            unknown = 0
        else:
            non_conversions = observed_non_conversion
        denominator = len(ids)
        observed = converted + observed_non_conversion
        arm_summaries[arm] = ArmSummary(
            assigned=len(ids),
            conversions=converted,
            non_conversions=non_conversions,
            unknown_outcomes=unknown,
            conversion_rate=(converted / denominator if denominator else None),
            completeness=(observed / len(ids) if ids else 0.0),
        )

    critical_issues: list[str] = []
    warnings: list[str] = []
    counts = [arm_summaries["control"].assigned, arm_summaries["treatment"].assigned]
    expected = [sum(counts) * config.allocation["control"], sum(counts) * config.allocation["treatment"]]
    total_assigned = sum(counts)
    srm_p_value = (
        float(chisquare(counts, f_exp=expected).pvalue) if total_assigned else 1.0
    )
    if (
        total_assigned >= config.analysis.srm_min_sample
        and srm_p_value < config.analysis.srm_alpha
    ):
        critical_issues.append("sample_ratio_mismatch")
    if total_assigned == 0:
        critical_issues.append("no_assignments")
    elif 0 in counts:
        critical_issues.append("arm_without_assignments")
    if any(
        not (config.started_at <= assignment.assigned_at <= observation_cutoff)
        for assignment in by_participant.values()
    ):
        critical_issues.append("assignment_outside_measurement_window")

    if any(summary.unknown_outcomes for summary in arm_summaries.values()):
        critical_issues.append("missing_outcomes")
    if duplicate_events:
        warnings.append("duplicate_events_deduplicated")
    if now < config.ends_at:
        warnings.append("measurement_window_incomplete")

    exposure_rate_difference: float | None = None
    exposure_test: TestResult | None = None
    if exposures is not None:
        exposed_ids: set[str] = set()
        exposure_ids: set[str] = set()
        for exposure in exposures:
            if (
                exposure.experiment_key != config.experiment_key
                or exposure.experiment_revision != config.revision
            ):
                raise ValueError("Exposure belongs to a different experiment revision")
            if exposure.exposure_id in exposure_ids:
                raise ValueError("Exposure input has duplicate exposure IDs")
            exposure_ids.add(exposure.exposure_id)
            if (
                exposure.participant_id in by_participant
                and by_participant[exposure.participant_id].assigned_at
                <= exposure.occurred_at
                <= observation_cutoff
            ):
                exposed_ids.add(exposure.participant_id)
            else:
                ignored_exposures += 1
        exposed_counts: dict[str, int] = {}
        for arm in ("control", "treatment"):
            exposed = sum(participant_id in exposed_ids for participant_id in assigned_ids[arm])
            exposed_counts[arm] = exposed
            assigned = arm_summaries[arm].assigned
            arm_summaries[arm] = arm_summaries[arm].model_copy(
                update={
                    "exposed": exposed,
                    "exposure_rate": exposed / assigned if assigned else None,
                }
            )
        exposure_result = calculate_proportion_statistics(
            exposed_counts["treatment"],
            arm_summaries["treatment"].assigned,
            exposed_counts["control"],
            arm_summaries["control"].assigned,
            config.analysis.alpha,
        )
        if exposure_result is not None:
            exposure_rate_difference = (
                arm_summaries["treatment"].exposure_rate
                - arm_summaries["control"].exposure_rate
            )
            exposure_test = exposure_result.test
            if exposure_test.p_value < config.analysis.alpha:
                warnings.append("differential_exposure")

    if ignored_events:
        warnings.append("out_of_window_or_unassigned_events_ignored")
    if ignored_exposures:
        warnings.append("out_of_window_or_unassigned_exposures_ignored")

    result = calculate_proportion_statistics(
        arm_summaries["treatment"].conversions,
        arm_summaries["treatment"].assigned,
        arm_summaries["control"].conversions,
        arm_summaries["control"].assigned,
        config.analysis.alpha,
    )
    if critical_issues:
        status, validity = "INVALID", "INVALID"
    elif now < config.ends_at:
        status, validity = "PROVISIONAL", "VALID"
    else:
        status, validity = "COMPLETE", "VALID"

    verdict = "inconclusive"
    if status == "COMPLETE" and result is not None:
        ci_low, ci_high = result.confidence_interval
        if result.test.p_value < config.analysis.alpha and ci_low > config.practical_threshold:
            verdict = "win"
        elif ci_high < 0:
            verdict = "loss"

    control_rate = (
        arm_summaries["control"].conversions / arm_summaries["control"].assigned
        if arm_summaries["control"].assigned
        else None
    )
    treatment_rate = (
        arm_summaries["treatment"].conversions / arm_summaries["treatment"].assigned
        if arm_summaries["treatment"].assigned
        else None
    )
    return AnalysisReport(
        experiment_key=config.experiment_key,
        experiment_revision=config.revision,
        configuration_hash=configuration_hash(config),
        status=status,
        validity=validity,
        verdict=verdict,
        arms=arm_summaries,
        risk_difference=(treatment_rate - control_rate if treatment_rate is not None and control_rate is not None else None),
        relative_lift=(
            (treatment_rate - control_rate) / control_rate
            if treatment_rate is not None and control_rate is not None and control_rate != 0
            else None
        ),
        confidence_interval=(result.confidence_interval if result else None),
        wald_confidence_interval=(result.wald_confidence_interval if result else None),
        primary_test=(result.test if result else None),
        srm_p_value=srm_p_value,
        exposure_rate_difference=exposure_rate_difference,
        exposure_test=exposure_test,
        duplicate_events=duplicate_events,
        ignored_events=ignored_events,
        ignored_exposures=ignored_exposures,
        critical_issues=tuple(critical_issues),
        warnings=tuple(warnings),
        analysis_at=now,
    )


def calculate_proportion_statistics(
    treatment_conversions: int,
    treatment_n: int,
    control_conversions: int,
    control_n: int,
    alpha: float,
) -> ProportionStatistics | None:
    if treatment_n < 0 or control_n < 0:
        raise ValueError("Arm sizes must be non-negative")
    if not (
        0 <= treatment_conversions <= treatment_n
        and 0 <= control_conversions <= control_n
    ):
        raise ValueError("Conversions must be between zero and arm size")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if treatment_n == 0 or control_n == 0:
        return None
    total = treatment_n + control_n
    total_conversions = treatment_conversions + control_conversions
    total_non_conversions = total - total_conversions
    table = [
        [treatment_conversions, treatment_n - treatment_conversions],
        [control_conversions, control_n - control_conversions],
    ]
    expected_cell_counts = [
        treatment_n * total_conversions / total,
        treatment_n * total_non_conversions / total,
        control_n * total_conversions / total,
        control_n * total_non_conversions / total,
    ]
    small_sample = min(expected_cell_counts) < 5
    if small_sample:
        odds_ratio, p_value = fisher_exact(table, alternative="two-sided")
        statistic = float(odds_ratio)
        test = TestResult(
            method="fisher_exact",
            statistic=statistic if isfinite(statistic) else None,
            p_value=float(p_value),
        )
    else:
        score = test_proportions_2indep(
            treatment_conversions,
            treatment_n,
            control_conversions,
            control_n,
            method="score",
            compare="diff",
            alternative="two-sided",
            correction=False,
        )
        test = TestResult(method="score", statistic=float(score.statistic), p_value=float(score.pvalue))
    try:
        confidence_interval = tuple(
            float(value)
            for value in confint_proportions_2indep(
                treatment_conversions,
                treatment_n,
                control_conversions,
                control_n,
                method="newcomb",
                compare="diff",
                alpha=alpha,
            )
        )
    except (ValueError, ZeroDivisionError) as error:
        raise StatisticUnavailableError(
            "Newcombe confidence interval is unavailable for this data"
        ) from error
    treatment_rate = treatment_conversions / treatment_n
    control_rate = control_conversions / control_n
    risk_difference = treatment_rate - control_rate
    standard_error = sqrt(
        treatment_rate * (1 - treatment_rate) / treatment_n
        + control_rate * (1 - control_rate) / control_n
    )
    critical_value = float(norm.ppf(1 - alpha / 2))
    wald_confidence_interval = (
        risk_difference - critical_value * standard_error,
        risk_difference + critical_value * standard_error,
    )
    return ProportionStatistics(
        test=test,
        confidence_interval=confidence_interval,
        wald_confidence_interval=wald_confidence_interval,
    )
