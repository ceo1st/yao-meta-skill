# Trust Policy

Yao Meta Skill treats scripts and distributed skill packages as supply-chain surfaces.

Governed or team-distributed skills should produce a trust report before release. The report must identify:

- secret exposure risk
- scripts that lack a visible CLI/help surface
- interactive or network-capable scripts
- dependency pinning status
- runtime trust metadata
- package integrity hash

High-risk secrets or unrestricted remote inline execution block governed release.
