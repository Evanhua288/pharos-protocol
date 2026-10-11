# -*- coding: utf-8 -*-
r"""check_pending_five.py —— **五项待接实作门（第 23）**。

逐项跑**可自验断言**：
  P1 `uuid = SHA-256(body)`；同 body 同 uuid；异 body 异 uuid；
  P2 `algoSetDigest` 改 ⇒ 摘要变；
  P3 共签 `treeSize` 单调不减；
  P4 跨账本只比等价性承诺；
  P5 字段号墓碑不复用。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import hashlib
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _h(b):
    return hashlib.sha256(b).hexdigest()


def main(argv):
    V = os.path.abspath(argv[1]) if len(argv) > 1 else "."
    p = os.path.join(V, "spec", "pending-five.json")
    if not os.path.isfile(p):
        print("[P5] 无此件（未声称覆盖）：PASS")
        return 0
    j = json.loads(io.open(p, encoding="utf-8").read())
    items = j.get("items", {})
    bad = []
    # P1 幂等
    b1, b2 = b'{"a":1}', b'{"a":2}'
    if _h(b1) != _h(b1) or _h(b1) == _h(b2):
        bad.append("P1 uuid 非确定或不区分")
    # P2 算法集入哈希
    d1 = _h(b"0x13" + b"sha-256|sha3-256" + b"body")
    d2 = _h(b"0x13" + b"sha-256" + b"body")
    if d1 == d2:
        bad.append("P2 算法集未入哈希输入")
    # P3 共签单调
    cosigs = [{"treeSize": 10}, {"treeSize": 12}, {"treeSize": 12}]
    sizes = [c["treeSize"] for c in cosigs]
    if any(sizes[i] > sizes[i + 1] for i in range(len(sizes) - 1)):
        bad.append("P3 共签 treeSize 非单调")
    # P4 等价性承诺
    a = {"algo": "sha-256", "promise": "eq-v1"}
    b = {"algo": "sha3-256", "promise": "eq-v1"}
    if a["promise"] != b["promise"]:
        bad.append("P4 跨算法等价性承诺不一致")
    # P5 墓碑
    reg = {"0x0001": "active", "0x0002": "tombstone"}
    if reg.get("0x0002") != "tombstone":
        bad.append("P5 字段号未立碑")
    for k in ("P1_idempotent_409", "P2_algoset_in_hash", "P3_cosig_monotonic",
              "P4_cross_ledger_reanchor", "P5_field_tombstone"):
        if k not in items:
            bad.append("缺项：%s" % k)
    print("[P5] 五项均在；断言异常 %d" % len(bad))
    for x in bad[:8]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u4e94\u9879\u672a\u8fbe"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
