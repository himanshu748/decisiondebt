"""Opt-in destructive-to-availability test, only our dedicated local container."""

import os
import subprocess
import sys
import pytest
from backend.app.settings import ROOT


@pytest.mark.skipif(
    os.getenv("DD_TEST_LIFECYCLE") != "1",
    reason="Set DD_TEST_LIFECYCLE=1 with the local API running to stop/restart decisiondebt-db",
)
def test_actual_outage_and_restart_persistence():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/check_lifecycle.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
