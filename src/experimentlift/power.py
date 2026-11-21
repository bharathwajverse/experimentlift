"""Documented normal-approximation planning calculation."""

from math import ceil, sqrt

from scipy.stats import norm


def required_sample_size_per_arm(
    baseline_conversion: float,
    treatment_conversion: float,
    power: float,
    alpha: float = 0.05,
) -> int:
    """Equal-allocation two-sided two-proportion normal-approximation planning."""
    if not 0 < baseline_conversion < 1 or not 0 < treatment_conversion < 1:
        raise ValueError("Conversion rates must be strictly between 0 and 1")
    if not 0 < power < 1 or not 0 < alpha < 1:
        raise ValueError("power and alpha must be between 0 and 1")
    effect = abs(treatment_conversion - baseline_conversion)
    if effect == 0:
        raise ValueError("Treatment conversion must differ from baseline")
    p_bar = (baseline_conversion + treatment_conversion) / 2
    z_alpha = norm.ppf(1 - alpha / 2)
    z_power = norm.ppf(power)
    numerator = (
        z_alpha * sqrt(2 * p_bar * (1 - p_bar))
        + z_power
        * sqrt(
            baseline_conversion * (1 - baseline_conversion)
            + treatment_conversion * (1 - treatment_conversion)
        )
    ) ** 2
    return ceil(numerator / effect**2)
