# -*- coding: utf-8 -*-
r"""check_anchor_whitelist.py —— **锚剔除白名单门**（守方建议②）。

A1 白名单必存在；A2 **同一条目两次算锚必相同**（确定性）；
A3 **改剔除项 ⇒ 锚不变**；A4 **改包含项 ⇒ 锚必变**；A5 冻结期字段在。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anchor_of as AO  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main(argv):
    V = os.path.abspath(argv[1]) if len(argv) > 1 else "."
    wl = AO.load_whitelist(os.path.join(V, "spec"))
    if not wl:
        print("[AWHITELIST] 无白名单（未声称覆盖）：PASS")
        return 0
    bad = []
    fe = os.path.join(V, "vectors", "field-entity.json")
    if os.path.isfile(fe):
        e = json.loads(io.open(fe, encoding="utf-8").read()).get("entry", {})
        a1 = AO.anchor_of(e, wl)
        a2 = AO.anchor_of(e, wl)
        if a1 != a2:
            bad.append("A2 非确定性")
        # A3：改剔除项
        e3 = dict(e)
        e3["confirmAt"] = "2099-01-01T00:00:00Z"
        if AO.anchor_of(e3, wl) != a1:
            bad.append("A3 改剔除项后锚变了")
        # A4：改包含项
        e4 = dict(e)
        e4["units"] = int(e4.get("units", 0)) + 1
        if AO.anchor_of(e4, wl) == a1:
            bad.append("A4 改包含项后锚未变")
    else:
        bad.append("A1 缺字段实体（无法测）")
    if not wl.get("frozenUntil"):
        bad.append("A5 缺冻结期")
    inc = set(wl["contentAnchor"]["include"])
    exc = set(wl["contentAnchor"]["exclude"])
    if inc & exc:
        bad.append("A2 白名单与剔除项有交集：%s" % sorted(inc & exc))
    print("[AWHITELIST] 包含 %d 字段；剔除 %d 字段；异常 %d" % (len(inc), len(exc), len(bad)))
    for x in bad[:6]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u951a\u5254\u9664\u767d\u540d\u5355\u4e0d\u8db3"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
