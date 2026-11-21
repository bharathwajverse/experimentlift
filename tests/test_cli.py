import subprocess
import sys


def test_cli_rejects_unknown_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "experimentlift.cli", "unknown"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert completed.returncode != 0
    assert "invalid choice" in completed.stderr
