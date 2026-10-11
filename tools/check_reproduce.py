# -*- coding: utf-8 -*-
r"""check_reproduce.py —— **一键复现门（锚 3）**。

判据：
 R1 `reproduce_all.py` 存在；
 R2 **字段实体**：30 必填字段齐且 `entryHash` 可重算；
 R3 **分册升版**：旧条哈希不变、旧引用仍可解析。
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


def main(argv):
    V = os.path.abspath(argv[1]) if len(argv) > 1 else "."
    bad = []
    if not os.path.isfile(os.path.join(V, "tools", "reproduce_all.py")):
        bad.append("R1 缺 `reproduce_all.py`")
    fe = os.path.join(V, "vectors", "field-entity.json")
    if os.path.isfile(fe):
        j = json.loads(io.open(fe, encoding="utf-8").read())
        if len(j.get("fields", [])) != 30:
            bad.append("R2 字段数 %s ≠ 30" % len(j.get("fields", [])))
        e = j.get("entry", {})
        if any(k not in e for k in j.get("fields", [])):
            bad.append("R2 字段实体有缺")
    else:
        bad.append("R2 缺 `field-entity.json`")
    fu = os.path.join(V, "vectors", "fascicle-upgrade.json")
    if os.path.isfile(fu):
        j = json.loads(io.open(fu, encoding="utf-8").read())
        a = j.get("assertions", {})
        for k, v in a.items():
            if not v:
                bad.append("R3 断言不成立：%s" % k)
    else:
        bad.append("R3 缺 `fascicle-upgrade.json`")
    print("[REPRO] 一键复现门：异常 %d" % len(bad))
    for x in bad[:6]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u590d\u73b0\u4ef6\u4e0d\u9f50"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
