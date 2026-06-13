# Runtime Permission Probes

Runtime permission probes verify that generated target adapters expose high-permission capabilities and make native-enforcement limits explicit.

## Summary

- OK: `True`
- Targets probed: `3`
- Passed: `3`
- Failed: `0`
- Native enforcement targets: `0`
- Explicit metadata fallbacks: `3`
- Required capabilities: `file_write, network, subprocess`

| Target | Status | Assurance | Native Enforcement | Metadata Fallback | Residual Risk |
| --- | --- | --- | --- | --- | --- |
| `openai` | `pass` | `metadata-fallback-explicit` | `False` | `True` | Client-native permission enforcement is not provided by this target; installer or operator must honor metadata. |
| `claude` | `pass` | `metadata-fallback-explicit` | `False` | `True` | Client-native permission enforcement is not provided by this target; installer or operator must honor metadata. |
| `generic` | `pass` | `metadata-fallback-explicit` | `False` | `True` | Client-native permission enforcement is not provided by this target; installer or operator must honor metadata. |

## Failures

- None

## Reviewer Note

A passing probe means the target contract is explicit and auditable. It does not claim that a host client enforces permissions natively.
