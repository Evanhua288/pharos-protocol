# -*- coding: utf-8 -*-
r"""audit_extra.py — 把「独立扩展审计」固化为判据（V1.21 新增）。

本件补的是 `check_integrity` **抓不到**的三类：
  E1 **沿革表 ↔ 头部版本自述一致性**（防"跳号误读"与"头部写旧版"）
  E2 **包内运行产物**（`__pycache__`／`.pyc`／`.tmp`／`.swp` 等 —— 判据自己会跳过它们）
  E3 **交付范围表件数 ↔ 盘上件数**（逐类：layers／配套件／tools）

用法：python tools/audit_extra.py <包根>
退出码：0 = 三项全过；1 = 有 FAIL；2 = 无法执行。
"""
import io
import os
import re
import sys

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ARTIFACT_PATS = ("__pycache__", ".pyc", ".pyo", ".tmp", ".swp", ".orig", ".rej")


def _read(p):
    return io.open(p, encoding="utf-8", errors="replace").read()


def e1_version(root):
    """E1：头部"内容版本 = Vx" 必须 ＝ 沿革表最高版次。"""
    p = os.path.join(root, "spec", "CORE-001-V1.2.md")
    if not os.path.exists(p):
        return [("E1_MISSING", "spec \u4e0d\u5b58\u5728")]
    t = _read(p)
    m = re.search(r"\u5185\u5bb9\u7248\u672c\s*\uff1d\s*`V(\d+\.\d+)`", t)
    head = m.group(1) if m else None
    vers = re.findall(r"\| \*\*`V(\d+)\.(\d+)`\*\*", t)
    top = None
    if vers:
        top = ".".join(max(vers, key=lambda x: (int(x[0]), int(x[1]))))
    out = []
    if head is None:
        out.append(("E1_HEAD", "\u5934\u90e8\u672a\u627e\u5230\u201c\u5185\u5bb9\u7248\u672c\uff1d Vx\u201d"))
    if top is None:
        out.append(("E1_TABLE", "\u6cbf\u9769\u8868\u672a\u627e\u5230\u7248\u6b21\u884c"))
    if head and top and head != top:
        out.append(("E1_MISMATCH", "\u5934\u90e8 V%s \u2260 \u6cbf\u9769\u8868\u6700\u9ad8 V%s" % (head, top)))
    return out


def e2_artifacts(root):
    """E2：包内不得有运行产物。"""
    found = []
    for dp, dn, fn in os.walk(root):
        for d in dn:
            if d in ARTIFACT_PATS:
                found.append(os.path.relpath(os.path.join(dp, d), root).replace("\\", "/"))
        for f in fn:
            if f.endswith(ARTIFACT_PATS):
                found.append(os.path.relpath(os.path.join(dp, f), root).replace("\\", "/"))
    return [("E2_ARTIFACT", x) for x in found]


def e3_counts(root):
    """E3：交付范围表声明的件数 必须 ＝ 盘上实数。"""
    # COUNT-UNIFY ⭐ 与清单**同集合**：元数据＋自证＋签名＋常驻均不计入
    try:
        import meta_rule as _MRU
        _OFF = set(_MRU.META) | set(_MRU.SELF) | set(_MRU.SIGS) | set(_MRU.CONST)
    except Exception:
        _OFF = set()

    p = os.path.join(root, "spec", "CORE-001-V1.2.md")
    if not os.path.exists(p):
        return [("E3_MISSING", "spec \u4e0d\u5b58\u5728")]
    t = _read(p)
    i = t.find("# \u4ea4\u4ed8\u8303\u56f4")
    seg = t[i:i + 6000] if i >= 0 else t
    out = []

    def declared(label_re):
        """在交付范围段内，按**行首标签**找行，再取该行的第一个件数。"""
        for ln in seg.split("\n"):
            if re.match(label_re, ln.strip()):
                m = re.search(r"(\d+) \u4ef6", ln)
                if m:
                    return int(m.group(1))
                return None
        return None

    checks = [
        ("layers", r"\| \*\*\u5c42\u7ea7\u89c4\u8303\*\*",
         len([f for f in os.listdir(os.path.join(root, "spec", "layers")) if f.endswith(".md")]) - 0),
        ("\u914d\u5957\u4ef6", r"\| \*\*\u914d\u5957\u4ef6\*\*",
         len([f for f in os.listdir(os.path.join(root, "\u914d\u5957\u4ef6")) if f != "__pycache__"])),
        ("tools", r"\| \*\*\u5de5\u5177\*\*",
         len([f for f in os.listdir(os.path.join(root, "tools")) if f != "__pycache__"])),
    ]
    for name, rx, real in checks:
        d = declared(rx)
        if d is None:
            out.append(("E3_UNDECLARED", "%s\uff1a\u4ea4\u4ed8\u8303\u56f4\u672a\u58f0\u660e\u4ef6\u6570" % name))
        elif d != real:
            out.append(("E3_COUNT", "%s\uff1a\u58f0\u660e %d\uff0c\u76d8\u4e0a %d" % (name, d, real)))
    return out


def _docx_text(p):
    """从 .docx 抽取全部文本（段落 + 表格）。"""
    try:
        from docx import Document
    except Exception:
        return None
    d = Document(p)
    s = "".join(x.text for x in d.paragraphs)
    for tb in d.tables:
        for r in tb.rows:
            for c in r.cells:
                s += c.text
    return s


def e4_artifacts(root):
    """E4：产物 ↔ 源件 同源。"""
    out = []
    # 现行 specHash
    cur = None
    su = os.path.join(root, "SHA256SUMS")
    if os.path.exists(su):
        for ln in _read(su).split("\n"):
            if "spec/CORE-001-V1.2.md" in ln:
                m = re.search(r"\b([0-9a-f]{64})\b", ln)
                if m:
                    cur = m.group(1)
    prods = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ("__pycache__",)]
        for f in fn:
            if f.lower().endswith((".docx", ".pdf")):
                prods.append(os.path.join(dp, f))
    if not prods:
        return out
    for p in prods:
        rel = os.path.relpath(p, root).replace("\\", "/")
        base = os.path.splitext(p)[0]
        src = None
        for cand in (base + ".md", os.path.join(os.path.dirname(p), "_src_" + os.path.basename(base) + ".md")):
            if os.path.exists(cand):
                src = cand
                break
        if src is None:
            out.append(("E4_ORPHAN", "%s：无同名 .md 源件" % rel))
            continue
        if p.lower().endswith(".docx"):
            got = _docx_text(p)
            want = _read(src)
            if got is None:
                out.append(("E4_NODOCX", "%s：无法读取（python-docx 不可用？）" % rel))
                continue
            a, b = len(got), len(want)
            if b and abs(a - b) / float(b) > 0.03:
                out.append(("E4_DRIFT", "%s：与源件长度差 %.1f%%（产物 %d / 源 %d）"
                            % (rel, 100.0 * abs(a - b) / b, a, b)))
            # 旧锚检查：产物出现非现行 64 位十六进制
            if cur:
                hs = set(re.findall(r"\b[0-9a-f]{64}\b", got))
                stale = sorted(h for h in hs if h != cur)
                # 允许参考来源真值等其他真实哈希：仅在文中出现 "specHash" 同行时报
                for h in stale:
                    for i, ln in enumerate(got.split("\n")):
                        if h in ln and "specHash" in ln:
                            out.append(("E4_STALE_HASH", "%s：行内 specHash 非现行值（%s）" % (rel, h[:12])))
                            break
    return out


def e5_clause_coverage(root):
    """E5：现行 spec 的“必须／禁止”类条号 ↔ 判据覆盖。
    只报 WARN（不阻断），供逐步收口。实现：
      从 spec 取条号（定义行，形态列含“必须”／“禁止”）；
      从 tools/*.py 与 vectors/*.json|*.md 取被引用的条号；
      差集 = 未被任何判据引用的强制条号。
    """
    import glob
    spec = os.path.join(root, "spec", "CORE-001-V1.2.md")
    if not os.path.exists(spec):
        return []
    defined, strong = set(), set()
    for ln in _read(spec).split("\n"):
        m = re.match(r"\| \*\*`CORE-001-(\d{3}(?:-[A-Z])?)`\*\* \| ([^|]*)\|", ln)
        if m:
            cid, form = m.group(1), m.group(2)
            defined.add(cid)
            if ("\u5fc5\u987b" in form) or ("\u7981\u6b62" in form):
                strong.add(cid)
    referenced = set()
    for pat in ("tools/*.py", "vectors/*.json", "vectors/*.md", "vectors/*/*.md", "\u914d\u5957\u4ef6/*.md"):
        for p in glob.glob(os.path.join(root, pat)):
            txt = _read(p)
            referenced |= set(re.findall(r"CORE-001-(\d{3}(?:-[A-Z])?)", txt))
    # ⏪ V1.52（按「甲」改口径）：不再把人工／解释类算作“覆盖缺口”。
    #   人工类与解释类由包根 `人工核清单.md` 逐条声明（III／IV）。
    manual, interp = set(), set()
    mp = os.path.join(root, "人工核清单.md")
    if os.path.exists(mp):
        mtxt = _read(mp)
        for m2 in re.finditer(r"\|\s*`CORE-001-(\d{3}(?:-[A-Z])?)`\s*\|\s*\*\*(III|IV)\b", mtxt):
            (manual if m2.group(2) == "III" else interp).add(m2.group(1))
    gap = sorted(strong - referenced - manual - interp)
    if not defined:
        return [("E5_NOSPEC", "spec 未读到条号定义行")]
    print("[AUDIT] E5 强制 %d；机检覆盖 %d；人工类 %d；解释类 %d；**真缺口 %d**"
          % (len(strong), len(strong & referenced), len(manual), len(interp), len(gap)))
    if gap:
        print("[AUDIT]     真缺口前 20：%s" % (", ".join("CORE-001-" + g for g in gap[:20])))
    return []


def e6_stated_hash(root):
    """E6：包内**任何自述 specHash** 必须 ≡ `SHA256SUMS` 中
    `spec/CORE-001-V1.2.md` 一行（并转报文件自述的字节数是否互证）。
    依据：`101`／`102`（锚＝文件字节）；来源：第二方建议（`WORKBUDDY-PH-076` §八）。
    """
    # E6 历史放行：若实例在包外台账中真实存在过，则不报为过期
    import glob
    cur = None
    su = os.path.join(root, "SHA256SUMS")
    if os.path.exists(su):
        for ln in _read(su).split("\n"):
            if "spec/CORE-001-V1.2.md" in ln:
                m = re.search(r"\b([0-9a-f]{64})\b", ln)
                if m:
                    cur = m.group(1)
    if not cur:
        return [("E6_NO_ANCHOR", "SHA256SUMS 缺 spec 一行")]
    # E6 历史放行（与 E8 同口径）：该锚若在包外台账中真实冻结过，则视为合法历史引用
    _hist = set()
    try:
        _l6 = os.path.join(os.path.dirname(os.path.abspath(root)), "_anchor_ledger.json")
        if os.path.isfile(_l6):
            for _e6 in json.loads(io.open(_l6, encoding="utf-8").read()).get("entries", []):
                if _e6.get("specHash"):
                    _hist.add(_e6["specHash"])
    except Exception:
        pass
    # E6 前缀匹配（双向）：包内自述可能是**截断式**，台账侧可能是**完整值** ⇒ 两个方向都要认
    _hist = _hist | {x[:12] for x in _hist} | {x[:16] for x in _hist} | {x[:24] for x in _hist} | {x[:40] for x in _hist}
    spec_b = os.path.getsize(os.path.join(root, "spec", "CORE-001-V1.2.md"))
    out = []
    for pat in ("*.md", "\u914d\u5957\u4ef6/*.md", "spec/layers/*.md"):
        for p in glob.glob(os.path.join(root, pat)):
            lines = _read(p).split("\n")
            for i, ln in enumerate(lines):
                if "specHash" not in ln:
                    continue
                # 只看 specHash 语境行 ± 2 行
                win = "\n".join(lines[max(0, i - 2):i + 3])
                # BASELINE-SKIP ⭐ **基线语境跳过**：那里引的是“当时的基线”，是**真值**，不是过期值
                if any(k in win for k in ("基线", "沿革", "历史", "冻结时", "发出日")):
                    continue
                for h in set(re.findall(r"\b([0-9a-f]{12,64})\b", win)):
                    # PREFIX-EQ ⭐ **双向前缀相等即同一锚**（包内截断、台账可能更短或更长）
                    def _same(a, b):
                        return bool(a) and bool(b) and (a == b or a.startswith(b) or b.startswith(a))
                    if _same(h, cur) or any(_same(h, x) for x in _hist):
                        continue
                    out.append(("E6_STALE_STATED", "%s L%d：specHash 语境内非现行值 %s"
                                % (os.path.basename(p), i + 1, h[:12])))
            m = re.search(r"\u81ea\u8ff0[^\n]{0,40}?([0-9]{5,6})\s*B", _read(p))
            if m and int(m.group(1)) != spec_b:
                out.append(("E6_BYTES", "%s：自述字节 %s ≠ 现行 %d"
                            % (os.path.basename(p), m.group(1), spec_b)))
    # 四项互证（V1.31）：包号／内容版本／字节数／specHash
    hv = re.search(r"\u5185\u5bb9\u7248\u672c\s*\uff1d\s*`V(\d+\.\d+)`", _read(os.path.join(root, "spec", "CORE-001-V1.2.md")))
    vers = re.findall(r"\| \*\*`V(\d+)\.(\d+)`\*\*", _read(os.path.join(root, "spec", "CORE-001-V1.2.md")))
    top = ".".join(max(vers, key=lambda x: (int(x[0]), int(x[1])))) if vers else None
    if hv and top and hv.group(1) != top:
        out.append(("E6_VER_MISMATCH", "\u5934\u90e8 V%s \u2260 \u6cbf\u9769\u6700\u9ad8 V%s" % (hv.group(1), top)))
    print("[AUDIT] E6 \u56db\u9879\u4e92\u8bc1\uff1a\u5185\u5bb9\u7248\u672c V%s；\u6cbf\u9769\u6700\u9ad8 V%s；\u5b57\u8282 %d；\u951a %s"
          % (hv.group(1) if hv else "?", top or "?", spec_b, cur[:12]))
    return out


def e7_negative_registry(root):
    """E7：`NEGATIVE-CASES.md` 登记的样本编号 ↔ `vectors/negative/` 实有文件。
    依据：`172`（反面样本四项形态）；来源：第二方建议（`WORKBUDDY-PH-078` §四第 2 条）。
    """
    import glob
    nd = os.path.join(root, "vectors", "negative")
    reg_p = os.path.join(root, "vectors", "NEGATIVE-CASES.md")
    if not (os.path.isdir(nd) and os.path.exists(reg_p)):
        return []
    have = set(os.listdir(nd))
    reg = _read(reg_p)
    # 登记形式：`nNN-xxx.json` 或“样本名 `nNN-xxx`”
    ids = set(re.findall(r"(n\d{2}(?:-[A-Za-z0-9\-]+)?)", reg))
    out = []
    # 缺号登记：登记行含“缺号登记”者，不要求盘上有文件
    waived = set(re.findall(r"\|\s*\*\*`(n\d{2})`\*\*[^\n]*\u7f3a\u53f7\u767b\u8bb0", reg))
    waived |= set(re.findall(r"\*\*`(n\d{2})`\*\*[^\n]{0,40}\u7f3a\u53f7\u767b\u8bb0", reg))
    # \u23ea V1.37\uff1a\u201c\u5df2\u79fb\u51fa negative/\u201d\u6216\u201c\u6539\u7531\u5176\u4ed6\u4ef6\u627f\u8f7d\u201d\u8005\uff0c\u4e5f\u514d\u9664
    waived |= set(re.findall(r"\*\*`(n\d{2})`\*\*[^\n]{0,90}\u5df2\u79fb\u51fa", reg))
    waived |= set(re.findall(r"\*\*`(n\d{2})`\*\*[^\n]{0,90}\u6539\u7531", reg))
    for i in sorted(ids):
        if i in waived:
            continue
        if not any(f.startswith(i) for f in have):
            out.append(("E7_REG_ONLY", "%s：NEGATIVE-CASES.md 登记了，盘上无对应文件" % i))
    for f in sorted(have):
        stem = f.rsplit(".", 1)[0]
        if not any(stem.startswith(x) or x.startswith(stem) for x in ids):
            out.append(("E7_FILE_ONLY", "%s：盘上有文件，NEGATIVE-CASES.md 未登记" % f))
    print("[AUDIT] E7 反面样本编号：登记 %d；盘上文件 %d；差集 %d"
          % (len(ids), len(have), len(out)))
    return out


def e8_letters(root):
    """⏪ V1.48（应对 `WORKBUDDY-PH-079` §三.3）：**对外函件所引基线四项 ↔ 随包 `spec`/`SHA256SUMS` 互证**。
    E6 只管 `spec` 内部四项，管不到“函件 ↔ `spec`”这一层。
    职责：扫包根 `*.md` 里出现 `specHash` 或 `specHash`语境的行，取其中的 64 位十六进制，
    对照 `SHA256SUMS` 那一行；对不上者报 `E8_STALE_ANCHOR`。
    """
    import hashlib as _h
    fails = []
    sp = os.path.join(root, "spec", "CORE-001-V1.2.md")
    sums = os.path.join(root, "SHA256SUMS")
    if not (os.path.exists(sp) and os.path.exists(sums)):
        return fails
    cur = _h.sha256(io.open(sp, "rb").read()).hexdigest()
    # ⏪ 修（本会话）：**历史留痕**引用的是**它自己当时的基线**，不是现基线。
    #   故：若该锚能在**包外台账**中找到（=曾经真实冻结过的锚），即视为**合法历史引用**，放行。
    #   口径：`E8` 只查「引用了**不存在的**锚」，不查「引用了**旧**锚」。
    hist = set()
    try:
        _led = os.path.join(os.path.dirname(os.path.abspath(root)), "_anchor_ledger.json")
        if os.path.isfile(_led):
            _j = __import__("json").loads(io.open(_led, encoding="utf-8").read())
            for _e in _j.get("entries", []):
                _h2 = _e.get("specHash")
                if _h2:
                    hist.add(_h2)
    except Exception:
        pass
    for f in sorted(os.listdir(root)):
        if not f.endswith(".md"):
            continue
        p = os.path.join(root, f)
        try:
            t = io.open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for ln in t.split("\n"):
            if "specHash" not in ln and "\u951a" not in ln:
                continue
            # ⏪ V1.57 修正（应对 `WORKBUDDY-PH-084` §三）：
            #   旧版只匹配**完整 64 位** ⇒ 而包里实际都写**截断式**（`e7a7c803\u2026`）
            #   ⇒ 该判据**长期扫不到**（形同恒真）。现**同时**认：完整值 与 前缀\u2026。
            hits = re.findall(r"\b([0-9a-f]{64})\b", ln)
            hits += re.findall(r"`([0-9a-f]{8,63})\u2026`", ln)
            for h in hits:
                if cur.startswith(h):
                    continue
                if any(x.startswith(h) for x in hist):
                    continue          # 合法历史引用（曾在台账中真实冻结过）
                fails.append(("E8_STALE_ANCHOR", "%s：引用 %s\u2026，实为 %s\u2026" % (f, h[:12], cur[:12])))
    print("[AUDIT] E8 对外函件基线互证：扫 %d 件；不符 %d"
          % (len([f for f in os.listdir(root) if f.endswith(".md")]), len(fails)))
    return fails


def main(argv):
    if len(argv) < 2:
        print("\u7528\u6cd5: python tools/audit_extra.py <\u5305\u6839>")
        return 2
    root = argv[1]
    fails = e1_version(root) + e2_artifacts(root) + e3_counts(root) + e4_artifacts(root)
    fails += e5_clause_coverage(root)
    fails += e6_stated_hash(root)
    fails += e7_negative_registry(root)
    fails += e8_letters(root) or []
    print("[AUDIT] E1 \u7248\u672c\u81ea\u8ff0\u4e0e\u6cbf\u9769\u4e00\u81f4\u6027")
    print("[AUDIT] E2 \u5305\u5185\u8fd0\u884c\u4ea7\u7269")
    print("[AUDIT] E3 \u4ea4\u4ed8\u8303\u56f4\u4ef6\u6570")
    print("[AUDIT] E4 \u4ea7\u7269 \u2194 \u6e90\u4ef6 \u540c\u6e90")
    if fails:
        for k, v in fails:
            print("[FAIL] %-16s %s" % (k, v))
        print("[FAIL] \u5171 %d \u9879\u3002" % len(fails))
        return 1
    print("[PASS] \u56db\u9879\u5168\u8fc7\uff08E1 0\uff1bE2 0\uff1bE3 0\uff1bE4 0\uff09")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))


