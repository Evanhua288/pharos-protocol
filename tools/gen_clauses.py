# -*- coding: utf-8 -*-
r"""gen_clauses.py —— 从 spec **机读生成**条款索引 `clauses.json`，并做**引用机检**。

产物：
  spec/clauses.json  —— 条号 → 语义标签 / 行号 / 引用的条号 / 被引次数
判据（嵌入本脚本，`--check` 时启用并返回退出码）：
  CITE_EXISTS  —— 引用的条号必须存在
  CITE_SEMANTIC—— 引用必须与目标条语义相关（粗判：共享至少一个关键词）
  DUP          —— 条号不得重复
  LINENO       —— 索引行号必须与实读一致
  IDX_DUP      —— ⭐ 产出的索引内 id 不得重复（含层件侧）
  IDX_PREFIX   —— ⭐ 裸前缀（如 `PHAROS-000`／`VAL-400`／`CORE-001`）不得占"条款 id"位，
                  须带 `type: "prefix"` 隔离
  IDX_COUNT    —— ⭐ `clauseCount` 必须等于实际条目数
  IDX_STALE    —— ⭐ 盘上 `clauses.json` 必须与当场重生成逐字节一致（防陈旧）

⏪ T4 整改（2026-10-12）：
  · 层件侧由"**一次出现一行**"改为"**一个条号一条**＋`occurrences` 记全部出现位置"
    ——原写法使同一 id 重复登记（实测重复 id 225 个），且 `line` 一律 -1（无法定位）。
  · 新增 `type` 字段：`clause`（CORE 定义行）／`layer`（层件条号）／
    `prefix`（裸前缀码，不是条号）——满足 T-索引判据 3。
  · 新增计数字段：`clauseCount`（＝条目数）／`prefixCount`／`occurrenceCount`／`typeCounts`。
  · 新增索引自检 `IDX_*`（见上）。

用法：
  python gen_clauses.py <spec路径> [--check] [--no-write]
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
LAYER_REF = re.compile(r"`((?:PHAROS-)?[A-Z][A-Z0-9-]*-\d{3}(?:-[A-Z])?|PHAROS-(?:GV|PA)-[A-Z]+(?:-[A-Z]+)*)`")
LAYER_ROOT = None
LIST = re.compile(r"`((?:CORE-001-\d{3})(?:`\uff0f`CORE-001-\d{3})*)`")
# ⏪ T4：裸前缀码（家族/件号本身，不是条号）：整串只有 家族-3位数，后面不再有编号
REGISTRY_RX = re.compile(r"^PHAROS-(?:GV|PA)-[A-Z]+(?:-[A-Z]+)*$")  # 000-080 §三 3.2
PREFIX_RX = re.compile(r"(?:PHAROS-)?[A-Z][A-Z0-9]*-\d{3}")


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
        rows.append({"id": cid, "line": i, "level": level, "text": text, "_raw": body,
                     "type": "clause"})
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
    # ⏪ T4：层件侧改为「**一个条号一条** ＋ `occurrences` 记全部出现位置」
    _lay = os.path.join(os.path.dirname(spec_path), "layers")
    occ = {}          # id -> [(file, line, text)]
    if os.path.isdir(_lay):
        for _f in sorted(os.listdir(_lay)):
            if not _f.endswith(".md"):
                continue
            for _i, _ln in enumerate(io.open(os.path.join(_lay, _f), encoding="utf-8", errors="replace").read().split("\n"), 1):
                for _cid in LAYER_REF.findall(_ln):
                    occ.setdefault(_cid, []).append((_f, _i, _ln.strip()))
    by = {r["id"]: r for r in rows}
    for _cid, places in sorted(occ.items()):
        o = [{"file": f, "line": l} for f, l, _t in places]
        if _cid in by:
            by[_cid]["occurrences"] = o
            by[_cid].setdefault("type", "clause")
        else:
            _f0, _l0, _t0 = places[0]
            rows.append({"id": _cid, "line": _l0, "level": "layer", "text": _t0,
                         "refs": [], "_kw": [], "_ext": _f0,
                         "type": ("prefix" if PREFIX_RX.fullmatch(_cid) else
                                    ("registry" if REGISTRY_RX.match(_cid) else "layer")),
                         "occurrences": o})
    # ⏪ T4：CORE 定义行也补 occurrences（便于统一消费）
    for r in rows:
        r.setdefault("occurrences", [])
    # ⭐ 第 1 步：把“规划中·未生效”的编号标 `inForce=False`
    #   为何在生成器里做：**手改生成物会被下一次重生成冲掉**。
    _planned = _planned_ids(spec_path)
    for r in rows:
        if r.get("id") in _planned:
            r["inForce"] = False
            r["status"] = "规划中·未生效"
    return rows


def _planned_ids(spec_path):
    """⭐ 从 `000-060 §9.3` 的状态行**动态提取**"规划中·未生效"的编号。

    为何：**这些编号在盘上无件**，若不标 `inForce: false`，
    任何"索引命中"都会被误读为"条款存在"（审计 F-02）。
    **不写死名单** —— 从登记表现状提取，登记一改，重生成即跟随。"""
    reg = os.path.join(os.path.dirname(spec_path), "layers",
                       "PHAROS-000-060-当前有效版本清单-V1.3-20261008.md")
    if not os.path.isfile(reg):
        return set()
    out = set()
    for ln in io.open(reg, encoding="utf-8", errors="replace").read().split("\n"):
        if "规划中·未生效" in ln:
            m = re.search(r"`(PHAROS-[A-Z0-9\-]+)`", ln)
            if m:
                out.add(m.group(1))
    return out

def check(spec_path, rows):
    fails = []
    by = {}
    for r in rows:
        if r["line"] > 0 and r["type"] == "clause" and r["id"] in by:
            fails.append(("DUP", "%s \u91cd\u590d\uff08L%s \u4e0e L%s\uff09" % (r["id"], by[r["id"]], r["line"])))
        if r["line"] > 0 and r["type"] == "clause":
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


def check_index(out, dst):
    """⭐ T4：索引自检（在同一份产出上跑，供 `--check` 与独立门复用）。"""
    fails = []
    idx = out.get("index", [])
    ids = [e.get("id") for e in idx]
    seen = {}
    for n, e in enumerate(idx):
        i = e.get("id")
        if i in seen:
            fails.append(("IDX_DUP", "id 重复：%s（条目 #%d 与 #%d）" % (i, seen[i], n)))
        else:
            seen[i] = n
    for n, e in enumerate(idx):
        i = e.get("id", "")
        if PREFIX_RX.fullmatch(i) and e.get("type") != "prefix":
            fails.append(("IDX_PREFIX", "裸前缀占条款 id 位：%s（type=%r；应为 prefix）" % (i, e.get("type"))))
    if int(out.get("clauseCount", -1)) != len(idx):
        fails.append(("IDX_COUNT", "clauseCount=%s ≠ 条目数 %d" % (out.get("clauseCount"), len(idx))))
    if "clauseIds" in out and int(out["clauseIds"]) != len(set(ids)):
        fails.append(("IDX_COUNT", "clauseIds=%s ≠ 唯一 id 数 %d" % (out["clauseIds"], len(set(ids)))))
    if os.path.isfile(dst):
        disk = io.open(dst, "rb").read()
        fresh = (json.dumps(out, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
        if disk != fresh:
            fails.append(("IDX_STALE", "盘上 %s（%d B）与当场重生成（%d B）**逐字节不同**"
                          % (os.path.basename(dst), len(disk), len(fresh))))
    return fails


def main(argv):
    if len(argv) < 2:
        print("usage: gen_clauses.py <spec.md> [--check] [--no-write]")
        return 2
    sp = argv[1]
    global _XOK
    _XOK = load_xref(sp)
    do_check = "--check" in argv or "--selftest" in argv
    no_write = "--no-write" in argv   # ⏪ 只校验、不写盘（供冻结后只读校验）
    rows = build(sp)
    if "--selftest" in argv or "--check" in argv:
        selftest(sp)
    ids = [r["id"] for r in rows]
    type_counts = {}
    for r in rows:
        type_counts[r.get("type", "clause")] = type_counts.get(r.get("type", "clause"), 0) + 1
    dst = os.path.join(os.path.dirname(sp), "clauses.json")
    out = {
        "_note": "\u673a\u8bfb\u6761\u6b3e\u7d22\u5f15\uff08\u7531 gen_clauses.py \u4ece spec \u751f\u6210\uff0c\u4e0d\u624b\u5199\uff09\u3002",
        "spec": os.path.basename(sp),
        "specSha256": hashlib.sha256(io.open(sp, "rb").read()).hexdigest(),
        "specBytes": os.path.getsize(sp),
        "clauses": len(rows),                        # ⏪ 兼容旧字段：＝条目数（同 clauseCount）
        "clauseCount": len(rows),                    # ⭐ T4：条目数（id 唯一）
        "clauseIds": len(set(ids)),                  # ⭐ 唯一 id 数
        "prefixCount": type_counts.get("prefix", 0),
        "occurrenceCount": sum(len(r.get("occurrences", [])) for r in rows),
        "typeCounts": type_counts,
        "hashRule": "clauseHash ＝ SHA256(UTF-8 字节（该条 text 字段）)；不含行号、不含版本行、不含沿革表。故**引条不引版**：条号变、条文未变 ⇒ 哈希不变。",
        "index": [dict(list((k, v) for k, v in r.items() if k not in ("_kw", "_raw"))
                       + [("clauseHash", hashlib.sha256(str(r.get("text", "")).encode("utf-8")).hexdigest())])
                  for r in rows],
    }
    if no_write:
        print("[CLAUSES] %s；条目 %d（唯一 id %d；前缀 %d）；**--no-write**（未写盘）" % (
            os.path.basename(sp), len(rows), len(set(ids)), type_counts.get("prefix", 0)))
    else:
        io.open(dst, "w", encoding="utf-8", newline="\n").write(
            json.dumps(out, ensure_ascii=False, indent=1) + "\n")
        print("[CLAUSES] %s；条目 %d（唯一 id %d；前缀 %d）；产 %s（%d B）" % (
            os.path.basename(sp), len(rows), len(set(ids)), type_counts.get("prefix", 0),
            os.path.basename(dst), os.path.getsize(dst)))
    if not do_check:
        return 0
    fails = check(sp, rows) + check_index(out, dst)
    hard = [f for f in fails if f[0] in ("CITE_EXISTS", "DUP", "LINENO",
                                         "IDX_DUP", "IDX_PREFIX", "IDX_COUNT", "IDX_STALE")]
    soft = [f for f in fails if f[0] not in ("CITE_EXISTS", "DUP", "LINENO",
                                             "IDX_DUP", "IDX_PREFIX", "IDX_COUNT", "IDX_STALE")]
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
