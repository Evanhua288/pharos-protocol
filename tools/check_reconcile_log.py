# -*- coding: utf-8 -*-
r"""check_reconcile_log.py —— **对拍登记门**（承 `CORE-001-219`）。

判据：若声称“已对拍”（存在 `vectors/reconciliation-log.json` 且有 entries），
则每条记录**必须**含四项：`clause`\uff0f`env.specHash`\uff0f`hashOurs`\uff0f`hashTheirs`\uff0f`verdict`\uff1b
`verdict=unequal` 者**必须**给出 `diffBytes`（**不得只写“理解不同”**）。
退出码：0 通过；1 违反；2 无法执行。
本工具**只读**。
"""
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
        print("usage: check_reconcile_log.py <vectors目录>")
        return 2
    fp = os.path.join(argv[1], "reconciliation-log.json")
    if not os.path.isfile(fp):
        print("[RECONCILE] \u65e0\u5bf9\u62cd\u65e5\u5fd7\uff08\u672a\u58f0\u79f0\u5df2\u5bf9\u62cd\uff09\uff1aPASS")
        return 0
    try:
        j = json.loads(io.open(fp, encoding="utf-8").read())
    except Exception as e:
        print("[RECONCILE] \u65e5\u5fd7\u4e0d\u53ef\u8bfb\uff1a%s" % e)
        return 1
    bad = []
    for k, e in enumerate(j.get("entries", [])):
        for f in ("clause", "hashOurs", "hashTheirs", "verdict"):
            if not e.get(f):
                bad.append("entry#%d \u7f3a `%s`" % (k, f))
        if not (e.get("env") or {}).get("specHash"):
            bad.append("entry#%d \u7f3a `env.specHash`" % k)
        if e.get("verdict") == "unequal" and not e.get("diffBytes"):
            bad.append("entry#%d `unequal` \u4f46\u672a\u7ed9 `diffBytes`" % k)
        if e.get("verdict") not in ("equal", "unequal"):
            bad.append("entry#%d `verdict` \u975e\u6cd5" % k)
    print("[RECONCILE] \u6761\u76ee %d\uff1b\u5f02\u5e38 %d" % (len(j.get("entries", [])), len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u5bf9\u62cd\u767b\u8bb0\u4e0d\u5408\u683c"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
