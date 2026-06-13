#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "trust_check.py"


INTERFACE = """interface:
  display_name: "Trust Demo"
  short_description: "Trust check demo"
  default_prompt: "Use trust demo."
compatibility:
  canonical_format: "agent-skills"
  adapter_targets:
    - "generic"
  activation:
    mode: "manual"
    paths: []
  execution:
    context: "inline"
    shell: "bash"
  trust:
    source_tier: "local"
    remote_inline_execution: "forbid"
    remote_metadata_policy: "allow-metadata-only"
  degradation:
    generic: "neutral-source"
"""


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_trust"
    tmp_root.mkdir(parents=True, exist_ok=True)
    output_json = tmp_root / "security_trust_report.json"
    output_md = tmp_root / "security_trust_report.md"
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
    assert payload["summary"]["secret_findings"] == 0, payload
    assert payload["summary"]["package_sha256"], payload
    assert output_json.exists(), output_json
    assert output_md.exists(), output_md
    assert "Security Trust Report" in output_md.read_text(encoding="utf-8")

    secret_skill = tmp_root / "secret-skill"
    (secret_skill / "agents").mkdir(parents=True, exist_ok=True)
    (secret_skill / "scripts").mkdir(parents=True, exist_ok=True)
    (secret_skill / "SKILL.md").write_text(
        "---\nname: secret-skill\ndescription: Secret demo.\n---\n\n# Secret\n",
        encoding="utf-8",
    )
    (secret_skill / "agents" / "interface.yaml").write_text(INTERFACE, encoding="utf-8")
    (secret_skill / "scripts" / "leaky.py").write_text(
        "TOKEN = 'ghp_1234567890abcdefghijklmnopqrstuv'\n",
        encoding="utf-8",
    )
    secret_proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(secret_skill)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert secret_proc.returncode == 2, secret_proc.stdout
    secret_payload = json.loads(secret_proc.stdout)
    assert not secret_payload["ok"], secret_payload
    assert secret_payload["summary"]["secret_findings"] == 1, secret_payload
    assert secret_payload["secrets"][0]["type"] == "github_token", secret_payload

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
