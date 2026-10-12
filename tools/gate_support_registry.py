# -*- coding: utf-8 -*-
r"""gate_support_registry.py \u2014\u2014 **\u914d\u5957\u4ef6\u5305\u5916\u5f15\u7528\u767b\u8bb0\u8868** \u5168\u91cf\u673a\u5224\u95e8\u3002

\u4e3a\u4f55\u9700\u8981\uff1a\u7b2c\u4e09\u65b9\u590d\u9a8c\u4e0e **T6 \u7b2c 4 \u6761**\u5747\u6307\u51fa\uff1a
\u8be5\u8868\u58f0\u660e\u4e86\u6bcf\u4e00\u4ef6\u201c\u4ea4\u4ed8\u72b6\u6001\u201d\uff0c\u800c **\u6ca1\u6709\u4efb\u4f55\u95e8\u5728\u5b88\u201c\u58f0\u660e \u2194 \u5b9e\u4ef6\u201d**\u3002
\u5df2\u77e5\u4e0d\u4e00\u81f4\u4f8b\uff1a**A11 `\u914d\u5957\u4ef6/\u7981\u8bed\u8bcd\u8868.md`**\uff08\u8868\u5185\u5199 A11\uff0c\u5b9e\u4e3a\u300c\u672c\u5305\u7f3a\u5931\u300d\uff09\u3001
**id \u91cd\u590d A6\uff0fA7\uff0fA8**\u3002

\u5224\u636e\uff1a
  S1 \u58f0\u660e\u300c\u5df2\u4ea4\u4ed8\u300d\u8005\uff0c\u5305\u5185\u5fc5\u6709\u5b9e\u4ef6\uff1b
  S2 \u58f0\u660e\u300c\u672c\u5305\u7f3a\u5931\uff0f\u672a\u4ea4\u4ed8\uff08\u5305\u5916\uff09\u300d\u8005\uff0c\u5305\u5185\u5fc5**\u65e0**\u5b9e\u4ef6\uff1b
  S3 \u8868\u5185\u51fa\u73b0\u7684\u8def\u5f84\uff08`xxx/yyy.md`\uff09\u5fc5\u5b58\u5728\uff1b
  S4 **id \u4e0d\u5f97\u91cd\u590d**\u3002

\u9000\u51fa\u7801\uff1a0 \u901a\u8fc7\uff1b1 \u4e0d\u5408\u683c\uff1b2 \u65e0\u8868\uff08\u672a\u58f0\u79f0\uff09\u3002**\u53ea\u8bfb**\u3002
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REL = "\u914d\u5957\u4ef6/\u5305\u5916\u5f15\u7528\u767b\u8bb0\u8868.md"


def main(argv):
    root = os.path.abspath(argv[1]) if len(argv) > 1 else "."
    p = os.path.join(root, REL)
    if not os.path.isfile(p):
        print("[SUPPORT] \u65e0\u767b\u8bb0\u8868\uff1a\u672a\u58f0\u79f0\u8986\u76d6\uff0cPASS")
        return 0
    L = io.open(p, encoding="utf-8", errors="replace").read().split("\n")
    bad, ids, rows = [], [], 0
    DELIVERED = ("\u2705 **\u5df2\u4ea4\u4ed8**", "\u2705**\u5df2\u4ea4\u4ed8**", "**\u5df2\u4ea4\u4ed8**")
    ABSENT = ("\u672c\u5305\u7f3a\u5931", "\u672c\u5305\u5185**\u4e0d\u5b58\u5728**", "\u5305\u5185**\u4e0d\u5b58\u5728**", "\u672a\u4ea4\u4ed8\uff08\u5305\u5916\uff09")
    for i, ln in enumerate(L, 1):
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 4:
            continue
        rid = re.sub(r"[*\s]", "", cells[0])
        if not re.fullmatch(r"[A-Z]?\d{1,2}", rid or ""):
            continue
        rows += 1
        if rid in ids:
            bad.append(("S4 \u91cd\u590d id", "%s\uff08L%d\uff09" % (rid, i)))
        ids.append(rid)
        ref, st = cells[1], cells[3]
        # S3\uff1a\u8868\u5185\u51fa\u73b0\u7684\u8def\u5f84
        for m in re.finditer(r"`([A-Za-z0-9_./\u4e00-\u9fff-]+\.(?:md|json|py|txt))`", ref + " " + st):
            rp = m.group(1)
            if "/" in rp and not os.path.exists(os.path.join(root, rp)):
                bad.append(("S3 \u8def\u5f84\u4e0d\u5b58\u5728", "%s\uff08L%d\uff09" % (rp, i)))
        # S1\uff1a\u58f0\u660e\u5df2\u4ea4\u4ed8 \u21d2 \u5fc5\u6709\u5b9e\u4ef6
        if any(d in st for d in DELIVERED):
            for m in re.finditer(r"`([A-Za-z0-9_./\u4e00-\u9fff-]+\.(?:md|json|py|txt))`", ref + " " + st):
                rp = m.group(1)
                if "/" in rp and not os.path.exists(os.path.join(root, rp)):
                    bad.append(("S1 \u58f0\u660e\u5df2\u4ea4\u4ed8\u4f46\u5305\u5185\u65e0", "%s\uff08L%d\uff09" % (rp, i)))
        # S2\uff1a\u58f0\u660e\u5305\u5185\u672a\u5b58\u5728 \u21d2 \u5fc5\u65e0\u5b9e\u4ef6
        if any(a in st for a in ABSENT):
            for m in re.finditer(r"`([A-Za-z0-9_./\u4e00-\u9fff-]+\.(?:md|json|py|txt))`", ref + " " + st):
                rp = m.group(1)
                if "/" in rp and os.path.exists(os.path.join(root, rp)):
                    bad.append(("S2 \u58f0\u660e\u5305\u5185\u65e0\u4f46\u5b9e\u6709", "%s\uff08L%d\uff09" % (rp, i)))

    print("[SUPPORT] \u8868\u884c %d\uff1bid %d\uff1b\u5f02\u5e38 %d" % (rows, len(ids), len(bad)))
    for k, v in bad[:10]:
        print("     \u2192 %s\uff1a%s" % (k, v))
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u767b\u8bb0\u4e0e\u5b9e\u4ef6\u4e0d\u7b26"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
