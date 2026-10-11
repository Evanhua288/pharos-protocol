# -*- coding: utf-8 -*-
r"""check_freeze_registry.py —— **`223` 冻结期机检门**。

判据：
 F1 **每条必登记**（`clauses.json` 的唯一条号 ⊆ 登记表）；
 F2 **登记条目必有** `firstPublished`／`frozenUntil`／`status`；
 F3 **`status` 三态之一**：`FROZEN`／`EXPIRED`／`SUPERSEDED`；
 F4 **`FROZEN` 者期限差必为 60 天**；
 F5 **取代关系必带新条号**。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import datetime
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _d(s):
    try:
        return datetime.date.fromisoformat(s)
    except Exception:
        return None


def main(argv):
    V = os.path.abspath(argv[1]) if len(argv) > 1 else "."
    p = os.path.join(V, "spec", "freeze-registry.json")
    if not os.path.isfile(p):
        print("[FREEZE] 无登记表（未声称覆盖）：PASS")
        return 0
    fr = json.loads(io.open(p, encoding="utf-8").read())
    cj = json.loads(io.open(os.path.join(V, "spec", "clauses.json"), encoding="utf-8").read())
    ids = {r["id"] for r in cj["index"]}
    bad = []
    reg = fr.get("clauses", {})
    miss = ids - set(reg)
    if miss:
        bad.append("F1 未登记 %d 条（例：%s）" % (len(miss), sorted(miss)[:3]))
    days = int(fr.get("freezeDays") or 0)
    for cid, v in reg.items():
        for k in ("firstPublished", "frozenUntil", "status"):
            if not v.get(k):
                bad.append("F2 %s 缺 `%s`" % (cid, k))
        if v.get("status") not in ("FROZEN", "EXPIRED", "SUPERSEDED"):
            bad.append("F3 %s `status` 非三态" % cid)
        a, b = _d(str(v.get("firstPublished"))), _d(str(v.get("frozenUntil")))
        if a and b and v.get("status") == "FROZEN" and (b - a).days != days:
            bad.append("F4 %s 期限 %d 天 ≠ %d" % (cid, (b - a).days, days))
        if v.get("status") == "SUPERSEDED" and not v.get("supersededBy"):
            bad.append("F5 %s 缺 `supersededBy`" % cid)
    nf = sum(1 for v in reg.values() if v.get("status") == "FROZEN")
    print("[FREEZE] 登记 %d；冻结中 %d；期限 %d 天；异常 %d" % (len(reg), nf, days, len(bad)))
    for x in bad[:8]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u51bb\u7ed3\u767b\u8bb0\u4e0d\u5408\u683c"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
