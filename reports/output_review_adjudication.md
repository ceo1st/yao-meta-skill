# Output Review Adjudication

This report adjudicates reviewer choices from the blind A/B output review pack against the separate answer key.

- Pairs: `5`
- Judgments: `0`
- Pending: `5`
- Agreement rate: `n/a`
- Invalid decisions: `0`

No reviewer decisions recorded yet.

Generate a template with `--write-template`, fill `winner_variant` with `A` or `B`, then rerun adjudication.

## Case Adjudication

| Case | Reviewer | Expected | Status | Confidence | Reason |
| --- | --- | --- | --- | ---: | --- |
| skill-package-contract | pending | A | pending |  |  |
| output-eval-expectation | pending | A | pending |  |  |
| ir-before-packaging | pending | B | pending |  |  |
| near-neighbor-boundary | pending | B | pending |  |  |
| file-backed-governed-package | pending | B | pending |  |  |

## Next Fixes

- Keep the blind review pack separate from the answer key until decisions are recorded.
- Treat disagreement cases as prompts for rubric tuning or output improvement.
- Add model-executed holdout runs after this human adjudication harness is stable.
