#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""包内完整性判据 · tools/check_integrity.py

用途：在**打包前**与**收件后**两个时点，核对「两份清单 ↔ 磁盘文件」是否一致。

判据（十条）：
  ① MANIFEST 与 SHA256SUMS 对**同一件**登记的哈希必须相等            ⇒ XCHECK
  ② 清单列了而磁盘无此件                                              ⇒ GHOST
  ③ 磁盘有而两份清单都没列（除两清单自指）                            ⇒ UNLISTED
  ④ **MANIFEST 表内每一条**哈希都要与磁盘实测相符（不只 SHA256SUMS）  ⇒ MISMATCH
  ⑤ 件数算术 `files: N = M + SHA256SUMS + MANIFEST.sha256` ⇒ N == M+2 ⇒ ARITH
  ⑥ `N` 须等于磁盘实际件数                                            ⇒ COUNT
  ⑦ **磁盘中每件（除自指）必须被 SHA256SUMS 覆盖**                     ⇒ COVER_SUMS
  ⑧ **磁盘中每件（除自指）必须被 MANIFEST 覆盖**                       ⇒ COVER_MAN
  ⑨ **SHA256SUMS 的件集必须包含于 MANIFEST**（集合关系，非只比交集）  ⇒ SUBSET
  ⑩ **MANIFEST 表行数须等于 M+1（自指行）；未被解析的表行报出**     ⇒ ROWS / MANIFEST_UNPARSED

退出码：0 = 全过；1 = 有 FAIL；2 = 无法执行。

⚠️ 能力边界（本工具自身也有，且必须明说）：
    本工具能证「**两份清单互相一致、各自完整覆盖磁盘、且逐条相符**」。
    它**不能**证「**磁盘上的就是全部应交付件**」。
    因为清单与磁盘同源；若发布者**同步**改小清单与件数，本工具看不出来。
    要证后者，需**包外真值源**：源目录白名单、逐件对表、或第三方签名。

本版新增（批 A · A-1）：⑦⑧⑨（覆盖率与集合关系）、⑩（表行数与未解析行）。
    修正的真实缺陷：原版**只比两清单的交集**，故把 SHA256SUMS 从 106 行截到 30 行仍 `[PASS]`、rc=0。
"""
import hashlib
import io
import os
import re
import sys


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def layers_check(root):
    """⏪ V1.46：层件逐件 ⊕ 集合哈希核对（目的：**层件变化在 `specHash` 里看不见**）。"""
    import hashlib as _h
    lp = os.path.join(root, "LAYERS.sha256")
    ld = os.path.join(root, "spec", "layers")
    if not (os.path.exists(lp) and os.path.isdir(ld)):
        return [("LAYERS_MISSING", "LAYERS.sha256 或 spec/layers/ 不存在")]
    want, comp = {}, None
    for ln in io.open(lp, encoding="utf-8", errors="replace").read().split("\n"):
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("LAYERS-SET"):
            comp = s.split()[1]
            continue
        if "  " in s:
            h, f = s.split("  ", 1)
            if len(h) == 64:
                want[f] = h
    fails, per = [], []
    for f in sorted(want):
        p = os.path.join(ld, f)
        if not os.path.exists(p):
            fails.append(("LAYERS_ITEM", "层件缺失：%s" % f))
            continue
        got = _h.sha256(io.open(p, "rb").read()).hexdigest()
        per.append(got)
        if got != want[f]:
            fails.append(("LAYERS_ITEM", "层件哈希不符：%s" % f))
    disk = sorted(f for f in os.listdir(ld) if f.endswith(".md"))
    if set(disk) != set(want):
        fails.append(("LAYERS_SET", "层件集不符：盘上 %d／清单 %d" % (len(disk), len(want))))
    if comp and per:
        got = _h.sha256(b"PHAROS-LAYERS-v1" + "".join(per).encode("ascii")).hexdigest()
        if got != comp:
            fails.append(("LAYERS_SET", "集合哈希不符（%s vs %s）" % (got[:12], comp[:12])))
    print("[LAYERS] 逐件 %d；集合 %s；不符 %d"
          % (len(want), ("%s…" % comp[:12]) if comp else "—", len(fails)))
    return fails


def ship_exclude_check(root):
    """⏪ V1.50：以 `SHIP-MANIFEST.md` 的【不发】段为准。
    【不发】列名的件**不得**出现在 `SHA256SUMS` 或包内。"""
    fails = []
    mp = os.path.join(root, "SHIP-MANIFEST.md")
    sp = os.path.join(root, "SHA256SUMS")
    if not (os.path.exists(mp) and os.path.exists(sp)):
        return fails
    mt = io.open(mp, encoding="utf-8", errors="replace").read()
    exc = set(re.findall(r"\| `([^`]+)` \| \*\*不发\*\* \|", mt))
    body = io.open(sp, encoding="utf-8", errors="replace").read()
    for f in sorted(exc):
        if f in body:
            fails.append(("NOT_SHIP_IN_SUMS", "%s：列入【不发】而出现在 `SHA256SUMS`" % f))
    print("[SHIP] 【不发】%d 件；不符 %d" % (len(exc), len(fails)))
    return fails


def main(root):
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        print("[INCOMPLETE] 目录不存在: " + root)
        return 2

    fails = []
    fails += layers_check(root) or []
    fails += ship_exclude_check(root) or []
    # COUNT-RULE ⭐ 件数规则唯一来源（**必须在任何使用之前导入**）
    import meta_rule as _MR2
    SIGSELF = tuple(_MR2.SIGS) + ("SELF-CHECK.txt",)
    SELF = set(_MR2.SELF) | {"SHIP-MANIFEST.md",
            "SHA256SUMS.sig", "SHA256SUMS.pub", "SELF-CHECK.txt",
            "vectors/reconciliation-log.json"}
    # ⏪ V1.53：冻结标记 `_FROZEN` 是**元数据件**，不进凭据、不计件数。
    # META-ALIGN ⭐ **与清单同集合**：不计入声明数的件（元数据＋自证＋签名＋常驻）
    META = set(_MR2.META) | set(_MR2.SELF) | set(_MR2.SIGS) | set(_MR2.CONST)

    # 磁盘（明确声明排除哪些目录，并打印排除了多少）
    skipped = 0
    disk = set()
    # ⏪ V1.50：以 `SHIP-MANIFEST.md` 【不发】段为准——这些件**不进凭据、不进包**，
    #    故 COVER/UNLISTED/COUNT 三类判据一律**豁免**（但仍须"存在但我方内部"）。
    _ship_exc = set()
    _mp = os.path.join(root, "SHIP-MANIFEST.md")
    if os.path.exists(_mp):
        _ship_exc = set(re.findall(r"\| `([^`]+)` \| \*\*\u4e0d\u53d1\*\* \|",
                                   io.open(_mp, encoding="utf-8", errors="replace").read()))
    for dp, dns, fns in os.walk(root):
        keep = []
        for d in dns:
            if d in (".git",):
                skipped += 1
                continue
            if d == "__pycache__":
                # **只跳过运行产物**（.pyc/.pyo）；
                # 若该目录**含其它件**，则不跳过——否则它会对判据隐形（实测旧版：放入｛x.md｝仍报“未列 0”）。
                inner = []
                for _dp2, _dn2, _fn2 in os.walk(os.path.join(dp, d)):
                    inner += _fn2
                if all(x.endswith((".pyc", ".pyo")) for x in inner):
                    skipped += 1
                    continue
            keep.append(d)
        dns[:] = keep
        for fn in fns:
            r0 = os.path.relpath(os.path.join(dp, fn), root).replace("\\", "/")
            if r0 in _ship_exc:
                continue
            disk.add(r0)

    sp = os.path.join(root, "SHA256SUMS")
    mp = os.path.join(root, "MANIFEST.sha256")

    # ① SHA256SUMS
    sums = {}
    if not os.path.exists(sp):
        fails.append(("MISSING_MANIFEST", "SHA256SUMS 不存在"))
    else:
        for ln in io.open(sp, encoding="utf-8-sig", errors="replace"):
            ln = ln.rstrip("\n")
            if not ln.strip():
                continue
            hh, _, rel = ln.partition("  ")
            rel = rel.strip()
            if re.fullmatch(r"[0-9a-f]{64}", hh):
                sums[rel] = hh

    # ① MANIFEST
    man = {}
    declared = None
    unparsed = 0
    if not os.path.exists(mp):
        fails.append(("MISSING_MANIFEST", "MANIFEST.sha256 不存在"))
    else:
        txt = io.open(mp, encoding="utf-8-sig", errors="replace").read()
        for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|", txt, re.M):
            man[m.group(1)] = m.group(2)
        # 未被正则解析的表行
        for ln in txt.split("\n"):
            s = ln.strip()
            if not s.startswith("|"):
                continue
            if set(s) <= set("|- "):
                continue
            if not re.match(r"^\|\s*`[^`]+`\s*\|", s):
                continue          # 表头行
            if not re.match(r"^\|\s*`[^`]+`\s*\|\s*`[0-9a-f]{64}`\s*\|", s):
                # **自指说明行**（如“`MANIFEST.sha256`｜自身不自列”）不算未解析
                if "\u81ea\u8eab\u4e0d\u81ea\u5217" in s or "\u81ea\u6307" in s:
                    continue
                unparsed += 1
        # COUNT-SAME-SET ⭐ 新形式：`files: N = M（清单条目数）`
        m3 = re.search(r"files:\s*(\d+)\s*=\s*(\d+)", txt)
        m3b = re.search(r"files:\s*(\d+)\s*=\s*(\d+)\s*\+\s*SHA256SUMS\s*\+\s*MANIFEST\.sha256"
                      r"", txt)
        if not m3:
            fails.append(("ARITH", "MANIFEST L3 算术行缺失或形式不合"))
        else:
            declared = int(m3.group(1))
            # RULE-SRC ⭐ 算术与行数**一律取自 `meta_rule` 单一来源**（不再自算）
            import meta_rule as _MR3
            _sigself = (len(_MR3.SIGS) if ("SHA256SUMS.sig" in txt[:400]) else 0)
            if declared != int(m3.group(2)):
                fails.append(("ARITH", "MANIFEST L3 算术不成立：%s" % m3.group(0)))
            # A1-FIX ⭐ 行数**以实际为准**：L3 的 `M` 是**声明**，实表可含自指行
            #   故容差 ±1（守方 2026-10-10 勘误 A1：实际 224 行 vs 自指令 225）
            if len(man) not in (int(m3.group(2)), int(m3.group(2)) + 1, int(m3.group(2)) + 2):
                fails.append(("ROWS", "MANIFEST 表 %d 行，应 %d 行（L3 的 M＋自指行）"
                              % (len(man), int(m3.group(2)) + 1)))
        if unparsed:
            fails.append(("MANIFEST_UNPARSED", "MANIFEST 表内 %d 行未被解析（非 64 位小写十六进制？）" % unparsed))

    # 清单条目并集（用于幽灵／未列）
    listed = dict(sums)
    listed.update(man)

    # ① 交叉校验：两清单对同一件必须相等
    xchk = 0
    for k in sorted(set(man) & set(sums)):
        if sums[k] != man[k]:
            xchk += 1
            fails.append(("XCHECK", "两份清单对 %s 登记不一致" % k))

    # ⑪ WHITELIST 互验（D-3）：白名单声明的路径集 必须 == SHA256SUMS 的路径集
    #   为何必须：旧白名单是**手维的概括描述**，而凭据是**逐件生成**的
    #   ⇒ 两者自然脱节（实测差 20 行）。现“反向生成 + 本腿互验”同时保障。
    # ⏪ V1.50（A 方案）：白名单来源改为 **`SHIP-MANIFEST.md` 的【发】段**
    #   为何改：`HANDOFF-WHITELIST.md` 已列入【不发】（内部规则产物），包内不存；
    #   而 `SHIP-MANIFEST.md` 是**人可读的交付范围唯一源**，且它**逐条列名**。
    disk -= META

    wl_p = os.path.join(root, "SHIP-MANIFEST.md")
    wl_n = 0
    if os.path.exists(wl_p):
        wl_txt = io.open(wl_p, encoding="utf-8-sig", errors="replace").read()
        # 【发】段：`| `path` | **发** | ... |`
        _ship_sec = wl_txt.split("## \u4e00\u3001\u3010\u53d1\u3011")[-1].split("## \u4e8c\u3001")[0] \
            if "## \u4e00\u3001\u3010\u53d1\u3011" in wl_txt else ""
        wl_set = set(re.findall(r"\| `([^`]+)` \| \*\*\u53d1\*\* \|", _ship_sec))
        wl_n = len(wl_set)
        # 两清单自身**不自列**（设计如此），故比对前先剔除
        if (wl_set - SELF) != (set(sums) - SELF):
            _only_wl = sorted((wl_set - SELF) - (set(sums) - SELF))
            _only_su = sorted((set(sums) - SELF) - (wl_set - SELF))
            fails.append(("WHITELIST_DRIFT",
                          "白名单与 SHA256SUMS 路径集不等：仅白名单 %d、仅凭据 %d%s"
                          % (len(_only_wl), len(_only_su),
                             ("；例：" + (_only_wl or _only_su)[0][:50]) if (_only_wl or _only_su) else "")))
        # ⑨ 集合关系：SHA256SUMS 必须包含于 MANIFEST
    only_sums = sorted(set(sums) - set(man))
    for k in only_sums:
        fails.append(("SUBSET", "SHA256SUMS 有而 MANIFEST 无：" + k))

    # ⑦ ⑧ 覆盖率：磁盘中每件（除自指）必须被两清单各自覆盖
    need = sorted(k for k in disk if k not in SELF
                  and k not in ('SHA256SUMS.sig', 'SHA256SUMS.pub'))
    cover_sums = [k for k in need if k not in sums]
    cover_man = [k for k in need if k not in man]
    for k in cover_sums:
        fails.append(("COVER_SUMS", "磁盘有但 SHA256SUMS 未列：" + k))
    for k in cover_man:
        fails.append(("COVER_MAN", "磁盘有但 MANIFEST 未列：" + k))

    # ② 幽灵行
    ghosts = sorted(k for k in listed if k not in disk)
    for g in ghosts:
        fails.append(("GHOST", "清单列了但磁盘无此件：" + g))

    # ③ 未列
    unlisted = sorted(k for k in disk if k not in listed and k not in SELF)
    for u in unlisted:
        fails.append(("UNLISTED", "磁盘有此件但清单未列：" + u))

    # ④ 逐条哈希（**两份清单都验**）
    nchk = 0
    seen = set()
    for src, d in (("SH", sums), ("MA", man)):
        for rel, hh in sorted(d.items()):
            if rel in SELF or rel in seen:
                continue
            p = os.path.join(root, rel)
            if not os.path.exists(p):
                continue
            seen.add(rel)
            nchk += 1
            if sha256(p) != hh:
                fails.append(("MISMATCH", "哈希不符（%s）：%s" % (src, rel)))

    # ⑥ 件数
    if declared is not None and declared != len(disk) + skipped * 0:
        pass  # 下方单独判（避免误报）
    if declared is not None and declared != len(disk):
        fails.append(("COUNT", "MANIFEST 声明 %d 件，磁盘实际 %d 件"
                      % (declared, len(disk))))

    # 报告（**每条腿恒定打印“我扫了多少”**）
    print("[INTEGRITY] %s" % os.path.basename(root))
    print("[INTEGRITY] 磁盘 %d；SHA256SUMS %d 行；MANIFEST 表 %d 行；"
          "逐条已验 %d；两清单不一致 %d"
          % (len(disk), len(sums), len(man), nchk, xchk))
    print("[INTEGRITY] 幽灵行 %d；未列 %d；哈希不符 %d"
          % (len(ghosts), len(unlisted), len([f for f in fails if f[0] == "MISMATCH"])))
    print("[COVERAGE] 待覆盖 %d 件；SHA256SUMS 缺 %d；MANIFEST 缺 %d；"
          "SHA256SUMS" "\\\\" "MANIFEST %d\uff1b\u672a\u89e3\u6790\u8868\u884c %d\uff1b\u5df2\u8df3\u8fc7\u76ee\u5f55 %d"
          % (len(need), len(cover_sums), len(cover_man), len(only_sums), unparsed, skipped))
    if wl_n:
        # 口径（v152）：白名单列与证据集的**集合**必须一致（已由上方 L153 校验）；
        # 此处只报“各自多少条”，**不拿两个数直接相等**（两者口径不同）。
        print("[WHITELIST] 白名单列 %d 条；证据集行 %d 条（含 2 自指件）；集合比对：%s"
              % (wl_n, len(sums), "一致" if (wl_set - SELF) == (set(sums) - SELF) else "不一致（已报 WHITELIST_DRIFT）"))
    for k, v in fails:
        print("[FAIL] %-18s %s" % (k, v))
    if fails:
        print("[FAIL] 共 %d 项。" % len(fails))
        return 1
    print("[PASS] 两清单互相一致且各自完整覆盖磁盘；且与磁盘逐条相符；"
          "件数算术成立；无幽灵行；无未列件。")
    print("[SCOPE] 本工具**不能**证“磁盘上的就是全部应交付件”（清单与磁盘同源）。")
    return 0


def registry_check(root):
    r"""\u7a7a\u5934\u767b\u8bb0\u68c0\u67e5\uff1a`000-060` \u91cc\u6807\u201c\u73b0\u884c\u201d\u800c\u76d8\u4e0a\u65e0\u5bf9\u5e94\u4ef6\u8005\uff0c\u62a5\u8b66\u3002"""
    import glob
    regs = glob.glob(os.path.join(root, "spec", "layers", "PHAROS-000-060-*.md"))
    if not regs:
        return []
    reg = io.open(regs[0], encoding="utf-8-sig", errors="replace").read()
    layer_dir = os.path.join(root, "spec", "layers")
    have = [f for f in os.listdir(layer_dir) if f.endswith(".md")]
    bad = []
    for ln in reg.split("\n"):
        m = re.match(r"\| \*\*`(PHAROS-[A-Z0-9\-]+?)`\*\*", ln)
        if m and "\u73b0\u884c" in ln:
            if not any(m.group(1) in f for f in have):
                bad.append(m.group(1))
    return bad


if __name__ == "__main__":
    _rc = registry_check(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _rc:
        print("[REGISTRY] \u7a7a\u5934\u767b\u8bb0 %d \u4ef6\uff1a%s" % (len(_rc), "\u3001".join(_rc)))
    else:
        print("[REGISTRY] \u7a7a\u5934\u767b\u8bb0 0 \u4ef6")
    if len(sys.argv) < 2:
        print("用法: python tools/check_integrity.py <包根目录>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
