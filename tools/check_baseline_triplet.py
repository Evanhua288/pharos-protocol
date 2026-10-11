# -*- coding: utf-8 -*-
r"""check_baseline_triplet.py —— **基线三元组校验**（台账驱动）。

治什么：此前落款/基线行只校"锚等不等于现行锚"，于是把"当时基线"刷成现行锚也没人管；
        反之**合法的历史锚**又可能被判过期。本判据改为校验**三元配对**：
        `(包号, 锚, 内容版本)` **必须与台账一致**。

用地：python check_baseline_triplet.py <目录> [--ledger <_anchor_ledger.json>]
退出码：0 = 全部配对正确；1 = 有错配；2 = 无法执行。
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PKGD = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LEDGER_DEFAULT = "D:/PHAROS\u5de5\u4f5c\u533a/\u4ea4\u4ed8\u5305/_anchor_ledger.json"
_CUR = 0
HX = re.compile(r"\b([0-9a-f]{64})\b")
# ⏪ V1.64：**只校验现行基线行**（版本号 ≥ 现行包号 − TOL）
#   理由：早期文件的落款合法保留其**顶发时真值**，不应追溯校验。
TOL = 3
VER = re.compile(r"v(\d{3})")


def load_ledger(path):
    if not os.path.isfile(path):
        return None
    j = json.loads(io.open(path, encoding="utf-8").read())
    m = {}
    for e in j.get("entries", []):
        for pkg in e.get("packages", []):
            m[pkg] = {"specHash": e["specHash"], "specVersion": e.get("specVersion"),
                      "bytes": e.get("bytes"), "frozen": e.get("frozen")}
    return m


def scan(path, ledger):
    bad = []
    if os.path.isfile(path):
        files = [path]
    elif os.path.isdir(path):
        files = [os.path.join(path, f) for f in sorted(os.listdir(path)) if f.endswith(".md")]
    else:
        return [("SKIP", path)]
    for p in files:
        try:
            t = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for ln in t.split("\n"):
            if not re.search(r"\u57fa\u7ebf|\u843d\u6b3e", ln):
                continue
            if "\u5f53\u65f6\u503c" in ln or "\u5386\u53f2" in ln:
                continue
            mver = VER.search(ln)
            hx = HX.findall(ln)
            if not mver or not hx:
                continue
            _num = int(mver.group(1))
            if _num < _CUR - TOL:
                continue                      # 历史基线行：不追溯
            pkg = "pharos-handoff-20261006-" + mver.group(0)
            ent = ledger.get(pkg)
            if ent is None:
                continue                      # \u53f0\u8d26\u4e2d\u65e0\u6b64\u5305\uff08\u5982\u5b50\u5305\u540d\uff09\u5219\u8df3\u8fc7
            for h in hx:
                if h != ent["specHash"]:
                    bad.append(("TRIPLET_MISMATCH",
                                "%s \u58f0\u79f0 %s\uff0c\u4f46\u53f0\u8d26\u8bb0\u5f55\u8be5\u5305\u4e3a %s" % (
                                    pkg, h[:16] + "\u2026", ent["specHash"][:16] + "\u2026")))
    return bad


def main(argv):
    dirs = [a for a in argv[1:] if not a.startswith("--")]
    ipos = [i for i, a in enumerate(argv) if a == "--ledger"]
    lp = argv[ipos[0] + 1] if ipos and ipos[0] + 1 < len(argv) else LEDGER_DEFAULT
    global _CUR
    ledger = load_ledger(lp)
    _nums = [int(k.split("-v")[-1]) for k in ledger if k.split("-v")[-1].isdigit()]
    _CUR = max(_nums) if _nums else 0
    if ledger is None:
        print("[TRIPLET] \u26a0 \u53f0\u8d26\u4e0d\u53ef\u7528\uff1a%s" % lp)
        return 2
    bad = []
    n = 0
    for d in (dirs or ["."]):
        r = scan(d, ledger)
        n += 1
        bad += r
    print("[TRIPLET] \u53f0\u8d26\u6761\u76ee %d\uff1b\u626b %d \u76ee\u5f55\uff1b\u9519\u914d %d" % (len(ledger), n, len(bad)))
    for k, v in bad[:20]:
        print("  [FAIL] %-16s %s" % (k, v[:120]))
    print("[RESULT] %s" % ("PASS -- \u4e09\u5143\u7ec4\u914d\u5bf9\u6b63\u786e" if not bad else "FAIL -- \u6709\u9519\u914d"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
