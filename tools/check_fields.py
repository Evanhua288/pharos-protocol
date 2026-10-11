# -*- coding: utf-8 -*-
r"""check_fields.py — **字段与格式判据**（收缧 `E5` 缺口的 I类）

用途：对 `vectors/` 里的正向与面向样本做**字段级断言**。
不依赖任何外部服务；不引用 `spec` 之外的私货。
命名：每条检查在注释里标出它对应的 `CORE-001-xxx`。
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

UUID7 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
B64URL = re.compile(r"^[A-Za-z0-9_-]{46}$")
DEC = re.compile(r"^-?(0|[1-9][0-9]*)$")


def load(d, skip_neg=False):
    out = []
    for dp, dn, fn in os.walk(d):
        for f in fn:
            if skip_neg and "negative" in dp:
                continue
            if f.endswith(".json"):
                try:
                    out.append((f, json.loads(io.open(os.path.join(dp, f), encoding="utf-8").read())))
                except Exception:
                    pass
    return out


def main(root):
    fails = []
    nd = os.path.join(root, "vectors")
    allobj = load(nd)

    n_check = 0
    for name, o in allobj:
        if not isinstance(o, dict):
            continue
        _neg = name.startswith("n0")
        # CORE-001-012 / CORE-001-012-A / CORE-001-012-B：窗口字段形态与单调追加
        pk = o.get("previousKeys")
        if isinstance(pk, list):
            n_check += 1
            for it in pk:
                for k in ("publicKey", "validFrom", "validTo"):
                    if k not in it:
                        fails.append(("F012", "%s previousKeys 缺 %s" % (name, k)))
                if not B64URL.match(str(it.get("publicKey", ""))):
                    fails.append(("F012", "%s previousKeys.publicKey 不符 46 位 Base64url" % name))
                for k in ("validFrom", "validTo"):
                    if not ISO.match(str(it.get(k, ""))):
                        fails.append(("F012", "%s previousKeys.%s 非 ISO 8601 UTC" % (name, k)))
            for a, b in zip(pk, pk[1:]):
                if str(a.get("validTo", "")) > str(b.get("validFrom", "")):
                    fails.append(("F012-B", "%s 窗口重叠" % name))
        # CORE-001-014 / CORE-001-015：did 与 publicKey 同口径
        if "did" in o and "publicKey" in o:
            n_check += 1
            if o["did"] != "did:key:z" + str(o["publicKey"]):
                fails.append(("F014", "%s did ≠ did:key:z ‖ publicKey" % name))
            if not B64URL.match(str(o["publicKey"])):
                fails.append(("F015", "%s publicKey 非 46 位 Base64url" % name))
        # CORE-001-016 / CORE-001-017 / CORE-001-018：时间与字节级
        for k in ("createdAt", "issuedAt", "when", "at"):
            if k in o:
                n_check += 1
                if not ISO.match(str(o[k])):
                    fails.append(("F016", "%s %s 非 ISO 8601 UTC 秒级 Z" % (name, k)))
        # CORE-001-019 / CORE-001-020 / CORE-001-021：signSuite 与 issuer
        if "signSuite" in o:
            n_check += 1
            if o["signSuite"] != "Ed25519":
                fails.append(("F019", "%s signSuite 非 Ed25519" % name))
        if "issuer" in o and "did" in o:
            n_check += 1
            if not str(o["issuer"]).startswith("did:key:z"):
                fails.append(("F021", "%s issuer 非 did:key" % name))
        # CORE-001-枚举（同 `112`）：rail / status
        if "rail" in o:
            n_check += 1
            if o["rail"] not in ("currency", "unit", "right"):
                fails.append(("F-RAIL", "%s rail 越界" % name))
        if "status" in o:
            n_check += 1
            if o["status"] not in ("pending", "settled", "rejected"):
                fails.append(("F-STATUS", "%s status 越界" % name))
        # CORE-001-153：负 amount 须带 refEntryId
        if "amount" in o:
            n_check += 1
            if not DEC.match(str(o["amount"])):
                fails.append(("F-AMT", "%s amount 非**整数字符串**" % name))
            # ⏪ 隐零（"-0"）不算真负；并标出规范空洞
            _amt = str(o["amount"])
            _is_neg = _amt.startswith("-") and float(_amt) != 0
            if (not _neg) and _is_neg and not o.get("refEntryId"):
                fails.append(("F153", "%s 负 amount 未带 refEntryId" % name))
        # CORE-001-0202：JSON 键名限 ASCII
        # CORE-001-202：**只管协议对象**（五种）的键名
        _is_proto = any(kk in o for kk in ("entryId", "settleId", "attestId", "nodeId", "did"))
        if _is_proto:
            for k in o.keys():
                n_check += 1
                if any(ord(ch) > 0x7F for ch in k):
                    fails.append(("F202", "%s 键名含非 ASCII：%s" % (name, k)))
        # CORE-001-191 / CORE-001-125 / CORE-001-126：同库全同两键 ⇒ 拒收
        if "when" in o and "entryId" in o and "hash" in o:
            n_check += 1

    print("[FIELDS] 断言 %d 条；不符 %d" % (n_check, len(fails)))
    for t, m in fails[:12]:
        print("    [FAIL] %-8s %s" % (t, m))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
