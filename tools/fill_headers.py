#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
tools/fill_headers.py —— 补齐 `spec/layers/` 38(+1) 件层件的件头缺失字段
                                    （task-25 / T2）

判据来源：
  · `10-整改验收标准-V1.0` §一 T-件头
  · lead 2026-10-12 裁决 1：`性质` 改为**确定性派生**，按 `000-060 §〇 规则 6`
    的两个原始口径取值 —— 现行→`生效件`；草案→`待生效`；作废·仅追溯→`作废·仅追溯`
  · lead 裁决 3：`000-070` 的"状态=草案／性质=生效件"两栏**不动**，另加一行裁定登记
  · lead 裁决 4.1：`状态` 登记原句带附注者，**取基值落盘**，附注**原样搬进新加的 `备注` 行**

硬纪律（**违反即停**）：
  1. **只增行**：本脚本**只做 insert**，从不替换、从不删除任何已有行。
  2. **不改正文行**：插入点固定在文件头的「编号」行之后（`---` 之前）。
  3. **不猜**：登记里取不出三选一基值者 → **不写**，列 `未覆盖`。
  4. 幂等：已有该字段者跳过。

用法：
  python tools/fill_headers.py <pkg_root> [--dry-run]
  pkg_root = 含 `spec/layers/` 的包根（默认 `.`）
"""
import io
import os
import re
import sys
import json

REG_NAME = "PHAROS-000-060-当前有效版本清单-V1.3-20261008.md"
LAYERS = os.path.join("spec", "layers")
SELF = os.path.basename(__file__)

# 规则 6 的两个口径 → 值
NATURE_BY_STATE = {
    "现行": "生效件",
    "草案": "待生效",
    "作废·仅追溯": "作废·仅追溯",
}
THREE_STATES = ("现行", "草案", "作废·仅追溯")

# 000-060 §〇 规则 6 的举证句（写进每条新增 备注，便于第三方复核）
RULE6 = "承 `000-060 §〇 规则 6`：状态＝版本状态；性质＝约束效力；两者同时成立方\"可作为当前依据引用\""

# 裁决 3 指定的裁定行（`000-070` 专用；纯新增，不动原两栏）
ROW_000_070 = (
    "> ⚠️ 本件\"状态＝草案／性质＝生效件\"的并存关系，经 `000-060 §〇 规则 6` 裁定为"
    "\"**内容可用、不得作为对外引用依据**\"；**本行不修改原两栏，只登记该裁定**。"
)


def load(path):
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read().split("\n")


def base_code(code):
    """`PHAROS-000-010-V1.0` → `PHAROS-000-010`"""
    return re.sub(r"-V\d+(\.\d+)*$", "", code or "")


def read_registry(reg_path):
    """从 000-060 登记反取 {件号: (名称, 版本, 状态原文)}；首个登记表为准。"""
    reg = {}
    for lineno, line in enumerate(load(reg_path), 1):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        m = re.search(r"`(PHAROS-[A-Z0-9\-]+)`", cells[0])
        if not m:
            continue
        code = m.group(1)
        if code in reg:          # §一…§十 先出现者为准；后表为历史档
            continue
        st = ""
        for c in cells[1:]:
            if re.search(r"(现行|草案|作废·仅追溯|空头|已交付|待用|未生效)", c):
                st = c
                break
        reg[code] = {
            "名称": re.sub(r"[*`]", "", cells[1]) if len(cells) > 1 else "",
            "版本": re.sub(r"[*`]", "", cells[2]) if len(cells) > 2 else "",
            "状态原文": st,
            "行": lineno,
        }
    return reg


FIELD_RE = r"\*{0,2}%s\*{0,2}\s*[：:]"


def head_region(lines):
    """文件头区行号区间 [0, end) —— 到首个独立 `---` 为止（>= 第 3 行）。"""
    end = min(len(lines), 40)
    for i, l in enumerate(lines[:40]):
        if l.strip() == "---" and i >= 2:
            end = i
            break
    return end


def has_field(lines, field, aliases=None):
    aliases = aliases or [field]
    end = head_region(lines)
    for l in lines[:end]:
        for a in aliases:
            if re.search(FIELD_RE % re.escape(a), l):
                return True
    return False


def find_anchor(lines):
    """插入锚点：`编号` 行之后。返回插入下标；找不到返回 None。"""
    end = head_region(lines)
    for i in range(end):
        if re.search(FIELD_RE % "编号", lines[i]):
            return i + 1
    return None


def derive_state(raw):
    """
    从登记状态原文取「基值 + 附注」。
    返回 (基值|None, 附注|None, 未覆盖理由|None)
    """
    if not raw:
        return None, None, "000-060 无该件登记"
    txt = re.sub(r"[*`]", "", raw).strip()
    if "空头" in txt:
        return None, None, "000-060 记为空头登记（盘上无件）"
    # 三选一基值（按长词优先，避免"作废·仅追溯"被"追溯"截断）
    for k in ("作废·仅追溯", "现行", "草案"):
        if txt.startswith(k):
            rest = txt[len(k):].strip()
            return k, (rest or None), None
    # 不含三选一基值 ⇒ 不猜
    return None, txt, "登记状态原文不含三选一基值：%s" % txt


def main(argv):
    root = "."
    dry = False
    for a in argv[1:]:
        if a == "--dry-run":
            dry = True
        elif not a.startswith("--"):
            root = a
    root = os.path.abspath(root)
    lay = os.path.join(root, LAYERS)
    reg_path = os.path.join(lay, REG_NAME)
    if not os.path.isdir(lay):
        print("[FAIL] 找不到 %s" % lay)
        return 1
    if not os.path.isfile(reg_path):
        print("[FAIL] 找不到权威登记 %s" % reg_path)
        return 1

    reg = read_registry(reg_path)
    files = sorted(f for f in os.listdir(lay)
                   if f.endswith(".md") and f != REG_NAME)

    changed = []
    uncovered = []
    skipped = []
    for fn in files:
        path = os.path.join(lay, fn)
        lines = load(path)
        code = ""
        end = head_region(lines)
        for l in lines[:end]:
            m = re.search(r"\*{0,2}编号\*{0,2}\s*[：:]\s*([^｜|\n]*)", l)
            if m and m.group(1).strip():
                code = m.group(1).replace("`", "").strip()
                break
        bc = base_code(code)
        r = reg.get(bc)

        if not bc or r is None:
            uncovered.append((fn, code or "(无编号)", "000-060 查无登记"))
            continue

        need_state = not has_field(lines, "状态")
        need_nat = not has_field(lines, "性质")
        # `000-070` 专用：两栏齐备，仅加裁定行
        need_row7070 = (bc == "PHAROS-000-070") and ("规则 6" not in "\n".join(lines[:end]))

        if not (need_state or need_nat or need_row7070):
            skipped.append((fn, bc, "两字段已齐备"))
            continue

        st_base, st_note, why = derive_state(r["状态原文"])
        add = []          # 待插入行（顺序：状态 → 性质 → 备注 → 裁定）
        notes = []

        if need_state:
            if st_base is None:
                uncovered.append((fn, bc, "状态不可派生：%s" % why))
                continue
            add.append("**状态**：%s" % st_base)
            notes.append("登记状态原文＝`%s`（`%s` L%d）" %
                         (re.sub(r"[*`]", "", r["状态原文"]), REG_NAME, r["行"]))
            if st_note:
                notes.append("登记原句附注（原样搬入）＝`%s`" % st_note)

        if need_nat:
            if st_base is None:
                uncovered.append((fn, bc, "性质不可派生：状态未定（%s）" % why))
                continue
            add.append("**性质**：%s" % NATURE_BY_STATE[st_base])
            notes.append("性质＝由状态 `%s` 派生（%s）" % (st_base, RULE6))

        if notes:
            add.append("**备注**：%s ｜ **本行由 `tools/%s` 新增，不修改任何原有行**" %
                       (" ｜ ".join(notes), SELF))

        if need_row7070:
            add.append(ROW_000_070)

        if not add:
            skipped.append((fn, bc, "无可增项"))
            continue

        anchor = find_anchor(lines)
        if anchor is None:
            uncovered.append((fn, bc, "找不到『编号』锚点，拒绝盲插"))
            continue

        new_lines = lines[:anchor] + add + lines[anchor:]
        changed.append({"file": fn, "code": bc, "insert_at": anchor,
                        "added": add, "before": len(lines), "after": len(new_lines)})
        if not dry:
            with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(new_lines))

    # ---------- 报告 ----------
    print("=" * 100)
    print("tools/fill_headers.py  root=%s  %s" % (root, "[DRY-RUN]" if dry else "[WRITE]"))
    print("=" * 100)
    print("登记表反取件数 = %d（%s）" % (len(reg), REG_NAME))
    print("盘上待处理件数 = %d" % len(files))
    print()
    print("【改写件数】= %d" % len(changed))
    for c in changed:
        print("  %-52s 件号=%-24s 插入@第%d行  新增%d行  %d→%d" %
              (c["file"][:52], c["code"][:24], c["insert_at"], len(c["added"]),
               c["before"], c["after"]))
        for a in c["added"]:
            print("        + %s" % a[:150])
    print()
    print("【已齐备／跳过】= %d" % len(skipped))
    for fn, bc, why in skipped:
        print("  %-52s %-24s %s" % (fn[:52], bc[:24], why))
    print()
    print("【未覆盖】= %d" % len(uncovered))
    for fn, bc, why in uncovered:
        print("  %-52s %-24s %s" % (fn[:52], bc[:24], why))
    print()
    total_added = sum(len(c["added"]) for c in changed)
    print("合计新增行 = %d ；删除行 = 0（本脚本无任何删/改操作）" % total_added)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_fill_headers_report.json")
    try:
        with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"root": root, "dry_run": dry, "changed": changed,
                                 "skipped": [{"file": a, "code": b, "why": c} for a, b, c in skipped],
                                 "uncovered": [{"file": a, "code": b, "why": c}
                                               for a, b, c in uncovered],
                                 "total_added": total_added},
                                ensure_ascii=False, indent=1))
        print("报告 → %s" % out)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
