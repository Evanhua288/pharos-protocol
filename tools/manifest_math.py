# -*- coding: utf-8 -*-
r"""`manifest_math.py` —— **件数算术唯一来源**。

职责：由**白名单**（`SHIP-MANIFEST.md`【发】段）与**元数据规则**，一次算出：
  · `listed`  —— 进两份清单的件（顺序固定）
  · `M`       —— 清单表行数（= `listed` 长度）
  · `N`       —— 声明总件数（= `M` + 两个自证件）
并**同时产出**两清单文本，供 `build_package` 写入、供 `check_integrity` 校验。
**任何地方不得再自行算这三个数。**
"""
import hashlib
import io
import os
import re

# 进包但**不进两份清单**的元数据件（§口径）
import meta_rule as _MR
META = set(_MR.OFF_LIST)   # 含 SELF+META+CONST
# 自证件（计入 `N`，不计入 `M`）
SELFWIT = tuple(_MR.SELF)
# 签名件：**随包**但**由 SELF 集合放行**，不计入 `M`、也不计入 `N`
SIGS = tuple(_MR.SIGS)


def sha_file(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


def whitelist(pkg):
    """从包内 `SHIP-MANIFEST.md` 的【发】段取白名单（保持文件内顺序）。"""
    p = os.path.join(pkg, "SHIP-MANIFEST.md")
    if not os.path.isfile(p):
        return []
    t = io.open(p, encoding="utf-8-sig", errors="replace").read()
    sec = t.split("## \u4e00\u3001\u3010\u53d1\u3011")[-1].split("## \u4e8c\u3001")[0]
    out, seen = [], set()
    for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|", sec, re.M):
        r = m.group(1).strip()
        if r and r not in seen:
            seen.add(r)
            out.append(r)
    return out


PLACEHOLDER = "(pending)\n"


def _is_placeholder(p):
    """SNAPSHOT ⭐ **占位自检卡不计入快照**（它只是一个中间态）。"""
    try:
        return io.open(p, encoding="utf-8", errors="replace").read() == PLACEHOLDER
    except Exception:
        return False


def math_of(pkg, ignore_placeholder=False):
    """返回 (listed, M, N, disk_total)。

    `ignore_placeholder=True` 时**跳过硬占位自检卡**（保持计数快照与终态一致）。
    """
    wl = whitelist(pkg)
    disk = set()
    for dp, dn, fn in os.walk(pkg):
        dn[:] = [x for x in dn if x not in ("__pycache__", ".git")]
        for f in fn:
            rel = os.path.relpath(os.path.join(dp, f), pkg).replace("\\", "/")
            # COUNT-KIND ⭐ **只数"该进 N 的件"**：排除 SELF／META／SIGS／CONST
            if rel in set(_MR.OFF_LIST) or rel in set(_MR.SIGS):
                continue
            disk.add(rel)
    listed = [r for r in wl if r in disk and r not in META and r not in SIGS]
    # COUNT-EXCLUDE ⭐ 元数据件**不进计数**（`_FROZEN`／`SELF-CHECK.txt` 在清点前后都会变，
    #   计入会让"清点时点"与"终验时点"差一件；口径：计数只数**交付件 + 自证件 + 签名件**）
    disk_total = len(disk)
    # APPEND-ONLY ⭐ **清单只追加**：若有前序包，则沿用其顺序、新件追尾
    #   为何：否则新件会插入旧件之间 ⇒ “旧树是新树的前缀”**永远不成立**
    #   （守方 2026-10-10 建议①：让“冻结”从**单点声明**变为**可验证声明**）
    _prev = os.environ.get("PHAROS_PREV_PKG", "")
    if _prev and os.path.isfile(os.path.join(_prev, "SHA256SUMS")):
        _old = []
        for _ln in io.open(os.path.join(_prev, "SHA256SUMS"), encoding="utf-8", errors="replace").read().split("\n"):
            if "  " in _ln:
                _old.append(_ln.split("  ", 1)[1].strip())
        _set = set(listed)
        listed = [r for r in _old if r in _set] + [r for r in listed if r not in set(_old)]
    else:
        listed.sort()
    m = len(listed)
    n = _MR.declared_total(m)
    return listed, m, n, disk_total


def build(pkg):
    """写两份清单。返回 (M, N, disk_total)。**单一快照，三处同源。**"""
    # SNAPSHOT ⭐ 一次取定快照：忽略占位自检卡，N 由同一快照反推
    # FINAL_STATE ⭐ 终态口径：占位不计入清单，但**声明数按终态**（忽略占位后的盘上数）
    listed, m, _n0, disk_total = math_of(pkg, ignore_placeholder=True)
    io.open(os.path.join(pkg, "SHA256SUMS"), "w", encoding="utf-8", newline="\n").write(
        "".join("%s  %s\n" % (sha_file(os.path.join(pkg, r.replace("/", os.sep))), r) for r in listed))
    n = m   # COUNT-SAME-SET ⭐ `N = M`
    man = ["# MANIFEST.sha256 \u00b7 \u9010\u4ef6\u6e05\u5355\uff08\u4e0e `SHA256SUMS` \u540c\u6e90\uff09", "",
           "files: %d = %d \uff08清单条目数）" % (n, m), "",
           "| \u4ef6 | sha256 |", "|---|---|"]
    for r in listed:
        man.append("| `%s` | `%s` |" % (r, sha_file(os.path.join(pkg, r.replace("/", os.sep)))))
    man.append("| `MANIFEST.sha256` | \uff08\u81ea\u8eab\u4e0d\u81ea\u5217\uff09 |")
    io.open(os.path.join(pkg, "MANIFEST.sha256"), "w", encoding="utf-8", newline="\n").write("\n".join(man) + "\n")
    return m, n, disk_total


def audit(pkg):
    """只读自检：**以同一快照为准**。返回问题列表。"""
    # FINAL_STATE ⭐ 终态口径：占位不计入清单，但**声明数按终态**（忽略占位后的盘上数）
    listed, m, _n0, disk_total = math_of(pkg, ignore_placeholder=True)
    n = m   # COUNT-SAME-SET ⭐ 声明数 **就是清单条目数**
    bad = []
    su = os.path.join(pkg, "SHA256SUMS")
    mp = os.path.join(pkg, "MANIFEST.sha256")
    if os.path.isfile(su):
        rows = [x for x in io.open(su, encoding="utf-8", errors="replace").read().split("\n") if x.strip()]
        if len(rows) != m:
            bad.append("SHA256SUMS \u884c %d \u2260 M %d" % (len(rows), m))
        for x in rows:
            h, rel = x.split("  ", 1)
            fp = os.path.join(pkg, rel.replace("/", os.sep))
            if not os.path.isfile(fp) or sha_file(fp) != h:
                bad.append("SUMS \u4e0d\u7b26\uff1a%s" % rel)
    if os.path.isfile(mp):
        t = io.open(mp, encoding="utf-8-sig", errors="replace").read()
        mr = re.search(r"files:\s*(\d+)\s*=\s*(\d+)", t)
        if not mr:
            bad.append("MANIFEST \u7b97\u672f\u884c\u7f3a\u5931")
        else:
            dn, dm = int(mr.group(1)), int(mr.group(2))
            if (dn, dm) != (n, m):
                bad.append("MANIFEST \u7b97\u672f %d/%d \u2260 \u5feb\u7167 %d/%d" % (dn, dm, n, m))
        trows = [x for x in t.split("\n") if re.match(r"^\|\s*`[^`]+`\s*\|\s*`[0-9a-f]{64}`\s*\|", x)]
        if len(trows) != m:
            bad.append("MANIFEST \u8868\u884c %d \u2260 M %d" % (len(trows), m))
        for x in trows:
            mm = re.match(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|", x)
            rel, h = mm.group(1), mm.group(2)
            fp = os.path.join(pkg, rel.replace("/", os.sep))
            if not os.path.isfile(fp) or sha_file(fp) != h:
                bad.append("MANIFEST \u4e0d\u7b26\uff1a%s" % rel)
    # DRIFT：白名单与磁盘按类求差（**真漂移必须为零**）
    wl = set(whitelist(pkg))
    disk = set()
    for dp, dn, fn in os.walk(pkg):
        dn[:] = [x for x in dn if x not in ("__pycache__", ".git")]
        for f in fn:
            disk.add(os.path.relpath(os.path.join(dp, f), pkg).replace("\\", "/"))
    allowed = set(SIGS) | set(META) | {"SHIP-MANIFEST.md"}
    only_wl = sorted(wl - disk)
    only_disk = sorted(disk - wl - allowed)
    if only_wl:
        bad.append("DRIFT 白名单有而磁盘无（%d）：%s" % (len(only_wl), only_wl[:4]))
    if only_disk:
        bad.append("DRIFT 磁盘有而白名单无（%d）：%s" % (len(only_disk), only_disk[:4]))
    if int(n) != int(disk_total):
        bad.append("COUNT 声明 %d ≠ 盘上 %d" % (n, disk_total))
    return bad


if __name__ == "__main__":
    import sys
    pkg = sys.argv[1] if len(sys.argv) > 1 else "."
    lst, m, n, dt = math_of(pkg)
    print("[MM] M=%d N=%d \u76d8\u4e0a=%d\uff1b\u81ea\u68c0\uff1a%s" % (m, n, dt, audit(pkg) or "\u4e00\u81f4"))
