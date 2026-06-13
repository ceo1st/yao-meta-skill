#!/usr/bin/env python3
import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ["agents", "docs", "evals", "references", "runtime", "scripts", "security", "skill-ir", "templates"]
ROOT_FILES = ["SKILL.md", "README.md", "manifest.json", "requirements-ci.txt", "Makefile"]
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".yaml", ".yml", ".py", ".sh", ".txt", ".toml"}
SECRET_PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
]


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


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def iter_scan_files(skill_dir: Path) -> list[Path]:
    files = []
    for rel in ROOT_FILES:
        path = skill_dir / rel
        if path.exists() and path.is_file():
            files.append(path)
    for rel in SCAN_DIRS:
        folder = skill_dir / rel
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            if path.suffix in TEXT_SUFFIXES and path.stat().st_size <= 1_000_000:
                files.append(path)
    return sorted(set(files))


def relpath(skill_dir: Path, path: Path) -> str:
    return str(path.relative_to(skill_dir))


def scan_secrets(skill_dir: Path, files: list[Path]) -> list[dict[str, Any]]:
    findings = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append({"type": name, "path": relpath(skill_dir, path), "line": line})
    return findings


def script_inventory(skill_dir: Path) -> list[dict[str, Any]]:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return []
    inventory = []
    for path in sorted(scripts_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        flags = script_flags(text)
        inventory.append(
            {
                "path": relpath(skill_dir, path),
                "has_argparse": "argparse" in text,
                "has_main_guard": 'if __name__ == "__main__"' in text,
                "uses_input": flags["uses_input"],
                "uses_network": flags["uses_network"],
                "uses_subprocess": flags["uses_subprocess"],
            }
        )
    return inventory


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def script_flags(text: str) -> dict[str, bool]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {
            "uses_input": bool(re.search(r"\b(?:input|getpass)\s*\(", text)),
            "uses_network": bool(re.search(r"\b(?:urlopen|Request)\s*\(|\brequests\.", text)),
            "uses_subprocess": "subprocess." in text,
        }
    calls = [call_name(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    return {
        "uses_input": any(name in {"input", "getpass.getpass"} or name.endswith(".getpass") for name in calls),
        "uses_network": any(name in {"urlopen", "Request"} or name.startswith("requests.") for name in calls),
        "uses_subprocess": any(name.startswith("subprocess.") for name in calls),
    }


def dependency_status(skill_dir: Path) -> dict[str, Any]:
    candidates = ["requirements-ci.txt", "requirements.txt", "pyproject.toml", "package-lock.json", "uv.lock", "poetry.lock"]
    present = [name for name in candidates if (skill_dir / name).exists()]
    pinned = []
    unpinned = []
    requirements = skill_dir / "requirements-ci.txt"
    if requirements.exists():
        for line in requirements.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "==" in stripped or " @ " in stripped:
                pinned.append(stripped)
            else:
                unpinned.append(stripped)
    return {"present": present, "pinned": pinned, "unpinned": unpinned}


def interface_trust(skill_dir: Path) -> dict[str, Any]:
    interface = load_yaml(skill_dir / "agents" / "interface.yaml")
    trust = interface.get("compatibility", {}).get("trust", {})
    return {
        "source_tier": trust.get("source_tier", ""),
        "remote_inline_execution": trust.get("remote_inline_execution", ""),
        "remote_metadata_policy": trust.get("remote_metadata_policy", ""),
    }


def package_digest(files: list[Path], skill_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in files:
        rel = relpath(skill_dir, path)
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def build_trust_report(skill_dir: Path) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    files = iter_scan_files(skill_dir)
    secrets = scan_secrets(skill_dir, files)
    scripts = script_inventory(skill_dir)
    deps = dependency_status(skill_dir)
    trust = interface_trust(skill_dir)
    failures = []
    warnings = []

    if secrets:
        failures.append(f"High-risk secret patterns found: {len(secrets)}")
    if trust.get("remote_inline_execution") not in {"forbid", "deny", "false"}:
        failures.append("remote_inline_execution must be forbid for governed release")
    if deps["unpinned"]:
        warnings.append(f"Unpinned dependency entries: {', '.join(deps['unpinned'])}")
    if not deps["present"]:
        warnings.append("No dependency or lock file detected")
    missing_help = [item["path"] for item in scripts if not item["has_argparse"]]
    if missing_help:
        warnings.append(f"Scripts without argparse/help surface: {', '.join(missing_help[:8])}")
    interactive = [item["path"] for item in scripts if item["uses_input"]]
    if interactive:
        warnings.append(f"Interactive scripts require reviewer awareness: {', '.join(interactive[:8])}")
    network = [item["path"] for item in scripts if item["uses_network"]]
    if network:
        warnings.append(f"Network-capable scripts require bounded host policy: {', '.join(network[:8])}")

    summary = {
        "scanned_files": len(files),
        "script_count": len(scripts),
        "secret_findings": len(secrets),
        "dependency_files": deps["present"],
        "network_script_count": len(network),
        "interactive_script_count": len(interactive),
        "package_sha256": package_digest(files, skill_dir),
    }
    return {
        "ok": not failures,
        "skill_dir": display_path(skill_dir),
        "summary": summary,
        "failures": failures,
        "warnings": warnings,
        "secrets": secrets,
        "scripts": scripts,
        "dependencies": deps,
        "trust_metadata": trust,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Security Trust Report",
        "",
        f"- OK: `{payload['ok']}`",
        f"- Scanned files: `{summary['scanned_files']}`",
        f"- Scripts: `{summary['script_count']}`",
        f"- Secret findings: `{summary['secret_findings']}`",
        f"- Network-capable scripts: `{summary['network_script_count']}`",
        f"- Interactive scripts: `{summary['interactive_script_count']}`",
        f"- Package SHA256: `{summary['package_sha256']}`",
        "",
        "## Failures",
        "",
    ]
    lines.extend([f"- {item}" for item in payload["failures"]] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {item}" for item in payload["warnings"]] or ["- None"])
    lines.extend(["", "## Dependency Evidence", ""])
    lines.append(f"- Files: `{', '.join(payload['dependencies']['present']) or 'none'}`")
    lines.append(f"- Pinned entries: `{len(payload['dependencies']['pinned'])}`")
    lines.append(f"- Unpinned entries: `{len(payload['dependencies']['unpinned'])}`")
    lines.extend(["", "## Script Surface", "", "| Script | Argparse | Main Guard | Input | Network | Subprocess |", "| --- | --- | --- | --- | --- | --- |"])
    for item in payload["scripts"]:
        lines.append(
            f"| {item['path']} | {item['has_argparse']} | {item['has_main_guard']} | {item['uses_input']} | {item['uses_network']} | {item['uses_subprocess']} |"
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Skill OS trust and security checks.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    output_json = Path(args.output_json).resolve() if args.output_json else skill_dir / "reports" / "security_trust_report.json"
    output_md = Path(args.output_md).resolve() if args.output_md else skill_dir / "reports" / "security_trust_report.md"
    payload = build_trust_report(skill_dir)
    payload["artifacts"] = {"json": display_path(output_json), "markdown": display_path(output_md)}
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
