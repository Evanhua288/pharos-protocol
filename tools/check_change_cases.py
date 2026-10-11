# -*- coding: utf-8 -*-
r"""check_change_cases.py —— **`223` 变更案例门**。

判据：
 C1 变例必须带 `desc`/`expect`/`why`；
 C2 **变更类案例的期望必须是拒绝类**（`VIOLATION`/`REJECT`）；
 C3 **至少一个正例**（合规变更应放行）；
 C4 **必须涵盖五条核心禁止**：冻结期内改、无双哈希、无实例、以对拍取代、回溯。
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

MUST = ("freeze", "dual_hash", "no_instance" if False else "instance", "reconcile_over", "retro")


def main(argv):
    if len(argv) < 2:
        print("usage: check_change_cases.py <\u5305\u76ee\u5f55>")
        return 2
    p = os.path.join(os.path.abspath(argv[1]), "vectors", "change-223-cases.json")
    if not os.path.isfile(p):
        print("[CHG] 无案例（未声称覆盖）：PASS")
        return 0
    j = json.loads(io.open(p, encoding="utf-8").read())
    bad, kinds, pos = [], set(), 0
    for c in j.get("cases", []):
        for k in ("desc", "expect", "why", "kind"):
            if not c.get(k):
                bad.append("C1 %s 缺 `%s`" % (c.get("id"), k))
        kinds.add(c.get("kind", ""))
        exp = (c.get("expect") or [""])[0]
        if c.get("kind", "").startswith("正例") or c.get("id", "").startswith("正例"):
            pos += 1
            if exp != "OK":
                bad.append("C3 正例 %s 期望应 OK" % c.get("id"))
        elif exp not in ("VIOLATION", "REJECT"):
            bad.append("C2 %s 期望应为拒绝类" % c.get("id"))
    if pos < 1:
        bad.append("C3 缺正例")
    need = {"edit_in_freeze", "no_dual_hash", "no_instance", "reconcile_over_clause", "retro_edit"}
    miss = need - kinds
    if miss:
        bad.append("C4 缺核心禁止案例：%s" % sorted(miss))
    print("[CHG] 案例 %d（正例 %d）；异常 %d" % (len(j.get("cases", [])), pos, len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 `223` \u53d8\u66f4\u6848\u4f8b\u4e0d\u5408\u683c"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
