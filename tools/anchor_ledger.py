# -*- coding: utf-8 -*-
r"""anchor_ledger.py —— **锚台账读取器**（判据统一口径的唯一入口）。

规则（治"三套前缀豁免各说各话"）：
  · **台账内**的 64 位值 ⇒ **合法**（无论是现行锚还是历史锚）；
  · **台账外**的 64 位值 ⇒ **非法**（除非等于"正在生成的新锚"）；
  · 台账显式列出的 `illegal` ⇒ **永远非法**（不对应任何字节）。

用法（作库）：
    import anchor_ledger as AL
    AL.load()                      # 从默认位置读台账
    AL.is_legal(value)             # True/False
    AL.kind(value)                 # 'current' | 'historical' | 'illegal' | 'unknown'
"""
import hashlib
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PKGD = "D:/PHAROS" + "\u5de5\u4f5c\u533a" + "/\u4ea4\u4ed8\u5305"
LEDGER = os.path.join(PKGD, "_anchor_ledger.json")
_LEGAL = None
_ILLEGAL = {}
_CURRENT = None


def load(ledger_path=LEDGER, spec_path=None):
    """读台账；若给了 `spec_path`，把它的 sha256 也视为**现行锚**（合法）。"""
    global _LEGAL, _ILLEGAL, _CURRENT
    _LEGAL = set()
    _ILLEGAL = {}
    _CURRENT = None
    if os.path.isfile(ledger_path):
        j = json.loads(io.open(ledger_path, encoding="utf-8").read())
        for e in j.get("entries", []):
            _LEGAL.add(e.get("specHash"))
        _ILLEGAL = dict(j.get("illegal", {}))
        _CURRENT = j.get("current")
    if spec_path and os.path.isfile(spec_path):
        raw = io.open(spec_path, "rb").read()
        h = hashlib.sha256(raw).hexdigest()
        _LEGAL.add(h)
        _CURRENT = h
    return _LEGAL


def set_current(value):
    global _CURRENT
    _CURRENT = value
    if _LEGAL is not None:
        _LEGAL.add(value)


def kind(value):
    """返回 'current' | 'historical' | 'illegal' | 'unknown'。"""
    if value is None:
        return "unknown"
    if value in _ILLEGAL:
        return "illegal"
    if _CURRENT and value == _CURRENT:
        return "current"
    if _LEGAL and value in _LEGAL:
        return "historical"
    return "unknown"


def is_legal(value):
    return kind(value) in ("current", "historical")


def stats():
    return {"legal": len(_LEGAL or ()), "illegal": len(_ILLEGAL), "current": _CURRENT}


if __name__ == "__main__":
    load()
    print("[LEDGER-READER] %s" % stats())
    for v in sys.argv[1:]:
        print("  %s  %s" % (v[:20], kind(v)))
