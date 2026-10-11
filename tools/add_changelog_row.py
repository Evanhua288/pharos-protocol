# -*- coding: utf-8 -*-
r"""add_changelog_row.py —— **沿革行插入 ＋ 回读校验**（治本会话 9 次同因事故）。

为什么有它：本会话我 **9 次**用"正则插入 + 打印成功"代替"回读验证"，
            导致每次都是**头部版本 ≠ 沿革表最高**报红（`E1_MISMATCH`）。

用法：
  # ① 只校验一致性（安全，无副作用）
  python add_changelog_row.py <spec路径> --check

  # ② 追加/更新一行沿革（幂等：已存在则替换）
  python add_changelog_row.py <spec路径> --add V1.71 "<该行正文，不含表头竖线>"

退出码：0 = 通过/已写入且校验通过；1 = 不一致；2 = 用法错。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HDR = re.compile(r"\u5185\u5bb9\u7248\u672c[^\n]{0,40}?(V\d+\.\d+)")
ROW = re.compile(r"^\| \*\*`(V1\.\d+)`\*\* \|", re.M)


def vnum(v):
    m = re.match(r"V1\.(\d+)", v)
    return int(m.group(1)) if m else -1


def check(spec_path):
    t = io.open(spec_path, encoding="utf-8", errors="replace").read()
    h = HDR.search(t)
    rows = ROW.findall(t)
    hv = h.group(1) if h else None
    mx = max(rows, key=vnum) if rows else None
    ok = bool(hv and mx and hv == mx)
    print("[CHANGELOG] \u5934\u90e8\u7248\u672c=%s\uff1b\u6cbf\u9769\u6700\u9ad8=%s\uff1b\u4e00\u81f4=%s" % (hv, mx, ok))
    if not ok:
        print("  [FAIL] **\u5934\u90e8\u4e0e\u6cbf\u9769\u4e0d\u4e00\u81f4**\uff08\u8fd9\u6b63\u662f `E1_MISMATCH`\uff09")
    else:
        print("  [OK]")
    return 0 if ok else 1


def add(spec_path, ver, body):
    t = io.open(spec_path, encoding="utf-8", errors="replace").read()
    line = "| **`%s`** | %s |" % (ver, body.rstrip("|"))
    rows = ROW.findall(t)
    if ver in rows:
        t = re.sub(r"^\| \*\*`" + re.escape(ver) + r"`\*\* \|.*$", lambda m: line, t, count=1, flags=re.M)
        print("[CHANGELOG] \u5df2\u66ff\u6362 %s \u884c" % ver)
    else:
        # \u63d2\u5728**\u7248\u672c\u53f7\u6700\u9ad8**\u7684\u90a3\u4e00\u884c\u4e4b\u524d\uff08\u4fdd\u6301\u964d\u5e8f\uff09
        best = None
        for m in ROW.finditer(t):
            if vnum(m.group(1)) < vnum(ver) and (best is None or vnum(m.group(1)) > vnum(best.group(1))):
                best = m
        if best is None:
            first = ROW.search(t)
            if not first:
                print("  [FAIL] \u672a\u627e\u5230\u6cbf\u9769\u8868")
                return 1
            t = t[:first.start()] + line + "\n" + t[first.start():]
        else:
            eol = t.find("\n", best.start())
            t = t[:eol + 1] + line + "\n" + t[eol + 1:]
        print("[CHANGELOG] \u5df2\u63d2\u5165 %s \u884c" % ver)
    io.open(spec_path, "w", encoding="utf-8", newline="\n").write(t)
    # ⭐ **\u5199\u540e\u5fc5\u56de\u8bfb**
    return check(spec_path)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    sp = argv[1]
    if argv[2] == "--check":
        return check(sp)
    if argv[2] == "--add":
        if len(argv) < 5:
            print("usage: ... --add <Vx.y> <\u884c\u6b63\u6587>")
            return 2
        return add(sp, argv[3], argv[4])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
