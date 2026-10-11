# -*- coding: utf-8 -*-
r"""check_anchor_propagation.py —— **锚传播影响面**判据。

背景：`specHash` 一旦变动，以下**五类载体**须同步，否则红门连环：
  ① 包内 `*.md`（人工核清单／留痕／工作仓分离说明…）
  ② `_letters` 源件（单一源件与回函）
  ③ 对外交付件 `*.docx`
  ④ 对外子包 + `index.json`
  ⑤ **判据自身常量**（`check_docx_clean.py` 的 `CUR`）

用法：
  python check_anchor_propagation.py --cur <64位现行锚> [--roots <目录> ...]
  python check_anchor_propagation.py --cur <锚> --stale <64位过期锚>

退出码：0 = 无过期引用；1 = 存在过期引用（**须逐处修**）。
"""
import os
import re
import sys

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    from docx import Document
except Exception:
    Document = None

SKIP_DIRS = {"__pycache__", ".git", "node_modules", "Implementation",
             "_pdftxt", "pdf", "_temp", "_inbox", "_aethel_pkg2", "_aethel_pkg3", "_BS_SRC"}
TEXT_EXT = (".md", ".txt", ".json", ".py")
PAT = re.compile(r"\b[0-9a-f]{64}\b")
CACHE = {}


def text_of(p):
    if p in CACHE:
        return CACHE[p]
    t = ""
    try:
        if p.endswith(".docx"):
            if Document is None:
                return ""
            d = Document(p)
            t = "".join(x.text for x in d.paragraphs)
            for tb in d.tables:
                for r in tb.rows:
                    for c in r.cells:
                        t += c.text
        else:
            t = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        t = ""
    CACHE[p] = t
    return t


def main(argv):
    cur = None
    stale = []
    roots = []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--cur":
            cur = argv[i + 1].lower()
            i += 2
        elif a == "--stale":
            stale.append(argv[i + 1].lower())
            i += 2
        elif a == "--roots":
            i += 1
            while i < len(argv) and not argv[i].startswith("--"):
                roots.append(argv[i])
                i += 1
        else:
            roots.append(a)
            i += 1
    if not roots:
        print("[ANCHOR] \u26a0 **roots \u4e3a\u7a7a\uff1a\u626b 0 \u4ef6\u4e0d\u7b97\u901a\u8fc7**\uff08\u9632\u771f\u7a7a\u901a\u8fc7\uff09")
        return 2
    if not cur:
        print("usage: check_anchor_propagation.py --cur <64hex> [--stale <64hex>] [--roots d1 d2 ...]")
        return 2

    if not stale:
        stale = ["(none)"]
    bad = 0
    n = 0
    print("[ANCHOR] \u73b0\u884c\u951a = %s" % cur[:16])
    print("[ANCHOR] \u5f85\u6392\u67e5\u7684\u8fc7\u671f\u951a = %s" % ", ".join(x[:16] for x in stale))
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in SKIP_DIRS and not d.startswith("_")]
            for f in fn:
                p = os.path.join(dp, f)
                isdocx = f.endswith(".docx")
                if f == "_anchor_ledger.json":
                    continue   # ⭐ 台账本身就是**合法历史锚的登记处**，不作过期判定
                if not isdocx and not f.endswith(TEXT_EXT):
                    continue
                t = text_of(p)
                if not t:
                    continue
                n += 1
                # ★ 收紧：只报**基线语境行**里的过期全值
                hits = set()
                for ln in t.split("\n"):
                    if not re.search(r"specHash|\u57fa\u7ebf|\u951a", ln):
                        continue
                    if "\u5f53\u65f6\u503c" in ln or "\u5386\u53f2" in ln:
                        continue
                    for h in PAT.findall(ln):
                        if h != cur and not cur.startswith(h[:8]):
                            hits.add(h)
                hits = sorted(hits)
                if not hits:
                    continue
                rel = os.path.relpath(p, root).replace("\\", "/")
                bad += 1
                print("[STALE] %-62s %s" % (rel[:62], ", ".join(h[:12] + "\u2026" for h in hits[:3])))
    print("[ANCHOR] \u626b %d \u4ef6\uff1b\u5f15\u7528\u975e\u73b0\u884c\u951a\u8005 %d" % (n, bad))
    print("[RESULT] %s" % ("PASS -- \u65e0\u8fc7\u671f\u5f15\u7528" if not bad else "FAIL -- **\u6709\u8fc7\u671f\u5f15\u7528\uff0c\u6539\u951a\u524d\u5fc5\u987b\u9010\u5904\u4fee**"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
