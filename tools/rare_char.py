# -*- coding: utf-8 -*-
import sys as _sys
try:
    if hasattr(_sys.stdout, "reconfigure"):
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
r"""查错字：列出**出现次数最少的汉字**，并给出它在哪个文件、哪一行。
用法：python tools/rare_char.py <目录> [阈值=2]"""
import io
import os
import sys

d = sys.argv[1]
TH = int(sys.argv[2]) if len(sys.argv) > 2 else 2
cnt = {}
where = {}
for dp, dn, fn in os.walk(d):
    dn[:] = [x for x in dn if x not in {"__pycache__", ".git"}]
    for f in fn:
        if not f.endswith((".md", ".txt")):
            continue
        p = os.path.join(dp, f)
        for i, ln in enumerate(io.open(p, encoding="utf-8-sig", errors="replace").read().split("\n"), 1):
            for ch in ln:
                if "\u4e00" <= ch <= "\u9fff":
                    cnt[ch] = cnt.get(ch, 0) + 1
                    if ch not in where:
                        where[ch] = (os.path.basename(f)[:34], i, ln.strip()[:56])
rare = sorted([c for c, n in cnt.items() if n <= TH], key=lambda c: cnt[c])
print("=" * 66)
print("可疑字（全语料出现 ≤%d 次）：%d 个" % (TH, len(rare)))
print("→ 你只需看**这些字里有没有不像词的**。有就告诉我。")
print("=" * 66)
for c in rare:
    f, i, ln = where.get(c, ("", 0, ""))
    print("  %s  U+%04X  ×%d   [%s L%d]" % (c, ord(c), cnt[c], f, i))
    print("        %s" % ln)
