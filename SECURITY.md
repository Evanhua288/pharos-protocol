# Security Policy

## Scope

This policy covers the specification text and the reference
implementation in this repository.

## Reporting a vulnerability

Report privately. Do **not** open a public issue for a security matter.

- Security contact: **evanhua288@gmail.com** (interim address, replaceable; not the public issue tracker)
- Acknowledgement within **72 hours**
- Assessment and conclusion within **30 days**
- Coordinated disclosure: we publish a fixed release and record both the
  **pre-fix** and **post-fix** Merkle roots so third parties can verify that
  the fix was an extension, not a silent rewrite.

## What this repository will never contain

- Ed25519 signing private keys
- Release pipeline scripts and anchor ledgers
- Customer lists, pricing rules, cost details
- Internal decision records

If any of the above is found inside a distributed package, treat it as a
release defect and report it through the channel above.

## Safe harbour

We will not pursue or support legal action against researchers who act in
good faith under this policy, avoid privacy violations and service
disruption, and give us reasonable time to respond before disclosure.

## What a fix does and does not mean

A fixed release evidences that the implementation is **consistent with the
published specification**. It does **not** evidence that any party is
compliant with any law, regulation, standard, or certification scheme.

## Where to find releases

Signed releases are published at https://github.com/Evanhua288/pharos-protocol/releases/latest.
