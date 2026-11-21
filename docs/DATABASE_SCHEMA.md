# Database schema (planned)

Phase 2 has no database. Phase 3 will add workspace-scoped `workspaces`,
`experiments`, `experiment_revisions`, `variants`, `assignments`, `exposures`,
`events`, `metrics`, `analysis_runs`, `ai_generations` and `audit_events`.

Planned constraints: unique `(workspace_id, experiment_id, participant_id)`
assignment; workspace event idempotency key; immutable active revision snapshot;
and separate exposure rows.
