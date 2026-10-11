# -*- coding: utf-8 -*-
r"""check_write_scope.py —— **写入白名单硬门**。

背景：`AST-P0A-2026-001 §八／§九` 证实——**对方（我方）的"锚传播"写进了 ASTRALINK 的工作区**，
      把其分析件里的哈希常量替换为我方当时的现行锚（21:16／21:55／22:02／23:33 与发版同步）。

判据：
  **任何写入路径必须落在白名单内**；白名单外一律**拒绝**（抛异常）。**只读不受限。**

用法（作为库）：
    from check_write_scope import guarded_open, assert_write_ok
    assert_write_ok(path)          # 写前校验，越界抛 WriteScopeError
    with guarded_open(path, "w") as f: ...   # 安全写法

用法（作为脚本，自查）：
    python check_write_scope.py                 # 打印白名单与当前违规项
    python check_write_scope.py <路径>          # 判单个路径
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ⭐ 白名单：**只有这四个根允许写入**
ALLOW_ROOTS = (
    "D:/PHAROS\u5de5\u4f5c\u533a",                       # \u6211\u65b9\u6b63\u672c\u5de5\u4f5c\u4ed3
    "D:/\u68f1\u955c\u592a\u521d\u89e3\u8bfb\u5206\u6790",                    # \u6211\u65b9\u89e3\u8bfb\u5206\u6790\u4ea4\u4ed8\u7269
    "default-workspace/\u5f85\u53d1-\u6280\u672f\u6808",         # \u6280\u672f\u6808\u53d1\u9001\u76ee\u5f55
    "default-workspace/ACC-ASTRALINK\u6d77\u5916\u4e3b\u4f53\u6ce8\u518c/\u5f85\u53d1-",   # \u4ec5**\u5f85\u53d1-\u00b7\u00b7**\u5b50\u76ee\u5f55
)

# ⭐ 明确**禁写**（即使在白名单父目录下）
DENY_MARKERS = (
    "ACC-ASTRALINK\u6d77\u5916\u4e3b\u4f53\u6ce8\u518c/P0-",
    "ACC-ASTRALINK\u6d77\u5916\u4e3b\u4f53\u6ce8\u518c/v258\u590d\u9a8c",
    "ACC-ASTRALINK\u6d77\u5916\u4e3b\u4f53\u6ce8\u518c/_aethel",
    "ACC-ASTRALINK\u6d77\u5916\u4e3b\u4f53\u6ce8\u518c/\u5f85\u53d1-AST-LET",
    "pharos_p1",
    "xwechat_files",
)


class WriteScopeError(RuntimeError):
    pass


def _norm(p):
    return os.path.abspath(p).replace("\\", "/")


def is_allowed(path):
    q = _norm(path)
    if any(d in q for d in DENY_MARKERS):
        return False, "\u547d\u4e2d**\u7981\u5199**\u6807\u8bb0"
    ok = False
    for r in ALLOW_ROOTS:
        if r.startswith("D:") or r.startswith("C:"):
            if q.startswith(_norm(r)):
                ok = True
        else:
            # \u76f8\u5bf9\u5f62\u5f0f\uff1a\u5339\u914d\u5c3e\u90e8
            if r.replace("/", "/") in q:
                ok = True
    return ok, ("\u5728\u767d\u540d\u5355\u5185" if ok else "**\u4e0d\u5728\u767d\u540d\u5355\u5185**")


def assert_write_ok(path):
    ok, why = is_allowed(path)
    if not ok:
        raise WriteScopeError("\u26d4 \u5199\u5165\u8d8a\u754c\uff1a%s\uff08%s\uff09" % (path, why))
    return True


def guarded_open(path, mode="r", **kw):
    if any(c in mode for c in "wax+"):
        assert_write_ok(path)
    return io.open(path, mode, **kw)


def main(argv):
    print("  === \u5199\u5165\u767d\u540d\u5355\uff08\u4ec5\u6b64\u56db\u6839\uff09===")
    for r in ALLOW_ROOTS:
        print("     \u2705 %s" % r)
    print("  === \u7981\u5199\u6807\u8bb0 ===")
    for d in DENY_MARKERS:
        print("     \u26d4 %s" % d)
    if len(argv) > 1:
        for p in argv[1:]:
            ok, why = is_allowed(p)
            print("  %s %s\uff08%s\uff09" % ("\u2705" if ok else "\u26d4", p, why))
        return 0
    # \u81ea\u67e5\uff1a\u626b\u6211\u65b9\u811a\u672c\u76ee\u5f55\uff0c\u770b\u662f\u5426\u6709\u786c\u7f16\u7801\u7684\u7981\u5199\u8def\u5f84
    A = "D:/PHAROS" + "\u5de5\u4f5c\u533a" + "/_\u6e90\u4e0e\u811a\u672c/prism_taichu_analysis"
    bad = []
    if os.path.isdir(A):
        for f in sorted(os.listdir(A)):
            if not f.endswith(".py"):
                continue
            t = io.open(os.path.join(A, f), encoding="utf-8", errors="replace").read()
            for d in DENY_MARKERS:
                if d in t:
                    bad.append((f, d))
    print("  === \u81ea\u67e5\uff1a\u6211\u65b9\u811a\u672c\u91cc\u51fa\u73b0\u7981\u5199\u8def\u5f84\u8005 ===")
    for f, d in bad:
        print("     \u26a0 %-34s %s" % (f, d))
    print("     \u5171 %d \u5904" % len(bad))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
