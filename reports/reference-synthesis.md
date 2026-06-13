# Reference Synthesis

Skill: `yao-meta-skill`
- Description: Create, refactor, evaluate, and package agent skills from workflows, prompts, transcripts, docs, or notes. Use when asked to create a skill, turn a repeated process into a reusable skill, improve an existing skill, add evals, or package a skill for team reuse.
- Intent confidence: `30/100` (`low`)

## Live GitHub Benchmarks

### obra/superpowers
- URL: https://github.com/obra/superpowers
- Stars: `226125`
- Borrow: Borrow the way it turns a messy workflow into a repeatable operating path.
- Borrow: Borrow the clear execution entrypoints and command structure.

### affaan-m/ECC
- URL: https://github.com/affaan-m/ECC
- Stars: `214381`
- Borrow: Borrow the way it turns a messy workflow into a repeatable operating path.
- Borrow: Borrow the clear execution entrypoints and command structure.

### multica-ai/andrej-karpathy-skills
- URL: https://github.com/multica-ai/andrej-karpathy-skills
- Stars: `174264`
- Borrow: Borrow explicit validation and quality gates that make iteration safer.
- Borrow: Borrow the way it separates explanation, examples, and reusable structure.

## Curated World-Class Pattern Tracks

### Official workflow product ergonomics
- Type: `official`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: workflow.
- Borrow: Borrow a first-time operator flow that explains itself before it asks for more structure.
- Avoid: Do not mimic product polish that adds UI bulk without improving clarity.

### Hypothesis-test-learn loop
- Type: `research`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: general fit.
- Borrow: Borrow a small hypothesis-test-learn loop so the first revision is evidence-backed.
- Avoid: Do not create experimental overhead that exceeds the skill's real risk tier.

### Boundary-first design
- Type: `principles`
- Evidence mode: `curated-pattern-track`
- Why relevant: This track matches: general fit.
- Borrow: Borrow the discipline of defining what the skill should not own before growing the package.
- Avoid: Do not expand execution assets until route boundaries stay clean.

## Borrow Now

- Borrow a first-time operator flow that explains itself before it asks for more structure.
- Borrow a small hypothesis-test-learn loop so the first revision is evidence-backed.
- Borrow the discipline of defining what the skill should not own before growing the package.
- Borrow the way it turns a messy workflow into a repeatable operating path.
- Borrow the clear execution entrypoints and command structure.

## Avoid Now

- Do not mimic product polish that adds UI bulk without improving clarity.
- Do not create experimental overhead that exceeds the skill's real risk tier.
- Do not expand execution assets until route boundaries stay clean.
- Do not import process overhead that only exists for that project's scale.
- Do not copy repo-specific commands or environment assumptions verbatim.

## Pattern Gate

- Summary: 3 accepted, 3 deferred using threshold 4/4.
- Acceptance threshold: `4/4`
- Accepted patterns:
  - **Official workflow product ergonomics**: 4/4 (recurrence, generativity, distinctiveness, boundary)
  - **obra/superpowers**: 4/4 (recurrence, generativity, distinctiveness, boundary)
  - **affaan-m/ECC**: 4/4 (recurrence, generativity, distinctiveness, boundary)
- Deferred patterns:
  - **Hypothesis-test-learn loop**: missing distinctiveness
  - **Boundary-first design**: missing distinctiveness
  - **multica-ai/andrej-karpathy-skills**: missing generativity

## Default Recommendation

- Summary: Start by borrowing this pattern: Borrow a first-time operator flow that explains itself before it asks for more structure. Avoid this for the first pass: Do not mimic product polish that adds UI bulk without improving clarity.
- Why: Intent still has gaps, so the system should surface the recommendation and ask for correction before deepening the package.
- User decision required: `True`

## Visibility Mode

- Mode: `explicit`
- Reasons: intent_uncertain
- User note: Surface the recommendation because intent is still settling or there is a real design conflict that needs a user call.
- Reviewer note: Keep the full benchmark and synthesis evidence visible for authors and reviewers.

## Conflict Check

- No material design conflict detected. Keep the synthesis silent for the user.

## Quality Lift Thesis

- Use GitHub repositories for concrete package and workflow patterns.
- Use curated official or commercial tracks for entrypoint and operator ergonomics.
- Use research tracks to justify the smallest evaluation loop that still catches regressions.
- Use principle tracks to keep the package small, boundary-aware, and outcome-driven.

## Decision Prompt

Use the recommendation by default. Only surface the underlying benchmark tradeoffs when intent is uncertain or a real design conflict needs a deliberate call.
