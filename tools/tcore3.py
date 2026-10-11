#!/usr/bin/env python3
import sys as _sys
try:
    if hasattr(_sys.stdout, "reconfigure"):
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
# -*- coding: utf-8 -*-
"""T-CORE-3 置空对照实验（V0.4）。

用法: python tools/tcore3.py entries.json <engine_module>

V0.4 修:
  - blank_grades 改递归 (嵌套 meta.score / SCORE_UPPER / awareness 不再免检)
  - 须由使用方提供 engine_module, 不得内置常数结算
  - settle() 结果不可为常数; 自动检测常数实现并 FAIL
"""
import copy
import importlib.util
import io
import json
import os
import sys

GRADE_KEYS = ("score", "grade", "level", "tier", "rank", "percentile",
              "rating", "completiondegree", "awareness")


def load(p):
    return json.loads(io.open(p, encoding="utf-8-sig").read())


import re as _re

# V0.6 修：原先用子串匹配（`g in kl`），会误伤——如 `crank` 含 `rank`。
#   tcore1/tcore2 早已加词边界，唯此处未加，三个工具口径不一致。
_GRADE_PAT = _re.compile(r"\b(" + "|".join(_re.escape(g) for g in GRADE_KEYS) + r")\b", _re.I)


def is_grade_key(k):
    return bool(_GRADE_PAT.search(str(k)))


def blank_deep(o):
    if isinstance(o, dict):
        return {k: (None if is_grade_key(k) else blank_deep(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [blank_deep(v) for v in o]
    return o


def main(args):
    if len(args) < 1:
        print("[INCOMPLETE] 需 entries.json")
        return 2
    raw = load(args[0])
    arr = raw if isinstance(raw, list) else [raw]

    if len(args) >= 2:
        # V0.6 修：支持按**文件路径**加载（原先只支持同目录裸模块名，
        #   传 /tmp/eng.py 会报 No module named）。
        spec_src = args[1]
        if os.path.isfile(spec_src):
            spec = importlib.util.spec_from_file_location("_pharos_engine", spec_src)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as ex:
                print("[INCOMPLETE] 引擎执行失败 %s: %s" % (spec_src, ex))
                return 2
        else:
            sys.path.insert(0, ".")
            try:
                mod = __import__(spec_src.replace(".py", ""))
            except Exception as ex:
                print("[INCOMPLETE] 无法加载结算引擎 %s: %s" % (spec_src, ex))
                return 2
        if not hasattr(mod, "settle"):
            print("[INCOMPLETE] 引擎未导出 settle()。")
            return 2
        settle = mod.settle
    else:
        print("[INCOMPLETE] 需提供结算引擎模块。")
        print("[INCOMPLETE] 不得内置常数结算 (V0.4 禁止)。")
        print("[INCOMPLETE] FIN-100 6 是空标题, 引擎接口须由实现方自拟并申报。")
        return 2

    a = settle(copy.deepcopy(arr))
    b = settle(blank_deep(copy.deepcopy(arr)))
    sa, sb = json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True)

    # V0.6 常数检测（强化）：原先只加一个 {"__probe__": 1} 探针——
    #   防御式引擎会**跳过**不认识的元素，于是 sa == sc，**非常数实现被误判为常数**。
    #   改为两个**实质不同**的输入对照；只有当引擎对二者完全同答时才判常数。
    probe_a = settle(copy.deepcopy(arr))
    probe_b = settle([])
    probe_c = settle(copy.deepcopy(arr) + [{"amount": "1234567"}])
    const = (json.dumps(probe_a, sort_keys=True) == json.dumps(probe_b, sort_keys=True)
             == json.dumps(probe_c, sort_keys=True))
    if const:
        print("[FAIL] settle() 对三个实质不同输入返回同一结果 -> 常数实现, 本实验无效")
        return 1

    ok = (sa == sb)
    print("[%s] settle(orig) == settle(blanked)" % ("PASS" if ok else "FAIL"))
    print("[COVERAGE] blank_deep 为递归置空; 嵌套等级字段已覆盖")
    print("[COVERAGE] 结算引擎由使用方提供: %s" % args[1])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
