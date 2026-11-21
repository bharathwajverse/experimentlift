"""Database integration checks; CI provides a disposable PostgreSQL 16 database."""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("EXPERIMENTLIFT_TEST_DATABASE_URL"),
    reason="requires disposable PostgreSQL test database",
)


@pytest.fixture
def db():
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.orm import Session

    from experimentlift.db.models import Base

    url = os.environ["EXPERIMENTLIFT_TEST_DATABASE_URL"]
    assert url.startswith("postgresql+psycopg://")
    engine = create_engine(url)
    with engine.begin() as conn:
        assert conn.scalar(text("select current_setting('server_version_num')::int")) >= 160000
    assert set(Base.metadata.tables).issubset(inspect(engine).get_table_names())
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE workspaces CASCADE"))
    yield engine, Session
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE workspaces CASCADE"))
    engine.dispose()


def _seed(session):
    from experimentlift.db.models import Experiment, ExperimentRevision, Variant, Workspace

    wid, eid, rid, control, treatment = (uuid4() for _ in range(5))
    # Models declare table-level ForeignKeyConstraints only, without ORM
    # relationship() metadata, so SQLAlchemy derives no dependency edges and
    # falls back to mapper-name ordering (Experiment sorts before Workspace).
    # Flush each parent before its children, otherwise the child INSERT wins
    # the race and PostgreSQL rejects it with fk_experiment_workspace.
    session.add(Workspace(id=wid, name="Synthetic workspace"))
    session.flush()
    session.add(Experiment(id=eid, workspace_id=wid, experiment_key="sample"))
    session.flush()
    session.add(
        ExperimentRevision(
            id=rid, workspace_id=wid, experiment_id=eid, number=1,
            configuration={"data_source": "SYNTHETIC"},
            configuration_hash="a" * 64,
            starts_at=datetime.now(UTC) - timedelta(days=1),
            ends_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    session.flush()
    session.add_all([
        Variant(id=control, workspace_id=wid, revision_id=rid, arm="control", allocation=0.5),
        Variant(id=treatment, workspace_id=wid, revision_id=rid, arm="treatment", allocation=0.5),
    ])
    session.commit()
    return wid, eid, rid, control, treatment


def test_assignment_replay_conflict_and_reconnection(db):
    from experimentlift.db.store import AssignmentConflict, assign

    engine, Session = db
    with Session(engine) as session:
        wid, eid, rid, control, treatment = _seed(session)
        first = assign(session, wid, eid, rid, "synthetic-participant", control)
        session.commit()
        assert assign(session, wid, eid, rid, "synthetic-participant", control).id == first.id
        with pytest.raises(AssignmentConflict):
            assign(session, wid, eid, rid, "synthetic-participant", treatment)
    with Session(engine) as session:
        assert assign(session, wid, eid, rid, "synthetic-participant", control).id == first.id


def test_concurrent_assignment_has_one_winner(db):
    from experimentlift.db.models import Assignment
    from experimentlift.db.store import AssignmentConflict, assign
    from sqlalchemy import select

    engine, Session = db
    with Session(engine) as session:
        wid, eid, rid, control, treatment = _seed(session)

    def allocate(variant):
        with Session(engine) as session:
            try:
                record = assign(session, wid, eid, rid, "parallel", variant)
                session.commit()
                return record.variant_id
            except AssignmentConflict:
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(allocate, (control, treatment)))
    assert len([result for result in results if result is not None]) == 1
    with Session(engine) as session:
        assert len(session.scalars(select(Assignment)).all()) == 1


def test_event_replay_and_conflicting_payload(db):
    from experimentlift.db.models import Event
    from experimentlift.db.store import EventConflict, assign, record_event
    from sqlalchemy import select

    engine, Session = db
    now = datetime.now(UTC)
    with Session(engine) as session:
        wid, eid, rid, control, _ = _seed(session)
        assignment = assign(session, wid, eid, rid, "synthetic-participant", control)
        session.commit()
        first = record_event(
            session, wid, eid, rid, assignment.id, "synthetic-key",
            "converted", "synthetic", now,
        )
        session.commit()
        assert record_event(
            session, wid, eid, rid, assignment.id, "synthetic-key",
            "converted", "synthetic", now,
        ).id == first.id
        with pytest.raises(EventConflict):
            record_event(
                session, wid, eid, rid, assignment.id, "synthetic-key",
                "not_converted", "synthetic", now,
            )
        assert len(session.scalars(select(Event)).all()) == 1


def test_workspace_and_revision_cross_links_rejected(db):
    from sqlalchemy.exc import IntegrityError
    from experimentlift.db.models import Assignment, Experiment, Workspace

    engine, Session = db
    with Session(engine) as session:
        wid, eid, rid, control, _ = _seed(session)
        other = uuid4()
        session.add(Workspace(id=other, name="Other"))
        session.commit()
        session.add(Assignment(
            workspace_id=other, experiment_id=eid, revision_id=rid,
            variant_id=control, participant_id="cross", assignment_id="cross",
        ))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.add(Experiment(workspace_id=wid, experiment_key="sample"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_failed_transaction_rolls_back(db):
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError
    from experimentlift.db.models import Assignment, Experiment

    engine, Session = db
    with Session(engine) as session:
        wid, eid, rid, control, _ = _seed(session)
        session.add(Assignment(
            workspace_id=wid, experiment_id=eid, revision_id=rid,
            variant_id=control, participant_id="p", assignment_id="one",
        ))
        session.add(Experiment(workspace_id=wid, experiment_key="sample"))
        with pytest.raises(IntegrityError):
            session.commit()
    with Session(engine) as session:
        assert session.scalars(select(Assignment)).all() == []


def test_revision_activation_and_history_are_immutable(db):
    from sqlalchemy import select
    from sqlalchemy.exc import DBAPIError
    from experimentlift.db.models import AuditEvent, ExperimentRevision, Variant

    engine, Session = db
    with Session(engine) as session:
        wid, eid, rid, control, _ = _seed(session)
        revision = session.get(ExperimentRevision, rid)
        revision.state = "active"
        session.commit()
        revision.configuration = {"data_source": "OBSERVED"}
        with pytest.raises(DBAPIError):
            session.commit()
        session.rollback()
        variant = session.get(Variant, control)
        variant.allocation = 0.7
        with pytest.raises(DBAPIError):
            session.commit()
        session.rollback()
        session.add(AuditEvent(workspace_id=wid, experiment_id=eid, action="synthetic", detail={}))
        session.commit()
        audit = session.scalar(select(AuditEvent))
        audit.detail = {"changed": True}
        with pytest.raises(DBAPIError):
            session.commit()


def test_revision_cannot_be_inserted_active(db):
    from sqlalchemy.exc import DBAPIError
    from experimentlift.db.models import Experiment, ExperimentRevision, Workspace

    engine, Session = db
    wid, eid = uuid4(), uuid4()
    with Session(engine) as session:
        session.add(Workspace(id=wid, name="Synthetic workspace"))
        # Flush the workspace first; without relationship() metadata the
        # Experiment INSERT otherwise sorts ahead of Workspace and would fail
        # on fk_experiment_workspace, making this test pass for the wrong
        # reason (IntegrityError is a DBAPIError) instead of reaching the
        # revision guard below.
        session.flush()
        session.add(Experiment(id=eid, workspace_id=wid, experiment_key="sample"))
        session.commit()
        session.add(ExperimentRevision(
            workspace_id=wid, experiment_id=eid, number=1,
            configuration={}, configuration_hash="c" * 64,
            starts_at=datetime.now(UTC) - timedelta(days=1),
            ends_at=datetime.now(UTC) + timedelta(days=1),
            state="active",
        ))
        with pytest.raises(DBAPIError):
            session.commit()


def test_schema_constraints_and_event_revision_provenance(db):
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError
    from experimentlift.db.models import Event, ExperimentRevision, Variant
    from experimentlift.db.store import assign

    engine, Session = db
    with Session(engine) as session:
        wid, eid, rid, control, _ = _seed(session)
        assignment = assign(session, wid, eid, rid, "synthetic", control)
        other_revision = ExperimentRevision(
            workspace_id=wid, experiment_id=eid, number=2,
            configuration={}, configuration_hash="b" * 64,
            starts_at=datetime.now(UTC) - timedelta(days=1),
            ends_at=datetime.now(UTC) + timedelta(days=1),
        )
        session.add(other_revision)
        session.commit()
        session.add(Event(
            workspace_id=wid, experiment_id=eid, revision_id=other_revision.id,
            assignment_id=assignment.id, idempotency_key="foreign-revision",
            status="converted", source="synthetic", occurred_at=datetime.now(UTC),
        ))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.add(Variant(
            workspace_id=wid, revision_id=rid, arm="unknown", allocation=0.5,
        ))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert not session.scalars(select(Event)).all()


def test_historical_rows_are_append_only(db):
    from sqlalchemy import select
    from sqlalchemy.exc import DBAPIError
    from experimentlift.db.models import Assignment, Event, Exposure
    from experimentlift.db.store import assign, record_event

    engine, Session = db
    now = datetime.now(UTC)
    with Session(engine) as session:
        wid, eid, rid, control, _ = _seed(session)
        assignment = assign(session, wid, eid, rid, "synthetic-participant", control)
        session.flush()
        assignment_id = assignment.id
        event = record_event(
            session, wid, eid, rid, assignment_id, "synthetic-key",
            "converted", "synthetic", now,
        )
        session.add(Exposure(
            workspace_id=wid, experiment_id=eid, revision_id=rid,
            assignment_id=assignment_id, exposure_id="synthetic-exposure",
            occurred_at=now,
        ))
        session.commit()
        event_id = event.id

        assignment = session.get(Assignment, assignment_id)
        assignment.participant_id = "rewritten"
        with pytest.raises(DBAPIError):
            session.commit()
        session.rollback()

        event = session.get(Event, event_id)
        event.status = "not_converted"
        with pytest.raises(DBAPIError):
            session.commit()
        session.rollback()

        exposure = session.scalar(select(Exposure))
        exposure.occurred_at = now + timedelta(seconds=1)
        with pytest.raises(DBAPIError):
            session.commit()


def test_experiment_identity_and_metric_contract_are_frozen(db):
    from sqlalchemy import select
    from sqlalchemy.exc import DBAPIError
    from experimentlift.db.models import Experiment, ExperimentRevision, Metric

    engine, Session = db
    with Session(engine) as session:
        wid, eid, rid, control, _ = _seed(session)
        session.add(Metric(
            workspace_id=wid, revision_id=rid, name="conversion",
            definition={"kind": "binary"},
        ))
        session.commit()
        metric = session.scalar(select(Metric))
        metric.definition = {"kind": "binary", "window": "7d"}
        session.commit()
        detached = ExperimentRevision(
            workspace_id=wid, experiment_id=eid, number=2,
            configuration={}, configuration_hash="d" * 64,
            starts_at=datetime.now(UTC) - timedelta(days=1),
            ends_at=datetime.now(UTC) + timedelta(days=1),
        )
        session.add(detached)
        session.commit()
        metric = session.scalar(select(Metric))
        metric.revision_id = detached.id
        with pytest.raises(DBAPIError):
            session.commit()
        session.rollback()
        experiment = session.get(Experiment, eid)
        experiment.experiment_key = "renamed"
        with pytest.raises(DBAPIError):
            session.commit()
        session.rollback()
        revision = session.get(ExperimentRevision, rid)
        revision.state = "active"
        session.commit()
        metric = session.scalar(select(Metric))
        metric.definition = {"kind": "binary", "window": "14d"}
        with pytest.raises(DBAPIError):
            session.commit()
        session.rollback()
        session.add(Metric(
            workspace_id=wid, revision_id=rid, name="late",
            definition={"kind": "binary"},
        ))
        with pytest.raises(DBAPIError):
            session.commit()
