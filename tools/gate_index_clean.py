# -*- coding: utf-8 -*-
r"""gate_index_clean.py —— ⭐ T-索引 门（机读索引清洁度 ＋ 与当场重生成一致）。

判据（《10-整改验收标准》§一 T-索引）：
  IDX-1 REGEN   生成物与**当场重生成**逐字节一致（禁止手改生成物）
  IDX-2 DUP     **重复 id ＝ 0**
  IDX-3 PREFIX  **裸前缀（如 `PHAROS-000`／`VAL-400`）不得出现在"条款 id"位**
                （须带 `type: "prefix"`）
  IDX-4 COUNT   **`clauseCount` ＝ 实际条目数**（并核 `clauseIds`＝唯一 id 数）
附核：
  IDX-5 STALE   产出记录的 `specSha256` 必须等于现算 spec sha256

做法：把 `<包>/spec/` 复制到临时目录，用**包内** `tools/gen_clauses.py` 当场重生成，
再把临时产物与 `<包>/spec/clauses.json` 逐字节比对 —— **全程只读被检对象**。

用法：python tools/gate_index_clean.py <包目录> [--keep]（`--keep` 保留临时目录以便取证）
退出码：0 PASS；1 违反；2 无法执行。
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PREFIX_RX = re.compile(r"(?:PHAROS-)?[A-Z][A-Z0-9]*-\d{3}")


def main(argv):
    if len(argv) < 2:
        print("usage: gate_index_clean.py <包目录> [--keep]")
        return 2
    V = os.path.abspath(argv[1])
    keep = "--keep" in argv
    sp = os.path.join(V, "spec", "CORE-001-V1.2.md")
    cj = os.path.join(V, "spec", "clauses.json")
    gen = os.path.join(V, "tools", "gen_clauses.py")
    for f in (sp, cj, gen):
        if not os.path.isfile(f):
            print("[INDEX] 缺件：%s" % f)
            return 2
    raw = io.open(cj, "rb").read()
    try:
        j = json.loads(raw.decode("utf-8"))
    except Exception as e:
        print("[INDEX] clauses.json 不是合法 JSON：%s" % e)
        return 1
    fails = []

    # ---- IDX-5 STALE：产出记录的 specSha256 == 现算 ----
    cur = hashlib.sha256(io.open(sp, "rb").read()).hexdigest()
    if j.get("specSha256") != cur:
        fails.append(("IDX-5 STALE", "clauses.json.specSha256=%s ≠ 现算 %s"
                      % (str(j.get("specSha256"))[:16], cur[:16])))

    # ---- IDX-1 REGEN：当场重生成逐字节比对 ----
    tmp = tempfile.mkdtemp(prefix="idxclean-")
    try:
        shutil.copytree(os.path.join(V, "spec"), os.path.join(tmp, "spec"))
        r = subprocess.run([sys.executable, gen, os.path.join(tmp, "spec", "CORE-001-V1.2.md")],
                           capture_output=True, cwd=V)
        fresh = os.path.join(tmp, "spec", "clauses.json")
        if r.returncode != 0 or not os.path.isfile(fresh):
            fails.append(("IDX-1 REGEN", "重生成失败（rc=%d）：%s" % (r.returncode,
                          r.stderr.decode("utf-8", "replace")[:200])))
        else:
            fb = io.open(fresh, "rb").read()
            if fb != raw:
                d1 = hashlib.sha256(raw).hexdigest()[:16]
                d2 = hashlib.sha256(fb).hexdigest()[:16]
                fails.append(("IDX-1 REGEN", "盘上 %d B（%s）≠ 重生成 %d B（%s）"
                              % (len(raw), d1, len(fb), d2)))
            else:
                print("  [OK]   IDX-1 REGEN   逐字节一致（%d B，sha256 %s）" % (len(fb), hashlib.sha256(fb).hexdigest()[:16]))
    finally:
        if keep:
            print("  [KEEP] 临时目录：%s" % tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    # ---- IDX-2/3/4：条目结构 ----
    idx = j.get("index", [])
    seen, dup = {}, []
    for n, e in enumerate(idx):
        i = e.get("id")
        if i in seen:
            dup.append((i, seen[i], n))
        else:
            seen[i] = n
    if dup:
        fails.append(("IDX-2 DUP", "重复 id %d 个；前 5：%s"
                      % (len(dup), "; ".join("%s(#%d,#%d)" % d for d in dup[:5]))))
        bad = {}
        for i, _a, _b in dup:
            bad[i] = bad.get(i, 1) + 1
        for i, c in sorted(bad.items(), key=lambda x: -x[1])[:10]:
            print("        重复 %s ×%d" % (i, c))
    badpfx = [e.get("id") for e in idx if PREFIX_RX.fullmatch(str(e.get("id"))) and e.get("type") != "prefix"]
    if badpfx:
        fails.append(("IDX-3 PREFIX", "裸前缀占条款 id 位 %d 个（前 5：%s）"
                      % (len(badpfx), ", ".join(badpfx[:5]))))
    if int(j.get("clauseCount", -1)) != len(idx):
        fails.append(("IDX-4 COUNT", "clauseCount=%s ≠ 条目数 %d" % (j.get("clauseCount"), len(idx))))
    if "clauseIds" in j and int(j["clauseIds"]) != len(seen):
        fails.append(("IDX-4 COUNT", "clauseIds=%s ≠ 唯一 id 数 %d" % (j["clauseIds"], len(seen))))

    print("[INDEX] %s" % os.path.basename(V))
    print("  条目 %d｜唯一 id %d｜重复 id %d｜裸前缀(未隔离) %d｜clauseCount=%s｜prefixCount=%s"
          % (len(idx), len(seen), len(dup), len(badpfx), j.get("clauseCount"), j.get("prefixCount")))
    if fails:
        for k, m in fails:
            print("  [FAIL] %-14s %s" % (k, m))
        print("[RESULT] FAIL（%d 项）" % len(fails))
        return 1
    print("  [OK]   IDX-2 DUP     重复 id = 0")
    print("  [OK]   IDX-3 PREFIX  裸前缀均已带 type: prefix")
    print("  [OK]   IDX-4 COUNT   clauseCount = %d = 条目数" % len(idx))
    print("[RESULT] PASS（T-索引 4/4）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
