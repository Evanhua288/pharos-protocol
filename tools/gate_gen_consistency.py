# -*- coding: utf-8 -*-
r"""gate_gen_consistency.py —— **生成物一致性门**（F-10 / T-索引 判据 1–4）。

检什么（对象：`spec/clauses.json`、`spec/alias-map.json`、`LAYERS.sha256`）：
  A) `spec/clauses.json` —— **当场重生成**（经 `tools/gen_clauses.py` 的 `build()`）后**逐字节比**；
     并附 **IDX_DUP**（id 重复）／**IDX_PREFIX**（裸前缀占条款 id 位）／**IDX_COUNT**（`clauseCount` ＝ 条目数）。
  B) `spec/alias-map.json` —— ① **规范书写形式**逐字节比（`json.dumps(ensure_ascii=False, indent=1)+"\n"`）；
     ② **`specSha256` 新鲜度**（须等于现算 spec sha256）；③ `clauseCount` ＝ `len(entries)`；
     ④ canonical 不得悬挂于 `clauses.json`。
     ⚠️ 本包的 `alias-map.json` **无仓内生成器**（全 `tools/` 搜不到写入者）⇒ **无法全量重生成**，
     本门只做"规范形式 ＋ 新鲜度 ＋ 计数 ＋ 无悬挂"四项，并在输出里明写"全量重生成＝未覆盖"。
  C) `LAYERS.sha256` —— 按 `spec/layers/*.md`（**按文件名升序**）重算
     `<sha256>  <basename>` 每行一件，末行 `# SET <sha256(各件 hash 首尾相接)>`，**逐字节比**；
     并报"实有但未登记／登记但盘上无"。

纪律：**只读**（不写任何文件）；退出码 0＝PASS，1＝FAIL，2＝无法执行。

用法：
    python tools/gate_gen_consistency.py .            # 在包目录或 pharos-core 目录内
    python tools/gate_gen_consistency.py <根目录>
"""
import hashlib
import importlib.util
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FAILS = []
NOTES = []
UNCOVERED = []


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(p):
    return sha256_bytes(io.open(p, "rb").read())


def first_diff(a, b):
    """返回首个不同字节偏移与所在行（1 基）。"""
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i, a[:i].count(b"\n") + 1
    if len(a) != len(b):
        return n, a[:n].count(b"\n") + 1
    return None, None


def load_generator(tools_dir):
    """载入 gen_clauses（只用其 build/load_xref；不调用 main，避免写盘）。"""
    gp = os.path.join(tools_dir, "gen_clauses.py")
    if not os.path.isfile(gp):
        return None, None
    try:
        spec_ = importlib.util.spec_from_file_location("_gc_gate", gp)
        mod = importlib.util.module_from_spec(spec_)
        spec_.loader.exec_module(mod)
        return mod, io.open(gp, encoding="utf-8", errors="replace").read()
    except Exception as e:
        NOTES.append("gen_clauses 载入失败：%s" % e)
        return None, None


def check_clauses(root, tools_dir):
    sp = os.path.join(root, "spec", "CORE-001-V1.2.md")
    dst = os.path.join(root, "spec", "clauses.json")
    if not os.path.isfile(sp) or not os.path.isfile(dst):
        UNCOVERED.append("clauses.json：缺 spec 或产物，未检")
        return
    mod, src = load_generator(tools_dir)
    if mod is None:
        FAILS.append(("A clauses.json", "无法载入生成器 tools/gen_clauses.py ⇒ 不能重生成"))
        return
    try:
        mod._XOK = mod.load_xref(sp)
        rows = mod.build(sp)
    except Exception as e:
        FAILS.append(("A clauses.json", "重生成抛错：%s" % e))
        return
    ids = [r["id"] for r in rows]
    tc = {}
    for r in rows:
        tc[r.get("type", "clause")] = tc.get(r.get("type", "clause"), 0) + 1
    # hashRule 为生成器内的字面量：从源码提取（提取失败则用盘上值并记为告警）
    m = re.search(r'"hashRule"\s*:\s*"((?:[^"\\]|\\.)*)"', src or "")
    disk = json.loads(io.open(dst, encoding="utf-8").read())
    if m:
        hash_rule = m.group(1).encode().decode("unicode_escape") if "\\u" in m.group(1) else m.group(1)
    else:
        hash_rule = disk.get("hashRule", "")
        NOTES.append("hashRule 未能从生成器源码提取，改用盘上值（仅此一字段）")
    out = {
        "_note": "\u673a\u8bfb\u6761\u6b3e\u7d22\u5f15\uff08\u7531 gen_clauses.py \u4ece spec \u751f\u6210\uff0c\u4e0d\u624b\u5199\uff09\u3002",
        "spec": os.path.basename(sp),
        "specSha256": sha256_file(sp),
        "specBytes": os.path.getsize(sp),
        "clauses": len(rows),
        "clauseCount": len(rows),
        "clauseIds": len(set(ids)),
        "prefixCount": tc.get("prefix", 0),
        "occurrenceCount": sum(len(r.get("occurrences", [])) for r in rows),
        "typeCounts": tc,
        "hashRule": hash_rule,
        "index": [dict(list((k, v) for k, v in r.items() if k not in ("_kw", "_raw"))
                       + [("clauseHash", sha256_bytes(str(r.get("text", "")).encode("utf-8")))])
                  for r in rows],
    }
    fresh = (json.dumps(out, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    d_raw = io.open(dst, "rb").read()
    if fresh == d_raw:
        print("  [PASS] A clauses.json                逐字节一致（%d B；条目 %d）" % (len(d_raw), len(rows)))
    else:
        off, line = first_diff(fresh, d_raw)
        FAILS.append(("A clauses.json", "与当场重生成**逐字节不同**（盘 %d B vs 重生成 %d B；首个不同字节 offset=%s，约第 %s 行）"
                      % (len(d_raw), len(fresh), off, line)))
        # 结构化定位：哪些字段变了
        try:
            df = json.loads(d_raw)
            for k in ("specSha256", "specBytes", "clauses", "clauseCount", "clauseIds",
                      "prefixCount", "occurrenceCount", "typeCounts"):
                if df.get(k) != out.get(k):
                    FAILS.append(("A clauses.json", "  字段 `%s`：盘上=%r ／ 重生成=%r" % (k, df.get(k), out.get(k))))
            di = {e.get("id"): e for e in df.get("index", [])}
            fi = {e.get("id"): e for e in out["index"]}
            onlyd = [i for i in di if i not in fi]
            onlyf = [i for i in fi if i not in di]
            if onlyd:
                FAILS.append(("A clauses.json", "  仅盘上有 %d 条 id（前 5）：%s" % (len(onlyd), "、".join(onlyd[:5]))))
            if onlyf:
                FAILS.append(("A clauses.json", "  仅重生成有 %d 条 id（前 5）：%s" % (len(onlyf), "、".join(onlyf[:5]))))
            chg = [i for i in set(di) & set(fi) if di[i] != fi[i]]
            if chg:
                k0 = chg[0]
                d0, f0 = di[k0], fi[k0]
                diffk = [k for k in set(d0) | set(f0) if d0.get(k) != f0.get(k)]
                FAILS.append(("A clauses.json", "  同 id 内容不同 %d 条；样本 `%s` 差异字段=%s" % (len(chg), k0, diffk[:6])))
        except Exception as e:
            FAILS.append(("A clauses.json", "  （结构化定位失败：%s）" % e))
    # T-索引 判据 2/3/4
    seen, dup = {}, []
    for n, e in enumerate(out["index"]):
        i = e.get("id")
        if i in seen:
            dup.append(i)
        else:
            seen[i] = n
    if dup:
        FAILS.append(("A clauses.json", "IDX_DUP：id 重复 %d 个（前 5：%s）" % (len(dup), "、".join(dup[:5]))))
    else:
        print("  [PASS] A clauses.json / IDX_DUP      重复 id = 0")
    pref = getattr(mod, "PREFIX_RX", None)
    bad_pref = []
    if pref is not None:
        for e in out["index"]:
            i = e.get("id", "")
            if pref.fullmatch(i) and e.get("type") != "prefix":
                bad_pref.append(i)
    if bad_pref:
        FAILS.append(("A clauses.json", "IDX_PREFIX：裸前缀占条款 id 位 %d 个（前 5：%s）" % (len(bad_pref), "、".join(bad_pref[:5]))))
    else:
        print("  [PASS] A clauses.json / IDX_PREFIX  裸前缀占位 = 0（prefix 型 %d 条）" % out["prefixCount"])
    if int(out.get("clauseCount", -1)) != len(out["index"]):
        FAILS.append(("A clauses.json", "IDX_COUNT：clauseCount=%s ≠ 条目数 %d" % (out.get("clauseCount"), len(out["index"]))))
    else:
        print("  [PASS] A clauses.json / IDX_COUNT   clauseCount = 条目数 = %d" % len(out["index"]))


def check_alias(root):
    ap = os.path.join(root, "spec", "alias-map.json")
    sp = os.path.join(root, "spec", "CORE-001-V1.2.md")
    cp = os.path.join(root, "spec", "clauses.json")
    if not os.path.isfile(ap):
        UNCOVERED.append("alias-map.json：不存在，未检")
        return
    raw = io.open(ap, "rb").read()
    try:
        d = json.loads(raw.decode("utf-8"))
    except Exception as e:
        FAILS.append(("B alias-map.json", "非合法 JSON：%s" % e))
        return
    canon = (json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    if canon == raw:
        print("  [PASS] B alias-map.json / 规范形式     逐字节一致（%d B）" % len(raw))
    else:
        off, line = first_diff(canon, raw)
        FAILS.append(("B alias-map.json", "规范形式不符（`indent=1` 复现 %d B vs 盘 %d B；首个不同 offset=%s，约第 %s 行）"
                      % (len(canon), len(raw), off, line)))
    if os.path.isfile(sp):
        cur = sha256_file(sp)
        if d.get("specSha256") == cur:
            print("  [PASS] B alias-map.json / specSha256   与现算一致（%s）" % cur[:16])
        else:
            FAILS.append(("B alias-map.json", "`specSha256` **陈旧**：盘上=%s ／ 现算 spec=%s"
                          % (str(d.get("specSha256"))[:16], cur[:16])))
    if int(d.get("clauseCount", -1)) != len(d.get("entries", [])):
        FAILS.append(("B alias-map.json", "`clauseCount`=%s ≠ `entries` 数 %d" % (d.get("clauseCount"), len(d.get("entries", [])))))
    else:
        print("  [PASS] B alias-map.json / clauseCount  %d = entries 数" % len(d.get("entries", [])))
    if os.path.isfile(cp):
        try:
            cids = set(e.get("id") for e in json.loads(io.open(cp, encoding="utf-8").read()).get("index", []))
            dang = [e.get("canonical") for e in d.get("entries", []) if e.get("canonical") not in cids]
            if dang:
                FAILS.append(("B alias-map.json", "canonical 悬挂于 clauses.json：%d 个（前 5：%s）" % (len(dang), "、".join(map(str, dang[:5])))))
            else:
                print("  [PASS] B alias-map.json / 无悬挂       canonical 均在 clauses.json 内")
        except Exception as e:
            NOTES.append("alias-map 悬挂检查跳过：%s" % e)
    UNCOVERED.append("alias-map.json **全量重生成**：仓内 `tools/` 无其生成器（搜 `addedIn`/`removedIn`/写入者 0 命中）⇒ 本门只做规范形式＋新鲜度＋计数＋无悬挂")


def check_layers(root):
    lp = os.path.join(root, "LAYERS.sha256")
    la = os.path.join(root, "spec", "layers")
    if not os.path.isfile(lp) or not os.path.isdir(la):
        UNCOVERED.append("LAYERS.sha256：缺件或缺 spec/layers，未检")
        return
    fs = sorted(f for f in os.listdir(la) if f.endswith(".md"))
    hs = [sha256_file(os.path.join(la, f)) for f in fs]
    setv = sha256_bytes("".join(hs).encode("utf-8"))
    fresh = ("\n".join("%s  %s" % (h, f) for h, f in zip(hs, fs)) + "\n# SET " + setv + "\n").encode("utf-8")
    disk = io.open(lp, "rb").read()
    if fresh == disk:
        print("  [PASS] C LAYERS.sha256               逐字节一致（%d 件；SET=%s）" % (len(fs), setv[:16]))
    else:
        off, line = first_diff(fresh, disk)
        FAILS.append(("C LAYERS.sha256", "与当场重生成**逐字节不同**（盘 %d B vs 重生成 %d B；首个不同 offset=%s，约第 %s 行）"
                      % (len(disk), len(fresh), off, line)))
    try:
        reg = [r[66:] for r in io.open(lp, encoding="utf-8").read().split("\n")
               if r.strip() and not r.startswith("#")]
    except Exception:
        reg = []
    unreg = [f for f in fs if f not in reg]
    gone = [f for f in reg if f not in fs]
    if unreg:
        FAILS.append(("C LAYERS.sha256", "**实有但未登记** %d 件：%s" % (len(unreg), "、".join(unreg[:6]))))
    if gone:
        FAILS.append(("C LAYERS.sha256", "**登记但盘上无** %d 件：%s" % (len(gone), "、".join(gone[:6]))))
    if not unreg and not gone:
        print("  [PASS] C LAYERS.sha256 / 件集           登记 %d ＝ 实有 %d" % (len(reg), len(fs)))


def main(argv):
    if len(argv) < 2:
        print("usage: gate_gen_consistency.py <根目录>")
        return 2
    root = os.path.abspath(argv[1])
    tools_dir = os.path.join(root, "tools")
    if not os.path.isdir(os.path.join(root, "spec")):
        print("[RESULT] FAIL -- 不是包/仓根（无 spec/）：%s" % root)
        return 1
    print("== gate_gen_consistency：%s" % root)
    check_clauses(root, tools_dir)
    check_alias(root)
    check_layers(root)
    print("-" * 68)
    for kind, msg in FAILS:
        print("  [FAIL] %-22s %s" % (kind, msg))
    for n in NOTES:
        print("  [WARN] %s" % n)
    for u in UNCOVERED:
        print("  [未覆盖] %s" % u)
    ok = not FAILS
    print("  [RESULT] %s（硬门 %d）" % ("PASS -- 生成物与当场重生成一致" if ok else "FAIL -- 生成物陈旧或与重生成不符", len(FAILS)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
