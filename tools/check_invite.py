# -*- coding: utf-8 -*-
r"""check_invite.py — 机检：**评审邀请包 ＝ 交付范围表**（差集必须为空）。

事实源：`评审邀请清单.txt`（一行一路径；`#` 为注释）。
判据：
  A. **应交未给 = ∅**：清单里每一条**必须在盘上存在**；
  B. **范围外 = ∅**：盘上**每一件必须在清单里**（或位于清单所列目录之下）。

用法：
    python tools/check_invite.py <包根> [--strict]
退出码：0 = 两差集均空；1 = 有差集；2 = 用法错。
"""
import io
import os
import sys

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LIST_NAME = "\u8bc4\u5ba1\u9080\u8bf7\u6e05\u5355.txt"
SKIP_DIRS = {"__pycache__", ".git", ".github"}


def load_list(root):
    p = os.path.join(root, LIST_NAME)
    if not os.path.exists(p):
        return None
    s = set()
    for ln in io.open(p, encoding="utf-8", errors="replace").read().split("\n"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        rel = ln.replace("\\", "/")
        if rel.startswith("./"):
            rel = rel[2:]
        if rel:
            s.add(rel)
    return s


def disk_files(root):
    s = set()
    for dp, dn, fn in os.walk(root):
        dn[:] = [x for x in dn if x not in SKIP_DIRS]
        for f in fn:
            rel = os.path.relpath(os.path.join(dp, f), root).replace("\\", "/")
            if rel == LIST_NAME:
                continue
            s.add(rel)
    return s


def main(argv):
    if len(argv) < 2:
        print("\u7528\u6cd5: python tools/check_invite.py <\u5305\u6839> [--strict]")
        return 2
    root, strict = argv[1], "--strict" in argv
    L = load_list(root)
    if L is None:
        print("[INVITE] \u672a\u627e\u5230 %s" % LIST_NAME)
        return 2
    D = disk_files(root)
    dirs = set(x for x in L if x.endswith("/"))

    miss = sorted(x for x in L if not os.path.exists(os.path.join(root, x)))
    # ⏪ V1.53：`_FROZEN` 是**冻结标记（元数据件）**，不属清单范围，故 B 类判据豁免。
    META_FILES = {"_FROZEN"}
    extra = sorted(x for x in D if x not in L and x not in META_FILES
                   and not any(x.startswith(d) for d in dirs))

    print("[INVITE] \u6e05\u5355\uff1a%d \u6761\uff08\u542b\u76ee\u5f55 %d\uff09\uff1b\u76d8\u4e0a\uff1a%d \u4ef6" % (len(L), len(dirs), len(D)))
    print("[INVITE] A \u5e94\u4ea4\u672a\u7ed9\uff1a%d" % len(miss))
    for x in miss[:20]:
        print("    [MISS]  %s" % x)
    print("[INVITE] B \u8303\u56f4\u5916\uff1a%d" % len(extra))
    for x in extra[:20]:
        print("    [EXTRA] %s" % x)
    ok = not (miss or extra)
    if strict and not ok:
        print("[FAIL] \u5dee\u96c6\u975e\u7a7a\uff08A %d\uff1bB %d\uff09" % (len(miss), len(extra)))
        return 1
    print("[PASS] \u5dee\u96c6\u4e3a\u7a7a\uff08A 0\uff1bB 0\uff09" if ok else "[WARN] \u5dee\u96c6\u975e\u7a7a\uff08\u672a\u52a0 --strict\uff09")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
