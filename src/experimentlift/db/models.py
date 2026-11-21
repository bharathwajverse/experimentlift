"""M1 relational contract. UUID rows are internal; domain keys remain opaque strings."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, Numeric,
    String, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# Flush-ordering contract: these models intentionally declare table-level
# ForeignKeyConstraint metadata only and no ORM relationship()s, so a Session
# derives no parent/child dependency edges and orders INSERTs by mapper name.
# Because "Experiment" sorts before "Workspace", a session that holds a parent
# and its children pending in the same flush emits the child first and
# PostgreSQL rejects it. Production paths use Core inserts with explicit
# ordering; code that uses session.add()/add_all() must flush each parent
# before adding its children.


def uid():
    return mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


def workspace():
    return mapped_column(PGUUID(as_uuid=True), nullable=False)


def timestamp():
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[UUID] = uid()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = timestamp()


class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = uid()
    external_subject: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    created_at: Mapped[datetime] = timestamp()


class WorkspaceMembership(Base):
    __tablename__ = "workspace_memberships"
    id: Mapped[UUID] = uid()
    workspace_id: Mapped[UUID] = workspace()
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name="fk_membership_workspace"),
        ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_membership_user"),
        UniqueConstraint("workspace_id", "user_id", name="uq_membership_workspace_user"),
        CheckConstraint("role IN ('owner', 'member')", name="ck_membership_role"),
    )


class Experiment(Base):
    __tablename__ = "experiments"
    id: Mapped[UUID] = uid()
    workspace_id: Mapped[UUID] = workspace()
    experiment_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = timestamp()
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name="fk_experiment_workspace"),
        UniqueConstraint("workspace_id", "id", name="uq_experiment_workspace_id"),
        UniqueConstraint("workspace_id", "experiment_key", name="uq_experiment_key"),
        CheckConstraint("length(trim(experiment_key)) > 0", name="ck_experiment_key"),
    )


class ExperimentRevision(Base):
    __tablename__ = "experiment_revisions"
    id: Mapped[UUID] = uid()
    workspace_id: Mapped[UUID] = workspace()
    experiment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False)
    configuration_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, server_default="draft")
    created_at: Mapped[datetime] = timestamp()
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "experiment_id"], ["experiments.workspace_id", "experiments.id"], name="fk_revision_experiment"),
        UniqueConstraint("workspace_id", "id", name="uq_revision_workspace_id"),
        UniqueConstraint("workspace_id", "experiment_id", "id", name="uq_revision_experiment_id"),
        UniqueConstraint("workspace_id", "experiment_id", "number", name="uq_revision_number"),
        CheckConstraint("number >= 1", name="ck_revision_number"),
        CheckConstraint("ends_at > starts_at", name="ck_revision_window"),
        CheckConstraint("state IN ('draft', 'active', 'closed')", name="ck_revision_state"),
        CheckConstraint("configuration_hash ~ '^[0-9a-f]{64}$'", name="ck_revision_hash"),
    )


class Variant(Base):
    __tablename__ = "variants"
    id: Mapped[UUID] = uid()
    workspace_id: Mapped[UUID] = workspace()
    revision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    arm: Mapped[str] = mapped_column(String(16), nullable=False)
    allocation: Mapped[float] = mapped_column(Numeric(12, 10), nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "revision_id"], ["experiment_revisions.workspace_id", "experiment_revisions.id"], name="fk_variant_revision"),
        UniqueConstraint("workspace_id", "revision_id", "id", name="uq_variant_revision_id"),
        UniqueConstraint("workspace_id", "revision_id", "arm", name="uq_variant_arm"),
        CheckConstraint("arm IN ('control', 'treatment')", name="ck_variant_arm"),
        CheckConstraint("allocation > 0 AND allocation < 1", name="ck_variant_allocation"),
    )


class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[UUID] = uid()
    workspace_id: Mapped[UUID] = workspace()
    experiment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    revision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    variant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    participant_id: Mapped[str] = mapped_column(String(256), nullable=False)
    assignment_id: Mapped[str] = mapped_column(String(256), nullable=False)
    assigned_at: Mapped[datetime] = timestamp()
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "experiment_id", "revision_id"], ["experiment_revisions.workspace_id", "experiment_revisions.experiment_id", "experiment_revisions.id"], name="fk_assignment_revision"),
        ForeignKeyConstraint(["workspace_id", "revision_id", "variant_id"], ["variants.workspace_id", "variants.revision_id", "variants.id"], name="fk_assignment_variant"),
        UniqueConstraint("workspace_id", "experiment_id", "participant_id", name="uq_assignment_participant"),
        UniqueConstraint("workspace_id", "assignment_id", name="uq_assignment_external_id"),
        UniqueConstraint("workspace_id", "experiment_id", "revision_id", "id", name="uq_assignment_revision_id"),
        CheckConstraint("length(trim(participant_id)) > 0", name="ck_assignment_participant"),
        CheckConstraint("length(trim(assignment_id)) > 0", name="ck_assignment_external_id"),
    )


class Exposure(Base):
    __tablename__ = "exposures"
    id: Mapped[UUID] = uid()
    workspace_id: Mapped[UUID] = workspace()
    experiment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    revision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    assignment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    exposure_id: Mapped[str] = mapped_column(String(256), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "experiment_id", "revision_id", "assignment_id"], ["assignments.workspace_id", "assignments.experiment_id", "assignments.revision_id", "assignments.id"], name="fk_exposure_assignment"),
        UniqueConstraint("workspace_id", "exposure_id", name="uq_exposure_external_id"),
        Index("ix_exposure_assignment_time", "assignment_id", "occurred_at"),
    )


class Event(Base):
    __tablename__ = "events"
    id: Mapped[UUID] = uid()
    workspace_id: Mapped[UUID] = workspace()
    experiment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    revision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    assignment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = timestamp()
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "experiment_id", "revision_id", "assignment_id"], ["assignments.workspace_id", "assignments.experiment_id", "assignments.revision_id", "assignments.id"], name="fk_event_assignment"),
        UniqueConstraint("workspace_id", "idempotency_key", name="uq_event_idempotency"),
        CheckConstraint("status IN ('converted', 'not_converted')", name="ck_event_status"),
        CheckConstraint("length(trim(idempotency_key)) > 0", name="ck_event_key"),
        CheckConstraint("length(trim(source)) > 0", name="ck_event_source"),
        Index("ix_event_revision_time", "revision_id", "occurred_at"),
    )


class Metric(Base):
    __tablename__ = "metrics"
    id: Mapped[UUID] = uid()
    workspace_id: Mapped[UUID] = workspace()
    revision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "revision_id"], ["experiment_revisions.workspace_id", "experiment_revisions.id"], name="fk_metric_revision"),
        UniqueConstraint("workspace_id", "revision_id", "name", name="uq_metric_name"),
    )


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id: Mapped[UUID] = uid()
    workspace_id: Mapped[UUID] = workspace()
    revision_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    report_version: Mapped[str] = mapped_column(String(32), nullable=False)
    data_source: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = timestamp()
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "revision_id"], ["experiment_revisions.workspace_id", "experiment_revisions.id"], name="fk_analysis_revision"),
        UniqueConstraint("workspace_id", "revision_id", "run_number", name="uq_analysis_run_number"),
        CheckConstraint("run_number >= 1", name="ck_analysis_run_number"),
        CheckConstraint("data_source IN ('SYNTHETIC', 'OBSERVED')", name="ck_analysis_source"),
        CheckConstraint("length(trim(report_version)) > 0", name="ck_analysis_version"),
        Index("ix_analysis_revision_created", "revision_id", "created_at"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[UUID] = uid()
    workspace_id: Mapped[UUID] = workspace()
    experiment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False)
    occurred_at: Mapped[datetime] = timestamp()
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "experiment_id"], ["experiments.workspace_id", "experiments.id"], name="fk_audit_experiment"),
        CheckConstraint("length(trim(action)) > 0", name="ck_audit_action"),
        Index("ix_audit_experiment_time", "experiment_id", "occurred_at"),
    )
