# server/tests/test_ci_workflow_required_jobs.py
from __future__ import annotations

from pathlib import Path
import re


def test_ci_workflow_has_required_pytest_job_key_and_guard_step() -> None:
    # repo_root/server/tests/ -> parents[2] == repo_root
    repo_root = Path(__file__).resolve().parents[2]
    wf = repo_root / ".github" / "workflows" / "ci.yml"
    assert wf.exists(), f"CI workflow fehlt: {wf}"

    txt = wf.read_text(encoding="utf-8", errors="strict")

    # Required job key muss existieren (Branch Protection hängt daran)
    assert re.search(r"(?m)^\s{2}pytest\s*:\s*$", txt), "CI workflow muss 'jobs: -> pytest:' enthalten"

    # Stabiler Job-Name im pytest-Job (empfohlen + hier enforced)
    assert re.search(
        r"(?m)^\s{4}name\s*:\s*['\"]?pytest['\"]?\s*$", txt
    ), "CI workflow: im pytest-job muss 'name: pytest' gesetzt sein"

    # Guard-Step muss im Workflow vorhanden bleiben (sonst kann drift wieder passieren)
    assert "server/scripts/ci_guard_required_job_pytest.ps1" in txt, (
        "CI workflow muss den Guard-Step enthalten (ci_guard_required_job_pytest.ps1)"
    )

    # Web build job soll vorhanden sein (nicht required check, aber MVP-Härtung)
    assert re.search(r"(?m)^\s{2}web_build\s*:\s*$", txt), "CI workflow muss 'jobs: -> web_build:' enthalten"