# -*- coding: utf-8 -*-
r"""check_merkle.py —— **Merkle 实作门**（逐 n 全叶包含证明 ＋ RFC 节点数）。

判据：
 M1 n=1..9 **每个叶**的包含证明都能验过；
 M2 **篡改叶后必失败**；
 M3 **RFC 6962 原文节点数**：`PROOF(3,D[7])=4`、`PROOF(4,D[7])=1`、`PROOF(6,D[7])=3`；
 M4 **边界**：空树根＝`SHA-256()`；单叶树根＝叶哈希；审计路径为空；
 M5 **n=7 i=3 审计路径长度＝3**（RFC 例子）。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merkle as M  # noqa: E402


def main(argv):
    bad = []
    total = 0
    for n in range(1, 10):
        ls = [M.leaf_hash(b"d" + str(i).encode()) for i in range(n)]
        root = M.mth(ls)
        for i in range(n):
            total += 1
            if not M.verify_inclusion(i, n, ls[i], M.inclusion_path(i, ls), root):
                bad.append("M1 包含证明失败：n=%d i=%d" % (n, i))
    ls7 = [M.leaf_hash(b"d" + str(i).encode()) for i in range(7)]
    if M.verify_inclusion(3, 7, M.leaf_hash(b"x"), M.inclusion_path(3, ls7), M.mth(ls7)):
        bad.append("M2 篡改叶后仍验过")
    ns = (len(M.consistency_proof(3, ls7, True)), len(M.consistency_proof(4, ls7, True)),
          len(M.consistency_proof(6, ls7, True)))
    if ns != (4, 1, 3):
        bad.append("M3 一致性节点数 %s，应 (4,1,3)" % (ns,))
    if M.mth([]) != hashlib.sha256(b"").digest():
        bad.append("M4 空树根不符")
    if M.mth([ls7[0]]) != ls7[0] or M.inclusion_path(0, [ls7[0]]) != []:
        bad.append("M4 单叶树边界不符")
    if len(M.inclusion_path(3, ls7)) != 3:
        bad.append("M5 n=7 i=3 路径长度 %d，应 3" % len(M.inclusion_path(3, ls7)))
    print("[MERKLE] 包含证明 %d 条；一致性节点数 %s；异常 %d" % (total, ns, len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 Merkle \u5b9e\u4f5c\u4e0d\u5408\u683c"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
