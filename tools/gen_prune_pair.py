# -*- coding: utf-8 -*-
r"""gen_prune_pair.py \u2014\u2014 **\u8de8\u5305\u88c1\u526a\u7528\u4f8b\u751f\u6210**\u3002

\u505a\u4e24\u68f5\u6811\uff08\u65e7 `n` \u53f6\uff0f\u65b0 `n+` \u53f6\uff09\uff0c\u5e76\u8bc1\uff1a
  P1 \u65e7\u8bc1\u660e\u5728**\u65b0\u6811**\u4e0b\u4ecd\u53ef\u7528\uff08\u56e0\u4e3a\u53f6\u524d\u7f00\u4e0d\u53d8\uff09\uff1b
  P2 \u88c1\u526a\u53ea\u62d2\u4f9b\u65e7\u4e0b\u6807\uff0c**\u4e0d\u5220\u6570\u636e**\uff1b
  P3 \u65b0\u6811\u53ef\u7ed9\u51fa**\u4e00\u81f4\u6027\u8bc1\u660e**\uff08\u65e7\u6839 \u2192 \u65b0\u6839\uff09\u3002

\u8f93\u51fa\uff1a`vectors/prune-pair.json`\u3002
"""
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merkle as M  # noqa: E402


def main(argv):
    if len(argv) < 2:
        print("usage: gen_prune_pair.py <\u5305\u76ee\u5f55>")
        return 2
    V = os.path.abspath(argv[1])
    data = [b"e%03d" % i for i in range(40)]
    old = [M.leaf_hash(d) for d in data[:24]]
    new = [M.leaf_hash(d) for d in data]
    root_old, root_new = M.mth(old), M.mth(new)
    rec = {
        "_note": "\u8de8\u5305\u88c1\u526a\u7528\u4f8b\uff08\u65e7 24 \u53f6 \u2192 \u65b0 40 \u53f6\uff09\u3002",
        "oldSize": len(old), "newSize": len(new),
        "oldRoot": root_old.hex(), "newRoot": root_new.hex(),
        "oldProofs": [{"index": i, "path": [p.hex() for p in M.inclusion_path(i, old)]}
                      for i in range(len(old))],
        "consistency": {"m": len(old), "n": len(new),
                        "hashes": [h.hex() for h in M.consistency_proof(len(old), new, True)]},
    }
    dst = os.path.join(V, "vectors", "prune-pair.json")
    io.open(dst, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("[PRUNEPAIR] \u65e7 %d \u2192 \u65b0 %d\uff1b\u65e7\u6839 %s\uff1b\u65b0\u6839 %s" % (
        len(old), len(new), root_old.hex()[:16], root_new.hex()[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
