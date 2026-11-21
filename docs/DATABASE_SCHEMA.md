# M1 PostgreSQL contract (pending CI verification)

PostgreSQL 16 is the integration target, Psycopg 3 is the driver, SQLAlchemy
2.x owns the relational metadata and Alembic owns migration history. All stored
times use `TIMESTAMPTZ`; callers supply aware UTC-normalized times. Internal
row IDs are UUIDs; the existing domain's opaque `experiment_key`,
`participant_id`, `assignment_id` and integer revision remain distinct fields.
No assignment salt or participant profile is stored.

| Table | Ownership and invariant |
|---|---|
| `workspaces` | Workspace root UUID |
| `users` | Future auth subject only; no login implemented |
| `workspace_memberships` | Unique workspace/user, checked owner/member role |
| `experiments` | Unique `(workspace_id, experiment_key)` |
| `experiment_revisions` | Unique number per experiment; hashed JSON config and window; active revisions guarded by database trigger |
| `variants` | Unique control/treatment arms per revision; allocation check; trigger blocks mutation after activation |
| `assignments` | One participant per workspace/experiment across revisions; composite FKs bind variant and revision to same workspace and experiment |
| `exposures` | Separate exposure ID and timestamp, composite FK to assignment |
| `events` | Conversion status only (`converted` or `not_converted`); workspace-unique idempotency key, explicit event source, composite FK to assignment |
| `metrics` | Unique named definition per revision |
| `analysis_runs` | Unique run number per revision; versioned JSON report and required `SYNTHETIC`/`OBSERVED` provenance; append-only trigger |
| `audit_events` | Experiment-owned history; append-only trigger, no secrets in detail |

`ai_generations` is deferred. Activation requires both arms and allocations
totalling one. Database triggers protect active revision, variant and audit
history in the migration; SQLAlchemy metadata alone does not install triggers.
Application-level assignment and event helpers use PostgreSQL `ON CONFLICT DO
NOTHING` on named unique constraints and then compare persisted data; conflicting
replays raise explicit errors. Callers own the enclosing transaction and its
rollback. Unique constraints serialize competing writes. Assignment scope is
experiment-wide (not revision-wide) to preserve the first arm across edits.
Event source is additional provenance; the Phase 2 `OutcomeEvent` has no source
field, so a future adapter must supply one. Results require explicit version and
data-source fields; they do not recompute statistics.

Migration `0001_initial` contains frozen, manually reviewed DDL for all 12
tables and database triggers. `alembic check` compares it to current ORM
metadata on PostgreSQL in CI.

Known limitations of the immutability guards (documented, accepted for M1):

- The guard triggers are plain row-level `BEFORE UPDATE OR DELETE` triggers.
  A connection that owns the tables can `DROP TRIGGER`/`DISABLE TRIGGER`, and
  `TRUNCATE` bypasses row triggers entirely. The guards protect against
  application bugs and ordinary writers, not against an owner-privileged
  connection. The test fixture relies on this: it resets state with
  `TRUNCATE TABLE workspaces CASCADE`.
- `downgrade()` drops all 12 tables and therefore all history. The constraint
  is documented, not enforced: never run `alembic downgrade` against a shared
  or production database. `env.py` requires an explicit
  `postgresql+psycopg://` URL, so an accidental SQLite run is impossible.

Downgrade deletes all M1 rows and is permitted **only in a disposable test
database**. No production database has been touched.
