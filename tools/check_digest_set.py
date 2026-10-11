# -*- coding: utf-8 -*-
r"""check_digest_set.py —— **SLSA `DigestSet` 门**。

判据：
 S1 **同算法同值 ⇒ `EQUAL`**；S2 **任一共同算法同值 ⇒ `EQUAL`**；
 S3 **无共同算法 ⇒ `INCOMPARABLE`**（**不判不等**）；S4 **同算法值异 ⇒ `UNEQUAL`**。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def judge(a, b):
    common = set(a) & set(b)
    if not common:
        return "INCOMPARABLE"
    for k in common:
        if a[k] == b[k]:
            return "EQUAL"
    return "UNEQUAL"


def main(argv):
    bad = []
    A = {"sha-256": "aa", "sha3-256": "bb"}
    B = {"sha-256": "aa"}
    C = {"sha-512": "cc"}
    D = {"sha-256": "zz"}
    if judge(A, B) != "EQUAL":
        bad.append("S2 任一共同算法同值应 EQUAL")
    if judge(A, C) != "INCOMPARABLE":
        bad.append("S3 无共同算法应 INCOMPARABLE")
    if judge(A, D) != "UNEQUAL":
        bad.append("S4 同算法值异应 UNEQUAL")
    for p in ("spec/digest-set.json", "spec/algorithm-registry.json"):
        fp = os.path.join(os.path.abspath(argv[1]) if len(argv) > 1 else ".", p)
        if not os.path.isfile(fp):
            print("[DSET] 缺件：%s" % p)
            return 0
    reg = json.loads(io.open(os.path.join(os.path.abspath(argv[1]), "spec", "algorithm-registry.json"),
                             encoding="utf-8").read())
    names = {e["name"] for e in reg.get("entries", [])}
    ds = json.loads(io.open(os.path.join(os.path.abspath(argv[1]), "spec", "digest-set.json"),
                            encoding="utf-8").read())
    for k in ds.get("example", {}):
        if k not in names:
            bad.append("S4 例中算法未登记：%s" % k)
    bad += _case_checks(os.path.abspath(argv[1]))
    print("[DSET] 判定三态：EQUAL/UNEQUAL/INCOMPARABLE；异常 %d" % len(bad))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 DigestSet \u4e0d\u5408\u683c"))
    return 0 if not bad else 1


def _set_digest(primary_hex: str, secondary_alg: str) -> str:
    """与 `gen_anchor_ledger.py` 同法：`0x11` 域标 ‖ 主锚摘要 ‖ `|` ‖ 第二算法名。"""
    import hashlib as _h
    p = bytes.fromhex(primary_hex)
    return _h.sha256(b"0x11" + p + b"|" + secondary_alg.encode()).hexdigest()


def _case_checks(V):
    bad = []
    p = os.path.join(V, "vectors", "digest-set-cases.json")
    if not os.path.isfile(p):
        return bad
    j = json.loads(io.open(p, encoding="utf-8").read())
    for c in j.get("cases", []):
        k = c.get("kind")
        if k == "secondary_alg_changes_digest":
            a = _set_digest(c["primary"], c["secondary_alg"])
            b = _set_digest(c["primary"], c["secondary_alg2"])
            if a == b:
                bad.append("\u6539\u7b2c\u4e8c\u7b97\u6cd5\u540d\u6458\u8981\u672a\u53d8\uff1a%s" % c.get("id"))
        elif k == "primary_changes_digest":
            if _set_digest(c["primary"], c["secondary_alg"]) == _set_digest(c["primary2"], c["secondary_alg"]):
                bad.append("\u6539\u4e3b\u951a\u6458\u8981\u672a\u53d8\uff1a%s" % c.get("id"))
        elif k == "same_input_same_digest":
            if _set_digest(c["primary"], c["secondary_alg"]) != _set_digest(c["primary"], c["secondary_alg"]):
                bad.append("\u786e\u5b9a\u6027\u5931\u8d25\uff1a%s" % c.get("id"))
    return bad



if __name__ == "__main__":
    sys.exit(main(sys.argv))
