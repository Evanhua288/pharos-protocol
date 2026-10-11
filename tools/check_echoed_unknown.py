# -*- coding: utf-8 -*-
r"""check_echoed_unknown.py —— **`159`（未知键原值回显）机检门**。

判据：`vectors/` 内一个 `capabilities-echo-*.json` 示例**必须**含两个顶层键：
  `features`（**输入**）与 `echoedUnknownKeys`（**期望回显**）；
且 **`echoedUnknownKeys` 的每个键 必须都不在 `features` 的**已定义名单**里**（否则它不是“未知键”）；
且 **原值逐字相等**（`echoedUnknownKeys[k] == features[k]`）。

退出码：0 通过；1 违反；2 无法执行。**本工具只读**。
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 已定义的 `features` 键（承 `\u00a75D.2`）
DEFINED = {"previousKeys", "attestation_sig", "dispute_canonical", "gap_reporting",
           "settle_query", "fork_reporting", "settle_diff"}


def main(argv):
    if len(argv) < 2:
        print("usage: check_echoed_unknown.py <vectors目录>")
        return 2
    d = argv[1]
    if not os.path.isdir(d):
        print("[159] \u76ee\u5f55\u4e0d\u5b58\u5728")
        return 2
    files = [f for f in sorted(os.listdir(d)) if f.startswith("capabilities-echo-") and f.endswith(".json")]
    if not files:
        print("[159] \u65e0\u56de\u663e\u793a\u4f8b\uff08\u672a\u58f0\u79f0\u8986\u76d6\uff09\uff1aPASS")
        return 0
    bad = []
    for f in files:
        j = json.loads(io.open(os.path.join(d, f), encoding="utf-8").read())
        fe = j.get("features")
        ek = j.get("echoedUnknownKeys")
        if not isinstance(fe, dict) or not isinstance(ek, dict):
            bad.append("%s \u7f3a `features` \u6216 `echoedUnknownKeys`" % f)
            continue
        for k, v in ek.items():
            if k in DEFINED:
                bad.append("%s \u56de\u663e\u4e86**\u5df2\u5b9a\u4e49\u952e** `%s`" % (f, k))
            if k not in fe:
                bad.append("%s \u56de\u663e\u4e86 `features` \u4e2d\u4e0d\u5b58\u5728\u7684\u952e `%s`" % (f, k))
            elif fe[k] != v:
                bad.append("%s `%s` \u539f\u503c\u4e0d\u7b26\uff08\u56de\u663e %r \u2260 \u8f93\u5165 %r\uff09" % (f, k, v, fe[k]))
        # 若 features 含未定义键，则必须在回显中出现
        for k in fe:
            if k not in DEFINED and k not in ek:
                bad.append("%s \u672a定义键 `%s` **\u672a\u56de\u663e**" % (f, k))
    print("[159] \u793a\u4f8b %d \u4ef6\uff1b\u5f02\u5e38 %d" % (len(files), len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u672a\u77e5\u952e\u672a\u6309 `159` \u539f\u503c\u56de\u663e"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
