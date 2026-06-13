#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_conformance_suite.py"
EXPORT_IR = ROOT / "scripts" / "export_skill_ir.py"


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_conformance"
    tmp_root.mkdir(parents=True, exist_ok=True)
    output_json = tmp_root / "conformance_matrix.json"
    output_md = tmp_root / "conformance_matrix.md"
    subprocess.run(
        [
            sys.executable,
            str(EXPORT_IR),
            str(ROOT),
            "--output-json",
            str(ROOT / "skill-ir" / "examples" / "yao-meta-skill.json"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
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
    assert payload["summary"]["target_count"] == 5, payload
    assert payload["summary"]["pass_count"] == 5, payload
    assert {item["target"] for item in payload["targets"]} == {"openai", "claude", "agent-skills", "vscode", "generic"}, payload
    assert output_json.exists(), output_json
    assert output_md.exists(), output_md
    assert "Runtime Conformance Matrix" in output_md.read_text(encoding="utf-8")

    broken = tmp_root / "broken-skill"
    (broken / "agents").mkdir(parents=True, exist_ok=True)
    (broken / "reports").mkdir(parents=True, exist_ok=True)
    (broken / "SKILL.md").write_text("---\nname: broken-skill\n---\n\n# Broken\n", encoding="utf-8")
    (broken / "manifest.json").write_text(json.dumps({"name": "broken-skill"}, indent=2), encoding="utf-8")
    (broken / "agents" / "interface.yaml").write_text("interface: {}\ncompatibility: {}\n", encoding="utf-8")
    broken_proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(broken), "--target", "generic"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert broken_proc.returncode == 2, broken_proc.stdout
    broken_payload = json.loads(broken_proc.stdout)
    assert not broken_payload["ok"], broken_payload
    assert broken_payload["targets"][0]["failures"], broken_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
