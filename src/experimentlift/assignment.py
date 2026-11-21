"""Stable, in-memory assignment persistence for the Phase 2 vertical slice."""

from __future__ import annotations

import hashlib
import hmac
from math import isfinite

from .models import Assignment


class AssignmentStore:
    """Persists first assignment in process; a later database store replaces this."""

    def __init__(
        self,
        experiment_key: str,
        salt: str,
        allocation: dict[str, float] | None = None,
        revision: int = 1,
    ) -> None:
        if not experiment_key:
            raise ValueError("experiment_key is required")
        if not salt:
            raise ValueError("salt is required")
        if revision < 1:
            raise ValueError("revision must be at least 1")
        self.experiment_key = experiment_key
        self.revision = revision
        self._salt = salt.encode("utf-8")
        self.allocation = (
            {"control": 0.5, "treatment": 0.5}
            if allocation is None
            else dict(allocation)
        )
        if set(self.allocation) != {"control", "treatment"}:
            raise ValueError("Allocation requires exactly control and treatment arms")
        if any(not isfinite(value) for value in self.allocation.values()):
            raise ValueError("Allocation values must be finite")
        if any(value <= 0 for value in self.allocation.values()):
            raise ValueError("Allocation values must be positive")
        if abs(sum(self.allocation.values()) - 1.0) > 1e-12:
            raise ValueError("Allocation must sum to 1.0")
        self._assignments: dict[str, Assignment] = {}

    @property
    def count(self) -> int:
        return len(self._assignments)

    @property
    def salt_hash(self) -> str:
        return hashlib.sha256(self._salt).hexdigest()

    def assign(self, participant_id: str) -> Assignment:
        """Return the persisted first assignment; never re-randomize."""
        if participant_id in self._assignments:
            return self._assignments[participant_id]

        digest = hmac.new(
            self._salt,
            f"{self.experiment_key}:{self.revision}:{participant_id}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
        bucket = int.from_bytes(digest[:8], "big") / 2**64
        cumulative = 0.0
        variant = "treatment"
        for candidate in ("control", "treatment"):
            probability = self.allocation[candidate]
            cumulative += probability
            if bucket < cumulative:
                variant = candidate
                break
        assignment_digest = hmac.new(
            self._salt,
            (
                f"assignment:{self.experiment_key}:{self.revision}:{participant_id}"
            ).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assignment = Assignment(
            experiment_key=self.experiment_key,
            experiment_revision=self.revision,
            participant_id=participant_id,
            variant=variant,
            assignment_id=assignment_digest,
        )
        self._assignments[participant_id] = assignment
        return assignment
