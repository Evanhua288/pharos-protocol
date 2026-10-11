# -*- coding: utf-8 -*-
r"""gen_freeze_proof.py —— 为两个包生成**冻结扩展证明**。"""
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merkle as M  # noqa: E402


def leaves_of(pkg):
    su = os.path.join(pkg, "SHA256SUMS")
    rows = [x.strip() for x in io.open(su, encoding="utf-8", errors="replace").read().split("\n") if "  " in x]
    return [M.leaf_hash(r.encode("utf-8")) for r in rows]


def main(argv):
    if len(argv) < 2:
        print("usage: gen_freeze_proof.py <\u5305\u76ee\u5f55> [\u65e7\u5305\u76ee\u5f55]")
        return 2
    new = os.path.abspath(argv[1])
    old = os.path.abspath(argv[2]) if len(argv) > 2 else new
    lo, ln = leaves_of(old), leaves_of(new)
    m, n = len(lo), len(ln)
    if m > n:
        print("[FREEZEPROOF] \u65e7 %d > \u65b0 %d\uff1a\u4e0d\u662f\u6269\u5c55" % (m, n))
        return 1
    ro, rn = (M.mth(lo) if lo else b""), (M.mth(ln) if ln else b"")
    # PREFIX-CHECK ⭐ **叶子按行原文构建** ⇒ 若前 m 行原文不全同，则旧树不是前缀
    _ok_prefix = (lo == ln[:m]) if m <= len(ln) else False
    if m == n and ro != rn:
        # MODE=replace\uff1a\u53f6\u6570\u4e0d\u53d8\u4f46\u5185\u5bb9\u53d8 \u21d2 **\u58f0\u660e\u5f0f\u66ff\u6362**\uff0c\u4e0d\u662f\u6269\u5c55
        rec = {"_note": "\u8de8\u5305\u51bb\u7ed3\u5173\u7cfb\uff08**\u66ff\u6362**\uff09\u3002",
               "_rule": "\u53f6\u6570\u76f8\u540c\u4f46\u6839\u4e0d\u540c \u21d2 **\u5fc5\u987b\u58f0\u660e\u4e3a\u66ff\u6362**\uff1b\u4e0d\u5f97\u4f2a\u79f0\u6269\u5c55\u3002",
               "mode": "replace", "oldSize": m, "newSize": n,
               "oldRoot": ro.hex(), "newRoot": rn.hex(), "proof": [],
               "strictExtension": False}
        dst = os.path.join(new, "vectors", "freeze-extension.json")
        io.open(dst, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
        print("[FREEZEPROOF] \u53f6\u6570\u76f8\u540c\u3001\u6839\u4e0d\u540c \u21d2 mode=replace\uff08\u58f0\u660e\u5f0f\u66ff\u6362\uff09")
        return 0
    if not _ok_prefix:
        # 前 m 行原文有变 ⇒ **必须声明为替换**
        rec = {"_note": "跨包冻结关系（**替换**）。",
               "_rule": "前 m 行原文有变 ⇒ **必须声明为替换**；不得伪称扩展。",
               "mode": "replace", "oldSize": m, "newSize": n,
               "oldRoot": ro.hex(), "newRoot": rn.hex(), "proof": [],
               "strictExtension": False}
        dst = os.path.join(new, "vectors", "freeze-extension.json")
        io.open(dst, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
        print("[FREEZEPROOF] 前 %d 行原文有变 ⇒ mode=replace（声明式替换）" % m)
        return 0
    proof = M.consistency_proof(m, ln, True)
    rec = {"_note": "\u8de8\u5305\u51bb\u7ed3\u6269\u5c55\u8bc1\u660e\uff08RFC 6962 \u4e00\u81f4\u6027\u8bc1\u660e\uff09\u3002",
           "_rule": "\u65e7\u6811\u5fc5\u4e3a\u65b0\u6811**\u4e25\u683c\u524d\u7f00**\uff1b\u5b9e\u73b0\u7aef\u72ec\u7acb\u91cd\u7b97\u53cc\u6839\u540e\u624d\u5224\u3002",
           "oldSize": m, "newSize": n,
           "oldRoot": M.mth(lo).hex() if lo else "",
           "newRoot": M.mth(ln).hex() if ln else "",
           "proof": [h.hex() for h in proof],
           "mode": "extend",
           "strictExtension": bool(M.verify_consistency(m, n, proof, ro, rn, ln))}
    dst = os.path.join(new, "vectors", "freeze-extension.json")
    io.open(dst, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("[FREEZEPROOF] \u65e7 %d \u53f6 \u2192 \u65b0 %d \u53f6\uff1b\u4e25\u683c\u6269\u5c55=%s" % (m, n, rec["strictExtension"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
