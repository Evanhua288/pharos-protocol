# -*- coding: utf-8 -*-
r"""gen_proof_ledger.py —— **用真实条目建 Merkle 树并出证明账本**。

叶源：`vectors/*.json` 各组样例逐例（`id` 为身份）。
叶哈希：`SHA-256(0x00 ‖ canonical(样例))`，`canonical` ＝ **键排序、无空白**的 JSON 字节。
输出：`vectors/proof-ledger.json`。

用法：python gen_proof_ledger.py <包目录>
"""
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merkle as M  # noqa: E402

GROUPS = ("reversal-negative.json", "archive-negative.json", "qualification-cases.json",
          "replay-interaction.json", "proxy-risk-cases.json", "positive-cases.json")


def canon(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main(argv):
    if len(argv) < 2:
        print("usage: gen_proof_ledger.py <\u5305\u76ee\u5f55>")
        return 2
    V = os.path.abspath(argv[1])
    vd = os.path.join(V, "vectors")
    ids, leaves = [], []
    for g in GROUPS:
        p = os.path.join(vd, g)
        if not os.path.isfile(p):
            continue
        j = json.loads(io.open(p, encoding="utf-8").read())
        for c in j.get("cases", []):
            cid = "%s#%s" % (g.replace(".json", ""), c.get("id"))
            ids.append(cid)
            leaves.append(M.leaf_hash(canon(c)))
    if not leaves:
        print("[PROOF] \u65e0\u53f6")
        return 2
    order = sorted(range(len(ids)), key=lambda i: ids[i])
    ids = [ids[i] for i in order]
    leaves = [leaves[i] for i in order]
    root = M.mth(leaves)
    rec = {
        "_note": "\u8bc1\u660e\u8d26\u672c\uff08\u7531 gen_proof_ledger.py \u73b0\u7b97\uff09\u3002\u53f6\uff1d\u5411\u91cf\u6837\u4f8b\uff1b\u6839\uff1dRFC 6962 MTH\u3002",
        "_rule": "canonical \uff1d \u952e\u6392\u5e8f\u3001\u65e0\u7a7a\u767d JSON\uff1b\u53f6\u54c8\u5e0c \uff1d SHA-256(0x00 \u2016 canonical)\u3002",
        "leafHashAlg": "sha-256",
        "treeSize": len(leaves),
        "root": root.hex(),
        "leaves": [{"id": i, "hash": h.hex(), "path": [p.hex() for p in M.inclusion_path(k, leaves)]}
                   for k, (i, h) in enumerate(zip(ids, leaves))],
        "consistencyExample": {"m": max(1, len(leaves) - 1), "n": len(leaves),
                               "hashes": [h.hex() for h in M.consistency_proof(max(1, len(leaves) - 1), leaves, True)]},
    }
    dst = os.path.join(vd, "proof-ledger.json")
    io.open(dst, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("[PROOF] \u53f6 %d\uff1b\u6839 %s\uff1b\u4ea7 %s" % (len(leaves), root.hex()[:16], os.path.basename(dst)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
