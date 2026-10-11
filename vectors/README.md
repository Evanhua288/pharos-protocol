# Test Vectors

This directory is a **standalone release artifact**. It can be taken
without the reference implementation and used to check any independent
implementation of the specification.

Each file states its own rule and its expected value. Where a value is
a hash, it is written in lowercase hex.

| File | Bytes | sha256 (first 16) |
|---|---|---|
| `EXPECTED.md` | 15810 | `c68b27ce24356c15` |
| `NEGATIVE-CASES.md` | 10859 | `75682e43169d586c` |
| `archive-negative.json` | 1480 | `c4e725f75bcf3faa` |
| `capabilities-echo-159.json` | 581 | `48bb2fb99bdabc56` |
| `chain-negative.json` | 1968 | `6b0df9ecf1a7735d` |
| `change-223-cases.json` | 1679 | `dff2b0a00ae06a0d` |
| `digest-set-cases.json` | 1024 | `86135e9c9e2ef580` |
| `error-codes.json` | 4445 | `0b75c9d912891ff3` |
| `extension-cases.json` | 1587 | `dc14361b997e7c8a` |
| `fascicle-upgrade.json` | 1010 | `62b9c4d7b8da324e` |
| `field-entity.json` | 2365 | `742774c2223aef0d` |
| `positive-cases.json` | 2042 | `8809599180df8703` |
| `proof-ledger.json` | 20291 | `95f75e40973f63ae` |
| `proxy-risk-cases.json` | 2568 | `1213da9e998e63a4` |
| `prune-pair.json` | 9687 | `2df3ed36943199b0` |
| `qualification-cases.json` | 1833 | `f1d450e03c0de680` |
| `replay-interaction.json` | 1821 | `811cc8cfdb1e9f99` |
| `reversal-negative.json` | 2406 | `faf8bc27e22139d8` |
| `task-loop.json` | 972 | `b899b5fb0656e7a4` |
| `v1-minimal.json` | 278 | `ef9fd92c039e88a6` |
| `v1b-chained.json` | 346 | `1d8113bcfdb7c2bc` |
| `v2-amount-precision.json` | 161 | `f2d3c49e2f55677a` |
| `v3-absent.json` | 219 | `4a4131ad5fd6fb4f` |
| `v3-null.json` | 242 | `38567e326eb435c5` |
| `v4-cjk.json` | 336 | `11e07ce8af74996c` |
| `v5-negative-zero.json` | 251 | `7c4e63cd2c8223fc` |
| `v6-settlement-clean.json` | 241 | `a875acb78c3a5ac4` |
| `v7-identity-minimal.json` | 332 | `d9e6fc7c01586dfe` |
| `v8-identity-rotation.json` | 499 | `60c9036ec16e6d75` |

## How to use

    python tools/reproduce_all.py <package-dir>

A vector that cannot be reproduced is a defect report, not an opinion.

## What a matching vector does and does not mean

It means the implementation agrees with the published rule.
It does not mean any party is compliant with any law, regulation,
standard, or certification scheme.
