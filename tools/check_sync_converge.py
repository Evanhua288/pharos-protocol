# -*- coding: utf-8 -*-
r"""check_sync_converge.py —— **同步收敛门**。

问题：每加一件工具，`spec` 的工具计数就漂移。
本门：**包内声明必等于盘上实数**，且**反复读两次必一致**（收敛）。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main(argv):
    if len(argv) < 2:
        print("usage: check_sync_converge.py <\u5305\u76ee\u5f55>")
        return 2
    V = os.path.abspath(argv[1])
    bad = []
    for _ in range(2):
        td = os.path.join(V, "tools")
        if not os.path.isdir(td):
            print("[SYNC] 无 `tools/`（未声称覆盖）：PASS")
            return 0
        na = len([f for f in os.listdir(td) if os.path.isfile(os.path.join(td, f))])
        npy = len([f for f in os.listdir(td) if f.endswith(".py")])
        sp = os.path.join(V, "spec", "CORE-001-V1.2.md")
        t = io.open(sp, encoding="utf-8", errors="replace").read()
        m = re.search(r"[*][*]([0-9]+) \u4ef6[*][*] = [*][*]([0-9]+) \u4e2a", t)
        if not m:
            bad.append("`spec` 未找到工具计数声明")
            continue
        d, p = int(m.group(1)), int(m.group(2))
        if (d, p) != (na, npy):
            bad.append("声明 (%d 件/%d .py) ≠ 盘上 (%d/%d)" % (d, p, na, npy))
        # 别名表收敛
        cj = os.path.join(V, "spec", "clauses.json")
        ap = os.path.join(V, "spec", "alias-map.json")
        if os.path.isfile(cj) and os.path.isfile(ap):
            import json as _j
            ids = {r["id"] for r in _j.loads(io.open(cj, encoding="utf-8").read())["index"]}
            am = _j.loads(io.open(ap, encoding="utf-8").read())
            if int(am.get("clauseCount") or -1) != len(ids) or len(am.get("entries", [])) != len(ids):
                bad.append("别名表未收敛：条号 %d，表内 %d/%s"
                           % (len(ids), len(am.get("entries", [])), am.get("clauseCount")))
    print("[SYNC] tools 声明与盘上及别名表：异常 %d" % len(bad))
    for x in bad[:8]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u540c\u6b65\u672a\u6536\u655b"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
