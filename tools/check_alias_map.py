# -*- coding: utf-8 -*-
r"""check_alias_map.py —— **条号别名门**。

判据：
 A1 **canonical 必须存在于 `clauses.json`**（无悬挂）；
 A2 **一个 alias 只能指向一个 canonical**（无歧义）；
 A3 **alias 不得与任何 canonical 重名**（防歧义）；
 A4 **`specSha256` 必须等于现算 spec `sha256`**（防陈旧）；
 A5 **每条 canonical 必须有 `addedIn`**。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import hashlib
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main(argv):
    if len(argv) < 2:
        print("usage: check_alias_map.py <包目录>")
        return 2
    V = os.path.abspath(argv[1])
    sp = os.path.join(V, "spec", "CORE-001-V1.2.md")
    cj = os.path.join(V, "spec", "clauses.json")
    am = os.path.join(V, "spec", "alias-map.json")
    for f in (sp, cj, am):
        if not os.path.isfile(f):
            print("[ALIAS] 缺件：%s" % f)
            return 1
    j = json.loads(io.open(cj, encoding="utf-8").read())
    m = json.loads(io.open(am, encoding="utf-8").read())
    canon = {r["id"] for r in j["index"]}
    live = {c for c in canon if "-" not in c.split("-")[-1] or True}
    bad = []
    seen_alias = {}
    ent = m.get("entries", [])
    ents = {e.get("canonical"): e for e in ent}
    for c in sorted(canon):
        if c not in ents:
            bad.append("A1 无悬挂：条 %s 未登记" % c)
    for e in ent:
        c = e.get("canonical")
        if c not in canon:
            bad.append("A1 无悬挂：登记了不存在的 canonical %s" % c)
        if not e.get("addedIn"):
            bad.append("A5 %s 缺 `addedIn`" % c)
        for a in e.get("aliases", []):
            if a in seen_alias and seen_alias[a] != c:
                bad.append("A2 歧义：alias %s 同时指向 %s 与 %s" % (a, seen_alias[a], c))
            seen_alias[a] = c
    for a in seen_alias:
        if a in canon:
            bad.append("A3 alias %s 与 canonical 同名" % a)
    _want = j.get("clauseIds")
    if _want is not None and int(m.get("clauseCount") or -1) != int(_want):
        bad.append("A6 `clauseCount` 与实件不符：声明 %s，实 %d" % (m.get("clauseCount"), len(canon)))
    _live = {r["id"] for r in j["index"]}
    _cov = {e.get("canonical") for e in ent}
    if _live - _cov:
        bad.append("A7 未登记的条 %d 条（例：%s）" % (len(_live - _cov), sorted(_live - _cov)[:3]))
    if m.get("specSha256") != hashlib.sha256(io.open(sp, "rb").read()).hexdigest():
        bad.append("A4 `specSha256` 与现算 spec 不符")
    print("[ALIAS] 登记 %d；实件 %d；alias %d；异常 %d" % (len(ent), len(canon), len(seen_alias), len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u6761\u53f7\u522b\u540d\u4e0d\u5408\u683c"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
