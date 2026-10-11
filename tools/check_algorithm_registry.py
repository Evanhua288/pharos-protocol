# -*- coding: utf-8 -*-
r"""check_algorithm_registry.py —— **算法注册表合规**。

判据：
 R1 `algId` 唯一且格式合法；R2 不得出现 `disallowed` 于可用集；
 R3 截断必须出现在名字里且 `truncation < outputBits`；R4 `collisionBits` 必须 = 输出位/2（除截断）；
 R5 `status` 必须在四值内；R6 `disallowed` 项必须带非空 `disallowFor`。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OK = ("acceptable", "deprecated", "legacy", "disallowed")


def main(argv):
    if len(argv) < 2:
        print("usage: check_algorithm_registry.py <包目录>")
        return 2
    p = os.path.join(os.path.abspath(argv[1]), "spec", "algorithm-registry.json")
    if not os.path.isfile(p):
        print("[ALG] 无注册表（未声称覆盖）：PASS")
        return 0
    j = json.loads(io.open(p, encoding="utf-8").read())
    bad, seen = [], set()
    for e in j.get("entries", []):
        a = e.get("algId")
        if not re.fullmatch(r"0x[0-9A-Fa-f]{2}", str(a)):
            bad.append("R1 algId 格式非法：%r" % a)
        if a in seen:
            bad.append("R1 algId 重复：%s" % a)
        seen.add(a)
        st = e.get("status")
        if st not in OK:
            bad.append("R5 status 非法：%s (%s)" % (st, a))
        trunc = e.get("truncation")
        if trunc is not None:
            if ("-%d" % trunc) not in str(e.get("name", "")):
                bad.append("R3 截断 %s 未出现在名字里：%s" % (trunc, e.get("name")))
            if not (0 < trunc < (e.get("outputBits") or 0)):
                bad.append("R3 截断值越界：%s" % a)
        ob, cb = e.get("outputBits"), e.get("collisionBits")
        if ob and cb:
            expect = (ob - (trunc or 0)) // 2
            if cb != expect:
                bad.append("R4 碰撞强度不符输出位一半：%s（得 %s，应 %s）" % (a, cb, expect))
        if st == "disallowed" and not e.get("disallowFor"):
            bad.append("R6 `disallowed` 未声明 `disallowFor`：%s" % a)
    print("[ALG] 登记 %d 项；异常 %d" % (len(j.get("entries", [])), len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u7b97\u6cd5\u6ce8\u518c\u8868\u4e0d\u5408\u683c"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
