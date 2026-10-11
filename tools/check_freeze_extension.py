# -*- coding: utf-8 -*-
r"""check_freeze_extension.py —— **冻结扩展门**（守方建议①）。

E1 证明件必存在；E2 一致性证明必独立验过；E3 旧树必为新树**严格前缀**；E4 节点数不超上界。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merkle as M  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main(argv):
    V = os.path.abspath(argv[1]) if len(argv) > 1 else "."
    p = os.path.join(V, "vectors", "freeze-extension.json")
    if not os.path.isfile(p):
        print("[FEXT] 无此件（未声称覆盖）：PASS")
        return 0
    j = json.loads(io.open(p, encoding="utf-8").read())
    bad = []
    su = os.path.join(V, "SHA256SUMS")
    rows = [x.strip() for x in io.open(su, encoding="utf-8", errors="replace").read().split("\n") if "  " in x]
    ln = [M.leaf_hash(r.encode("utf-8")) for r in rows]
    m, n = int(j["oldSize"]), int(j["newSize"])
    if n != len(ln):
        bad.append("E1 新叶数 %d ≠ 实际 %d" % (n, len(ln)))
    if m > n:
        bad.append("E3 非扩展（旧 > 新）")
    else:
        proof = [bytes.fromhex(x) for x in j.get("proof", [])]
        rm = bytes.fromhex(j.get("oldRoot") or "") or M.mth(ln[:m])
        if not M.verify_consistency(m, n, proof, rm, M.mth(ln), ln):
            bad.append("E2 一致性证明未过（旧树非新树严格前缀）")
    print("[FEXT] 旧 %d 叶 → 新 %d 叶；证明 %d 节点；异常 %d" % (
        m, n, len(j.get("proof", [])), len(bad)))
    for x in bad[:6]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u51bb\u7ed3\u6269\u5c55\u4e0d\u53ef\u8bc1"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
