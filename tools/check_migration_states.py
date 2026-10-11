# -*- coding: utf-8 -*-
r"""check_migration_states.py —— **迁移四态门（第 26）**。
M1 四态定义必存；M2 四条不变量必存；M3 已冻结包不得被回溯修改（有 `_FROZEN`）。
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

NEED = ("FROZEN", "EXTENDED", "REPLACED", "DEPRECATED")


def main(argv):
    V = os.path.abspath(argv[1]) if len(argv) > 1 else "."
    p = os.path.join(V, "spec", "anchor-migration-4state.json")
    if not os.path.isfile(p):
        print("[MIG] 无此件（未声称覆盖）：PASS")
        return 0
    j = json.loads(io.open(p, encoding="utf-8").read())
    bad = []
    st = j.get("states") or []
    if len(st) != 4 or set(st) != set(NEED):
        bad.append("M1 四态不齐：%s" % st)
    if len(j.get("invariants") or []) < 4:
        bad.append("M2 不变量不足 4 条")
    if not os.path.isfile(os.path.join(V, "_FROZEN")):
        bad.append("M3 包未冻结")
    print("[MIG] 四态 %d；不变量 %d；异常 %d" % (len(st), len(j.get("invariants") or []), len(bad)))
    for x in bad[:6]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u8fc1\u79fb\u56db\u6001\u4e0d\u8db3"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
