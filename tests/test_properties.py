from hypothesis import given, strategies as st

from experimentlift.assignment import AssignmentStore
from experimentlift.power import required_sample_size_per_arm


@given(st.text(min_size=1), st.text(min_size=1))
def test_assignment_is_deterministic_for_participant(
    experiment_key: str, participant_id: str
) -> None:
    first = AssignmentStore(experiment_key, "secret").assign(participant_id)
    second = AssignmentStore(experiment_key, "secret").assign(participant_id)
    assert first.variant == second.variant


def test_required_sample_size_decreases_as_effect_increases() -> None:
    small_effect = required_sample_size_per_arm(0.10, 0.11, 0.80)
    large_effect = required_sample_size_per_arm(0.10, 0.15, 0.80)
    assert large_effect < small_effect
