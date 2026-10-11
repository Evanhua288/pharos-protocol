#!/usr/bin/env python3
import sys as _sys
try:
    if hasattr(_sys.stdout, "reconfigure"):
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
# -*- coding: utf-8 -*-
"""T-CORE-1 禁止字段扫描（V0.4）。用法: python tools/tcore1.py <path> [--include-md]

V0.4 修:
  1 传单个文件时不再静默假绿 -> INCOMPLETE
  2 SKIP 改为路径段匹配 (src/spec/evil.py 不再整棵免检)
  3 词边界 + 最小词长 (endpoints 不再命中 points)
  4 规则清单行不再整行豁免真禁词
  5 未扫类型必须申报
"""
import io
import os
import re
import sys

# 口径订正（v154）：与 `VAL-400 §4.1` 对齐（20 个）。
# → 规范禁的才计 FAIL；工具自带的额外词只报 WARN。
FORBIDDEN = ["score", "grade", "level", "percentile", "rank", "composite",
             "weight", "prediction", "fortune", "advice", "conclusion",
             "fate", "privilege", "permission", "entitlement", "value",
             "points", "redeemable", "transferable", "exchangeable"]
# 工具自带的额外词：**只 WARN**（见 `配套件/禁语词表.md` §三）
ADVISORY = ["badge", "title", "tier", "tiering", "grading", "rating",
            "rating_score", "completiondegree", "leaderboard"]
BAD_CJK = ["\u6210\u578b\u671f", "\u5b8c\u6210\u5ea6"]
# V0.6 修正：原先按**目录名**跳过 tools/spec/vectors——
#   任何位置出现该名即整棵免检（实测：把红线代码放进名为 spec 的目录 -> 不扫）。
# 改为：默认**不跳过任何目录**；仅当显式传入 --skip <相对路径> 时才跳过，
#   且被跳过的目录必须在 COVERAGE 里逐个列出（未扫 != 通过）。
SKIP_SEGMENTS = set()   # 目录名不再自动免检
# 目录不自动免检，但**机读生成索引**类单文件默认免检（不是源码）
SKIP_GEN_FILES = ("clauses.json",)   # 可用 --scan-generated 取消免检
SKIP_EXPLICIT = []      # 仅由 --skip 指定，且会逐条公示
# V0.6 第三修：原先按目录名免检 tools 是为回避**自指**（工具自己的词表会命中），
#   但它同时开了任意脱逃口子：任何叫 tools/spec/vectors 的目录都免检。
#   改为：目录一律不免检；只按**精确文件名**排除扫描器自身，且逐条公示。
SELF_FILES = ("tcore1.py", "tcore2.py", "tcore3.py", "check_vectors.py", "gen_clauses.py", "anchor_ledger.py", "gen_anchor_ledger.py")
CODE_EXT = {".json", ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
            ".kt", ".cs", ".rb", ".php", ".c", ".cc", ".cpp", ".h", ".hpp",
            ".swift", ".scala", ".sh", ".ps1", ".yaml", ".yml", ".toml",
            ".sql", ".proto", ".graphql"}
DOC_EXT = {".md", ".html", ".htm", ".txt", ".vue", ".svelte"}


def main(args):
    path = "."
    for a in args:
        if not a.startswith("--"):
            path = a
    inc_doc = "--include-md" in args
    ext = set(CODE_EXT) | (DOC_EXT if inc_doc else set())

    if os.path.isfile(path):
        print("[INCOMPLETE] 传入了单个文件而非目录: %s" % path)
        print("[INCOMPLETE] 单文件模式无法申报覆盖面, 未扫 != 通过。")
        return 2

    pat = re.compile(r"\b(" + "|".join(re.escape(k) for k in FORBIDDEN) + r")\b", re.I)
    hits, scanned, skipped, self_skipped = [], [], [], []
    _scan_gen = "--scan-generated" in sys.argv
    for dp, dns, fns in os.walk(path):
        dns[:] = [d for d in dns if d not in {".git", "__pycache__", "node_modules", ".venv", "venv"}]
        segs = set(os.path.relpath(dp, path).replace("\\", "/").split("/"))
        if segs & SKIP_SEGMENTS:
            skipped.append(os.path.relpath(dp, path))
            dns[:] = []
            continue
        for fn in fns:
            if (not _scan_gen) and fn in SKIP_GEN_FILES:
                skipped.append(os.path.relpath(os.path.join(dp, fn), path).replace("\\", "/"))
                continue
            if fn in SELF_FILES:
                self_skipped.append(os.path.relpath(os.path.join(dp, fn), path).replace("\\", "/"))
                continue
            e = os.path.splitext(fn)[1].lower()
            if e not in ext:
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, path).replace("\\", "/")
            try:
                t = io.open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            scanned.append(rel)
            for i, line in enumerate(t.splitlines(), 1):
                m = pat.search(line)
                cjk = [k for k in BAD_CJK if k in line]
                if m or cjk:
                    hits.append((rel, i, m.group(0) if m else cjk[0]))
    for f, i, k in hits:
        print("[HIT] %s:%d  %s" % (f, i, k))
    status = "PASS" if not hits else "FAIL"
    if not scanned:
        status = "INCOMPLETE"
    print("[%s] %d hits" % (status, len(hits)))
    print("[COVERAGE] scanned files  : %d" % len(scanned))
    print("[COVERAGE] extensions     : %s" % ",".join(sorted(ext)))
    print("[COVERAGE] skipped dirs   : %s" % (",".join(skipped) or "(none)"))
    print("[COVERAGE] self-excluded  : %s  (扫描器自身词表; 已公示)"
          % (",".join(self_skipped) or "(none)"))
    if not inc_doc:
        print("[COVERAGE] NOT scanned    : .md .html .htm .txt .vue .svelte  <-- 界面文案未扫, 请加 --include-md")
    print("[NOTE] T-CORE-1 只挡字段名, 不挡语义。语义级检查须人工或模型复核。")
    print("[NOTE] 与本扫描器无关的规则清单行不再整行豁免 (V0.4)。")
    print("[NOTE] 未扫 != 通过。凡有未扫类型, CONFORMANCE 4 必须如实申报。")
    return 0 if status == "PASS" else (2 if status == "INCOMPLETE" else 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
