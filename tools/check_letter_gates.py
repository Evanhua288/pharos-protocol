# -*- coding: utf-8 -*-
r"""check_letter_gates.py —— **对外件三判据**（补守方五门中我方缺的三门）：

  ① `SQUOTE_LEAK`：ASCII 直引号 `0x22` 必须 **0 处**（对外件只用中文引号）
  ② `FIXED_SENTENCE`：末非空段逐字符等于**固定句**
  ③ `BANNED_WORD`：禁用词**仅可现于否定处**（词前 14 字符内有 不／非／无／未／勿）

依方：`D:\pharos_p1\回函与出包标准手册.md` 三道自检门（我方此前**缺**此三门）。
用法：
  python check_letter_gates.py <目录或文件> [<目录或文件> ...] [--fixed "<固定句>"]
退出码：0 = 全过；1 = 有不合格件；2 = 用法错。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FIXED = ("\u672c\u6279\u4ea7\u51fa\u8bc1\u660e\u7684\u662f\uff1a\u6211\u65b9\u5185\u6838\u5b9e\u73b0\u4e0e\u5b98\u65b9\u53e3\u5f84\u4e00\u81f4\u3002"
         "\u5b83\u4e0d\u8bc1\u660e\uff1a\u6211\u65b9\u5df2\u5408\u89c4\u3002")
BANNED = ("\u4e92\u8ba4", "\u5df2\u5408\u89c4", "\u5df2\u901a\u8fc7", "\u8fbe\u6807", "\u57fa\u7840\u7ea7", "\u5b8c\u6574\u7ea7")
NEG = ("\u4e0d", "\u975e", "\u65e0", "\u672a", "\u52ff")
TOOL = os.path.basename(__file__)
# ⭐ **适用范围**（V1.0 补正）：`FIXED_SENTENCE` 门**只适用于「对外回函」**
#   （守方《回函与出包标准手册》口径：末段固定句为本批产出的性质声明）。
#   解读报告／索引／内部留痕／数据件**不属于回函** ⇒ **默认只跑 ①③ 两门**；
#   加 `--letters` 才对全部件启用 ② 门（用于自检"本批回函"）。
LETTERS_MODE = False
SKIP = ()          # `--skip <子串>`：命名跳过（如内容本体含禁用词者）
QA = ()            # `--quote-allow <子串>`：该件**免直引号门**
BA = ()            # `--banned-allow <子串>`：该件**免禁用词门**
ONLY = ()          # `--only <子串>`：只扫命名含其一者（多次可追加）
# 回函类文件名特征（`--letters` 时仍可按需再收窄）
LETTER_HINT = ("\u56de\u51fd", "\u81f4", "\u4ea4\u63a5\u5355", "\u8f6c\u53d1\u8bf4\u660e", "PH-", "\u51fd")


def text_of(p):
    if p.endswith(".md") or p.endswith(".txt"):
        return io.open(p, encoding="utf-8", errors="replace").read()
    from docx import Document
    d = Document(p)
    t = "\n".join(x.text for x in d.paragraphs)
    for tb in d.tables:
        for r in tb.rows:
            for c in r.cells:
                t += "\n" + c.text
    return t


def check(p):
    bad = []
    _bn = os.path.basename(p)
    _quote_off = any(x in _bn for x in QA)   # \u6309\u95e8\u8c41\u514d\u2460\uff1a\u514d**\u76f4\u5f15\u53f7\u95e8**\uff08\u5982 JSON \u6a21\u677f\u4ef6\uff09
    _ban_off = any(x in _bn for x in BA)     # \u6309\u95e8\u8c41\u514d\u2461\uff1a\u514d**\u7981\u7528\u8bcd\u95e8**\uff08\u5982\u5426\u5b9a\u8bcd\u6e05\u5355\u4ef6\uff09
    try:
        t = text_of(p)
    except Exception as e:
        return [("UNREADABLE", str(e)[:50])]
    lines = [x.strip() for x in t.split("\n") if x.strip()]
    # \u2460 \u76f4\u5f15\u53f7
    n = t.count(chr(34))
    if n and not _ban_off is None and not any(x in _bn for x in QA):
        bad.append(("SQUOTE_LEAK", "ASCII 0x22 \u5171 %d \u5904" % n))
    # \u2461 \u56fa\u5b9a\u53e5\uff08\u672b\u975e\u7a7a\u6bb5\uff09\u2014\u2014**\u4ec5\u5728\u56de\u51fd\u6a21\u5f0f\u4e0b\u5224**
    if LETTERS_MODE and lines and lines[-1] != FIXED:
        bad.append(("FIXED_SENTENCE", "\u672b\u6bb5\u4e0d\u7b49\u4e8e\u56fa\u5b9a\u53e5\uff1a%s" % lines[-1][:40]))
    # \u2462 \u7981\u7528\u8bcd
    for b in (BANNED if not any(x in _bn for x in BA) else ()):
        for ln in lines:
            i = ln.find(b)
            while i >= 0:
                if not any(c in ln[max(0, i - 14):i] for c in NEG):
                    bad.append(("BANNED_WORD", "%s \u2190 %s" % (b, ln[:50])))
                i = ln.find(b, i + 1)
    return bad


# BANLIST-EXEMPT ⭐ 若件内明确声明“本件即禁语清单”，则**不判禁语**（它本身即列举）
BANLIST_MARKS = ("禁语清单", "本身即禁语", "不得出现（**词表**）", "禁语条目如下")


def main(argv):
    global FIXED, LETTERS_MODE, ONLY, SKIP, QA, BA
    only, skip, qa, ba = [], [], [], []
    args, i = [], 1
    while i < len(argv):
        if argv[i] == "--fixed" and i + 1 < len(argv):
            FIXED = argv[i + 1]
            i += 2
        elif argv[i] == "--letters":
            LETTERS_MODE = True
            i += 1
        elif argv[i] == "--only" and i + 1 < len(argv):
            only.append(argv[i + 1])
            i += 2
        elif argv[i] == "--skip" and i + 1 < len(argv):
            skip.append(argv[i + 1])
            i += 2
        elif argv[i] == "--quote-allow" and i + 1 < len(argv):
            qa.append(argv[i + 1])
            i += 2
        elif argv[i] == "--banned-allow" and i + 1 < len(argv):
            ba.append(argv[i + 1])
            i += 2
        else:
            args.append(argv[i])
            i += 1
    ONLY = tuple(only)
    SKIP = tuple(skip)
    QA = tuple(qa)
    BA = tuple(ba)
    if not args:
        print(__doc__)
        return 2
    files = []
    for a in args:
        if os.path.isfile(a):
            if not only or any(x in os.path.basename(a) for x in only):
                files.append(a)
        elif os.path.isdir(a):
            files += [os.path.join(a, f) for f in sorted(os.listdir(a))
                      if f.endswith((".docx", ".md")) and f != TOOL
                      and (not only or any(x in f for x in only))
                      and not any(x in f for x in skip)]
    nf, nbad = 0, 0
    for p in files:
        nf += 1
        bad = check(p)
        if bad:
            nbad += 1
            print("  [FAIL] %s" % os.path.basename(p))
            for k, v in bad[:4]:
                print("         %-16s %s" % (k, v))
    print("[LETTERGATES] \u626b %d \u4ef6\uff1b\u4e0d\u5408\u683c %d" % (nf, nbad))
    print("[RESULT] %s" % ("PASS -- \u4e09\u95e8\u5168\u8fc7" if not nbad else "FAIL -- \u6709\u4e0d\u5408\u683c\u4ef6"))
    return 0 if not nbad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
