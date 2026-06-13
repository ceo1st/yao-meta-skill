# Security Trust Report

- OK: `True`
- Scanned files: `124`
- Scripts: `49`
- Secret findings: `0`
- Network-capable scripts: `2`
- Interactive scripts: `0`
- Package SHA256: `d70bd9083059198c4346c743131852b32038e59000d86ed11cae4399df6988ac`

## Failures

- None

## Warnings

- Scripts without argparse/help surface: scripts/render_context_reports.py, scripts/render_social_preview.py, scripts/skill_report_charts.py, scripts/skill_report_metrics.py, scripts/skill_report_model.py
- Network-capable scripts require bounded host policy: scripts/check_update.py, scripts/github_benchmark_scan.py

## Dependency Evidence

- Files: `requirements-ci.txt`
- Pinned entries: `1`
- Unpinned entries: `0`

## Script Surface

| Script | Argparse | Main Guard | Input | Network | Subprocess |
| --- | --- | --- | --- | --- | --- |
| scripts/build_confusion_matrix.py | True | True | False | False | False |
| scripts/build_skill_atlas.py | True | True | False | False | False |
| scripts/check_update.py | True | True | False | True | False |
| scripts/ci_test.py | True | True | False | False | True |
| scripts/collect_feedback.py | True | True | False | False | False |
| scripts/context_sizer.py | True | True | False | False | False |
| scripts/create_iteration_snapshot.py | True | True | False | False | False |
| scripts/cross_packager.py | True | True | False | False | False |
| scripts/diff_eval.py | True | True | False | False | False |
| scripts/export_skill_ir.py | True | True | False | False | False |
| scripts/github_benchmark_scan.py | True | True | False | True | False |
| scripts/governance_check.py | True | True | False | False | False |
| scripts/init_skill.py | True | True | False | False | False |
| scripts/judge_blind_eval.py | True | True | False | False | False |
| scripts/lint_skill.py | True | True | False | False | False |
| scripts/optimize_description.py | True | True | False | False | False |
| scripts/promotion_checker.py | True | True | False | False | False |
| scripts/render_artifact_design_profile.py | True | True | False | False | False |
| scripts/render_baseline_compare.py | True | True | False | False | False |
| scripts/render_context_reports.py | False | True | False | False | False |
| scripts/render_description_drift_history.py | True | True | False | False | False |
| scripts/render_eval_dashboard.py | True | True | False | False | True |
| scripts/render_intent_confidence.py | True | True | False | False | False |
| scripts/render_intent_dialogue.py | True | True | False | False | False |
| scripts/render_iteration_directions.py | True | True | False | False | False |
| scripts/render_iteration_ledger.py | True | True | False | False | False |
| scripts/render_output_risk_profile.py | True | True | False | False | False |
| scripts/render_portability_report.py | True | True | False | False | False |
| scripts/render_prompt_quality_profile.py | True | True | False | False | False |
| scripts/render_reference_scan.py | True | True | False | False | False |
| scripts/render_reference_synthesis.py | True | True | False | False | False |
| scripts/render_regression_history.py | True | True | False | False | False |
| scripts/render_review_viewer.py | True | True | False | False | False |
| scripts/render_skill_overview.py | True | True | False | False | False |
| scripts/render_social_preview.py | False | True | False | False | False |
| scripts/render_system_model.py | True | True | False | False | False |
| scripts/resource_boundary_check.py | True | True | False | False | False |
| scripts/run_conformance_suite.py | True | True | False | False | False |
| scripts/run_description_optimization_suite.py | True | True | False | False | False |
| scripts/run_eval_suite.py | True | True | False | False | True |
| scripts/run_output_eval.py | True | True | False | False | False |
| scripts/skill_report_charts.py | False | False | False | False | False |
| scripts/skill_report_metrics.py | False | False | False | False | False |
| scripts/skill_report_model.py | False | False | False | False | False |
| scripts/sync_local_install.py | True | True | False | False | True |
| scripts/trigger_eval.py | True | True | False | False | False |
| scripts/trust_check.py | True | True | False | False | False |
| scripts/validate_skill.py | True | True | False | False | False |
| scripts/yao.py | True | True | False | False | True |
