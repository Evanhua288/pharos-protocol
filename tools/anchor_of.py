# -*- coding: utf-8 -*-
r"""anchor_of.py —— **按白名单算锚**（守方建议②）。

口径：白名单内字段 → JCS 序列化 → `SHA-256(0x12 ‖ ...)`。
"""
import hashlib
import io
import json
import os
import sys


def canon(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_whitelist(spec_dir):
    p = os.path.join(spec_dir, "anchor-exclusion-whitelist.json")
    if not os.path.isfile(p):
        return None
    return json.loads(io.open(p, encoding="utf-8").read())


def anchor_of(entry, wl):
    inc = set(wl["contentAnchor"]["include"])
    sub = {k: v for k, v in entry.items() if k in inc}
    tag = bytes.fromhex(wl.get("domainTag", "0x12")[2:])
    return hashlib.sha256(tag + canon(sub)).hexdigest()


def main(argv):
    if len(argv) < 3:
        print("usage: anchor_of.py <\u6761\u76ee.json> <spec\u76ee\u5f55>")
        return 2
    e = json.loads(io.open(argv[1], encoding="utf-8").read())
    wl = load_whitelist(os.path.abspath(argv[2]))
    if not wl:
        print("[ANCHOR] \u65e0\u767d\u540d\u5355")
        return 2
    print("[ANCHOR] %s" % anchor_of(e, wl))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
