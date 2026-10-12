# -*- coding: utf-8 -*-
r"""gate_headers.py —— **层件文件头门**（F-06 闭合门）。

判据（照 `10-整改验收标准` §一 T-件头）：
  1) 六字段**齐备**（38/38）：`编号`／`名称`／`上位`／`状态`／`性质`／`日期`；
  2) `状态` 取值 ⊂ {现行, 草案, 作废·仅追溯}；
  3) `性质` **含"生效"** 或明标 **"待生效"**。

判据来源与两处口径差异（**如实标注，不擅自放宽**）：
  · `PHAROS-000-070-文件头规范与附则编写规则-V1.0-20261006.md` **§1.1 六行文件头（顺序固定）**为：
    `编号／名称／上位／状态／**批准人**／日期` —— 其第 5 项是 **批准人**，**不是** `性质`；
  · 本门按 **T-件头判据**判（第 5 项＝`性质`），并把"000-070 §1.1 写批准人"记为 `[WARN]`（口径差异，需人裁）。
  · `名称`：000-070 §1.1 要求独立一行 `**名称**：`；但 F-06 基线（8/38）未把 `名称` 计为缺失
    ⇒ 本门**主判**接受"`**名称**：` 行 **或** 文首 H1 标题"，并**另报** `**名称**：` 字面行计数（严格口径）。

层件集合 ＝ `spec/layers/*.md` **排除 `件名清单.md`**（后者是清单/索引，不是协议件）。

纪律：**只读**（不写任何文件）。退出码 0＝PASS，1＝FAIL，2＝无法执行。

用法：
    python tools/gate_headers.py .            # 在包目录或 pharos-core 目录内
    python tools/gate_headers.py <根目录>
"""
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SIX = ["编号", "名称", "上位", "状态", "性质", "日期"]
STATES = ["现行", "草案", "作废·仅追溯"]
INDEX_NAME = "件名清单.md"
SCAN_LINES = 40          # 文件头扫描窗口（行）


def loc(head_lines, field):
    """字段所在行号（1 基，相对文件头）；找不到返回 None。"""
    rx = re.compile(r"\*\*" + field + r"\*\*\s*[:：]")
    for i, l in enumerate(head_lines, 1):
        if rx.search(l):
            return i
    return None


def value_of(head_lines, field):
    rx = re.compile(r"\*\*" + field + r"\*\*\s*[:：]\s*(.*)$")
    for l in head_lines:
        m = rx.search(l)
        if m:
            return m.group(1).strip()
    return None


def first_token(v):
    return re.split(r"[｜|]", v or "")[0].replace("*", "").strip()


def tracked_layers(root):
    for cand in (root, os.path.join(os.path.dirname(root), "pharos-core")):
        if os.path.isdir(os.path.join(cand, ".git")):
            try:
                out = subprocess.run(["git", "-C", cand, "ls-tree", "-r", "-z", "--name-only", "HEAD", "spec/layers"],
                                     capture_output=True).stdout
                return set(x.decode("utf-8") for x in out.split(b"\0") if x)
            except Exception:
                return set()
    return set()


def main(argv):
    if len(argv) < 2:
        print("usage: gate_headers.py <根目录>")
        return 2
    root = os.path.abspath(argv[1])
    la = os.path.join(root, "spec", "layers")
    if not os.path.isdir(la):
        print("[RESULT] FAIL -- 无 spec/layers：%s" % root)
        return 2

    allmd = sorted(f for f in os.listdir(la) if f.endswith(".md"))
    files = [f for f in allmd if f != INDEX_NAME]
    print("== gate_headers：%s" % root)
    print("   spec/layers/*.md＝%d；判定的层件＝%d（排除 `%s`）；扫描窗口＝前 %d 行"
          % (len(allmd), len(files), INDEX_NAME, SCAN_LINES))

    tracked = tracked_layers(root)
    bad = []
    field_missing = {k: [] for k in SIX}
    ok_files = []
    both_sp = []            # 状态＋性质 齐备（F-06 口径）
    strict_name = 0
    for f in files:
        L = io.open(os.path.join(la, f), encoding="utf-8", errors="replace").read().split("\n")
        head = L[:SCAN_LINES]
        got, where = {}, {}
        for k in SIX:
            w = loc(head, k)
            if k == "名称" and w is None:
                h1 = next((i for i, x in enumerate(L[:SCAN_LINES], 1) if x.strip().startswith("# ")), None)
                if h1 is not None:
                    w = h1
            got[k] = w is not None
            where[k] = w
            if not got[k]:
                field_missing[k].append(f)
        if loc(head, "名称") is not None:
            strict_name += 1
        if got["状态"] and got["性质"]:
            both_sp.append(f)
        miss = [k for k in SIX if not got[k]]
        if miss:
            bad.append((f, miss, where))
            continue
        sv = first_token(value_of(head, "状态"))
        pv = value_of(head, "性质") or ""
        if sv not in STATES:
            bad.append((f, ["状态取值非法(%r)" % sv], where))
            continue
        if "生效" not in pv:
            bad.append((f, ["性质未含'生效'(%r)" % pv[:24]], where))
            continue
        ok_files.append(f)

    print("   六字段齐备＝%d/%d" % (len(ok_files), len(files)))
    print("   ⭐ 状态＋性质 齐备＝%d/%d（F-06 基线口径）" % (len(both_sp), len(files)))
    print("   `**名称**：` 字面行＝%d/%d（严格口径；主判接受 H1 标题）" % (strict_name, len(files)))
    for k in SIX:
        if field_missing[k]:
            print("   缺 `%s`＝%d 件：%s" % (k, len(field_missing[k]),
                                          "、".join(x[:26] for x in field_missing[k][:6]) + (" …" if len(field_missing[k]) > 6 else "")))
    if tracked:
        un = [f for f in files if ("spec/layers/" + f) not in tracked]
        if un:
            print("   [INFO] 未被 HEAD 跟踪（工作树新增）＝%d 件：%s" % (len(un), "、".join(x[:30] for x in un[:4])))
    print("-" * 68)
    for f, miss, where in bad[:40]:
        pos = "；".join("%s: %s" % (k, ("L%d" % where[k]) if where.get(k) else "—") for k in miss)
        print("  [FAIL] %-56s 缺/非法：%s" % (f[:56], pos))
    if len(bad) > 40:
        print("  … 共 %d 件不合格" % len(bad))
    print("   [WARN] 口径差异：`000-070` §1.1 第 5 项写 **批准人**，T-件头判据写 **性质** —— 本门按 T-件头判，请人裁")
    ok = not bad
    print("  [RESULT] %s（不合格 %d／层件 %d）"
          % ("PASS -- 层件六字段齐备且枚举合法" if ok else "FAIL -- 层件文件头未齐备", len(bad), len(files)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
