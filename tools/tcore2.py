#!/usr/bin/env python3
import sys as _sys
try:
    if hasattr(_sys.stdout, "reconfigure"):
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
# -*- coding: utf-8 -*-
"""T-CORE-2 禁止端点扫描（V0.4.1）。

用法: python tools/tcore2.py routes.json

V0.4.1 修:
  - V0.4 用集合成员判断是错的（/leaderboard 永不命中）——本版改回词边界正则
  - 词边界匹配（\b），不再子串误伤 /topics /stoptime /crank
  - 空清单 / 缺键 / 不存在 / BOM => INCOMPLETE 或容错
  - 声明 routes.json 须由框架自动生成（CORE-001-047）
"""
import io
import json
import os
import re
import sys

BAD = ["score", "grade", "level", "percentile", "rank", "composite",
       "weight", "points", "badge", "title", "tier", "tiering",
       "grading", "rating", "rating_score", "completiondegree",
       "leaderboard", "sort_by_user", "order_by_score",
        # V0.6 补：跨人排序的常见端点名
        "top", "topn", "top_n", "most", "popular"]
# V0.6 修正：原先 \b(词)\b 会漏掉全部派生形——
#   \brank\b 不匹配 ranking / ranked；\btier\b 不匹配 tiers；
#   且 tiering 永远不可能命中（tier 先匹配，后面还剩 ing）。
# 改为：词后允许常见派生后缀（s/es/ed/ing/ings/ly）。
SUFFIX = r"(?:s|es|ed|ing|ings|ly)?"
# V0.6 护栏：词后紧跟连字符者视为**复合词**（如 levels-of-detail、tier-one），
#   不算位阶字段名，避免误伤。（实测：/levels-of-detail 曾误报 levels）
PAT = re.compile(r"\b(" + "|".join(re.escape(k) for k in BAD) + r")"
                 + SUFFIX + r"\b(?!-)", re.I)
# V0.6 补：CORE-001-015 要求词表至少含中文等价词（tcore1 早已有，tcore2 缺）
BAD_CJK = ["\u6210\u578b\u671f", "\u5b8c\u6210\u5ea6"]
CJK_PAT = re.compile("|".join(BAD_CJK))


def main(p):
    print("[COVERAGE] routes file : %s" % p)
    if not os.path.exists(p):
        print("[INCOMPLETE] 清单不存在。未扫 != 通过。")
        return 2
    try:
        d = json.loads(io.open(p, encoding="utf-8-sig").read())
    except Exception as ex:
        print("[INCOMPLETE] 无法解析: %s" % ex)
        return 2
    routes = d.get("routes")
    if not isinstance(routes, list):
        print("[INCOMPLETE] 无 routes 键。须显式列出全部端点。")
        return 2
    if len(routes) == 0:
        print("[INCOMPLETE] routes 为空。空清单 == 未扫, 不是通过。")
        return 2
    hits = []
    for r in routes:
        blob = "%s %s %s %s" % (r.get("method", ""), r.get("path", ""),
                                r.get("returns", ""), r.get("name", ""))
        m = PAT.search(blob) or CJK_PAT.search(blob)
        if m:
            hits.append((r.get("method"), r.get("path"), m.group(0)))
    for m, pa, b in hits:
        print("[HIT] %s %s  (%s)" % (m, pa, b))
    print("[%s] %d hits" % ("PASS" if not hits else "FAIL", len(hits)))
    print("[COVERAGE] endpoints declared: %d" % len(routes))
    print("[COVERAGE] 本清单必须由框架自动生成 (CORE-001-047);")
    print("[COVERAGE] 手写清单 == 自证, 不作验收依据。")
    print("[NOTE] 词表 %d 词 + %d 中文词, 全部词边界匹配。"
          % (len(BAD), len(BAD_CJK)))
    # V0.6 补：CORE-001-049 要求词表公开**并**声明未收录词不构成证据
    print("[NOTE] 未收录词**不构成合规证据**；语义级合规须人工复核 (050)。")
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "routes.json"))
