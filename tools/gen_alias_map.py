# -*- coding: utf-8 -*-
r"""gen_alias_map.py —— **条号别名表的生成器**（本仓此前**无**此器，故密钥表只能查形态、不能重生）。

判据：
  A1 **无悬挂**：表内每个 `canonical` 必在 `clauses.json` 的唯一条号集内；
  A2 **无遗漏**：`clauses.json` 的唯一条号集 ⊆ 表内 `canonical` 集；
  A3 **无重复**：`canonical` 两两不同；
  A4 **新鲜**：`specSha256` 必 = 现算 `CORE-001` 摘要。

**只增不删**：已有条目原样保留；缺的补齐。
用法：`python tools/gen_alias_map.py [--check]`
"""
import hashlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AM = os.path.join(ROOT, "spec", "alias-map.json")
CJ = os.path.join(ROOT, "spec", "clauses.json")
SPEC = os.path.join(ROOT, "spec", "CORE-001-V1.2.md")


def build():
    j = json.loads(io.open(AM, encoding="utf-8").read())
    cj = json.loads(io.open(CJ, encoding="utf-8").read())
    ids = sorted({r["id"] for r in cj["index"] if isinstance(r, dict) and r.get("id")})
    ent = j.get("entries") or []
    have = {e.get("canonical") for e in ent if isinstance(e, dict)}
    added = 0
    for cid in ids:
        if cid not in have:
            ent.append({"canonical": cid, "aliases": [], "addedIn": "V1.86", "removedIn": None})
            added += 1
    # 按 canonical 排序：否则“原有顺序 + 追加”会使包与仓逐字节不同
    ent.sort(key=lambda e: e.get("canonical") or "")
    j["entries"] = ent
    j["clauseCount"] = len(ent)
    j["specSha256"] = hashlib.sha256(io.open(SPEC, "rb").read()).hexdigest()
    return j, added, len(ids)


def check(j):
    bad = []
    cj = json.loads(io.open(CJ, encoding="utf-8").read())
    ids = {r["id"] for r in cj["index"] if isinstance(r, dict) and r.get("id")}
    ent = j.get("entries") or []
    can = [e.get("canonical") for e in ent if isinstance(e, dict)]
    for c in can:
        if c not in ids:
            bad.append("A1 悬挂：%s" % c)
    miss = ids - set(can)
    if miss:
        bad.append("A2 遗漏 %d 条（例：%s）" % (len(miss), sorted(miss)[:3]))
    if len(can) != len(set(can)):
        bad.append("A3 重复 canonical")
    cur = hashlib.sha256(io.open(SPEC, "rb").read()).hexdigest()
    if j.get("specSha256") != cur:
        bad.append("A4 specSha256 陈旧")
    if int(j.get("clauseCount") or -1) != len(ent):
        bad.append("A5 clauseCount 不符")
    return bad


def main(argv):
    check_only = "--check" in argv
    j, added, n = build()
    if check_only:
        bad = check(json.loads(io.open(AM, encoding="utf-8").read()))
        print("[ALIASGEN] 条号 %d；表内 %d；待补 %d；异常 %d" % (
            n, len(j.get("entries") or []), added, len(bad)))
        for x in bad[:8]:
            print("     \u2192 %s" % x)
        print("[RESULT] %s" % ("PASS" if not bad else "FAIL"))
        return 0 if not bad else 1
    # 每次都写：`specSha256` 与 `clauseCount` 也要跟随更新，
    #   若只在 `added` 时写，两个字段会永远停在上次新增的那一刻。
    io.open(AM, "w", encoding="utf-8", newline="\n").write(
        json.dumps(j, ensure_ascii=False, indent=1) + "\n")
    bad = check(j)
    print("[ALIASGEN] 条号 %d；表内 %d；新增 %d；异常 %d" % (
        n, len(j.get("entries") or []), added, len(bad)))
    for x in bad[:8]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
