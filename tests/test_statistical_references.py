from math import sqrt

import pytest
from scipy.stats import norm
from statsmodels.stats.proportion import (
    proportion_confint,
    samplesize_proportions_2indep_onetail,
)

from experimentlift.analysis import calculate_proportion_statistics
from experimentlift.power import required_sample_size_per_arm


def test_score_test_newcombe_and_wald_match_independent_reference() -> None:
    result = calculate_proportion_statistics(
        treatment_conversions=30,
        treatment_n=100,
        control_conversions=20,
        control_n=100,
        alpha=0.05,
    )

    pooled = 50 / 200
    expected_z = (0.30 - 0.20) / sqrt(pooled * (1 - pooled) * (1 / 100 + 1 / 100))
    expected_p = 2 * norm.sf(abs(expected_z))
    t_low, t_high = proportion_confint(30, 100, alpha=0.05, method="wilson")
    c_low, c_high = proportion_confint(20, 100, alpha=0.05, method="wilson")
    difference = 0.10
    expected_newcombe = (
        difference - sqrt((0.30 - t_low) ** 2 + (c_high - 0.20) ** 2),
        difference + sqrt((t_high - 0.30) ** 2 + (0.20 - c_low) ** 2),
    )
    standard_error = sqrt(0.30 * 0.70 / 100 + 0.20 * 0.80 / 100)
    expected_wald = (
        difference - norm.ppf(0.975) * standard_error,
        difference + norm.ppf(0.975) * standard_error,
    )

    assert result.test.method == "score"
    assert result.test.statistic == pytest.approx(expected_z)
    assert result.test.p_value == pytest.approx(expected_p)
    assert result.confidence_interval == pytest.approx(expected_newcombe)
    assert result.wald_confidence_interval == pytest.approx(expected_wald)


def test_unequal_high_conversion_arms_do_not_trigger_fisher_incorrectly() -> None:
    result = calculate_proportion_statistics(
        treatment_conversions=29,
        treatment_n=30,
        control_conversions=70,
        control_n=100,
        alpha=0.05,
    )
    assert result.test.method == "score"


def test_small_expected_cell_uses_fisher_reference() -> None:
    result = calculate_proportion_statistics(3, 20, 0, 20, 0.05)
    assert result.test.method == "fisher_exact"
    assert result.test.p_value == pytest.approx(0.23076923076923075)


def test_sample_size_matches_statsmodels_reference() -> None:
    actual = required_sample_size_per_arm(0.10, 0.13, 0.80)
    reference = samplesize_proportions_2indep_onetail(
        0.03, 0.10, 0.80, alpha=0.05, alternative="two-sided"
    )
    assert actual == 1774
    assert actual - 1 < reference <= actual


@pytest.mark.parametrize(
    "arguments",
    [
        (1, 0, 0, 10, 0.05),
        (1, 10, 0, 10, 1.0),
    ],
)
def test_proportion_statistics_reject_invalid_inputs(
    arguments: tuple[int, int, int, int, float],
) -> None:
    with pytest.raises(ValueError):
        calculate_proportion_statistics(*arguments)
