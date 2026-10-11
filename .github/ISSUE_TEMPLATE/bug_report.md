---
name: Implementation consistency defect
about: An implementation does not match the published specification or vectors
title: "[INCONSISTENCY] "
labels: consistency
---

## What you ran

Command and the exact package (specification version and package release):

    python tools/reproduce_all.py <package-dir> <workspace-dir>

## Expected

Which published rule, vector, or proof you expected to hold. Cite the rule id.

## Observed

Paste the output. Include the first differing byte or value if there is one.

## Environment

- Python version:
- OS:
- Package release (from VERSION):
- Specification version (from VERSION):

## Scope check

- [ ] I did not modify anything inside the package.
- [ ] I did not read a private key (none is shipped).
- [ ] This report is about consistency with the specification, not about
      compliance with any law or certification scheme.
