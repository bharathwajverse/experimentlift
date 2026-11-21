"""Deterministic simulation checks for analysis operating characteristics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from statsmodels.stats.proportion import (
    proportion_confint,
)

from .analysis import calculate_proportion_statistics


@dataclass(frozen=True)
class SimulationResult:
    simulations: int
    actionable_win_rate: float
    actionable_win_rate_interval: tuple[float, float]
    actionable_decision_rate: float
    actionable_decision_rate_interval: tuple[float, float]
    coverage_rate: float
    mean_risk_difference: float


def evaluate_operating_characteristics(
    *,
    simulations: int,
    n_per_arm: int,
    control_conversion: float,
    treatment_conversion: float,
    practical_threshold: float,
    seed: int,
    alpha: float = 0.05,
) -> SimulationResult:
    """Estimate win-rule calibration or power with a seeded Monte Carlo run."""
    if simulations < 1 or n_per_arm < 2:
        raise ValueError("simulations >= 1 and n_per_arm >= 2 are required")
    if not 0 <= control_conversion <= 1 or not 0 <= treatment_conversion <= 1:
        raise ValueError("Conversion rates must be between 0 and 1")
    if practical_threshold < 0:
        raise ValueError("practical_threshold must be non-negative")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    rng = np.random.default_rng(seed)
    risk_differences: list[float] = []
    wins = 0
    losses = 0
    covered = 0
    true_difference = treatment_conversion - control_conversion
    for _ in range(simulations):
        control = int(rng.binomial(n_per_arm, control_conversion))
        treatment = int(rng.binomial(n_per_arm, treatment_conversion))
        risk_difference = treatment / n_per_arm - control / n_per_arm
        risk_differences.append(risk_difference)
        statistics = calculate_proportion_statistics(
            treatment,
            n_per_arm,
            control,
            n_per_arm,
            alpha,
        )
        if statistics is None:
            raise RuntimeError("Simulation arm sizes must be positive")
        ci_low, ci_high = statistics.confidence_interval
        if statistics.test.p_value < alpha and ci_low > practical_threshold:
            wins += 1
        elif ci_high < 0:
            losses += 1
        if ci_low <= true_difference <= ci_high:
            covered += 1
    win_interval = tuple(
        float(value)
        for value in proportion_confint(wins, simulations, alpha=alpha, method="wilson")
    )
    decisions = wins + losses
    decision_interval = tuple(
        float(value)
        for value in proportion_confint(
            decisions, simulations, alpha=alpha, method="wilson"
        )
    )
    return SimulationResult(
        simulations=simulations,
        actionable_win_rate=wins / simulations,
        actionable_win_rate_interval=win_interval,
        actionable_decision_rate=decisions / simulations,
        actionable_decision_rate_interval=decision_interval,
        coverage_rate=covered / simulations,
        mean_risk_difference=float(np.mean(risk_differences)),
    )
