# -*- coding: utf-8 -*-
r"""check_linenos.py — **条号↔行号 引用机检**（应 `WORKBUDDY-PH-082` §三②）

为何需要：我方向对方引用 `CORE-001-xxx` 的行号时，
曾系统性偏移 1–2 行（换行计数基准不同）。本工具把“条号↔行号”变成**可机检**。

引用写法（在任意 `.md` 里）：
    `CORE-001-197`（L510）      ← 本工具会校验 510 是否为真实行号
不写行号者不校验（避免误报）。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def real_lines(spec):
    m = {}
    for i, ln in enumerate(io.open(spec, encoding="utf-8", errors="replace").read().split("\n"), 1):
        for cid in re.findall(r"\| \*\*`CORE-001-(\d{3}(?:-[A-Z])?)`\*\* \|", ln):
            m.setdefault(cid, i)
    return m


def main(root):
    spec = os.path.join(root, "spec", "CORE-001-V1.2.md")
    if not os.path.exists(spec):
        print("[LINENO] 无 spec")
        return 0
    R = real_lines(spec)
    fails, n = [], 0
    for dp, dn, fn in os.walk(root):
        if "__pycache__" in dp or "_correspondence" in dp:
            continue
        for f in fn:
            if not f.endswith(".md"):
                continue
            fp = os.path.join(dp, f)
            for i, ln in enumerate(io.open(fp, encoding="utf-8", errors="replace").read().split("\n"), 1):
                # ⚠️ 判据自身必修：件里行号常写作 `**L510**`（带加粗），故先去掉 `*` 与空白再匹配
                flat = re.sub(r"[*`\s]", "", ln)
                # ⭐ V1.73 订正（B6）：引用写法可能是 `（L510）`／`：510`／`；:510`（**全角分号＋半角冒号**）
                #   故分隔符集合扩为 `（?L` ｜ `：` ｜ `:` ｜ `；:`
                for cid, claimed in re.findall(
                        r"CORE-001-(\d{3}(?:-[A-Z])?)(?:\uff08?L|\uff1a|:|\uff1b:)(\d+)", flat):
                    n += 1
                    if cid not in R:
                        fails.append(("LINENO_NOCLAUSE", "%s L%d 条号不存在" % (f, i)))
                    elif int(claimed) != R[cid]:
                        fails.append(("LINENO_OFFSET", "%s L%d：%s 声称 L%s，实为 L%d"
                                      % (f, i, cid, claimed, R[cid])))
    print("[LINENO] 校验 %d 处；不符 %d" % (n, len(fails)))
    for t, m2 in fails[:12]:
        print("    [FAIL] %-14s %s" % (t, m2))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
