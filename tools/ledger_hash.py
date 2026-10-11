# -*- coding: utf-8 -*-
import sys as _sys
try:
    if hasattr(_sys.stdout, "reconfigure"):
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
r"""PHAROS 参考实现：规范序列 + 规范账本哈希（CORE-001 §3B / 125-129）
用法：python ledger_hash.py <ledger.json>
依赖：rfc8785 （RFC 8785 JCS）。
"""
import hashlib
import json
import sys

import rfc8785


def entry_hash(o):
    core = {k: v for k, v in o.items() if k != "hash"}
    pre = o["prevHash"].encode("ascii")
    return hashlib.sha256(pre + rfc8785.dumps(core)).hexdigest()


def canonical_sequence(es):
    return sorted(es, key=lambda o: (o["when"], o["entryId"]))


def ledger_hash(es):
    seq = canonical_sequence(es)
    cat = "".join(entry_hash(o) for o in seq).encode("ascii")
    return hashlib.sha256(b"PHAROS-LEDGER-v1" + cat).hexdigest(), seq


if __name__ == "__main__":
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    lh, seq = ledger_hash(data)
    print("entries=%d" % len(data))
    print("ledgerHash=%s" % lh)
    for i, o in enumerate(seq, 1):
        print("%2d %s %s" % (i, o["when"], entry_hash(o)))
