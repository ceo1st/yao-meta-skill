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

## Reviewer Gate

Use Atlas before promoting a single skill into a shared library. If a route collision or missing owner appears, fix the portfolio boundary before adding more local complexity to one skill.
