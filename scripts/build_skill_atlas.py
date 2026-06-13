#!/usr/bin/env python3
import argparse
import csv
import html
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).resolve().parent.parent
IGNORE_PARTS = {
    ".git",
    "__pycache__",
    "dist",
    ".previews",
    "node_modules",
    ".venv",
    "venv",
}
STOPWORDS = {
    "a",
    "an",
    "and",
    "the",
    "to",
    "for",
    "from",
    "with",
    "into",
    "skill",
    "skills",
    "agent",
    "reusable",
    "use",
    "when",
    "create",
    "turn",
}
CADENCE_DAYS = {
    "monthly": 31,
    "quarterly": 100,
    "semiannual": 200,
    "annual": 370,
    "per-release": 120,
}
DEFAULT_SCOPE = {
    "scope": "release",
    "actionable": True,
    "scope_reason": "default release-actionable skill",
}


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end_index = lines[1:].index("---") + 1
    except ValueError:
        return {}, text
    frontmatter_text = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :]).lstrip()
    if yaml is not None:
        payload = yaml.safe_load(frontmatter_text) or {}
        return payload if isinstance(payload, dict) else {}, body
    payload = {}
    for line in frontmatter_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            payload[key.strip()] = value.strip().strip('"')
    return payload, body


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_scope_policy(workspace_root: Path) -> dict[str, Any]:
    path = workspace_root / "skill_atlas" / "policy.json"
    if not path.exists():
        return {"present": False, "path": safe_rel(workspace_root, path), "rules": []}
    payload = load_json(path)
    rules = payload.get("scope_rules", [])
    return {
        "present": True,
        "path": safe_rel(workspace_root, path),
        "schema_version": str(payload.get("schema_version", "")),
        "rules": rules if isinstance(rules, list) else [],
    }


def should_skip(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    if any(part in IGNORE_PARTS for part in rel.parts):
        return True
    return len(rel.parts) >= 2 and rel.parts[0] == "tests" and rel.parts[1].startswith("tmp")


def find_skill_dirs(workspace_root: Path) -> list[Path]:
    workspace_root = workspace_root.resolve()
    skill_dirs = []
    for skill_md in sorted(workspace_root.rglob("SKILL.md")):
        if should_skip(skill_md, workspace_root):
            continue
        skill_dirs.append(skill_md.parent)
    return skill_dirs


def tokens(text: str) -> set[str]:
    raw = re.findall(r"[a-zA-Z0-9_\-\u4e00-\u9fff]{2,}", text.casefold())
    return {item for item in raw if item not in STOPWORDS}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def safe_rel(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def path_matches_prefix(rel_path: str, prefix: str) -> bool:
    normalized_path = rel_path.strip("/")
    normalized_prefix = prefix.strip("/")
    if not normalized_prefix:
        return False
    return normalized_path == normalized_prefix or normalized_path.startswith(normalized_prefix + "/")


def scope_for_path(rel_path: str, policy: dict[str, Any]) -> dict[str, Any]:
    for rule in policy.get("rules", []):
        if not isinstance(rule, dict):
            continue
        prefix = str(rule.get("path_prefix", "")).strip()
        if not prefix or not path_matches_prefix(rel_path, prefix):
            continue
        return {
            "scope": str(rule.get("scope") or "supporting"),
            "actionable": bool(rule.get("actionable", False)),
            "scope_reason": str(rule.get("reason") or f"matched policy prefix {prefix}"),
        }
    return dict(DEFAULT_SCOPE)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def resource_names(skill_dir: Path) -> list[str]:
    names = []
    for folder in ("scripts", "references", "assets", "templates"):
        target = skill_dir / folder
        if not target.exists():
            continue
        for path in sorted(target.rglob("*")):
            rel = path.relative_to(skill_dir)
            if any(part in IGNORE_PARTS for part in rel.parts):
                continue
            if path.suffix in {".pyc", ".pyo"}:
                continue
            if path.is_file() and not path.is_symlink():
                names.append(f"{folder}/{path.name}")
    return names


def collect_skill(workspace_root: Path, skill_dir: Path, policy: dict[str, Any]) -> dict[str, Any]:
    frontmatter, _ = parse_frontmatter(skill_dir / "SKILL.md")
    manifest = load_json(skill_dir / "manifest.json")
    name = str(frontmatter.get("name") or manifest.get("name") or skill_dir.name)
    description = str(frontmatter.get("description") or "")
    targets = manifest.get("target_platforms", [])
    rel_path = safe_rel(workspace_root, skill_dir)
    scope = scope_for_path(rel_path, policy)
    return {
        "name": name,
        "path": rel_path,
        "description": description,
        "owner": str(manifest.get("owner", "")),
        "version": str(manifest.get("version", "")),
        "status": str(manifest.get("status", "")),
        "maturity": str(manifest.get("maturity_tier", manifest.get("skill_archetype", ""))),
        "updated_at": str(manifest.get("updated_at", "")),
        "review_cadence": str(manifest.get("review_cadence", "")),
        "targets": [str(item) for item in targets] if isinstance(targets, list) else [],
        "resources": resource_names(skill_dir),
        "token_set": sorted(tokens(description)),
        "atlas_scope": scope["scope"],
        "actionable": scope["actionable"],
        "scope_reason": scope["scope_reason"],
    }


def route_overlap(skills: list[dict[str, Any]], threshold: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = []
    collisions = []
    for i, left in enumerate(skills):
        for right in skills[i + 1 :]:
            score = round(jaccard(set(left["token_set"]), set(right["token_set"])), 3)
            status = "collision" if score >= threshold else "clear"
            row = {
                "skill_a": left["name"],
                "skill_b": right["name"],
                "path_a": left["path"],
                "path_b": right["path"],
                "score": score,
                "status": status,
                "actionable": bool(left.get("actionable") and right.get("actionable")),
                "scope_a": str(left.get("atlas_scope", "")),
                "scope_b": str(right.get("atlas_scope", "")),
            }
            rows.append(row)
            if status == "collision":
                collisions.append(row)
    duplicate_names = [
        {"name": name, "paths": [item["path"] for item in skills if item["name"] == name]}
        for name, count in Counter(item["name"] for item in skills).items()
        if count > 1
    ]
    for item in duplicate_names:
        collisions.append(
            {
                "skill_a": item["name"],
                "skill_b": item["name"],
                "path_a": item["paths"][0],
                "path_b": item["paths"][1],
                "score": 1.0,
                "status": "duplicate-name",
                "actionable": all(
                    skill.get("actionable")
                    for skill in skills
                    if skill["name"] == item["name"] and skill["path"] in set(item["paths"][:2])
                ),
                "scope_a": next(
                    (str(skill.get("atlas_scope", "")) for skill in skills if skill["path"] == item["paths"][0]),
                    "",
                ),
                "scope_b": next(
                    (str(skill.get("atlas_scope", "")) for skill in skills if skill["path"] == item["paths"][1]),
                    "",
                ),
            }
        )
    return rows, collisions


def dependency_graph(skills: list[dict[str, Any]]) -> dict[str, Any]:
    by_resource: dict[str, list[str]] = defaultdict(list)
    for skill in skills:
        for resource in skill.get("resources", []):
            by_resource[resource].append(skill["name"])
    shared = [
        {"resource": resource, "skills": sorted(names)}
        for resource, names in sorted(by_resource.items())
        if len(set(names)) > 1
    ]
    return {
        "nodes": [{"name": item["name"], "path": item["path"]} for item in skills],
        "shared_resources": shared,
    }


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def stale_skills(skills: list[dict[str, Any]], today: date) -> list[dict[str, Any]]:
    stale = []
    for skill in skills:
        updated = parse_date(skill.get("updated_at", ""))
        cadence = skill.get("review_cadence") or ""
        allowed_days = CADENCE_DAYS.get(cadence, 120)
        if not updated:
            stale.append(
                {
                    "name": skill["name"],
                    "path": skill["path"],
                    "reason": "missing updated_at",
                    "actionable": bool(skill.get("actionable")),
                    "scope": str(skill.get("atlas_scope", "")),
                }
            )
            continue
        age = (today - updated).days
        if age > allowed_days:
            stale.append(
                {
                    "name": skill["name"],
                    "path": skill["path"],
                    "reason": f"review overdue by cadence {cadence or 'unspecified'}",
                    "age_days": age,
                    "allowed_days": allowed_days,
                    "actionable": bool(skill.get("actionable")),
                    "scope": str(skill.get("atlas_scope", "")),
                }
            )
    return stale


def owner_review_gaps(skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps = []
    for skill in skills:
        missing = []
        if not skill.get("owner"):
            missing.append("owner")
        if not skill.get("review_cadence"):
            missing.append("review_cadence")
        if not skill.get("maturity"):
            missing.append("maturity")
        if missing:
            gaps.append(
                {
                    "name": skill["name"],
                    "path": skill["path"],
                    "missing": missing,
                    "actionable": bool(skill.get("actionable")),
                    "scope": str(skill.get("atlas_scope", "")),
                }
            )
    return gaps


def no_route_opportunities(workspace_root: Path) -> list[dict[str, Any]]:
    opportunities = []
    for path in sorted(workspace_root.rglob("failure-cases.md")):
        if should_skip(path, workspace_root):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("-"):
                continue
            lowered = stripped.casefold()
            if "no_route" in lowered or "no route" in lowered or "missed" in lowered or "under-trigger" in lowered:
                opportunities.append({"source": safe_rel(workspace_root, path), "note": stripped.lstrip("- ").strip()})
    return opportunities[:50]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["skill_a", "skill_b", "path_a", "path_b", "score", "status", "actionable", "scope_a", "scope_b"]
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    path.write_text(buffer.getvalue(), encoding="utf-8")


def render_html(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = []
    for skill in payload["catalog"]["skills"][:80]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(skill['name'])}</td>"
            f"<td>{html.escape(skill['path'])}</td>"
            f"<td>{html.escape(skill.get('owner') or 'missing')}</td>"
            f"<td>{html.escape(skill.get('maturity') or 'unknown')}</td>"
            f"<td>{html.escape(skill.get('review_cadence') or 'missing')}</td>"
            f"<td>{html.escape(skill.get('atlas_scope') or 'release')}</td>"
            "</tr>"
        )
    blockers = payload["actionable_route_collisions"][:20] + payload["actionable_owner_review_gaps"][:20] + payload["actionable_stale_skills"][:20]
    blocker_items = "".join(
        f"<li><strong>{html.escape(item.get('name', item.get('skill_a', 'issue')))}</strong> {html.escape(item.get('reason', item.get('status', ', '.join(item.get('missing', [])))))}</li>"
        for item in blockers
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Skill Atlas</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #172033; background: #fff; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 40px 24px; }}
    h1 {{ font-size: 34px; margin-bottom: 8px; }}
    .grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin: 28px 0; }}
    .card {{ border: 1px solid #d9e0ea; border-radius: 8px; padding: 16px; background: #f8fafc; }}
    .card span {{ display: block; color: #697386; font-size: 13px; }}
    .card strong {{ display: block; font-size: 28px; color: #1B365D; margin-top: 6px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th, td {{ text-align: left; border-bottom: 1px solid #e5e9f0; padding: 10px; vertical-align: top; }}
    th {{ color: #1B365D; font-size: 13px; }}
    li {{ margin: 8px 0; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>Skill Atlas</h1>
    <p>Portfolio-level review for route overlap, stale ownership, shared resources, and no-route opportunities.</p>
    <section class="grid">
      <div class="card"><span>Skills</span><strong>{summary['skill_count']}</strong></div>
      <div class="card"><span>Actionable</span><strong>{summary['actionable_skill_count']}</strong></div>
      <div class="card"><span>Route Collisions</span><strong>{summary['actionable_route_collision_count']}</strong></div>
      <div class="card"><span>Owner Gaps</span><strong>{summary['actionable_owner_gap_count']}</strong></div>
      <div class="card"><span>Stale Skills</span><strong>{summary['actionable_stale_count']}</strong></div>
      <div class="card"><span>No-Route Opportunities</span><strong>{summary['no_route_opportunity_count']}</strong></div>
    </section>
    <section>
      <h2>Actionable Issues</h2>
      <ul>{blocker_items or '<li>No blocking portfolio issues detected.</li>'}</ul>
    </section>
    <section>
      <h2>Full Portfolio Counts</h2>
      <p>All scanned skills remain visible: {summary['route_collision_count']} total route collisions, {summary['owner_gap_count']} total owner gaps, and {summary['stale_count']} total stale signals.</p>
    </section>
    <section>
      <h2>Catalog</h2>
      <table>
        <thead><tr><th>Name</th><th>Path</th><th>Owner</th><th>Maturity</th><th>Review</th><th>Scope</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def build_atlas(workspace_root: Path, output_dir: Path, report_html: Path, report_json: Path, threshold: float, today: date) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    scope_policy = load_scope_policy(workspace_root)
    skill_dirs = find_skill_dirs(workspace_root)
    skills = [collect_skill(workspace_root, skill_dir, scope_policy) for skill_dir in skill_dirs]
    overlap_rows, collisions = route_overlap(skills, threshold)
    graph = dependency_graph(skills)
    stale = stale_skills(skills, today)
    owner_gaps = owner_review_gaps(skills)
    opportunities = no_route_opportunities(workspace_root)
    actionable_skills = [skill for skill in skills if skill.get("actionable")]
    actionable_collisions = [item for item in collisions if item.get("actionable")]
    actionable_stale = [item for item in stale if item.get("actionable")]
    actionable_owner_gaps = [item for item in owner_gaps if item.get("actionable")]
    summary = {
        "skill_count": len(skills),
        "actionable_skill_count": len(actionable_skills),
        "route_collision_count": len(collisions),
        "actionable_route_collision_count": len(actionable_collisions),
        "owner_gap_count": len(owner_gaps),
        "actionable_owner_gap_count": len(actionable_owner_gaps),
        "stale_count": len(stale),
        "actionable_stale_count": len(actionable_stale),
        "shared_resource_count": len(graph["shared_resources"]),
        "no_route_opportunity_count": len(opportunities),
        "non_actionable_issue_count": (len(collisions) - len(actionable_collisions))
        + (len(owner_gaps) - len(actionable_owner_gaps))
        + (len(stale) - len(actionable_stale)),
    }
    catalog = {
        "workspace_root": display_path(workspace_root),
        "generated_at": today.isoformat(),
        "skills": skills,
        "summary": summary,
    }
    payload = {
        "ok": True,
        "workspace_root": display_path(workspace_root),
        "summary": summary,
        "scope_policy": scope_policy,
        "catalog": catalog,
        "route_collisions": collisions,
        "actionable_route_collisions": actionable_collisions,
        "dependency_graph": graph,
        "stale_skills": stale,
        "actionable_stale_skills": actionable_stale,
        "owner_review_gaps": owner_gaps,
        "actionable_owner_review_gaps": actionable_owner_gaps,
        "no_route_opportunities": opportunities,
        "artifacts": {
            "catalog": display_path(output_dir / "catalog.json"),
            "route_overlap_matrix": display_path(output_dir / "route_overlap_matrix.csv"),
            "dependency_graph": display_path(output_dir / "dependency_graph.json"),
            "stale_skills": display_path(output_dir / "stale_skills.json"),
            "owner_review_gaps": display_path(output_dir / "owner_review_gaps.json"),
            "no_route_opportunities": display_path(output_dir / "no_route_opportunities.json"),
            "report_json": display_path(report_json),
            "report_html": display_path(report_html),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(output_dir / "route_overlap_matrix.csv", overlap_rows)
    (output_dir / "dependency_graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "stale_skills.json").write_text(json.dumps(stale, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "owner_review_gaps.json").write_text(json.dumps(owner_gaps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "no_route_opportunities.json").write_text(json.dumps(opportunities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_html.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_html.write_text(render_html(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Skill Atlas for a workspace of agent skills.")
    parser.add_argument("--workspace-root", default=".")
    parser.add_argument("--output-dir", default=str(ROOT / "skill_atlas"))
    parser.add_argument("--report-html", default=str(ROOT / "reports" / "skill_atlas.html"))
    parser.add_argument("--report-json", default=str(ROOT / "reports" / "skill_atlas.json"))
    parser.add_argument("--overlap-threshold", type=float, default=0.42)
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args()
    today = datetime.strptime(args.today, "%Y-%m-%d").date()
    payload = build_atlas(
        Path(args.workspace_root).resolve(),
        Path(args.output_dir).resolve(),
        Path(args.report_html).resolve(),
        Path(args.report_json).resolve(),
        args.overlap_threshold,
        today,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
