#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_output_eval.py"


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_output_eval"
    tmp_root.mkdir(parents=True, exist_ok=True)
    output_json = tmp_root / "output_quality_scorecard.json"
    output_md = tmp_root / "output_quality_scorecard.md"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["ok"], payload
    assert payload["summary"]["case_count"] == 3, payload
    assert payload["summary"]["with_skill_pass_rate"] > payload["summary"]["baseline_pass_rate"], payload
    assert payload["summary"]["delta"] > 0, payload
    assert payload["summary"]["gate_pass"], payload
    assert output_json.exists(), output_json
    assert output_md.exists(), output_md
    markdown = output_md.read_text(encoding="utf-8")
    assert "Output Quality Scorecard" in markdown, markdown[:400]
    assert "with-skill" in markdown, markdown[:600]
    assert "Failure Taxonomy" in markdown, markdown[:1200]

    invalid_cases = tmp_root / "invalid_cases.jsonl"
    invalid_cases.write_text(json.dumps({"id": "bad", "prompt": "x"}) + "\n", encoding="utf-8")
    invalid_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(invalid_cases),
            "--output-json",
            str(tmp_root / "invalid.json"),
            "--output-md",
            str(tmp_root / "invalid.md"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert invalid_proc.returncode == 2, invalid_proc.stdout
    invalid_payload = json.loads(invalid_proc.stdout)
    assert not invalid_payload["ok"], invalid_payload
    assert invalid_payload["failures"], invalid_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
