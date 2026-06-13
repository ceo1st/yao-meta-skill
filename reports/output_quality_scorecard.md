# Output Quality Scorecard

This v0 scorecard compares static without-skill and with-skill outputs using assertion grading.

- Cases: `3`
- Baseline pass rate: `0.0`
- With-skill pass rate: `100.0`
- Delta: `100.0`
- Regressions: `0`
- Gate pass: `True`

## Case Results

| Case | Baseline | With Skill | Delta | Winner | Failed With-Skill Assertions |
| --- | ---: | ---: | ---: | --- | --- |
| skill-package-contract | 0.0 | 100.0 | 100.0 | with_skill | None |
| output-eval-expectation | 0.0 | 100.0 | 100.0 | with_skill | None |
| ir-before-packaging | 0.0 | 100.0 | 100.0 | with_skill | None |

## Failure Taxonomy

- No with-skill assertion failures.

## Next Fixes

- Add holdout cases before using this as a release gate.
- Promote repeated failed assertions into the output-risk profile.
- Keep assertions tied to material deliverables, not phrasing trivia.
