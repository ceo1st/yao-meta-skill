# Trust Security Method

Trust checks make skills safer to install and review, especially when they include scripts or are distributed to a team.

## When To Run

Run the trust report when:

- the skill contains scripts
- the skill will be shared with a team
- the package may be installed from a registry or plugin
- the skill reads external files, uses network access, or shells out
- the maturity tier is library or governed

## V0 Checks

- obvious secret patterns
- script help surface and interactive prompts
- dependency pinning
- runtime trust metadata
- network-capable scripts
- package integrity digest

## Release Rule

High-risk secrets or unrestricted remote inline execution block governed release. Warnings are reviewer-visible but do not block v0 unless the release owner decides the target environment requires stricter policy.
