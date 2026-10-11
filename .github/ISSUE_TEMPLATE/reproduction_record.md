---
name: Independent reproduction record
about: Report your own independent reproduction
title: "[REPRODUCTION] "
labels: reproduction
---

## Reproducer

Name or handle. No affiliation is required.

## Isolation

State where you unpacked the package and confirm it was read-only.

## Results

| Step | Command | Expected | Observed |
|---|---|---|---|
| 1 | tools/reproduce_all.py | REPRODUCIBLE | |
| 2 | tools/check_proof_ledger.py | PASS, leaves 34 | |
| 3 | tools/check_merkle.py | PASS | |

## Independently recomputed values

- Merkle root:
- specHash:
- Signature check:

## Conclusion

- [ ] A - fully reproduced
- [ ] B - partially reproduced (attach first differing byte)
- [ ] C - not reproduced (attach environment and error)
