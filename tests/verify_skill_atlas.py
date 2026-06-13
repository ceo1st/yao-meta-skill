#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_skill_atlas.py"


def write_skill(
    root: Path,
    name: str,
    description: str,
    manifest: dict,
    shared_reference: bool = False,
) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"""---
name: {name}
description: {description}
---

# {name}

## Workflow

1. Understand the request.
2. Produce the requested artifact.
3. Review the output.
""",
        encoding="utf-8",
    )
    (skill_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if shared_reference:
        references = skill_dir / "references"
        references.mkdir(parents=True, exist_ok=True)
        (references / "release-method.md").write_text("# Release Method\n", encoding="utf-8")
    return skill_dir


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_skill_atlas"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)

    write_skill(
        tmp_root,
        "alpha-release-skill",
        "Use when turning release notes and changelog snippets into a reusable release brief for teams.",
        {
            "name": "alpha-release-skill",
            "owner": "Release Team",
            "maturity_tier": "production",
            "review_cadence": "monthly",
            "updated_at": "2025-01-01",
            "target_platforms": ["openai", "generic"],
        },
        shared_reference=True,
    )
    write_skill(
        tmp_root,
        "beta-release-skill",
        "Use when turning changelog notes and release snippets into reusable release briefs for team review.",
        {
            "name": "beta-release-skill",
            "maturity_tier": "production",
            "updated_at": "2026-06-01",
            "target_platforms": ["openai"],
        },
        shared_reference=True,
    )
    write_skill(
        tmp_root,
        "gamma-doc-skill",
        "Use when cleaning messy documentation notes into a concise internal knowledge-base article.",
        {
            "name": "gamma-doc-skill",
            "owner": "Docs Team",
            "maturity_tier": "scaffold",
            "review_cadence": "quarterly",
            "updated_at": "2026-05-01",
            "target_platforms": ["generic"],
        },
    )
    evals = tmp_root / "evals"
    evals.mkdir()
    (evals / "failure-cases.md").write_text(
        "- no_route: repeated pricing approval prompts are missed by the current library.\n",
        encoding="utf-8",
    )

    output_dir = tmp_root / "atlas"
    report_html = tmp_root / "skill_atlas.html"
    report_json = tmp_root / "skill_atlas.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--workspace-root",
            str(tmp_root),
            "--output-dir",
            str(output_dir),
            "--report-html",
            str(report_html),
            "--report-json",
            str(report_json),
            "--today",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    summary = payload["summary"]
    assert summary["skill_count"] == 3, summary
    assert summary["route_collision_count"] >= 1, summary
    assert summary["owner_gap_count"] >= 1, summary
    assert summary["stale_count"] >= 1, summary
    assert summary["shared_resource_count"] >= 1, summary
    assert summary["no_route_opportunity_count"] >= 1, summary
    assert (output_dir / "catalog.json").exists(), output_dir
    assert (output_dir / "route_overlap_matrix.csv").exists(), output_dir
    assert (output_dir / "dependency_graph.json").exists(), output_dir
    assert (output_dir / "stale_skills.json").exists(), output_dir
    assert (output_dir / "owner_review_gaps.json").exists(), output_dir
    assert (output_dir / "no_route_opportunities.json").exists(), output_dir
    html = report_html.read_text(encoding="utf-8")
    assert "Skill Atlas" in html, html[:1000]
    assert "Route Collisions" in html, html[:3000]
    assert "No-Route Opportunities" in html, html[:3000]
    catalog = json.loads((output_dir / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["summary"]["skill_count"] == 3, catalog

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
