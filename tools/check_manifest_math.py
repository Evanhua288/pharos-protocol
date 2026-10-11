# -*- coding: utf-8 -*-
r"""check_manifest_math.py —— **件数算术同源门**。

问题：`N`／`M`／自指三数三处各算 ⇒ 永远对不上。
本门：**唥由 `manifest_math.audit()` 唤唤一处算**。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest_math as MM  # noqa: E402


def main(argv):
    if len(argv) < 2:
        print("usage: check_manifest_math.py <\u5305\u76ee\u5f55>")
        return 2
    V = os.path.abspath(argv[1])
    if not os.path.isfile(os.path.join(V, "SHIP-MANIFEST.md")):
        print("[MM] 无白名单（未声称覆盖）：PASS")
        return 0
    bad = MM.audit(V)
    listed, m, n, dt = MM.math_of(V)
    print("[MM] M=%d；N=%d；盘上=%d；异常 %d" % (m, n, dt, len(bad)))
    for x in bad[:8]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u4ef6\u6570\u7b97\u672f\u4e0d\u540c\u6e90"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
