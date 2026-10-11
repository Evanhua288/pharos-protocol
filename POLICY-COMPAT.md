# Version and Compatibility Policy

Rationale: during self-assessment we found that version numbers had been
used as debug counters — one integer discrepancy consumed eight releases.
This document corrects that practice.

## 1. Three version series, kept separate

| Series | Form | Who changes it |
|---|---|---|
| Specification version | MAJOR.MINOR.PATCH (e.g. 1.0.0) | Governance layer |
| Package release | YYYY.MM (e.g. 2026.10) | Releasing party |
| Working snapshot | internal integer | Internal only — **must never be cited externally** |

Hard rules:
- Year: an internal integer fix never bumps the specification version.
- External documents cite only the specification version and the package
  release; internal snapshot numbers must not appear.
- Within one specification version, a fix must not change irreversible
  behaviour.
- A green internal self-check is not a release condition; a release requires
  a third-party reproduction record.

## 2. Semantic versioning rules

| Change | Bump |
|---|---|
| Breaking (an existing implementation fails validation) | MAJOR |
| Additive and optional (existing implementation still passes) | MINOR |
| Wording only (no semantic change) | PATCH |

Always MAJOR:
1. Any change that invalidates an already-published test vector.
2. Any change to the anchor-exclusion include list.
3. Any change to leaf, node, or domain tag prefixes.
4. Any ordering change that makes a frozen extension proof unverifiable.

## 3. Backward compatibility promise

- C1 Within one MAJOR, published vectors and proofs remain valid forever and
  are never amended retroactively.
- C2 Prior versions stay supported for at least **24 months** from the
  release of a new MAJOR.
- C3 Deprecation is marked and announced in advance; the deprecation period
  is at least **12 months**.
- C4 A PATCH must not introduce any behaviour change.
- C5 A breaking change must ship with a migration path for existing vectors.

## 4. Mapping to the four freeze states

| Freeze state | Version event |
|---|---|
| FROZEN | released, append-only |
| EXTENDED | MINOR (consistency proof verifiable) |
| REPLACED | MAJOR (must be declared as a replacement) |
| DEPRECATED | deprecation period begins; data is never deleted |

This policy exists so that an integrator who has never met us can predict
that we will not betray their integration.

## 5. Contacts

- Version and compatibility questions: **evanhua288@gmail.com** (暂用，可替换)
- Security matters: see SECURITY.md
## 6. Publication

- Source repository: https://github.com/Evanhua288/pharos-protocol
- Signed releases: https://github.com/Evanhua288/pharos-protocol/releases/latest
