#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "yao.py"


def run(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stderr": proc.stderr,
    }


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_skill_overview"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    init_result = run(
        "init",
        "skill-overview-demo",
        "--description",
        "Turn rough requests into a compact reusable demo skill.",
        "--output-dir",
        str(tmp_root),
    )
    assert init_result["ok"], init_result

    created = tmp_root / "skill-overview-demo"
    assert (created / "README.md").exists(), created
    assert (created / "manifest.json").exists(), created
    assert (created / "reports" / "intent-dialogue.md").exists(), created
    assert (created / "reports" / "intent-dialogue.json").exists(), created
    assert (created / "reports" / "intent-confidence.md").exists(), created
    assert (created / "reports" / "intent-confidence.json").exists(), created
    assert (created / "reports" / "skill-overview.html").exists(), created
    assert (created / "reports" / "skill-overview.json").exists(), created
    assert (created / "reports" / "reference-synthesis.md").exists(), created
    assert (created / "reports" / "reference-synthesis.json").exists(), created
    assert (created / "reports" / "artifact-design-profile.md").exists(), created
    assert (created / "reports" / "artifact-design-profile.json").exists(), created
    assert (created / "reports" / "prompt-quality-profile.md").exists(), created
    assert (created / "reports" / "prompt-quality-profile.json").exists(), created
    assert (created / "reports" / "system-model.md").exists(), created
    assert (created / "reports" / "system-model.json").exists(), created
    assert (created / "reports" / "iteration-directions.md").exists(), created
    assert (created / "reports" / "iteration-directions.json").exists(), created

    overview_json = json.loads((created / "reports" / "skill-overview.json").read_text(encoding="utf-8"))
    directions_json = json.loads((created / "reports" / "iteration-directions.json").read_text(encoding="utf-8"))
    assert overview_json["report_contract"]["schema_version"] == "2.0", overview_json.get("report_contract")
    assert overview_json["report_contract"]["layout"] == "kami-white-audit-v2", overview_json.get("report_contract")
    expected_v2_keys = {
        "skill_summary",
        "scorecard",
        "capability_profile",
        "principle_model",
        "contract_boundary",
        "quality_review",
        "risk_governance",
        "package_assets",
        "iteration_roadmap",
        "report_contract",
    }
    assert expected_v2_keys.issubset(overview_json.keys()), overview_json.keys()
    assert [item["title"] for item in overview_json["iteration_roadmap"]["items"]] == [
        item["title"] for item in directions_json["directions"]
    ], {
        "overview_roadmap": overview_json["iteration_roadmap"],
        "iteration_directions": directions_json["directions"],
    }

    initial_report_html = (created / "reports" / "skill-overview.html").read_text(encoding="utf-8")
    assert directions_json["directions"][0]["title"] in initial_report_html, initial_report_html[:5000]

    rerender_result = run("skill-report", str(created))
    assert rerender_result["ok"], rerender_result
    assert rerender_result["payload"]["artifacts"]["html"].endswith("reports/skill-overview.html"), rerender_result

    report_html = (created / "reports" / "skill-overview.html").read_text(encoding="utf-8")
    assert 'lang="zh-CN"' in report_html, report_html[:200]
    assert 'data-report-lang="zh-CN"' in report_html, report_html[:400]
    assert 'class="language-switch"' in report_html, report_html[:2400]
    assert 'class="skip-link"' in report_html, report_html[:2400]
    assert 'class="progress-bar"' in report_html, report_html[:2400]
    assert 'aria-current' in report_html, report_html[-3000:]
    assert 'class="metrics-stack"' in report_html, report_html[:9000]
    assert 'class="metrics-lead"' in report_html, report_html[:9000]
    assert "class='metric-summary-list'" in report_html, report_html[:9000]
    assert "class='metric-card-head'" in report_html, report_html[:12000]
    assert 'data-set-lang="zh-CN"' in report_html, report_html[:2600]
    assert 'data-set-lang="en"' in report_html, report_html[:2800]
    assert 'data-lang="zh-CN"' in report_html, report_html[:3200]
    assert 'data-lang="en"' in report_html, report_html[:3400]
    assert "position: sticky" in report_html, report_html[:1200]
    assert "background: #ffffff" in report_html, report_html[:1600]
    assert ".report-nav {" in report_html and "overflow-x: auto" in report_html, report_html[:5000]
    assert "scaleX(" in report_html, report_html[-3000:]
    for label in ("技能概述", "总览指标", "能力画像", "原理结构", "契约边界", "质量评估", "风险治理", "包体资产", "迭代路线"):
        assert f">{label}</span>" in report_html, label
        assert len(label) == 4, label
    assert 'aria-label="Skill principle flow"' in report_html, report_html[:2400]
    for chart_label in ("评分雷达", "交付流程", "能力矩阵", "风险热力", "资产分布", "迭代时间"):
        assert chart_label in report_html, chart_label
    assert "技能名称" in report_html, report_html[:5000]
    assert "成熟度" in report_html, report_html[:5000]
    assert "更新时间" in report_html, report_html[:5000]
    assert "Skill name" in report_html, report_html[:5000]
    assert "输入材料" in report_html, report_html[:3000]
    assert "输出结果" in report_html, report_html[:3400]
    assert "Top 3 Next Moves" not in report_html, report_html[:3800]
    assert "下一步" in report_html, report_html[:4200]

    overview_json = json.loads((created / "reports" / "skill-overview.json").read_text(encoding="utf-8"))
    assert "执行流程" in report_html, report_html[:5000]
    assert "调用方式" in report_html, report_html[:5000]
    assert "证据不足" in report_html or "证据充分" in report_html, report_html[:8000]
    assert "理解用户请求" in report_html, report_html[:5000]
    assert overview_json["logic_steps"][0] in report_html, overview_json.get("logic_steps")
    assert overview_json["usage_steps"][0] in report_html, overview_json.get("usage_steps")
    assert overview_json["report_contract"]["default_language"] == "zh-CN", overview_json.get("report_contract")
    assert overview_json["report_contract"]["languages"] == ["zh-CN", "en"], overview_json.get("report_contract")
    assert overview_json["report_contract"]["nav_labels"] == [
        "技能概述",
        "总览指标",
        "能力画像",
        "原理结构",
        "契约边界",
        "质量评估",
        "风险治理",
        "包体资产",
        "迭代路线",
    ], overview_json.get("report_contract")

    intent_text = (created / "reports" / "intent-dialogue.md").read_text(encoding="utf-8")
    assert "Questions To Ask" in intent_text, intent_text[:400]

    directions_text = (created / "reports" / "iteration-directions.md").read_text(encoding="utf-8")
    assert "Top 3 Next Moves" in directions_text, directions_text[:400]

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
