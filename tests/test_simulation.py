from experimentlift.simulation import evaluate_operating_characteristics


def test_aa_simulation_has_false_positive_rate_near_nominal() -> None:
    result = evaluate_operating_characteristics(
        simulations=2_000,
        n_per_arm=1_000,
        control_conversion=0.10,
        treatment_conversion=0.10,
        practical_threshold=0.0,
        seed=7,
    )
    assert 0.035 <= result.actionable_decision_rate <= 0.065
    assert (
        result.actionable_decision_rate_interval[0]
        <= 0.05
        <= result.actionable_decision_rate_interval[1]
    )
    assert 0.93 <= result.coverage_rate <= 0.97
    assert abs(result.mean_risk_difference) < 0.003


def test_known_effect_simulation_reports_high_power_and_low_bias() -> None:
    result = evaluate_operating_characteristics(
        simulations=500,
        n_per_arm=4_000,
        control_conversion=0.10,
        treatment_conversion=0.14,
        practical_threshold=0.01,
        seed=9,
    )
    assert result.actionable_win_rate > 0.95
    assert result.actionable_win_rate_interval[0] > 0.93
    assert abs(result.mean_risk_difference - 0.04) < 0.002
    assert 0.92 <= result.coverage_rate <= 0.98


def test_sparse_simulation_uses_production_fisher_routing() -> None:
    result = evaluate_operating_characteristics(
        simulations=10,
        n_per_arm=3,
        control_conversion=0.0,
        treatment_conversion=1.0,
        practical_threshold=0.0,
        seed=1,
    )
    assert result.actionable_win_rate == 0.0
