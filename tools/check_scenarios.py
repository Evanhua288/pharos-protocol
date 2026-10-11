# -*- coding: utf-8 -*-
r"""check_scenarios.py — **情景与计数判据**（收缧 `E5` 真缺口的 II\/I 类）

每条断言在注释里标出它对应的 `CORE-001-xxx`。**只做可判定的**。
"""
import hashlib
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main(root):
    fails, n = [], 0
    spec = io.open(os.path.join(root, "spec", "CORE-001-V1.2.md"), encoding="utf-8", errors="replace").read()

    # ---- CORE-001-165：五对象字段总数 **三处一致**
    n += 1
    m = re.search(r"\u4e94对\u8c61\u5b57\u6bb5\u603b\u6570[^\n]{0,40}?(\d+)[^\n]{0,80}?`(\d\+\d\+\d\+\d\+\d+)`", spec)
    if not m:
        m = re.search(r"(`8\+7\+7\+6\+2`)[^\n]{0,60}?(30)", spec)
    if m:
        expr = m.group(1) if "+" in m.group(1) else m.group(2)
        tot = m.group(2) if "+" in m.group(1) else m.group(1)
        if sum(int(x) for x in expr.split("+")) != int(tot):
            fails.append(("C165", "字段数分解式与合计不符：%s ≠ %s" % (expr, tot)))
    else:
        fails.append(("C165", "未读到字段数分解式"))

    # ---- CORE-001-169：“直接改正不算新版本”的三类（可判：版本沿革里不得因错字单列版本）
    n += 1
    for ln in spec.split("\n"):
        if re.match(r"\| \*\*`V\d+\.\d+`\*\* \|", ln) and re.search(r"\u8865\u6b63\u9519\u5b57|\u6539\u9519\u5b57|\u9519\u5b57\u4fee\u6b63", ln):
            fails.append(("C169", "版本沿革中因错字单列版本：%s" % ln[:60]))

    # ---- CORE-001-193：同号异内容 ⇒ 拒收并报 E06（向量层可判）
    neg = os.path.join(root, "vectors", "negative")
    if os.path.isdir(neg):
        n += 1
        files = os.listdir(neg)
        if not any("dup" in f for f in files):
            fails.append(("C193", "缺同号异内容负向量（应有 dup-settle-id 类样本）"))

    # ---- CORE-001-147：SETTLE_DIFF 报文必带 settleId
    n += 1
    # ⭐ V1.61：改为**在条 147 与 §五C 的语境里判**（避开沿革表）
    _ok147 = False
    for _anchor in ("CORE-001-147", "五C"):
        _i = spec.find(_anchor)
        if _i < 0:
            continue
        _seg = spec[_i: _i + 1200]
        if "SETTLE_DIFF" in _seg and "settleId" in _seg:
            _ok147 = True
            break
    if "SETTLE_DIFF" not in spec:
        fails.append(("C147", "未读到 SETTLE_DIFF"))
    elif not _ok147:
        fails.append(("C147", "SETTLE_DIFF 必填 settleId 未在条 147／§五C 声明"))

    # ---- CORE-001-129：“账本相等必须逐条比对”不得以哈希相同代替
    n += 1
    has = ("逐条比对" in spec) and ("不得" in spec[spec.find("逐条比对") - 120: spec.find("逐条比对") + 120] if "逐条比对" in spec else "")
    if not has:
        fails.append(("C129", "未声明“账本相等必须逐条比对”"))

    # ---- CORE-001-185：冲正累计上限（可判：声明存在且引 E05）
    n += 1
    if "累计金额绝对值" not in spec or "E05" not in spec:
        fails.append(("C185", "冲正累计上限或 E05 未声明"))

    # ---- CORE-001-101 / CORE-001-102：**锚自洽** —— `SHA256SUMS` 那行 ≡ spec 实际 SHA-256
    #      （`102` 另判：行末统一 LF、不得先转换编码）
    n += 1
    sp = os.path.join(root, "spec", "CORE-001-V1.2.md")
    sums = os.path.join(root, "SHA256SUMS")
    if os.path.exists(sp) and os.path.exists(sums):
        raw = io.open(sp, "rb").read()
        real = hashlib.sha256(raw).hexdigest()
        line = ""
        for l in io.open(sums, encoding="utf-8", errors="replace").read().split("\n"):
            if "spec/CORE-001-V1.2.md" in l:
                line = l.strip()
                break
        if not line:
            fails.append(("C101", "SHA256SUMS 无 spec/CORE-001-V1.2.md 一行"))
        elif real not in line:
            fails.append(("C101", "SHA256SUMS 锚值与 spec 实际不符：%s" % line[:80]))
        if b"\r\n" in raw:
            fails.append(("C102", "spec 行末非 LF（含 CRLF）"))
    else:
        fails.append(("C101", "缺 spec 或 SHA256SUMS"))

    # ---- CORE-001-078 / CORE-001-084：**不一致须标 `specMismatch` 并列双方锚与版本号**
    n += 1
    if "specMismatch" not in spec:
        fails.append(("C078", "未声明 specMismatch 标注义务"))
    if not re.search(r"CORE-001-V<MAJOR>\.<MINOR>", spec):
        fails.append(("C084", "版本号形态 CORE-001-V<MAJOR>.<MINOR> 未声明"))


    # ---- CORE-001-032 / CORE-001-033 / CORE-001-153：**`amount` 口径三处必须一致**
    #   ⏪ 新增（应对 `ASTRALINK` 函 §3.1 冲突一暴露的内部矛盾）：
    #      `§二.4` 表行 与 `032`／`033` 与 `153` 三处说法必须同为「整数字符串／禁小数点」。
    n += 1
    flat = re.sub(r"[*`\s]", "", spec)
    has_int = ("amount必须为整数字符串" in flat) or ("amount" in flat and "整数字符串" in flat)
    has_nodot = "不得出现小数点" in flat
    # 表行若写「十进制字符串」即与 032/033 矛盾
    tbl_decimal = re.search(r"\| \*\*`amount`\*\* \|[^\n]*\u5341\u8fdb\u5236\u5b57\u7b26\u4e32", spec)
    if not has_int:
        fails.append(("C032", "`amount` 未声明为整数字符串（见 `032`）"))
    if not has_nodot:
        fails.append(("C033", "未声明「不得出现小数点」（见 `033`）"))
    if tbl_decimal and "整数字符串" not in tbl_decimal.group(0):
        fails.append(("C032_TABLE", "`§二.4` 表行 `amount` 仍写「十进制字符串」，与 `032`／`033` 矛盾"))
    # ⭐ V1.60：真读**三处**（标题行／合计行／104 行）并两两相等
    n += 1
    m_t = re.search(r"##\s*二、五个对象与\*\*三十\*\*个字段", spec)
    t30 = "30" if m_t else None
    m_a = re.search(r"合计\s*\*\*(\d+)\*\*\s*字段", spec)
    a30 = m_a.group(1) if m_a else None
    m_104 = re.search(r"^\| \*\*`CORE-001-104`\*\*.*?字段数现为\s*(\d+)", spec, re.M)
    l104 = m_104.group(1) if m_104 else None
    if not (t30 and a30 and l104) or not (t30 == a30 == l104 == "30"):
        fails.append(("C165B", "字段数三处不一致（标题%s／合计%s／104 %s）" % (t30, a30, l104)))

    # ---- CORE-001-188-A：**基线重置条款三要件**（并列披露／标明生效尺度／年报不得只给新值）
    n += 1
    if "CORE-001-188-A" not in spec:
        fails.append(("C188A", "缺 `CORE-001-188-A`（基线重置条款）"))
    else:
        i0 = spec.find("CORE-001-188-A", spec.find("CORE-001-188-A") + 1)
        seg = spec[i0:i0 + 800]
        # ⚠️ 判据自身必修：件里用了大量 `**` 强调，会**拆断**关键词（如 `当前**适用`）⇒ 比对前先去掉标记
        seg = re.sub(r"[*`\s]", "", seg)
        for req, kw in (("并列披露", "并列"), ("标明当前生效", "当前适用"),
                        ("年报不得只给新值", "不得只给新值"), ("上浮锚", "上浮锚")):
            n += 1
            if kw not in seg:
                fails.append(("C188A", "`188-A` 缺要件：%s（关键词 `%s`）" % (req, kw)))

    # ---- CORE-001-097：验签须与 Attestation.by 一致；不一致报 E03
    n += 1
    if not (("Attestation.by" in spec or "`by`" in spec) and "E03" in spec):
        fails.append(("C097", "未声明“验证者 ≡ Attestation.by，不一致报 E03”"))

    # ---- CORE-001-193 / CORE-001-064：同内容重复只留首次、不报码
    n += 1
    if "只留首次" not in spec:
        fails.append(("C193", "未声明同内容重复“只留首次、不报码”"))

    # ---- CORE-001-194：反向查询**两态**（FOUND / NO_LOCAL_INDEX）且不得以“无权”代替
    n += 1
    if "NO_LOCAL_INDEX" not in spec or "settleIds" not in spec:
        fails.append(("C194", "反向查询两态或响应体字段未声明"))

    # ---- CORE-001-062：不一致必须报 gap=true
    n += 1
    if "gap=true" not in spec:
        fails.append(("C062", "未声明“不一致必须报 gap=true”"))

    # ---- CORE-001-048：routes.example.json 须有与注册路由的一致性校验
    n += 1
    if "routes" not in spec or "一致性校验" not in spec:
        fails.append(("C048", "routes 一致性校验未声明"))

    # ---- CORE-001-028：一律用 did:key
    n += 1
    if "did:key" not in spec:
        fails.append(("C028", "未声明 did:key"))

    print("[SCEN] 断言 %d 条；不符 %d" % (n, len(fails)))
    for t, m2 in fails:
        print("    [FAIL] %-6s %s" % (t, m2))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
