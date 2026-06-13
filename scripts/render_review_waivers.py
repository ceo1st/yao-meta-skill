#!/usr/bin/env python3
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
KNOWN_GATE_KEYS = {
    "intent-canvas",
    "trigger-lab",
    "output-lab",
    "context-budget",
    "runtime-matrix",
    "trust-report",
    "permission-gates",
    "permission-runtime",
    "skill-atlas",
    "operations-loop",
    "registry-audit",
    "release-notes",
}
VALID_DECISIONS = {"accepted-risk", "false-positive", "temporary-exception"}
MIN_REASON_CHARS = 20


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def today_from(value: str | None) -> date:
    if not value:
        return date.today()
    return date.fromisoformat(value[:10])


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def waiver_id(entry: dict[str, Any]) -> str:
    raw = "|".join(
        [
            str(entry.get("gate_key", "")),
            str(entry.get("reviewer", "")),
            str(entry.get("created_at", "")),
            str(entry.get("reason", "")),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def normalize_waiver(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "id": str(entry.get("id") or ""),
        "gate_key": str(entry.get("gate_key") or ""),
        "decision": str(entry.get("decision") or "accepted-risk"),
        "reviewer": str(entry.get("reviewer") or ""),
        "reason": str(entry.get("reason") or ""),
        "created_at": str(entry.get("created_at") or ""),
        "expires_at": str(entry.get("expires_at") or ""),
        "evidence": str(entry.get("evidence") or ""),
        "scope": str(entry.get("scope") or "current-release"),
    }
    normalized["id"] = normalized["id"] or waiver_id(normalized)
    return normalized


def add_waiver(existing: list[dict[str, Any]], args: argparse.Namespace, today: date) -> list[dict[str, Any]]:
    created_at = args.created_at or today.isoformat()
    entry = normalize_waiver(
        {
            "gate_key": args.gate_key,
            "decision": args.decision,
            "reviewer": args.reviewer,
            "reason": args.reason,
            "created_at": created_at,
            "expires_at": args.expires_at,
            "evidence": args.evidence or "",
            "scope": args.scope,
        }
    )
    return [*existing, entry]


def validate_waivers(waivers: list[dict[str, Any]], today: date) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    normalized = []
    failures = []
    warnings = []
    seen_ids = set()

    for index, raw in enumerate(waivers, start=1):
        entry = normalize_waiver(raw)
        entry_failures = []
        entry_warnings = []
        if entry["id"] in seen_ids:
            entry_failures.append("duplicate waiver id")
        seen_ids.add(entry["id"])
        if entry["gate_key"] not in KNOWN_GATE_KEYS:
            entry_failures.append(f"unknown gate_key: {entry['gate_key'] or '<empty>'}")
        if entry["decision"] not in VALID_DECISIONS:
            entry_failures.append(f"invalid decision: {entry['decision'] or '<empty>'}")
        if not entry["reviewer"]:
            entry_failures.append("reviewer is required")
        if len(entry["reason"]) < MIN_REASON_CHARS:
            entry_failures.append(f"reason must be at least {MIN_REASON_CHARS} characters")
        created_at = parse_date(entry["created_at"])
        if created_at is None:
            entry_failures.append("created_at must be ISO date")
        expires_at = parse_date(entry["expires_at"])
        if expires_at is None:
            entry_failures.append("expires_at must be ISO date")
        elif expires_at < today:
            entry_warnings.append("waiver is expired")
        entry["status"] = "invalid" if entry_failures else ("expired" if entry_warnings else "active")
        entry["validation"] = {"failures": entry_failures, "warnings": entry_warnings}
        normalized.append(entry)
        failures.extend([f"waiver {index} ({entry['id']}): {item}" for item in entry_failures])
        warnings.extend([f"waiver {index} ({entry['id']}): {item}" for item in entry_warnings])

    return normalized, failures, warnings


def render_report(
    skill_dir: Path,
    waivers_json: Path | None = None,
    output_json: Path | None = None,
    output_md: Path | None = None,
    generated_at: str | None = None,
    add_args: argparse.Namespace | None = None,
) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    reports = skill_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    output_json = output_json or reports / "review_waivers.json"
    output_md = output_md or reports / "review_waivers.md"
    source_json = waivers_json or output_json
    today = today_from(generated_at)
    payload = load_json(source_json)
    raw_waivers = payload.get("waivers", []) if isinstance(payload.get("waivers", []), list) else []
    if add_args is not None:
        raw_waivers = add_waiver(raw_waivers, add_args, today)
    waivers, failures, warnings = validate_waivers(raw_waivers, today)
    active = [item for item in waivers if item["status"] == "active"]
    expired = [item for item in waivers if item["status"] == "expired"]
    invalid = [item for item in waivers if item["status"] == "invalid"]
    covered_gate_keys = sorted({item["gate_key"] for item in active})
    report = {
        "schema_version": "1.0",
        "ok": not failures,
        "skill_dir": display_path(skill_dir),
        "generated_at": generated_at or today.isoformat(),
        "summary": {
            "waiver_count": len(waivers),
            "active_count": len(active),
            "expired_count": len(expired),
            "invalid_count": len(invalid),
            "covered_gate_count": len(covered_gate_keys),
            "covered_gate_keys": covered_gate_keys,
        },
        "policy": {
            "blocker_waivers_allowed": False,
            "minimum_reason_chars": MIN_REASON_CHARS,
            "expires_required": True,
            "known_gate_keys": sorted(KNOWN_GATE_KEYS),
        },
        "waivers": waivers,
        "failures": failures,
        "warnings": warnings,
        "artifacts": {
            "json": display_path(output_json),
            "markdown": display_path(output_md),
        },
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Review Waivers",
        "",
        f"- OK: `{report['ok']}`",
        f"- Waivers: `{summary['waiver_count']}`",
        f"- Active: `{summary['active_count']}`",
        f"- Expired: `{summary['expired_count']}`",
        f"- Invalid: `{summary['invalid_count']}`",
        f"- Covered gates: `{', '.join(summary['covered_gate_keys']) or 'none'}`",
        "",
        "## Policy",
        "",
        "- Blocker waivers allowed: `False`",
        f"- Minimum reason chars: `{report['policy']['minimum_reason_chars']}`",
        "- Expiry is required for every waiver.",
        "",
        "## Waivers",
        "",
    ]
    if not report["waivers"]:
        lines.append("- None")
    else:
        lines.extend(["| ID | Gate | Decision | Reviewer | Status | Expires | Reason |", "| --- | --- | --- | --- | --- | --- | --- |"])
        for item in report["waivers"]:
            reason = str(item["reason"]).replace("|", "\\|")
            lines.append(
                f"| `{item['id']}` | `{item['gate_key']}` | `{item['decision']}` | {item['reviewer']} | `{item['status']}` | `{item['expires_at']}` | {reason} |"
            )
    lines.extend(["", "## Failures", ""])
    lines.extend([f"- {item}" for item in report["failures"]] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {item}" for item in report["warnings"]] or ["- None"])
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render or update Review Studio waiver evidence.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--waivers-json")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    parser.add_argument("--generated-at")
    parser.add_argument("--add-waiver", action="store_true")
    parser.add_argument("--gate-key", choices=sorted(KNOWN_GATE_KEYS))
    parser.add_argument("--decision", choices=sorted(VALID_DECISIONS), default="accepted-risk")
    parser.add_argument("--reviewer")
    parser.add_argument("--reason")
    parser.add_argument("--expires-at")
    parser.add_argument("--created-at")
    parser.add_argument("--evidence")
    parser.add_argument("--scope", default="current-release")
    args = parser.parse_args()

    add_args = None
    if args.add_waiver:
        required = {
            "--gate-key": args.gate_key,
            "--reviewer": args.reviewer,
            "--reason": args.reason,
            "--expires-at": args.expires_at,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            print(json.dumps({"ok": False, "failures": [f"Missing required fields for --add-waiver: {', '.join(missing)}"]}, ensure_ascii=False, indent=2))
            raise SystemExit(2)
        add_args = args

    payload = render_report(
        Path(args.skill_dir),
        waivers_json=Path(args.waivers_json).resolve() if args.waivers_json else None,
        output_json=Path(args.output_json).resolve() if args.output_json else None,
        output_md=Path(args.output_md).resolve() if args.output_md else None,
        generated_at=args.generated_at,
        add_args=add_args,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
