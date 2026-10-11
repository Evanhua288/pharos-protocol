# -*- coding: utf-8 -*-
import sys as _sys
try:
    if hasattr(_sys.stdout, "reconfigure"):
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
r"""包内双字词检查：凡出现**词表外的两字组合**，逐个列出供人工确认。
用法：python tools/char_check.py <文件或目录> [...]"""
import io
import re
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INV = os.path.join(HERE, "char_inventory.txt")


def load():
    s = set()
    for ln in io.open(INV, encoding="utf-8", errors="replace"):
        if ln.startswith("#"):
            continue
        w = ln.strip()
        for i in range(0, len(w) - 1, 2):
            s.add(w[i:i + 2])
    return s


def check(p, v):
    t = io.open(p, encoding="utf-8-sig", errors="replace").read()
    out = {}
    for i, ln in enumerate(t.split("\n"), 1):
        for m in re.finditer(r"[\u4e00-\u9fff]{2,}", ln):
            w = m.group(0)
            for j in range(len(w) - 1):
                bg = w[j:j + 2]
                if bg not in v:
                    out.setdefault(bg, (i, ln.strip()[:78]))
    return out


v = load()
targets = sys.argv[1:] or ["."]
n = bad = 0
for tg in targets:
    files = []
    if os.path.isdir(tg):
        for dp, dn, fn in os.walk(tg):
            dn[:] = [d for d in dn if d not in {"__pycache__", ".git"}]
            files += [os.path.join(dp, f) for f in fn if f.endswith((".md", ".txt"))]
    else:
        files = [tg]
    for p in files:
        n += 1
        s = check(p, v)
        if s:
            bad += 1
            print("[NEWWORD] %s" % p)
            for bg, (i, ln) in sorted(s.items()):
                print("    %s  L%d  %s" % (bg, i, ln))
print("[\u8bcd\u8868] \u5df2\u67e5 %d \u4ef6\uff1b\u542b\u65b0\u8bcd\u7ec4 %d \u4ef6\uff08\u8bcd\u8868 %d \u8bcd\uff09"
      % (n, bad, len(v)))
sys.exit(1 if bad else 0)
