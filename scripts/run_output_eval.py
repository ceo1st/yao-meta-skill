#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = ROOT / "evals" / "output" / "cases.jsonl"


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Output eval case at {path}:{line_number} must be an object")
        cases.append(payload)
    return cases


def normalize(text: str) -> str:
    return str(text).casefold()


def validate_case(case: dict[str, Any]) -> list[str]:
    failures = []
    for key in ("id", "prompt", "baseline_output", "with_skill_output", "assertions"):
        if key not in case:
            failures.append(f"{case.get('id', '<unknown>')}: missing {key}")
    assertions = case.get("assertions", [])
    if not isinstance(assertions, list) or not assertions:
        failures.append(f"{case.get('id', '<unknown>')}: assertions must be a non-empty list")
    for assertion in assertions if isinstance(assertions, list) else []:
        if not isinstance(assertion, dict):
            failures.append(f"{case.get('id', '<unknown>')}: assertion must be an object")
            continue
        if not assertion.get("id") or not assertion.get("description"):
            failures.append(f"{case.get('id', '<unknown>')}: assertion id and description are required")
    return failures


def check_assertion(output: str, assertion: dict[str, Any]) -> dict[str, Any]:
    lowered = normalize(output)
    required = [str(item) for item in assertion.get("required", [])]
    forbidden = [str(item) for item in assertion.get("forbidden", [])]
    missing = [item for item in required if normalize(item) not in lowered]
    present_forbidden = [item for item in forbidden if normalize(item) in lowered]
    passed = not missing and not present_forbidden
    return {
        "id": assertion.get("id", "assertion"),
        "description": assertion.get("description", ""),
        "weight": float(assertion.get("weight", 1) or 0),
        "failure_type": assertion.get("failure_type", "assertion_failed"),
        "passed": passed,
        "missing": missing,
        "present_forbidden": present_forbidden,
    }


def grade_output(output: str, assertions: list[dict[str, Any]]) -> dict[str, Any]:
    checks = [check_assertion(output, assertion) for assertion in assertions]
    total_weight = sum(item["weight"] for item in checks) or len(checks) or 1
    passed_weight = sum(item["weight"] for item in checks if item["passed"])
    failed = [item for item in checks if not item["passed"]]
    return {
        "score": round(passed_weight / total_weight * 100, 2),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "checks": checks,
        "failed": failed,
    }


def grade_case(case: dict[str, Any]) -> dict[str, Any]:
    assertions = case.get("assertions", [])
    baseline = grade_output(str(case.get("baseline_output", "")), assertions)
    with_skill = grade_output(str(case.get("with_skill_output", "")), assertions)
    return {
        "id": case["id"],
        "prompt": case["prompt"],
        "baseline": baseline,
        "with_skill": with_skill,
        "delta": round(with_skill["score"] - baseline["score"], 2),
        "winner": "with_skill" if with_skill["score"] >= baseline["score"] else "baseline",
        "failure_taxonomy": sorted({item["failure_type"] for item in with_skill["failed"]}),
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    case_count = len(results)
    baseline_average = sum(item["baseline"]["score"] for item in results) / case_count if case_count else 0
    with_skill_average = sum(item["with_skill"]["score"] for item in results) / case_count if case_count else 0
    regressions = [item for item in results if item["delta"] < 0]
    failures = sorted({failure for item in results for failure in item["failure_taxonomy"]})
    return {
        "case_count": case_count,
        "baseline_pass_rate": round(baseline_average, 2),
        "with_skill_pass_rate": round(with_skill_average, 2),
        "delta": round(with_skill_average - baseline_average, 2),
        "regression_count": len(regressions),
        "gate_pass": with_skill_average >= baseline_average and not regressions,
        "failure_taxonomy": failures,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Output Quality Scorecard",
        "",
        "This v0 scorecard compares static without-skill and with-skill outputs using assertion grading.",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Baseline pass rate: `{summary['baseline_pass_rate']}`",
        f"- With-skill pass rate: `{summary['with_skill_pass_rate']}`",
        f"- Delta: `{summary['delta']}`",
        f"- Regressions: `{summary['regression_count']}`",
        f"- Gate pass: `{summary['gate_pass']}`",
        "",
        "## Case Results",
        "",
        "| Case | Baseline | With Skill | Delta | Winner | Failed With-Skill Assertions |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for item in payload["results"]:
        failed = ", ".join(failure["id"] for failure in item["with_skill"]["failed"]) or "None"
        lines.append(
            f"| {item['id']} | {item['baseline']['score']} | {item['with_skill']['score']} | {item['delta']} | {item['winner']} | {failed} |"
        )
    lines.extend(["", "## Failure Taxonomy", ""])
    if summary["failure_taxonomy"]:
        for failure in summary["failure_taxonomy"]:
            lines.append(f"- {failure}")
    else:
        lines.append("- No with-skill assertion failures.")
    lines.extend(
        [
            "",
            "## Next Fixes",
            "",
            "- Add holdout cases before using this as a release gate.",
            "- Promote repeated failed assertions into the output-risk profile.",
            "- Keep assertions tied to material deliverables, not phrasing trivia.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def run_output_eval(cases_path: Path, output_json: Path, output_md: Path) -> dict[str, Any]:
    cases = load_cases(cases_path)
    validation_failures = [failure for case in cases for failure in validate_case(case)]
    if validation_failures:
        payload = {
            "ok": False,
            "cases": display_path(cases_path),
            "summary": {
                "case_count": len(cases),
                "baseline_pass_rate": 0,
                "with_skill_pass_rate": 0,
                "delta": 0,
                "regression_count": 0,
                "gate_pass": False,
                "failure_taxonomy": ["invalid_case"],
            },
            "results": [],
            "failures": validation_failures,
        }
    else:
        results = [grade_case(case) for case in cases]
        payload = {
            "ok": True,
            "cases": display_path(cases_path),
            "summary": build_summary(results),
            "results": results,
            "failures": [],
        }
    payload["artifacts"] = {"json": display_path(output_json), "markdown": display_path(output_md)}
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Output Eval Lab assertion grading for with-skill vs baseline outputs.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES))
    parser.add_argument("--output-json", default=str(ROOT / "reports" / "output_quality_scorecard.json"))
    parser.add_argument("--output-md", default=str(ROOT / "reports" / "output_quality_scorecard.md"))
    args = parser.parse_args()

    payload = run_output_eval(
        Path(args.cases).resolve(),
        Path(args.output_json).resolve(),
        Path(args.output_md).resolve(),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
