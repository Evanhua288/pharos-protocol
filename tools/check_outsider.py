# -*- coding: utf-8 -*-
r"""check_outsider.py — 外部读者检（V1.25 新增）。

**四问**（每一问都问"只看 `spec/` 一个文件会怎样"）：
  Q1 **可算否**：`§3B` 所需的键名与算法，是否都在 `spec/` 内？
  Q2 **可判否**：错误码与判定顺序，是否都在 `spec/` 内？
  Q3 **可接入否**：`spec/` 指向包内 `spec/` 之外的件，**是否已登记为辅助件**？
  Q4 **可交付否**：`spec/` 是否自陈**唯一锚**（`SHA256SUMS` 那一行）？

**能证什么**：**"只给 spec 一个文件"时，跨件引用**有没有登记****。
**不能证什么**：**语义可读性、术语自洽、外行能否读懂**——那要人读。

用法：python tools/check_outsider.py <包根>
退出码：0 = 四问皆过；1 = 有缺口；2 = 无法执行。
"""
import io
import os
import re
import sys

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SPEC = "spec/CORE-001-V1.2.md"
REG = "\u914d\u5957\u4ef6/\u5305\u5916\u5f15\u7528\u767b\u8bb0\u8868.md"
DIRS = ("vectors", "tools", "\u914d\u5957\u4ef6", "_correspondence")


def _read(p):
    return io.open(p, encoding="utf-8", errors="replace").read()


def main(root):
    p = os.path.join(root, SPEC)
    if not os.path.exists(p):
        print("[OUTSIDER] \u672a\u627e\u5230 %s" % SPEC)
        return 2
    t = _read(p)
    fails = []

    q1 = all(k in t for k in ("PHAROS-LEDGER-v1", "entryId", "prevHash"))
    print("[OUTSIDER] Q1 \u53ef\u7b97\u5426\uff08\u00a73B \u81ea\u542b\uff09\uff1a%s" % ("PASS" if q1 else "FAIL"))
    if not q1:
        fails.append(("Q1_NOT_SELF_CONTAINED", "\u00a73B \u7f3a\u7b97\u6cd5\u6216\u952e\u540d"))

    q2 = ("E10" in t) and ("\u5224\u5b9a\u987a\u5e8f" in t) and ("E09" in t)
    print("[OUTSIDER] Q2 \u53ef\u5224\u5426\uff08\u7801\u8868\uff0b\u987a\u5e8f\uff09\uff1a%s" % ("PASS" if q2 else "FAIL"))
    if not q2:
        fails.append(("Q2_NO_CODE_TABLE", "\u7801\u8868\u6216\u5224\u5b9a\u987a\u5e8f\u672a\u5728 spec \u5185"))

    outside = set()
    for m in re.finditer(r"`([^`]+\.(?:md|json|txt|py))`", t):
        rel = m.group(1)
        if rel.startswith("spec/") or any(k in rel for k in ("http", "did:", "RFC", "ISO")):
            continue
        if rel.split("/")[0] in DIRS:
            outside.add(rel)
    reg_p = os.path.join(root, REG)
    reg_t = _read(reg_p) if os.path.exists(reg_p) else ""
    registered = set(x for x in outside if os.path.basename(x) in reg_t)
    unreg = sorted(outside - registered)
    print("[OUTSIDER] Q3 \u53ef\u63a5\u5165\u5426\uff1aspec \u6307\u5411 spec/ \u4e4b\u5916 %d \u5904\uff1b\u5df2\u767b\u8bb0 %d\uff1b\u672a\u767b\u8bb0 %d"
          % (len(outside), len(registered), len(unreg)))
    for x in sorted(outside):
        print("[OUTSIDER]     \u2192 %s%s" % (x, "  (\u5df2\u767b\u8bb0)" if x in registered else "  [!] \u672a\u767b\u8bb0"))
    if unreg:
        fails.append(("Q3_UNREGISTERED", "spec \u6307\u5411\u672a\u767b\u8bb0\u7684\u5305\u5185\u4ed6\u5904\u4ef6\uff08%d\uff09" % len(unreg)))

    q4 = ("SHA256SUMS" in t) and ("\u552f\u4e00\u951a" in t)
    print("[OUTSIDER] Q4 \u53ef\u4ea4\u4ed8\u5426\uff08\u552f\u4e00\u951a\u81ea\u9648\uff09\uff1a%s" % ("PASS" if q4 else "FAIL"))
    if not q4:
        fails.append(("Q4_NO_ANCHOR", "\u672a\u81ea\u9648\u552f\u4e00\u951a\u4e3a SHA256SUMS \u90a3\u4e00\u884c"))

    if fails:
        for k, v in fails:
            print("[FAIL] %-22s %s" % (k, v))
        print("[FAIL] \u5171 %d \u9879\u3002" % len(fails))
        return 1
    print("[PASS] \u56db\u95ee\u7686\u8fc7\uff08Q1 0\uff1bQ2 0\uff1bQ3 0\uff1bQ4 0\uff09")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\u7528\u6cd5: python tools/check_outsider.py <\u5305\u6839>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
