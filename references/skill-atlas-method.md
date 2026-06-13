# Skill Atlas Method

Skill Atlas is the 2.0 operating layer for a workspace that contains many skills.

## Purpose

Single-skill quality is not enough for a team library. A skill portfolio also needs to reveal route collisions, stale ownership, duplicate resources, and repeated no-route opportunities.

## V0 Checks

- Catalog every `SKILL.md` under a workspace.
- Extract name, description, owner, maturity, targets, updated date, and review cadence.
- Detect similar descriptions as route-overlap candidates.
- Detect duplicate skill names.
- Detect shared script/reference filenames as dependency signals.
- Flag missing owner or review metadata.
- Flag stale skills based on `updated_at` and `review_cadence`.
- Extract no-route opportunities from failure notes.

## Scope Policy

Atlas keeps a full catalog, but release gates should distinguish actionable library skills from examples and test fixtures.

Use `skill_atlas/policy.json` to mark path prefixes as non-actionable when they are intentionally retained as examples, evolution snapshots, embedded generated skills, or validator fixtures. Non-actionable items still appear in the full report, route matrix, stale list, and owner gap list, but Review Studio should use the actionable counts for release readiness.

## Reviewer Gate

Use Atlas before promoting a single skill into a shared library. If an actionable route collision, missing owner, or stale governed skill appears, fix the portfolio boundary before adding more local complexity to one skill. Non-actionable issues should stay visible as evidence, not as release blockers.
