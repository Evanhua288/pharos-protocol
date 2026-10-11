# Release procedure and hard constraints

This file records the order in which a release is built. Getting the order
wrong is not a style issue: it silently produces a package whose own
declared anchor does not match its own bytes.

## The seven steps

1. **Clean the working repository.** Remove anything that must not ship.
2. **Build the package** with the single writer script.
3. **Run the self-check.** Never weaken a criterion in order to pass it.
4. **Write `_FROZEN`.** This must be the last action that changes package
   contents.
5. **Sign `SHA256SUMS`** with Ed25519, in "sign only, do not rewrite" mode.
6. **Compute the anchors** and write `spec/release-index.json`, then update
   the anchor ledger's `current`.
7. **Verify, then publish.** Verify against the package, not against the
   working repository.

## Hard constraints

| # | Constraint | Why |
|---|---|---|
| **C1** | **Compute anchors AFTER building the package, never before.** | The build rewrites specification metadata lines, so a spec hash taken before the build will not match the bytes that ship. This is the root cause of "declared anchor versus actual file" incidents. |
| **C2** | **After any change to `SHA256SUMS`, re-sign before shipping.** | The signature covers the raw bytes of `SHA256SUMS`. Changing one hash line invalidates the signature. |
| **C3** | **Before re-signing, prove that the private key derives the public key already published in the package.** | Signing with the wrong key silently publishes a package that nobody can verify. |
| **C4** | **Never put a `.bak` file inside a package.** | Backups are internal artifacts; inside a package they look like an unattested file. |

## What a pass means

A verified package evidences that an implementation agrees with the published
specification. It does not evidence that any party is compliant with any law,
regulation, standard, or certification scheme.
