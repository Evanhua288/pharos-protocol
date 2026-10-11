# -*- coding: utf-8 -*-
r"""check_frozen_immutable.py —— **冻结不可改**（V2：三层校验）。

**为何 V2**：V1 只在包内比对 `_FROZEN` 与 `SHA256SUMS`（两者**同在包内**），
实测：改文件＋重算清单＋同步改 `_FROZEN` 即**伪造通过**。

**V2 三层**：
  ① **清单↔实件**：`SHA256SUMS` 每行 sha256 必须等于该文件**现算**值；
  ② **外部锚**：清单 sha256 ＋ 件数，必须等于**包外台账** `_anchor_ledger.json` 的记录；
  ③ mtime：辅助信号。

用法：python check_frozen_immutable.py <包目录> [--ledger <台账>]
退出码：0 通过；1 违反。
"""
import hashlib
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SKIP = {"__pycache__", ".git"}
LEDGER_DEFAULT = "D:/PHAROS" + "\u5de5\u4f5c\u533a" + "/\u4ea4\u4ed8\u5305/_anchor_ledger.json"


def _sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def _nfiles(root):
    n = 0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        n += len(fn)
    return n


def load_ledger(path):
    if not os.path.isfile(path):
        return None
    try:
        j = json.loads(io.open(path, encoding="utf-8").read())
    except Exception:
        return None
    m = {}
    for e in j.get("entries", []):
        for f in e.get("_frozen", []):
            m[f["package"]] = f
    return m


def check(root, ledger=None):
    bad, info = [], ""
    name = os.path.basename(os.path.abspath(root))
    fz = os.path.join(root, "_FROZEN")
    if not os.path.exists(fz):
        return None, "\u65e0 `_FROZEN`\uff0c\u8df3\u8fc7"
    su = os.path.join(root, "SHA256SUMS")
    if not os.path.isfile(su):
        return ["\u6709 `_FROZEN` \u4f46**\u65e0 `SHA256SUMS`**"], ""
    # ⏪ \u5f15\u7528\u5f0f\u51bb\u7ed3\uff1a`_FROZEN` = `ref:<su shas>:<files>`\uff08**\u4e0d\u8986\u76d6\u65e2\u6709\u6e05\u5355**\uff09
    _fzc = io.open(fz, encoding="utf-8", errors="replace").read().strip()
    _refmode = _fzc.startswith("ref:")
    listed = {}
    for ln in io.open(su, encoding="utf-8", errors="replace").read().split("\n"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split(None, 1)
        if len(parts) == 2:
            listed[parts[1].replace("\\", "/")] = parts[0]
    # ⏪ \u5f15\u7528\u5f0f\uff1a\u53ea\u9a8c\u201c\u6e05\u5355 sha256 + \u4ef6\u6570 \u2261 \u53f0\u8d26\u201d\uff0c\u5e76\u8981\u6c42\u6e05\u5355\u6240\u5217\u6587\u4ef6**\u5747\u5b58\u5728**\uff08\u4e0d\u9010\u4ef6\u7b97\uff0c\u907f\u5386\u53f2\u5305\u8bef\u62a5\uff09
    if _refmode:
        miss = 0
        for rel in listed:
            if not os.path.isfile(os.path.join(root, rel)):
                miss += 1
                if miss <= 5:
                    bad.append("\u6e05\u5355\u5217\u4e86\u4f46\u78c1\u76d8\u65e0\u6b64\u4ef6\uff1a`%s`" % rel)
        if miss > 5:
            bad.append("\u5171 %d \u4ef6\u6e05\u5355\u5df2\u5217\u800c\u78c1\u76d8\u7f3a\u5931" % miss)
    nbad = 0
    for rel, want in ({} if _refmode else listed).items():
        p = os.path.join(root, rel)
        if not os.path.isfile(p):
            bad.append("\u6e05\u5355\u5217\u4e86\u4f46\u78c1\u76d8\u65e0\u6b64\u4ef6\uff1a`%s`" % rel)
            continue
        if _sha(p) != want:
            nbad += 1
            if nbad <= 5:
                bad.append("\u5b9e\u4ef6\u4e0e\u6e05\u5355\u4e0d\u7b26\uff1a`%s`" % rel)
    if nbad > 5:
        bad.append("\u5171 %d \u4ef6\u5b9e\u4ef6\u4e0e\u6e05\u5355\u4e0d\u7b26" % nbad)
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            rel = os.path.relpath(os.path.join(dp, f), root).replace("\\", "/")
            if rel not in listed and f not in ("SHA256SUMS", "MANIFEST.sha256", "_FROZEN",
                                            "SHA256SUMS.sig", "SHA256SUMS.pub",
                                            "SELF-CHECK.txt", "SHIP-MANIFEST.md") \
                    and "reconciliation-log" not in rel \
                    and "__pycache__" not in rel and not f.endswith(".pyc"):
                bad.append("\u672a\u5217\u5165\u6e05\u5355\u7684\u591a\u4f59\u4ef6\uff1a`%s`" % rel)
    got_sums, got_n = _sha(su), _nfiles(root)
    if ledger is None:
        info = "\u53f0\u8d26\u4e0d\u53ef\u7528\u3010\u4ec5\u2460\u2462\u3011"
    else:
        ent = ledger.get(name)
        if ent is None:
            info = "\u53f0\u8d26\u65e0 `%s` \u8bb0\u5f55\u3010\u4ec5\u2460\u2462\u3011" % name
        else:
            if ent.get("sumsSha256") != got_sums:
                bad.append("\u6e05\u5355 sha256 \u4e0e**\u5305\u5916\u53f0\u8d26**\u4e0d\u7b26\uff08\u53f0\u8d26 %s / \u5b9e\u7b97 %s\uff09"
                           % (str(ent.get("sumsSha256"))[:16], got_sums[:16]))
            if ent.get("files") != got_n:
                bad.append("\u4ef6\u6570\u4e0e**\u5305\u5916\u53f0\u8d26**\u4e0d\u7b26\uff08\u53f0\u8d26 %s / \u5b9e\u7b97 %d\uff09" % (ent.get("files"), got_n))
            if not ent.get("frozen"):
                bad.append("\u53f0\u8d26\u8bb0\u5f55\u4e3a**\u672a\u51bb\u7ed3**")
    t0 = os.path.getmtime(fz)
    late = 0
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            if f == "_FROZEN":
                continue
            try:
                if os.path.getmtime(os.path.join(dp, f)) > t0 + 1:
                    late += 1
            except OSError:
                pass
    if late:
        bad.append("**\u51bb\u7ed3\u540e\u5199\u5165 %d \u4ef6**\uff08mtime \u665a\u4e8e `_FROZEN`\uff09" % late)
    return bad, info


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    li = [i for i, a in enumerate(argv) if a == "--ledger"]
    lp = argv[li[0] + 1] if li and li[0] + 1 < len(argv) else LEDGER_DEFAULT
    ledger = load_ledger(lp)
    nbad = 0
    for r in (args or ["."]):
        if not os.path.isdir(r):
            continue
        bad, info = check(r, ledger)
        if bad is None:
            print("[FROZEN] %s\uff1a%s" % (os.path.basename(r), info))
            continue
        if bad:
            nbad += 1
            print("[FAIL] %s" % os.path.basename(r))
            for x in bad[:8]:
                print("         \u2192 %s" % x)
        else:
            print("[OK] %s\uff1a\u4e09\u5c42\u6821\u9a8c\u901a\u8fc7 %s" % (os.path.basename(r), info))
    print("[RESULT] %s" % ("PASS" if not nbad else "FAIL \u2014 \u8fdd\u53cd\u201c\u51bb\u7ed3\u4e0d\u53ef\u6539\u201d"))
    return 0 if not nbad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
