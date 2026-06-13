#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_output_execution.py"
LOCAL_RUNNER = ROOT / "scripts" / "local_output_eval_runner.py"


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_output_execution"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)

    recorded_json = tmp_root / "recorded.json"
    recorded_md = tmp_root / "recorded.md"
    recorded_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(recorded_json),
            "--output-md",
            str(recorded_md),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    recorded = json.loads(recorded_proc.stdout)
    assert recorded["ok"], recorded
    assert recorded["summary"]["case_count"] == 5, recorded
    assert recorded["summary"]["variant_run_count"] == 10, recorded
    assert recorded["summary"]["recorded_fixture_count"] == 10, recorded
    assert recorded["summary"]["command_executed_count"] == 0, recorded
    assert recorded["summary"]["model_executed_count"] == 0, recorded
    assert recorded["summary"]["token_estimated_count"] == 10, recorded
    assert recorded["summary"]["with_skill_pass_rate"] > recorded["summary"]["baseline_pass_rate"], recorded
    assert "No model-executed runs are recorded yet" in recorded_md.read_text(encoding="utf-8"), recorded_md

    local_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(tmp_root / "local.json"),
            "--output-md",
            str(tmp_root / "local.md"),
            "--runner-command",
            json.dumps([sys.executable, str(LOCAL_RUNNER)]),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    local = json.loads(local_proc.stdout)
    assert local["ok"], local
    assert local["summary"]["variant_run_count"] == 10, local
    assert local["summary"]["command_executed_count"] == 10, local
    assert local["summary"]["recorded_fixture_count"] == 0, local
    assert local["summary"]["model_executed_count"] == 0, local
    assert local["summary"]["timing_observed_count"] == 10, local
    assert local["summary"]["token_estimated_count"] == 10, local
    assert all(item["provider"] == "local-output-eval-runner" for item in local["runs"]), local
    local_md = (tmp_root / "local.md").read_text(encoding="utf-8")
    assert "Command runner evidence is present" in local_md, local_md
    assert "not provider-backed model evidence" in local_md, local_md

    runner = tmp_root / "runner.py"
    runner.write_text(
        "\n".join(
            [
                "import json, sys, time",
                "request = json.loads(sys.stdin.read())",
                "time.sleep(0.001)",
                "print(json.dumps({",
                "  'output': request['fixture_output'],",
                "  'execution_kind': 'model',",
                "  'provider': 'local-fixture',",
                "  'model': 'fixture-model',",
                "  'usage': {'input_tokens': 11, 'output_tokens': 17, 'total_tokens': 28}",
                "}))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    command_json = json.dumps([sys.executable, str(runner)])
    command_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(tmp_root / "command.json"),
            "--output-md",
            str(tmp_root / "command.md"),
            "--runner-command",
            command_json,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    command = json.loads(command_proc.stdout)
    assert command["ok"], command
    assert command["summary"]["command_executed_count"] == 10, command
    assert command["summary"]["model_executed_count"] == 10, command
    assert command["summary"]["timing_observed_count"] == 10, command
    assert command["summary"]["token_observed_count"] == 10, command
    assert command["summary"]["token_estimated_count"] == 0, command
    assert all(item["duration_ms"] is not None for item in command["runs"]), command
    assert all(item["model"] == "fixture-model" for item in command["runs"]), command

    bad_runner = tmp_root / "bad_runner.py"
    bad_runner.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
    bad_proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(ROOT / "evals" / "output" / "cases.jsonl"),
            "--output-json",
            str(tmp_root / "bad.json"),
            "--output-md",
            str(tmp_root / "bad.md"),
            "--runner-command",
            json.dumps([sys.executable, str(bad_runner)]),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert bad_proc.returncode == 2, bad_proc.stdout
    bad = json.loads(bad_proc.stdout)
    assert not bad["ok"], bad
    assert bad["summary"]["failure_count"] == 10, bad
    assert bad["failures"], bad

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
