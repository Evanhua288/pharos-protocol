# -*- coding: utf-8 -*-
r"""check_proof_ledger.py —— **证明账本门**。

判据：
 P1 **账本根可由叶重算**（现算 ≡ 存档）；
 P2 **每叶包含证明可验**；
 P3 **篡改叶后根必变**；
 P4 **一致性示例节点数 ≤ ceil(log2 n)+1**。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import io
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merkle as M  # noqa: E402


def main(argv):
    if len(argv) < 2:
        print("usage: check_proof_ledger.py <\u5305\u76ee\u5f55>")
        return 2
    p = os.path.join(os.path.abspath(argv[1]), "vectors", "proof-ledger.json")
    if not os.path.isfile(p):
        print("[PLEDGER] \u65e0\u8bc1\u660e\u8d26\u672c\uff08\u672a\u58f0\u79f0\u8986\u76d6\uff09\uff1aPASS")
        return 0
    j = json.loads(io.open(p, encoding="utf-8").read())
    bad = []
    hs = [bytes.fromhex(l["hash"]) for l in j["leaves"]]
    root = bytes.fromhex(j["root"])
    if M.mth(hs) != root:
        bad.append("P1 \u8d26\u672c\u6839\u4e0e\u73b0\u7b97\u4e0d\u7b26")
    for k, l in enumerate(j["leaves"]):
        path = [bytes.fromhex(x) for x in l["path"]]
        if not M.verify_inclusion(k, len(hs), hs[k], path, root):
            bad.append("P2 \u7b2c %d \u53f6\u5305\u542b\u8bc1\u660e\u5931\u8d25\uff08%s）" % (k, l["id"]))
    forged = list(hs)
    forged[0] = M.leaf_hash(b"forged")
    if M.mth(forged) == root:
        bad.append("P3 \u7be1\u6539\u53f6\u540e\u6839\u4e0d\u53d8")
    ce = j.get("consistencyExample", {})
    lim = math.ceil(math.log2(max(2, ce.get("n", 2)))) + 1
    if len(ce.get("hashes", [])) > lim:
        bad.append("P4 \u4e00\u81f4\u6027\u8282\u70b9\u6570 %d \u8d85\u4e0a\u754c %d" % (len(ce.get("hashes", [])), lim))
    print("[PLEDGER] \u53f6 %d\uff1b根 %s\uff1b异\u5e38 %d" % (len(hs), j["root"][:16], len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u8bc1\u660e\u8d26\u672c\u4e0d\u5408\u683c"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
