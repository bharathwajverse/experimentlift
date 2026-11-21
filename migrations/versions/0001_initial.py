"""Initial PostgreSQL 16 foundation.

Revision ID: 0001_initial
Revises:
"""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Frozen DDL: never import mutable application metadata into a migration.
    op.execute("""
        CREATE TABLE workspaces (
            id UUID PRIMARY KEY, name VARCHAR(200) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY, external_subject VARCHAR(256) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE workspace_memberships (
            id UUID PRIMARY KEY, workspace_id UUID NOT NULL,
            user_id UUID NOT NULL, role VARCHAR(32) NOT NULL,
            CONSTRAINT fk_membership_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
            CONSTRAINT fk_membership_user FOREIGN KEY (user_id) REFERENCES users(id),
            CONSTRAINT uq_membership_workspace_user UNIQUE (workspace_id, user_id),
            CONSTRAINT ck_membership_role CHECK (role IN ('owner', 'member'))
        )
    """)
    op.execute("""
        CREATE TABLE experiments (
            id UUID PRIMARY KEY, workspace_id UUID NOT NULL,
            experiment_key VARCHAR(128) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_experiment_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
            CONSTRAINT uq_experiment_workspace_id UNIQUE (workspace_id, id),
            CONSTRAINT uq_experiment_key UNIQUE (workspace_id, experiment_key),
            CONSTRAINT ck_experiment_key CHECK (length(trim(experiment_key)) > 0)
        )
    """)
    op.execute("""
        CREATE TABLE experiment_revisions (
            id UUID PRIMARY KEY, workspace_id UUID NOT NULL,
            experiment_id UUID NOT NULL, number INTEGER NOT NULL,
            configuration JSONB NOT NULL, configuration_hash VARCHAR(64) NOT NULL,
            starts_at TIMESTAMPTZ NOT NULL, ends_at TIMESTAMPTZ NOT NULL,
            state VARCHAR(16) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_revision_experiment FOREIGN KEY (workspace_id, experiment_id)
                REFERENCES experiments(workspace_id, id),
            CONSTRAINT uq_revision_workspace_id UNIQUE (workspace_id, id),
            CONSTRAINT uq_revision_experiment_id UNIQUE (workspace_id, experiment_id, id),
            CONSTRAINT uq_revision_number UNIQUE (workspace_id, experiment_id, number),
            CONSTRAINT ck_revision_number CHECK (number >= 1),
            CONSTRAINT ck_revision_window CHECK (ends_at > starts_at),
            CONSTRAINT ck_revision_state CHECK (state IN ('draft', 'active', 'closed')),
            CONSTRAINT ck_revision_hash CHECK (configuration_hash ~ '^[0-9a-f]{64}$')
        )
    """)
    op.execute("""
        CREATE TABLE variants (
            id UUID PRIMARY KEY, workspace_id UUID NOT NULL, revision_id UUID NOT NULL,
            arm VARCHAR(16) NOT NULL, allocation NUMERIC(12, 10) NOT NULL,
            CONSTRAINT fk_variant_revision FOREIGN KEY (workspace_id, revision_id)
                REFERENCES experiment_revisions(workspace_id, id),
            CONSTRAINT uq_variant_revision_id UNIQUE (workspace_id, revision_id, id),
            CONSTRAINT uq_variant_arm UNIQUE (workspace_id, revision_id, arm),
            CONSTRAINT ck_variant_arm CHECK (arm IN ('control', 'treatment')),
            CONSTRAINT ck_variant_allocation CHECK (allocation > 0 AND allocation < 1)
        )
    """)
    op.execute("""
        CREATE TABLE assignments (
            id UUID PRIMARY KEY, workspace_id UUID NOT NULL, experiment_id UUID NOT NULL,
            revision_id UUID NOT NULL, variant_id UUID NOT NULL,
            participant_id VARCHAR(256) NOT NULL, assignment_id VARCHAR(256) NOT NULL,
            assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_assignment_revision FOREIGN KEY (workspace_id, experiment_id, revision_id)
                REFERENCES experiment_revisions(workspace_id, experiment_id, id),
            CONSTRAINT fk_assignment_variant FOREIGN KEY (workspace_id, revision_id, variant_id)
                REFERENCES variants(workspace_id, revision_id, id),
            CONSTRAINT uq_assignment_participant UNIQUE (workspace_id, experiment_id, participant_id),
            CONSTRAINT uq_assignment_external_id UNIQUE (workspace_id, assignment_id),
            CONSTRAINT uq_assignment_revision_id UNIQUE (workspace_id, experiment_id, revision_id, id),
            CONSTRAINT ck_assignment_participant CHECK (length(trim(participant_id)) > 0),
            CONSTRAINT ck_assignment_external_id CHECK (length(trim(assignment_id)) > 0)
        )
    """)
    op.execute("""
        CREATE TABLE exposures (
            id UUID PRIMARY KEY, workspace_id UUID NOT NULL, experiment_id UUID NOT NULL,
            revision_id UUID NOT NULL, assignment_id UUID NOT NULL,
            exposure_id VARCHAR(256) NOT NULL, occurred_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT fk_exposure_assignment
                FOREIGN KEY (workspace_id, experiment_id, revision_id, assignment_id)
                REFERENCES assignments(workspace_id, experiment_id, revision_id, id),
            CONSTRAINT uq_exposure_external_id UNIQUE (workspace_id, exposure_id)
        )
    """)
    op.execute("CREATE INDEX ix_exposure_assignment_time ON exposures (assignment_id, occurred_at)")
    op.execute("""
        CREATE TABLE events (
            id UUID PRIMARY KEY, workspace_id UUID NOT NULL, experiment_id UUID NOT NULL,
            revision_id UUID NOT NULL, assignment_id UUID NOT NULL,
            idempotency_key VARCHAR(256) NOT NULL, source VARCHAR(128) NOT NULL,
            status VARCHAR(16) NOT NULL, occurred_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_event_assignment
                FOREIGN KEY (workspace_id, experiment_id, revision_id, assignment_id)
                REFERENCES assignments(workspace_id, experiment_id, revision_id, id),
            CONSTRAINT uq_event_idempotency UNIQUE (workspace_id, idempotency_key),
            CONSTRAINT ck_event_status CHECK (status IN ('converted', 'not_converted')),
            CONSTRAINT ck_event_key CHECK (length(trim(idempotency_key)) > 0),
            CONSTRAINT ck_event_source CHECK (length(trim(source)) > 0)
        )
    """)
    op.execute("CREATE INDEX ix_event_revision_time ON events (revision_id, occurred_at)")
    op.execute("""
        CREATE TABLE metrics (
            id UUID PRIMARY KEY, workspace_id UUID NOT NULL, revision_id UUID NOT NULL,
            name VARCHAR(128) NOT NULL, definition JSONB NOT NULL,
            CONSTRAINT fk_metric_revision FOREIGN KEY (workspace_id, revision_id)
                REFERENCES experiment_revisions(workspace_id, id),
            CONSTRAINT uq_metric_name UNIQUE (workspace_id, revision_id, name)
        )
    """)
    op.execute("""
        CREATE TABLE analysis_runs (
            id UUID PRIMARY KEY, workspace_id UUID NOT NULL, revision_id UUID NOT NULL,
            run_number INTEGER NOT NULL, report_version VARCHAR(32) NOT NULL,
            data_source VARCHAR(32) NOT NULL, result JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_analysis_revision FOREIGN KEY (workspace_id, revision_id)
                REFERENCES experiment_revisions(workspace_id, id),
            CONSTRAINT uq_analysis_run_number UNIQUE (workspace_id, revision_id, run_number),
            CONSTRAINT ck_analysis_run_number CHECK (run_number >= 1),
            CONSTRAINT ck_analysis_source CHECK (data_source IN ('SYNTHETIC', 'OBSERVED')),
            CONSTRAINT ck_analysis_version CHECK (length(trim(report_version)) > 0)
        )
    """)
    op.execute("CREATE INDEX ix_analysis_revision_created ON analysis_runs (revision_id, created_at)")
    op.execute("""
        CREATE TABLE audit_events (
            id UUID PRIMARY KEY, workspace_id UUID NOT NULL, experiment_id UUID NOT NULL,
            action VARCHAR(128) NOT NULL, detail JSONB NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_audit_experiment FOREIGN KEY (workspace_id, experiment_id)
                REFERENCES experiments(workspace_id, id),
            CONSTRAINT ck_audit_action CHECK (length(trim(action)) > 0)
        )
    """)
    op.execute("CREATE INDEX ix_audit_experiment_time ON audit_events (experiment_id, occurred_at)")
    op.execute("""
        CREATE FUNCTION experimentlift_immutable_row() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'immutable historical row'; END;
        $$;
    """)
    op.execute("""
        CREATE TRIGGER audit_events_append_only
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION experimentlift_immutable_row();
    """)
    op.execute("""
        CREATE TRIGGER analysis_runs_append_only
        BEFORE UPDATE OR DELETE ON analysis_runs
        FOR EACH ROW EXECUTE FUNCTION experimentlift_immutable_row();
    """)
    op.execute("""
        CREATE FUNCTION experimentlift_revision_guard() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.state <> 'draft' THEN
                RAISE EXCEPTION 'activated revision is immutable';
            END IF;
            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            END IF;
            IF NEW.workspace_id <> OLD.workspace_id OR NEW.experiment_id <> OLD.experiment_id
               OR NEW.number <> OLD.number OR NEW.id <> OLD.id THEN
                RAISE EXCEPTION 'revision identity is immutable';
            END IF;
            IF NEW.state NOT IN ('draft', 'active') THEN
                RAISE EXCEPTION 'draft can only activate';
            END IF;
            IF NEW.state = 'active' AND (
                SELECT count(*) <> 2 OR coalesce(sum(allocation), 0) <> 1
                FROM variants WHERE workspace_id = OLD.workspace_id AND revision_id = OLD.id
            ) THEN
                RAISE EXCEPTION 'activation requires exactly two complete variant allocations';
            END IF;
            RETURN NEW;
        END;
        $$;
    """)
    op.execute("""
        CREATE TRIGGER revision_frozen_after_activation
        BEFORE UPDATE OR DELETE ON experiment_revisions
        FOR EACH ROW EXECUTE FUNCTION experimentlift_revision_guard();
    """)
    op.execute("""
        CREATE FUNCTION experimentlift_variant_guard() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE target_workspace uuid; target_revision uuid;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                target_workspace := OLD.workspace_id;
                target_revision := OLD.revision_id;
            ELSE
                target_workspace := NEW.workspace_id;
                target_revision := NEW.revision_id;
            END IF;
            IF EXISTS (
                SELECT 1 FROM experiment_revisions
                WHERE workspace_id = target_workspace AND id = target_revision
                  AND state <> 'draft'
            ) THEN
                RAISE EXCEPTION 'activated revision variants are immutable';
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
        END;
        $$;
    """)
    op.execute("""
        CREATE TRIGGER variant_frozen_after_activation
        BEFORE INSERT OR UPDATE OR DELETE ON variants
        FOR EACH ROW EXECUTE FUNCTION experimentlift_variant_guard();
    """)


def downgrade():
    # Only on a disposable database: drops ALL M1 rows, including history.
    for table in (
        "audit_events", "analysis_runs", "metrics", "events", "exposures",
        "assignments", "variants", "experiment_revisions",
        "workspace_memberships", "experiments", "users", "workspaces",
    ):
        op.drop_table(table)
    op.execute("DROP FUNCTION experimentlift_variant_guard()")
    op.execute("DROP FUNCTION experimentlift_revision_guard()")
    op.execute("DROP FUNCTION experimentlift_immutable_row()")
