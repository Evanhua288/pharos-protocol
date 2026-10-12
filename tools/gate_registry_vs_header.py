# -*- coding: utf-8 -*-
r"""gate_registry_vs_header.py \u2014\u2014 **\u767b\u8bb0 vs \u4ef6\u5934\u72b6\u6001** \u95e8\uff08\u65b9\u6848 C\uff09\u3002

\u4e3a\u4f55\u9700\u8981\uff1a\u7b2c\u4e09\u65b9\u590d\u9a8c\u53d1\u73b0 **19 \u4ef6**\u7684 `000-060` \u767b\u8bb0\u4e0e\u4ef6\u5934 `\u72b6\u6001`
**\u542b\u4e49\u76f8\u53cd**\uff08\u767b\u8bb0=\u73b0\u884c\uff0f\u4ef6\u5934=\u8349\u6848\uff09\uff0c\u800c **`000-060` \u89c4\u5219 3\uff0f4 \u660e\u5199**
\u201c\u73b0\u884c\uff1d\u53ef\u4f5c\u5f53\u524d\u4f9d\u636e\u5f15\u7528\u201d\u3001\u201c\u8349\u6848\uff1d\u4e0d\u5f97\u5bf9\u5916\u5f15\u7528\u201d\uff0c
\u5374 **\u6ca1\u6709\u4efb\u4f55\u95e8\u5728\u5b88\u8fd9\u6761**\u3002

\u53d6\u57fa\u503c\u89c4\u5219\u4e0e `gate_headers` \u4e00\u81f4\uff08\u5230 `\uff5c`\u3001\u4e2d\u70b9\u3001\u7834\u6298\u53f7\u3001\u62ec\u53f7\u4e3a\u6b62\uff09\u3002
\u9000\u51fa\u7801\uff1a0 \u901a\u8fc7\uff1b1 \u4e0d\u4e00\u81f4\uff1b2 \u65e0\u6cd5\u6267\u884c\u3002**\u53ea\u8bfb**\u3002
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REG_NAME = "PHAROS-000-060-\u5f53\u524d\u6709\u6548\u7248\u672c\u6e05\u5355-V1.3-20261008.md"
STATES = ("\u73b0\u884c", "\u8349\u6848", "\u4f5c\u5e9f\u00b7\u4ec5\u8ffd\u6eaf", "\u5f85\u751f\u6548", "\u5f85\u7528\u9644\u4ef6", "\u89c4\u5212\u4e2d\u00b7\u672a\u751f\u6548")


def base(s):
    s = (s or "").strip()
    for sep in ("\uff5c", "|"):
        if sep in s:
            s = s.split(sep)[0]
    s = re.sub(r"^[*\s\u2b50]+|[*\s]+$", "", s)
    s = s.split("\u2014\u2014")[0]
    s = re.sub(r"[\uff08(].*$", "", s).strip()
    return re.sub(r"[*\s]+$", "", s).strip()


def strip_ver(c):
    return re.sub(r"-V\d+(\.\d+)*$", "", c.strip())


def main(argv):
    root = os.path.abspath(argv[1]) if len(argv) > 1 else "."
    la = os.path.join(root, "spec", "layers")
    reg_p = os.path.join(la, REG_NAME)
    if not os.path.isfile(reg_p):
        print("[REG-HDR] \u65e0 000-060\uff1a\u672a\u58f0\u79f0\u8986\u76d6\uff0cPASS")
        return 0

    reg = {}
    for ln in io.open(reg_p, encoding="utf-8", errors="replace").read().split("\n"):
        s = ln.strip()
        if not s.startswith("|"):
            continue
        ids = re.findall(r"`(PHAROS-[A-Z0-9\-]+?)`", s)
        if not ids:
            continue
        st = next((k for k in STATES if k in s), None)
        if not st:
            continue
        for cid in ids:
            reg.setdefault(strip_ver(cid), st)

    bad, unreg, ok = [], [], 0
    for f in sorted(os.listdir(la)):
        if not f.endswith(".md") or "\u4ef6\u540d\u6e05\u5355" in f:
            continue
        m = re.match(r"(PHAROS-(?:[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}(?:-[A-Z])?|GV-[A-Z]+|PA-[A-Z]+))", f)
        key = strip_ver(m.group(1)) if m else None
        L = io.open(os.path.join(la, f), encoding="utf-8", errors="replace").read().split("\n")
        hv = None
        for i in range(min(40, len(L))):
            mm = re.match(r"^\*\*\u72b6\u6001\*\*\s*[\uff1a:]\s*(.+)$", L[i])
            if mm:
                hv = base(mm.group(1))
                break
        if not key or key not in reg:
            unreg.append((f, key, hv))
            continue
        rv = base(reg[key])
        if hv != rv:
            bad.append((f, rv, hv))
        else:
            ok += 1

    print("[REG-HDR] \u767b\u8bb0 %d \u4e2a\u53f7\uff1b\u4e00\u81f4 %d\uff1b**\u4e0d\u4e00\u81f4 %d**\uff1b\u672a\u767b\u8bb0 %d"
          % (len(reg), ok, len(bad), len(unreg)))
    for f, rv, hv in bad[:10]:
        print("     \u2192 %s\uff1a\u767b\u8bb0=%s \u4ef6\u5934=%s" % (f, rv, hv))
    for f, k, hv in unreg[:6]:
        print("     [INFO] \u672a\u767b\u8bb0\uff1a%s\uff08\u53f7=%s\uff0c\u4ef6\u5934=%s\uff09" % (f, k, hv))
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL -- \u767b\u8bb0\u4e0e\u4ef6\u5934\u72b6\u6001\u4e0d\u4e00\u81f4"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
