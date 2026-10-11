# -*- coding: utf-8 -*-
import sys as _sys
try:
    if hasattr(_sys.stdout, "reconfigure"):
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
r"""layers 互斥扫描（v2，正确版）：
   同时对英文对象名与中文对象名扫描；只用二进制判定，避免编码假象。
"""
import os
import re
from collections import defaultdict

L = "D:/PHAROS" + "\u5de5\u4f5c\u533a" + "/\u4ea4\u4ed8\u5305/pharos-core/spec/layers"
files = [f for f in sorted(os.listdir(L)) if f.endswith(".md") and "\u4ef6\u540d\u6e05\u5355" not in f]

PAT = {
    "LedgerEntry": [b"LedgerEntry", "\u8d26\u672c\u6761\u76ee".encode()],
    "Settlement": [b"Settlement", "\u7ed3\u7b97".encode()],
    "Attestation": [b"Attestation", "\u5c65\u7ea6".encode()],
    "Identity": [b"Identity", "\u8eab\u4efd".encode()],
    "Node": [b"Node", "\u8282\u70b9".encode()],
    "sync.request": [b"sync.request", "\u5bf9\u8d26\u8bf7\u6c42".encode()],
    "sync.response": [b"sync.response", "\u5bf9\u8d26\u54cd\u5e94".encode()],
    "sync.dispute": [b"sync.dispute", "\u5206\u6b67".encode()],
    "features": [b"features", "\u80fd\u529b\u58f0\u660e".encode()],
}
hits = defaultdict(list)
for f in files:
    b = open(os.path.join(L, f), "rb").read()
    for k, ps in PAT.items():
        if any(p in b for p in ps):
            hits[k].append(f)

print("  \u5c42\u4ef6\u6570\uff1a%d\uff08\u5df2\u6392\u9664\u4ef6\u540d\u6e05\u5355\uff09" % len(files))
print()
print("  \u5bf9\u8c61 \u2192 \u547d\u4e2d\u5c42\u4ef6\u6570\uff08\u82f1\u6587\u540d \u6216 \u4e2d\u6587\u540d \u4efb\u4e00\uff09")
for k in PAT:
    v = hits.get(k, [])
    print("    %-16s %2d" % (k, len(v)))
print()
multi = {k: v for k, v in hits.items() if len(v) >= 2}
print("  \u22652 \u4ef6\u7684\uff1a%d \u7ec4" % len(multi))
for k, v in sorted(multi.items(), key=lambda kv: -len(kv[1])):
    print("    %-16s %2d \u4ef6" % (k, len(v)))
print()
print("  0 \u4ef6\u7684\uff1a%s" % "\u3001".join(k for k in PAT if not hits.get(k)))
