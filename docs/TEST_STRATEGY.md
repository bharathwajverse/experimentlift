# Test strategy

Tests cover deterministic A/A no-effect and known-effect fixtures, SRM,
duplicate event, missing outcome, zero conversion, low count/Fisher and
incomplete window cases. Property tests cover assignment determinism and
sample-size monotonicity. Independent tests calculate score-test, Newcombe,
Wald, Fisher and sample-size references without calling the implementation
helper. Input tests cover timezone awareness, allocation order, conflicts,
serialization, CLI errors and invalid generator/simulation parameters. Seeded
Monte Carlo tests check A/A decision-rate calibration, Monte Carlo uncertainty,
interval coverage and known-effect bias/power.

Adversarial boundary regressions additionally cover non-finite and immutable
allocation, revision provenance for every record type, pre-assignment and
post-analysis observations, future assignments, sparse Fisher parity, ignored
exposure warnings and simultaneous critical issues plus warnings in Markdown.

The known-effect power scenario uses 4,000 participants per arm because the
same effect with 2,000 per arm produced 0.848 actionable-win rate under its
fixed seed and 1pp practical threshold, below the predeclared 0.95 threshold.

Every fixture is synthetic. This phase does not validate provider integrations,
persistence, authentication or email delivery.
