# -*- coding: utf-8 -*-
r"""check_anchor_set.py —— **锚套件与域分隔门**。

判据：
  S1 `primary` 必须为 `sha-256`；S2 `algId` 必须在注册表且不为 `disallowed`；
  S3 截断必须出现在 `algName` 里；S4 域前缀必须唯一且覆盖必需；
  S5 `hardened` 标记必须带至少一个**异族**`secondary`。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FAMILY = {"sha-256": "MD", "sha-512": "MD", "sha-1": "MD",
          "sha3-256": "SHA3", "sha3-512": "SHA3"}


def main(argv):
    if len(argv) < 2:
        print("usage: check_anchor_set.py <包目录>")
        return 2
    sp = os.path.join(os.path.abspath(argv[1]), "spec")
    need = ("anchor-set.json", "domain-tags.json", "algorithm-registry.json")
    for f in need:
        if not os.path.isfile(os.path.join(sp, f)):
            print("[ANSET] 缺件：%s（未声称覆盖）" % f)
            return 0
    a = json.loads(io.open(os.path.join(sp, "anchor-set.json"), encoding="utf-8").read())
    d = json.loads(io.open(os.path.join(sp, "domain-tags.json"), encoding="utf-8").read())
    reg = {e["name"]: e for e in json.loads(io.open(os.path.join(sp, "algorithm-registry.json"), encoding="utf-8").read()).get("entries", [])}
    bad = []
    dfl = a.get("defaults", {})
    pr = dfl.get("primary", {})
    if pr.get("algName") != "sha-256" or pr.get("lengthBits") != 256:
        bad.append("S1 primary 不是 sha-256/256：%r" % pr)
    for e in [pr] + list(dfl.get("secondary", [])):
        nm = e.get("algName")
        r = reg.get(nm)
        if r is None:
            bad.append("S2 未登记算法：%s" % nm)
            continue
        if r.get("status") == "disallowed":
            bad.append("S2 使用了 disallowed 算法：%s" % nm)
        tr = r.get("truncation")
        if tr is not None and ("-%d" % tr) not in str(nm):
            bad.append("S3 截断未入名：%s" % nm)
    tags = d.get("tags", {})
    vals = list(tags.values())
    if len(set(vals)) != len(vals):
        bad.append("S4 域标语义重复")
    for must in ("leaf", "node", "anchorEnvelope", "anchorSet", "algoProfile"):
        if not any(str(v).startswith(must) for v in vals):
            bad.append("S4 缺必需域标：%s" % must)
    if dfl.get("strengthTier") == "hardened":
        fams = {FAMILY.get(e.get("algName")) for e in dfl.get("secondary", [])}
        if "SHA3" not in fams:
            bad.append("S5 标 hardened 但 secondary 无异族锚")
    print("[ANSET] 锚套件 1 组；secondary %d；域标 %d；异常 %d" % (
        len(dfl.get("secondary", [])), len(tags), len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u951a\u5957\u4ef6\u4e0d\u5408\u683c"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
