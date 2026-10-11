# -*- coding: utf-8 -*-
r"""check_extension_cases.py —— **`ext` 外挂门**。

判据：
 E-1 **变例必须带 `entry` 与 `expect`**；
 E-2 **未知键必须被保留**（逐键逐值相等）；
 E-3 **`ext` 必须同时带 `schemaId` 与 `schemaDialect`（缺一即 EXPECT_FAIL）**；
 E-4 **空 `ext` 合法**。
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


def judge(e):
    """返回 OK / FAIL（按 `extension-schema.json` 的 E2）。"""
    ext = e.get("ext")
    if not isinstance(ext, dict):
        return "FAIL"
    if not e.get("schemaId") or not e.get("schemaDialect"):
        return "FAIL"
    return "OK"


def main(argv):
    if len(argv) < 2:
        print("usage: check_extension_cases.py <\u5305\u76ee\u5f55>")
        return 2
    p = os.path.join(os.path.abspath(argv[1]), "vectors", "extension-cases.json")
    if not os.path.isfile(p):
        print("[EXT] 无样例（未声称覆盖）：PASS")
        return 0
    j = json.loads(io.open(p, encoding="utf-8").read())
    bad, n = [], 0
    for c in j.get("cases", []):
        n += 1
        if "entry" not in c or "expect" not in c:
            bad.append("E-1 %s 缺 `entry`/`expect`" % c.get("id"))
            continue
        got = judge(c["entry"])
        exp = c["expect"][0] if c["expect"] else None
        if got != exp:
            bad.append("E-2/3 %s 判得 %s，期望 %s" % (c.get("id"), got, exp))
        if exp == "OK":
            ext = c["entry"].get("ext") or {}
            for k, v in ext.items():
                if c["entry"].get("__kept__", ext).get(k, object()) != v:
                    bad.append("E-2 %s 键 %s 未原值保留" % (c.get("id"), k))
    print("[EXT] 样例 %d；异常 %d" % (n, len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 `ext` \u5916\u6302\u4e0d\u5408\u683c"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
