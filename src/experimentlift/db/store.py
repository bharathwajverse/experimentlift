"""Transactional idempotency primitives. Callers own commit/rollback."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .models import Assignment, Event


class AssignmentConflict(ValueError):
    """Participant already has a different experiment allocation."""


class EventConflict(ValueError):
    """Idempotency key is bound to a different event payload."""


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


def assign(
    session: Session, workspace_id: UUID, experiment_id: UUID,
    revision_id: UUID, participant_id: str, variant_id: UUID,
) -> Assignment:
    if not participant_id or not participant_id.strip():
        raise ValueError("participant_id must not be empty")
    candidate = dict(
        id=uuid4(), workspace_id=workspace_id, experiment_id=experiment_id,
        revision_id=revision_id, participant_id=participant_id,
        variant_id=variant_id, assignment_id=uuid4().hex,
    )
    session.execute(
        insert(Assignment).values(**candidate)
        .on_conflict_do_nothing(constraint="uq_assignment_participant")
    )
    record = session.scalar(
        select(Assignment).where(
            Assignment.workspace_id == workspace_id,
            Assignment.experiment_id == experiment_id,
            Assignment.participant_id == participant_id,
        )
    )
    if record is None:
        raise RuntimeError("assignment insert did not produce a row")
    if record.revision_id != revision_id or record.variant_id != variant_id:
        raise AssignmentConflict("participant already assigned to another revision or variant")
    return record


def record_event(
    session: Session, workspace_id: UUID, experiment_id: UUID,
    revision_id: UUID, assignment_id: UUID, idempotency_key: str,
    status: str, source: str, occurred_at: datetime,
) -> Event:
    if not idempotency_key or not idempotency_key.strip() or not source or not source.strip():
        raise ValueError("event key and source must not be empty")
    occurred_at = _utc(occurred_at)
    session.execute(
        insert(Event).values(
            id=uuid4(), workspace_id=workspace_id, experiment_id=experiment_id,
            revision_id=revision_id, assignment_id=assignment_id,
            idempotency_key=idempotency_key, status=status, source=source,
            occurred_at=occurred_at,
        ).on_conflict_do_nothing(constraint="uq_event_idempotency")
    )
    record = session.scalar(
        select(Event).where(
            Event.workspace_id == workspace_id,
            Event.idempotency_key == idempotency_key,
        )
    )
    if record is None:
        raise RuntimeError("event insert did not produce a row")
    if (
        record.experiment_id != experiment_id
        or record.revision_id != revision_id
        or record.assignment_id != assignment_id
        or record.status != status
        or record.source != source
        or record.occurred_at != occurred_at
    ):
        raise EventConflict("idempotency key is already bound to a different event")
    return record
