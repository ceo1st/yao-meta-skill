#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_review_waivers.py"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_review_waivers"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    skill = tmp_root / "waiver-demo"
    (skill / "reports").mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text("---\nname: waiver-demo\ndescription: Waiver demo.\n---\n\n# Demo\n", encoding="utf-8")

    empty = run(str(skill), "--generated-at", "2026-06-13")
    empty_payload = json.loads(empty.stdout)
    assert empty_payload["ok"], empty_payload
    assert empty_payload["summary"]["waiver_count"] == 0, empty_payload
    assert (skill / "reports" / "review_waivers.json").exists(), skill
    assert (skill / "reports" / "review_waivers.md").exists(), skill

    added = run(
        str(skill),
        "--generated-at",
        "2026-06-13",
        "--add-waiver",
        "--gate-key",
        "trust-report",
        "--reviewer",
        "Yao Team",
        "--reason",
        "Network-capable scripts are reviewed and bounded for this release.",
        "--expires-at",
        "2026-09-30",
    )
    added_payload = json.loads(added.stdout)
    assert added_payload["ok"], added_payload
    assert added_payload["summary"]["active_count"] == 1, added_payload
    assert added_payload["summary"]["covered_gate_keys"] == ["trust-report"], added_payload
    assert "trust-report" in (skill / "reports" / "review_waivers.md").read_text(encoding="utf-8")

    expired_source = tmp_root / "expired.json"
    expired_source.write_text(
        json.dumps(
            {
                "waivers": [
                    {
                        "gate_key": "operations-loop",
                        "decision": "temporary-exception",
                        "reviewer": "Yao Team",
                        "reason": "No local telemetry sample exists yet, accepted only for historical demo review.",
                        "created_at": "2026-01-01",
                        "expires_at": "2026-01-31",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    expired = run(str(skill), "--waivers-json", str(expired_source), "--output-json", str(tmp_root / "expired_report.json"), "--output-md", str(tmp_root / "expired_report.md"), "--generated-at", "2026-06-13")
    expired_payload = json.loads(expired.stdout)
    assert expired_payload["ok"], expired_payload
    assert expired_payload["summary"]["expired_count"] == 1, expired_payload
    assert expired_payload["summary"]["active_count"] == 0, expired_payload
    assert expired_payload["warnings"], expired_payload

    invalid_source = tmp_root / "invalid.json"
    invalid_source.write_text(
        json.dumps({"waivers": [{"gate_key": "trust-report", "reason": "too short"}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    invalid = run(str(skill), "--waivers-json", str(invalid_source), "--output-json", str(tmp_root / "invalid_report.json"), "--output-md", str(tmp_root / "invalid_report.md"), "--generated-at", "2026-06-13", check=False)
    invalid_payload = json.loads(invalid.stdout)
    assert invalid.returncode == 2, invalid.stdout
    assert not invalid_payload["ok"], invalid_payload
    assert invalid_payload["summary"]["invalid_count"] == 1, invalid_payload
    assert invalid_payload["failures"], invalid_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
