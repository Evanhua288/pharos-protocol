# -*- coding: utf-8 -*-
r"""gen_release_index.py —— **稳定锚登记表**（治"锚不稳"的根本）。

问题：`specHash = SHA-256(spec)` 把**元数据（沿革表 + 头部版本行）**一起纳入，
      于是"只补一条沿革说明"也会改锚 ⇒ 锚散布于约 142 个派生件，反复引发同步事故。

本器产 **`spec/release-index.json`**（**不改 `spec`，故不产生任何锚穿透**）：
  · `contentAnchor`  —— 对**规范正文**（**剔除沿革表与头部版本行**）现算的 SHA-256
  · `fileAnchor`     —— 对**整件**现算的 SHA-256（＝现行 `specHash`）
  · `specVersion`／`bytes`／`clauses`／`changelogRows`
用法：
  python gen_release_index.py <spec路径> [--write]
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

EV = re.compile(r"^\| \*\*`V1\.\d+`\*\*")          # 沿革表行
HDR = re.compile(r"\u5185\u5bb9\u7248\u672c")             # 头部版本行


def norm_lines(text):
    """返回 (正文行列表, 剔除的行号集合)。"""
    L = text.split("\n")
    drop = set()
    for i, ln in enumerate(L):
        if EV.match(ln) or HDR.search(ln):
            drop.add(i)
    body = [ln for i, ln in enumerate(L) if i not in drop]
    return body, drop, L


def _inject(text):
    """把一行元数据（沿革表行）插入沿革表内，
    **不改动正文行序** ⇒ 用于验证 contentAnchor 稳定。"""
    L = text.split("\n")
    for i, ln in enumerate(L):
        if EV.match(ln):
            L.insert(i, "| **`V1.99`** | **MINOR** | 造违例用元数据行 | — |")
            break
    else:
        L.append("| **`V1.99`** | **MINOR** | 造违例 | — |")
    return "\n".join(L)


def build(spec_path):
    raw = io.open(spec_path, "rb").read()
    text = raw.decode("utf-8", "replace")
    body, drop, L = norm_lines(text)
    canon = "\n".join(body).encode("utf-8")
    ver = ""
    m = re.search(r"\u5185\u5bb9\u7248\u672c[^\n]{0,30}?(V\d+\.\d+)", text)
    if m:
        ver = m.group(1)
    return {
        "_note": "\u7a33\u5b9a\u951a\u767b\u8bb0\u8868\uff08\u7531 gen_release_index.py \u751f\u6210\uff0c\u4e0d\u624b\u5199\uff09\u3002",
        "_rule": ("contentAnchor \u53ea\u8986\u76d6**\u89c4\u8303\u6b63\u6587**\uff08\u5254\u9664\u6cbf\u9769\u8868\u4e0e\u5934\u90e8\u7248\u672c\u884c\uff09\uff0c"
                  "\u6545\u201c\u53ea\u8865\u6cbf\u9769\u8bf4\u660e\u201d\u4e0d\u4f1a\u6539\u53d8\u5b83\uff1bfileAnchor \u7b49\u4e8e\u73b0\u884c specHash\u3002"),
        "specVersion": ver,
        "contentAnchor": hashlib.sha256(canon).hexdigest(),
        "fileAnchor": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "contentBytes": len(canon),
        "clauses": len([x for x in L if x.strip().startswith("| **`CORE-001-")]),
        "changelogRows": len([x for x in L if EV.match(x)]),
        "metadataLinesDropped": len(drop),
    }


def selftest(spec_path):
    """\u9020\u8fdd\u4f8b\uff1a\u5728\u6cbf\u9769\u8868\u672b\u5c3e\u52a0\u4e00\u884c\u5143\u6570\u636e\uff0c
    \u5219 fileAnchor \u5fc5\u53d8\u3001contentAnchor \u5fc5\u4e0d\u53d8\u3002"""
    import tempfile
    t = io.open(spec_path, encoding="utf-8", errors="replace").read()
    base = build(spec_path)
    d = tempfile.mkdtemp(prefix="ci-")
    p2 = os.path.join(d, "x.md")
    io.open(p2, "w", encoding="utf-8", newline="\n").write(
        _inject(t))
    aft = build(p2)
    import shutil
    shutil.rmtree(d, ignore_errors=True)
    ok1 = base["contentAnchor"] == aft["contentAnchor"]
    ok2 = base["fileAnchor"] != aft["fileAnchor"]
    print("     \u9020\u8fdd\u4f8b\uff1a\u4ec5\u6539\u5143\u6570\u636e \u21d2 contentAnchor \u4e0d\u53d8\uff1a%s\uff1bfileAnchor \u53d8\uff1a%s" % (ok1, ok2))
    return ok1 and ok2


def main(argv):
    if len(argv) < 2:
        print("usage: gen_release_index.py <spec.md> [--write]")
        return 2
    sp = argv[1]
    if "--selftest" in argv:
        sys.exit(0 if selftest(sp) else 1)
    info = build(sp)
    dst = os.path.join(os.path.dirname(sp), "release-index.json")
    if "--write" in argv:
        io.open(dst, "w", encoding="utf-8", newline="\n").write(
            json.dumps(info, ensure_ascii=False, indent=2) + "\n")
    print("[IDX] %s" % os.path.basename(sp))
    print("      \u5185\u5bb9\u951a\uff08\u7a33\u5b9a\uff09\uff1a%s" % info["contentAnchor"][:16])
    print("      \u6574\u4ef6\u951a\uff08\u73b0\u884c specHash\uff09\uff1a%s" % info["fileAnchor"][:16])
    print("      \u7248\u672c %s\uff1b%d B\uff08\u6b63\u6587 %d B\uff09\uff1b\u6761\u6b3e %d\uff1b\u6cbf\u9769\u884c %d\uff1b\u5254\u9664\u5143\u6570\u636e\u884c %d" % (
        info["specVersion"], info["bytes"], info["contentBytes"], info["clauses"],
        info["changelogRows"], info["metadataLinesDropped"]))
    if "--write" in argv:
        print("      \u5df2\u5199\uff1a%s" % os.path.basename(dst))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
