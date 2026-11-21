"""Migration round-trip checks use only an explicitly disposable PostgreSQL DB."""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("EXPERIMENTLIFT_TEST_DATABASE_URL"),
    reason="requires disposable PostgreSQL test database",
)


def test_upgrade_downgrade_reupgrade_and_drift():
    from sqlalchemy import create_engine, inspect
    from experimentlift.db.models import Base

    assert os.environ["DATABASE_URL"] == os.environ["EXPERIMENTLIFT_TEST_DATABASE_URL"]
    assert os.environ["DATABASE_URL"].startswith("postgresql+psycopg://")
    engine = create_engine(os.environ["DATABASE_URL"])
    try:
        subprocess.run([sys.executable, "-m", "alembic", "downgrade", "base"], check=True)
        assert not (set(Base.metadata.tables) & set(inspect(engine).get_table_names()))
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        assert set(Base.metadata.tables).issubset(inspect(engine).get_table_names())
        subprocess.run([sys.executable, "-m", "alembic", "check"], check=True)
    finally:
        engine.dispose()
