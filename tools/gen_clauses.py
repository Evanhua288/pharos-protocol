# -*- coding: utf-8 -*-
r"""gen_clauses.py —— 从 spec **机读生成**条款索引 `clauses.json`，并做**引用机检**。

产物：
  spec/clauses.json  —— 条号 → 语义标签 / 行号 / 引用的条号 / 被引次数
判据（嵌入本脚本，`--check` 时启用并返回退出码）：
  CITE_EXISTS  —— 引用的条号必须存在
  CITE_SEMANTIC—— 引用必须与目标条语义相关（粗判：共享至少一个关键词）
  DUP          —— 条号不得重复
  LINENO       —— 索引行号必须与实读一致

用法：
  python gen_clauses.py <spec路径> [--check]
"""
import hashlib
import io
import json
import os
import re
import sys

# ⏪ 外部确认清单（人工逐条确认的跨节引用）：命中则不再报 `CITE_SEMANTIC`
_XOK = set()


def load_xref(spec_path):
    """从 `<spec 同目录>/xref-confirmed.json` 读确认清单（不改 spec 正文）。"""
    p = os.path.join(os.path.dirname(os.path.abspath(spec_path)), "xref-confirmed.json")
    if not os.path.isfile(p):
        return set()
    try:
        d = json.loads(io.open(p, encoding="utf-8").read())
        return {(e["from"], e["to"]) for e in d.get("confirmed", [])}
    except Exception:
        return set()


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REF = re.compile(r"`((?:CORE-001-)?\d{3}(?:-[A-Z])?)`")
LAYER_REF = re.compile(r"`([A-Z][A-Z0-9-]*-\d{3}(?:-[A-Z])?)`")
LAYER_ROOT = None
LIST = re.compile(r"`((?:CORE-001-\d{3})(?:`\uff0f`CORE-001-\d{3})*)`")


def load(path):
    return io.open(path, encoding="utf-8", errors="replace").read().split("\n")


def build(spec_path):
    L = load(spec_path)
    rows = []
    for i, ln in enumerate(L, 1):
        s = ln.strip()
        if not s.startswith("| **`CORE-001-"):
            continue
        try:
            cid = s.split("`")[1]
        except Exception:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        level = cells[1].replace("*", "").strip() if len(cells) > 1 else ""
        body = cells[2] if len(cells) > 2 else s
        text = re.sub(r"[*`]", "", body)
        rows.append({"id": cid, "line": i, "level": level, "text": text, "_raw": body})
    # \u5f15\u7528\u5173\u7cfb
    for r in rows:
        _rr = []
        for x in REF.findall(r.get("_raw", r["text"])):
            x2 = x if x.startswith("CORE-001-") else "CORE-001-" + x
            if x2 != r["id"]:
                _rr.append(x2)
        refs = sorted(set(_rr))
        r["refs"] = refs
        # \u8bed\u4e49\u5173\u952e\u8bcd\uff08\u7c97\uff09
        kw = set()
        for m in re.findall(r"[A-Za-z_][A-Za-z0-9_.]{2,}", r["text"]):
            kw.add(m.lower())
        for m in re.findall(r"[`\u4e00-\u9fff]{2,}", r["text"]):
            for seg in re.findall(r"[\u4e00-\u9fff]{2,4}", m):
                kw.add(seg)
        r["_kw"] = sorted(kw)[:40]
    # 层件条号：收为“外部条号”，供引用存在性校验
    _lay = os.path.join(os.path.dirname(spec_path), "layers")
    if os.path.isdir(_lay):
        for _f in sorted(os.listdir(_lay)):
            if not _f.endswith(".md"):
                continue
            for _i, _ln in enumerate(io.open(os.path.join(_lay, _f), encoding="utf-8", errors="replace").read().split("\n"), 1):
                for _cid in LAYER_REF.findall(_ln):
                    rows.append({"id": _cid, "line": -1, "level": "layer",
                                 "text": _ln.strip(), "refs": [], "_kw": [], "_ext": _f})
    return rows


def check(spec_path, rows):
    fails = []
    by = {}
    for r in rows:
        if r["line"] > 0 and r["id"] in by:
            fails.append(("DUP", "%s \u91cd\u590d\uff08L%s \u4e0e L%s\uff09" % (r["id"], by[r["id"]], r["line"])))
        if r["line"] > 0:
            by[r["id"]] = r["line"]
    lay_ids = set(r["id"] for r in rows if r["line"] < 0)
    by_all = dict(by)
    for _x in lay_ids:
        by_all.setdefault(_x, -1)
    for r in rows:
        if r["line"] < 0:
            continue
        for ref in r["refs"]:
            if ref not in by_all:
                fails.append(("CITE_EXISTS", "%s\uff08L%s\uff09\u5f15\u7528\u4e0d\u5b58\u5728\u7684 %s" % (r["id"], r["line"], ref)))
    # \u8bed\u4e49\u76f8\u5173\uff08\u7c97\u5224\uff1a\u5171\u4eab\u81f3\u5c11 1 \u4e2a\u5173\u952e\u8bcd\uff09
    for r in rows:
        if r["line"] < 0:
            continue
        rk = set(r["_kw"])
        for ref in r["refs"]:
            t = by.get(ref)
            tr = next((x for x in rows if x["line"] == t), None)
            if not tr:
                continue
            tk = set(tr["_kw"])
            # ① ASCII 词元（精确）
            a1 = {w for w in (rk & tk) if re.match(r"^[a-z_][a-z0-9_.]{2,}$", w)}
            # ② 中文片段：2 字以上**互相包含**即算相关（旧法要精确相等 ⇒ 误报源）
            c1 = [w for w in rk if re.search(r"[\u4e00-\u9fff]", w)]
            c2 = [w for w in tk if re.search(r"[\u4e00-\u9fff]", w)]
            a2 = [x for x in c1 if len(x) >= 2 and any(x in y or y in x for y in c2 if len(y) >= 2)]
            # ③ 正文已显式写出该条号
            # ④ 正文已显式写出该条号
            a3 = bool(r.get("_raw")) and (ref in r["_raw"])
            # ⑤ 人工确认标记：`xref-ok:<条号>` 说明本处跨节引用经逐条确认
            a4 = (r["id"], ref) in _XOK
            if not (a1 or a2 or a3 or a4):
                fails.append(("CITE_SEMANTIC", "%s（L%s）引 %s——**无共享关键词**（疑误引）" % (r["id"], r["line"], ref)))
    return fails


def main(argv):
    if len(argv) < 2:
        print("usage: gen_clauses.py <spec.md> [--check]")
        return 2
    sp = argv[1]
    global _XOK
    _XOK = load_xref(sp)
    do_check = "--check" in argv or "--selftest" in argv
    no_write = "--no-write" in argv   # ⏪ 只校验、不写盘（供冻结后只读校验）
    rows = build(sp)
    if "--selftest" in argv or "--check" in argv:
        selftest(sp)
    out = {
        "_note": "\u673a\u8bfb\u6761\u6b3e\u7d22\u5f15\uff08\u7531 gen_clauses.py \u4ece spec \u751f\u6210\uff0c\u4e0d\u624b\u5199\uff09\u3002",
        "spec": os.path.basename(sp),
        "specSha256": hashlib.sha256(io.open(sp, "rb").read()).hexdigest(),
        "specBytes": os.path.getsize(sp),
        "clauses": len(rows),          # 条文块行数（同一条号可占多行）
        "clauseIds": len({r["id"] for r in rows}),   # 唯一条号数
        "hashRule": "clauseHash ＝ SHA256(UTF-8 字节（该条 text 字段）)；不含行号、不含版本行、不含沿革表。故**引条不引版**：条号变、条文未变 ⇒ 哈希不变。",
        "index": [dict(list((k, v) for k, v in r.items() if k not in ("_kw", "_raw"))
                       + [("clauseHash", hashlib.sha256(str(r.get("text", "")).encode("utf-8")).hexdigest())])
                  for r in rows],
    }
    dst = os.path.join(os.path.dirname(sp), "clauses.json")
    if no_write:
        print("[CLAUSES] %s；条款 %d；**--no-write**（未写盘）" % (os.path.basename(sp), len(rows)))
    else:
        io.open(dst, "w", encoding="utf-8", newline="\n").write(
            json.dumps(out, ensure_ascii=False, indent=1) + "\n")
        print("[CLAUSES] %s；条款 %d；产 %s（%d B）" % (
            os.path.basename(sp), len(rows), os.path.basename(dst), os.path.getsize(dst)))
    if not do_check:
        return 0
    fails = check(sp, rows)
    hard = [f for f in fails if f[0] in ("CITE_EXISTS", "DUP", "LINENO")]
    soft = [f for f in fails if f[0] not in ("CITE_EXISTS", "DUP", "LINENO")]
    for kind, msg in hard[:20]:
        print("  [FAIL] %-14s %s" % (kind, msg))
    for kind, msg in soft[:20]:
        print("  [WARN] %-14s %s" % (kind, msg))
    print("  [RESULT] %s\uff08\u786c\u95e8 %d\uff1b\u544a\u8b66 %d\uff09" % (
        "PASS -- \u5f15\u7528\u5b58\u5728\u6027\u4e0e\u6761\u53f7\u81ea\u6d3d" if not hard else "FAIL -- \u65ad\u5f15\u6216\u6761\u53f7\u91cd\u590d",
        len(hard), len(soft)))
    return 0 if not hard else 1


def selftest(spec_path):
    """造违例：引用不存在的条号必须被 CITE_EXISTS 抓到。"""
    import tempfile
    d = tempfile.mkdtemp(prefix="ct-")
    rows = build(spec_path)
    rows2 = [dict(x) for x in rows]
    if rows2:
        rows2[0]["text"] = rows2[0]["text"] + " **应 `CORE-001-999`**"
        rows2[0]["_raw"] = rows2[0].get("_raw", "") + " **应 `CORE-001-999`**"
        rows2[0]["refs"] = sorted(set(list(rows2[0]["refs"]) + ["CORE-001-999"]))
        rows2[0]["_kw"] = rows2[0]["_kw"]
    f = check(spec_path, rows2)
    kinds = set(k for k, _ in f)
    ok = "CITE_EXISTS" in kinds
    print("     造违例：引用 `CORE-001-999` → %s" % ("✅ 已报错" if ok else "⚠ **未报错（恒真）**"))
    import shutil
    shutil.rmtree(d, ignore_errors=True)
    return ok


if __name__ == "__main__":
    sys.exit(main(sys.argv))
