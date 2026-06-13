#!/usr/bin/env python3
import html
import math


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_skill_overview.py to render inline SVG report charts."

BRAND = "#1B365D"
BORDER = "#e8e6dc"
SOFT = "#faf9f5"
TEXT = "#141413"
MUTED = "#504e49"


def esc(value) -> str:
    return html.escape(str(value))


def figure(name: str, svg: str, caption: str) -> str:
    return (
        f'<figure class="chart-figure" data-chart="{esc(name)}">'
        f"{svg}"
        f"<figcaption>{esc(caption)}</figcaption>"
        "</figure>"
    )


def render_radar(scorecard: dict) -> str:
    keys = ["completeness_score", "trigger_score", "evidence_score", "maintainability_score", "portability_score"]
    labels = [scorecard[key]["label"] for key in keys if key in scorecard]
    scores = [scorecard[key]["score"] for key in keys if key in scorecard]
    center = 150
    radius = 92
    rings = []
    for pct in (0.25, 0.5, 0.75, 1.0):
        points = []
        for i in range(len(scores)):
            angle = -math.pi / 2 + 2 * math.pi * i / len(scores)
            points.append(f"{center + radius * pct * math.cos(angle):.1f},{center + radius * pct * math.sin(angle):.1f}")
        rings.append(f'<polygon points="{" ".join(points)}" fill="none" stroke="{BORDER}" stroke-width="1"/>')
    data_points = []
    label_nodes = []
    for i, score in enumerate(scores):
        angle = -math.pi / 2 + 2 * math.pi * i / len(scores)
        data_radius = radius * score / 100
        data_points.append(f"{center + data_radius * math.cos(angle):.1f},{center + data_radius * math.sin(angle):.1f}")
        lx = center + (radius + 32) * math.cos(angle)
        ly = center + (radius + 32) * math.sin(angle)
        label_nodes.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle">{esc(labels[i])}</text>'
        )
    svg = (
        '<svg viewBox="0 0 300 300" role="img" aria-label="评分雷达">'
        f'<text x="20" y="28" class="chart-title">评分雷达</text>'
        + "".join(rings)
        + f'<polygon points="{" ".join(data_points)}" fill="#E4ECF5" stroke="{BRAND}" stroke-width="2"/>'
        + "".join(label_nodes)
        + "</svg>"
    )
    return figure("radar", svg, "评分雷达展示结构完整度、触发边界、证据、维护和迁移的相对强弱。")


def render_flow(summary: dict) -> str:
    labels = summary.get("flow", ["输入材料", "Skill 包体", "可复用能力"])
    nodes = []
    for index, label in enumerate(labels[:3]):
        x = 38 + index * 210
        nodes.append(
            f'<g><rect x="{x}" y="56" width="150" height="74" rx="8" fill="#F6F8FB" stroke="{BORDER}"/>'
            f'<text x="{x + 75}" y="99" text-anchor="middle">{esc(label)}</text></g>'
        )
    svg = (
        '<svg viewBox="0 0 620 170" role="img" aria-label="交付流程">'
        '<text x="20" y="28" class="chart-title">交付流程</text>'
        '<path d="M188 93 H248 M398 93 H458" class="chart-line"/>'
        + "".join(nodes)
        + "</svg>"
    )
    return figure("flow", svg, "交付流程把用户输入、生成的包体和可复用能力放在一条线上。")


def render_matrix(profile: dict) -> str:
    matrix = profile.get("matrix", {})
    x = 70 + matrix.get("execution_certainty", 60) * 3.8
    y = 430 - matrix.get("knowledge_density", 60) * 3.2
    svg = (
        '<svg viewBox="0 0 520 460" role="img" aria-label="能力矩阵">'
        '<text x="20" y="30" class="chart-title">能力矩阵</text>'
        f'<rect x="70" y="70" width="380" height="320" fill="{SOFT}" stroke="{BORDER}"/>'
        f'<line x1="260" y1="70" x2="260" y2="390" stroke="{BORDER}"/>'
        f'<line x1="70" y1="230" x2="450" y2="230" stroke="{BORDER}"/>'
        '<text x="260" y="424" text-anchor="middle">执行确定性</text>'
        '<text x="22" y="230" transform="rotate(-90 22 230)" text-anchor="middle">知识密度</text>'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="{BRAND}"/>'
        f'<text x="{x + 18:.1f}" y="{y + 5:.1f}">{esc(profile.get("task_family", "Skill workflow"))}</text>'
        "</svg>"
    )
    return figure("matrix", svg, "能力矩阵说明这个 Skill 更偏知识密集还是执行确定。")


def render_layers(principle: dict) -> str:
    layers = principle.get("layers", ["入口层", "参考层", "脚本层", "评估层", "报告层"])
    blocks = []
    for index, layer in enumerate(layers[:5]):
        y = 55 + index * 48
        blocks.append(
            f'<rect x="{70 + index * 18}" y="{y}" width="{380 - index * 36}" height="34" rx="7" fill="#F6F8FB" stroke="{BORDER}"/>'
            f'<text x="260" y="{y + 22}" text-anchor="middle">{esc(layer)}</text>'
        )
    svg = (
        '<svg viewBox="0 0 520 320" role="img" aria-label="Skill principle flow">'
        '<text x="20" y="30" class="chart-title">分层结构</text>'
        + "".join(blocks)
        + "</svg>"
    )
    return figure("layers", svg, "分层结构展示入口、参考、脚本、评估和报告如何各司其职。")


def render_risk_heatmap(risk: dict) -> str:
    risks = risk.get("risks", [])
    cells = []
    for impact in range(1, 4):
        for probability in range(1, 4):
            count = sum(1 for item in risks if item.get("impact") == impact and item.get("probability") == probability)
            color = ["#faf9f5", "#EEF2F7", "#D0DCE9", BRAND][min(3, count)]
            x = 80 + (probability - 1) * 86
            y = 58 + (3 - impact) * 66
            cells.append(
                f'<rect x="{x}" y="{y}" width="78" height="58" rx="6" fill="{color}" stroke="{BORDER}"/>'
                f'<text x="{x + 39}" y="{y + 34}" text-anchor="middle">{count}</text>'
            )
    svg = (
        '<svg viewBox="0 0 380 300" role="img" aria-label="风险热力">'
        '<text x="20" y="30" class="chart-title">风险热力</text>'
        + "".join(cells)
        + '<text x="210" y="278" text-anchor="middle">发生概率</text>'
        + '<text x="24" y="160" transform="rotate(-90 24 160)" text-anchor="middle">影响程度</text>'
        + "</svg>"
    )
    return figure("risk_heatmap", svg, "风险热力图用影响程度和发生概率标出当前治理重点。")


def render_asset_donut(assets: dict) -> str:
    distribution = assets.get("distribution", [])[:6]
    total = sum(item.get("value", 1) for item in distribution) or 1
    colors = [BRAND, "#2D5A8A", "#D0DCE9", "#E4ECF5", "#e8e6dc", "#504e49"]
    offset = 0
    circles = []
    labels = []
    for index, item in enumerate(distribution):
        value = item.get("value", 1)
        dash = value / total * 100
        circles.append(
            f'<circle cx="130" cy="130" r="70" fill="none" stroke="{colors[index % len(colors)]}" '
            f'stroke-width="24" stroke-dasharray="{dash:.1f} {100 - dash:.1f}" stroke-dashoffset="{-offset:.1f}" '
            'pathLength="100" transform="rotate(-90 130 130)"/>'
        )
        offset += dash
        labels.append(f'<text x="235" y="{78 + index * 22}">{esc(item.get("label", "asset"))}</text>')
    svg = (
        '<svg viewBox="0 0 430 270" role="img" aria-label="资产分布">'
        '<text x="20" y="30" class="chart-title">资产分布</text>'
        + "".join(circles)
        + f'<text x="130" y="136" text-anchor="middle">{assets.get("file_count", 0)}项</text>'
        + "".join(labels)
        + "</svg>"
    )
    return figure("asset_donut", svg, "资产分布图展示当前包体的文件和目录重心。")


def render_timeline(roadmap: dict) -> str:
    items = roadmap.get("items", [])[:3]
    blocks = []
    for index, item in enumerate(items):
        x = 60 + index * 190
        title = str(item.get("title", "升级"))
        if len(title) > 18:
            title = title[:17] + "…"
        blocks.append(
            f'<circle cx="{x}" cy="92" r="10" fill="{BRAND}"/>'
            f'<text x="{x}" y="126" text-anchor="middle">下一步 {index + 1}</text>'
            f'<text x="{x}" y="150" text-anchor="middle">{esc(title)}</text>'
        )
    svg = (
        '<svg viewBox="0 0 520 210" role="img" aria-label="迭代时间">'
        '<text x="20" y="30" class="chart-title">迭代时间</text>'
        f'<line x1="60" y1="92" x2="{60 + max(0, len(items) - 1) * 190}" y2="92" class="chart-line"/>'
        + "".join(blocks)
        + "</svg>"
    )
    return figure("timeline", svg, "迭代时间线把下一步升级收束成少数可执行动作。")


def render_chart_set(model: dict) -> dict:
    return {
        "radar": render_radar(model.get("scorecard", {})),
        "flow": render_flow(model.get("skill_summary", {})),
        "matrix": render_matrix(model.get("capability_profile", {})),
        "layers": render_layers(model.get("principle_model", {})),
        "risk_heatmap": render_risk_heatmap(model.get("risk_governance", {})),
        "asset_donut": render_asset_donut(model.get("package_assets", {})),
        "timeline": render_timeline(model.get("iteration_roadmap", {})),
    }
