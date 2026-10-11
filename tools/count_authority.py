# -*- coding: utf-8 -*-
r"""count_authority.py —— **权威计数**（项 vs 包）。

用法：python count_authority.py <交付包目录>（默认上级）
输出：已冻结包数；不通过包数；不一致**项**数；存档包数；台账 entries。

⭐ 口径（承 `PH-091`）：**一切现算**；**「项」≠「包」**；**写死数字不作对拍依据**。
"""
import io
import json
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main(argv):
    pkgd = argv[1] if len(argv) > 1 else ".."
    core = os.path.join(pkgd, "pharos-core")
    tool = os.path.join(core, "tools", "check_frozen_immutable.py")
    pkgs, bad, items = [], [], 0
    for d in sorted(os.listdir(pkgd)):
        p = os.path.join(pkgd, d)
        if not (d.startswith("pharos-handoff-2026") and os.path.isfile(os.path.join(p, "_FROZEN"))):
            continue
        pkgs.append(d)
        r = subprocess.run([sys.executable, tool, p], capture_output=True)
        if r.returncode != 0:
            bad.append(d)
            items += len([x for x in (r.stdout or b"").decode("utf-8", "replace").split("\n") if "\u2192" in x])
    arch = sum(1 for d in os.listdir(pkgd)
               if d.startswith("pharos-handoff-2026") and os.path.isfile(os.path.join(pkgd, d, "spec", "CORE-001-V1.2.md")))
    led = os.path.join(pkgd, "_anchor_ledger.json")
    ent = len(json.loads(io.open(led, encoding="utf-8").read()).get("entries", [])) if os.path.isfile(led) else -1
    print("[COUNT] \u5df2\u51bb\u7ed3\u5305=%d\uff1b**\u4e0d\u901a\u8fc7\u5305=%d**\uff1b**\u4e0d\u4e00\u81f4\u9879=%d**" % (len(pkgs), len(bad), items))
    print("[COUNT] \u5b58\u6863\u5305=%d\uff1b\u53f0\u8d26 entries=%d" % (arch, ent))
    print("[COUNT] **\u53e3\u5f84\u58f0\u660e**\uff1a\u300c\u9879\u300d\uff1d**\u4e0d\u4e00\u81f4\u6761\u76ee\u6570**\uff1b\u300c\u5305\u300d\uff1d**\u88ab\u5224\u5b9a\u4e0d\u901a\u8fc7\u5305\u6570**\uff1b**\u4e00\u5305\u53ef\u542b\u591a\u9879**\uff1b**\u5199\u6b7b\u6570\u5b57\u4e0d\u4f5c\u5bf9\u62cd\u4f9d\u636e**")
    print("[COUNT] **\u53d6\u6570\u65f6\u70b9\uff1a\u672c\u6b21\u8fd0\u884c**\uff1b\u4e0d\u4f5c\u5bf9\u62cd\u4f9d\u636e")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
