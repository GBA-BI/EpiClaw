"""Smoke test for climate-health demo mode."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_demo(tmp_path: Path) -> None:
    skill_dir = Path(__file__).resolve().parents[1]
    script = skill_dir / "climate_health.py"
    result = subprocess.run(
        [sys.executable, str(script), "--demo", "--output", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=str(skill_dir),
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "report.md").exists()
    assert (tmp_path / "result.json").exists()
    payload = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert payload["skill"] == "climate-health"
