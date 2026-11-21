from experimentlift.assignment import AssignmentStore
import pytest


def test_assignment_is_stable_and_persisted() -> None:
    store = AssignmentStore(experiment_key="email-001", salt="test-salt")

    first = store.assign("participant-42")
    second = store.assign("participant-42")

    assert first.variant == second.variant
    assert first is second
    assert store.count == 1


def test_assignment_is_independent_of_allocation_mapping_order() -> None:
    normal = AssignmentStore(
        "email-001", "test-salt", {"control": 0.7, "treatment": 0.3}
    )
    reversed_order = AssignmentStore(
        "email-001", "test-salt", {"treatment": 0.3, "control": 0.7}
    )

    for index in range(100):
        participant = f"participant-{index}"
        assert normal.assign(participant).variant == reversed_order.assign(participant).variant


@pytest.mark.parametrize(
    "allocation",
    [
        {"control": 0.5},
        {"control": 0.5, "treatment": 0.4},
        {"control": -0.1, "treatment": 1.1},
        {"control": 0.5, "treatment": 0.5, "other": 0.0},
        {},
        {"control": float("nan"), "treatment": float("nan")},
    ],
)
def test_assignment_rejects_invalid_allocations(allocation: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        AssignmentStore("email-001", "secret", allocation)


def test_assignment_rejects_empty_secret() -> None:
    with pytest.raises(ValueError, match="salt"):
        AssignmentStore("email-001", "")


def test_assignment_id_does_not_disclose_participant_identifier() -> None:
    assignment = AssignmentStore("email-001", "secret").assign("customer@example.test")
    assert "customer@example.test" not in assignment.assignment_id


def test_assignment_identity_changes_with_revision() -> None:
    revision_one = AssignmentStore("email-001", "secret", revision=1).assign("p1")
    revision_two = AssignmentStore("email-001", "secret", revision=2).assign("p1")
    assert revision_one.assignment_id != revision_two.assignment_id
    assert revision_one.experiment_revision == 1
    assert revision_two.experiment_revision == 2
