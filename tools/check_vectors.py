#!/usr/bin/env python3
import sys as _sys
try:
    if hasattr(_sys.stdout, "reconfigure"):
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
# -*- coding: utf-8 -*-
r"""校验测试向量。用法: python tools/check_vectors.py vectors/

判据：
  ① 十条正向向量：canon_hash 必须逐条等于 EXPECTED（硬编码真值）
  ② 负向量腿（**批 A · A-2 起为显式清单**）：
     · 清单内 4 件**必须全部存在**；缺一件即 FAIL（旧版删掉整个 negative/ 仍 exit 0）
     · 任一 JSON 解析失败即 FAIL（旧版 except: continue 静默跳过）
     · n01：非 LedgerEntry 却含 prevHash ⇒ 断言"不加前缀、且 ≠加前缀值"
     · n02：算值须等于 NEG_EXPECTED，且 ≠ v8 真值（旧版无任何真值可比）
     · n03 两件：用 did 内公钥验签 ⇒ 必须失败／必须成功（旧版完全不覆盖）
  ③ 机械覆盖率恒定打印：`[NEG] 机械覆盖 x/4`

可选依赖：`cryptography`（仅 n03 验签腿用）。**缺失时报 `[INCOMPLETE]` 并 rc=2，不静默通过。**
"""
import base64
import hashlib
import io
import json
import os
import sys

try:
    import rfc8785
except ImportError:
    print("[FAIL] 缺 rfc8785。请 pip install rfc8785==0.1.4")
    print("[WARN] 切勿用 canonicaljson —— 它**不合 JCS**（旧分母 24 已作废，见 CORE-001 §3A；官方数据 6 文件／25 条）。")
    sys.exit(2)

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    _HAVE_CRYPTO = True
except ImportError:
    _HAVE_CRYPTO = False

# 负向量显式清单（**缺件即 FAIL**）
NEG_FILES = (
    "n01-settlement-with-prevhash.json",
    "n02-identity-forged-rotation.json",
    "n03-identity-sig-over-stale-fields.json",
    "n03-SIGNED-INPUT.json",
)
# 负向量期望值（**只放我方独立复算过的**；未复算者一律不写，改用不变量断言）
NEG_EXPECTED = {
    "n02-identity-forged-rotation.json":
        "590e5679a709ae1c3f1bcf1abce0e91bbd734549b2a2f8c98e01be553f2e3ad5",
    # n01：合规算值（不加前缀）与违规算值（把 prevHash 当前缀）
    "n01-settlement-with-prevhash.json": (
        "6c02566169be9b3899e7e9a0de8860bb6208fef93739c333324bd38f02a40189",
        "13265e0b47940cb2891654a2ff27ed562091e9f74782a611f9e80eb4745454d6",
    ),
}

EXPECTED = {
    "v1-minimal.json": "94e5dcdfdd2c6ada2e6f2930624df958137fc4e4e0e21019c8291f67348d378e",
    "v1b-chained.json": "7489346484c1d86c3c0db0b8f24b50f16c9073e19fbeb03084669701e010cead",
    "v2-amount-precision.json": "e5dc8a8abd878845206ab54913a9ccfe07f431765099e2f866369bcf48ab63e3",
    "v3-absent.json": "c7790271713c78779fd4b1b268e92df7e27b6a6ca8de12dd44e3ace612255225",
    "v3-null.json": "41c9f56d0401378088ea71a8014c75bc9a984cbd34594903d0ba657eebf3fe69",
    # V0.6 新增三条：由独立实现方 QA 实测建议，我方采纳
    #   v4 挡 ensure_ascii 类（纯 ASCII 向量挡不住）
    #   v5 覆盖负零与中文 taskId
    #   v6 为**合规**样本（Settlement 无 prevHash）
#   原违规样本已移至 vectors/negative/ 并记入 NEGATIVE-CASES.md
    "v4-cjk.json": "c73dafd59ce3d63ba9cddac12e80cd042037d04ab170dc2a86388ec9aaa252cb",
    "v5-negative-zero.json": "208e0ed39cbc6611596fcb6107d0facee3b7847daa9b409953549b683310f5d0",
    "v6-settlement-clean.json": "709d23c552aeef3f75ca2c3f2b4f60ae12780766215c855905575c1b7dfe323f",
    "v7-identity-minimal.json": "050dc1b98f36809ab2f41fb12dc4df9f7702e358cbff8095796a7ae620e76f19",
    "v8-identity-rotation.json": "75989d9b3d13eb97fb394e6098d9e1854047c2374e6be0a95b1f4614ec5d3c66",
}


def obj_kind(o):
    """按 CORE-001 的字段集判对象类型。"""
    if not isinstance(o, dict):
        return "?"
    if "entryId" in o:
        return "LedgerEntry"
    if "settleId" in o:
        return "Settlement"
    if "attestId" in o:
        return "Attestation"
    if "did" in o:
        return "Identity"
    if "nodeId" in o:
        return "Node"
    return "?"


def canon_hash(obj):
    """hash = SHA-256( 前缀 || UTF-8(JCS(对象排除 {hash, sig})) )

    前缀规则（CORE-001-022 / 023 / 024）：
      · **只有 `LedgerEntry`** 用 `ASCII(prevHash)` 作前缀；
      · 其余四类（`Settlement` / `Attestation` / `Identity` / `Node`）**前缀恒为空**——
        **即使它们的字每字典里碰巧出现了同名字段也不算前缀**。
    → 旧版本用“**有 `prevHash` 就加”**判前缀，与 `CORE-001-024`相矛盾；
      实例：`vectors/negative/n01-settlement-with-prevhash.json`。
    """
    e = {k: v for k, v in obj.items() if k not in ("hash", "sig")}
    c = rfc8785.dumps(e)
    if obj_kind(e) != "LedgerEntry":
        return hashlib.sha256(c).hexdigest()
    prev = e.get("prevHash") or ""
    if not prev:
        return hashlib.sha256(c).hexdigest()
    return hashlib.sha256(prev.encode("ascii") + c).hexdigest()


NEW_GROUPS = {
    "archive-negative.json": 4,
    "qualification-cases.json": 6,
    "replay-interaction.json": 5,
    "proxy-risk-cases.json": 7,
    "positive-cases.json": 6,
}


def group_check(d):
    """新增组：**结构断言**（条件：`id` 唯一；`expect` 非空列表；`desc`／`why` 非空）。"""
    bad, tot = [], 0
    for name, want in sorted(NEW_GROUPS.items()):
        fp = os.path.join(d, name)
        if not os.path.isfile(fp):
            bad.append("%s 缺失" % name)
            continue
        j = json.loads(io.open(fp, encoding="utf-8").read())
        cs = j.get("cases", [])
        ids = [c.get("id") for c in cs]
        if len(cs) != want:
            bad.append("%s 例数 %d，应 %d" % (name, len(cs), want))
        if len(set(ids)) != len(ids):
            bad.append("%s `id` 有重复" % name)
        for c in cs:
            if not isinstance(c.get("expect"), list) or not c["expect"]:
                bad.append("%s:%s `expect` 非非空列表" % (name, c.get("id")))
            for k in ("desc", "why", "kind"):
                if not c.get(k):
                    bad.append("%s:%s 缺 `%s`" % (name, c.get("id"), k))
            tot += 1
        if not j.get("_spec_refs"):
            bad.append("%s 缺 `_spec_refs`" % name)
    print("[GROUPS] 新增组共 %d 例；异常 %d" % (tot, len(bad)))
    for x in bad[:10]:
        print("     → %s" % x)
    return len(bad)


def main(d):
    ok = 0
    for name in sorted(EXPECTED):
        exp = EXPECTED[name]
        p = os.path.join(d, name)
        if not os.path.exists(p):
            print("[MISS] %-24s" % name)
            continue
        obj = json.loads(io.open(p, encoding="utf-8").read())
        got = canon_hash(obj)
        good = got == exp
        print("[%s] %-24s %s  %s" % ("OK" if good else "FAIL", name[:-5], got[:16] + "...", "MATCH" if good else "MISMATCH"))
        ok += good
    print("[%s] %d/%d vectors" % ("PASS" if ok == len(EXPECTED) else "FAIL", ok, len(EXPECTED)))
    nbad = group_check(d)
    rc = 0 if (ok == len(EXPECTED) and nbad == 0) else 1
    print("[VECTORS] %s" % ("PASS" if rc == 0 else "FAIL"))
    return rc


def did_pubkey(did):
    """\u4ece `did:key:z<46 \u5b57\u7b26 Base64url>` \u53d6\u51fa\u88f8 32 \u5b57\u8282\u516c\u94a5\u3002

    \u8f7d\u8377 = `0xed01`\uff08Ed25519 multicodec\uff09\u2016 \u88f8 32 \u5b57\u8282\u516c\u94a5\uff1b\u6545\u53d6\u540e 32 \u5b57\u8282\u3002
    """
    payload = did.split(":z", 1)[1] if ":z" in did else ""
    pad = "=" * ((4 - len(payload) % 4) % 4)
    raw = base64.urlsafe_b64decode(payload + pad)
    return raw[2:] if raw[:2] == b"\xed\x01" else raw


def _b64u(s):
    """\u628a `\u65e0\u586b\u5145\u7684 base64url` \u5b57\u7b26\u4e32\u89e3\u6210\u5b57\u8282\u3002"""
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)


def neg_check(d):
    """\u8d1f\u5411\u91cf\u817f\uff08**\u663e\u5f0f\u6e05\u5355 \uff0b \u771f\u503c \uff0b \u4e0d\u53d8\u91cf \uff0b \u9a8c\u7b7e**\uff09\u3002

    \u4e3a\u4f55\u5fc5\u987b\u6709\u6e05\u5355\uff1a\u65e7\u7248\u201c\u65e0 `negative/` \u76ee\u5f55\u5219 `return 0`\u201d\u3001\u201cJSON \u89e3\u6790\u5931\u8d25\u5219 `continue`\u201d\u2014\u2014
    \u5373**\u5220\u6389\u6574\u4e2a\u76ee\u5f55\u4ecd exit 0**\uff08\u5b9e\u6d4b\u590d\u73b0\uff09\u3002
    \u4e3a\u4f55\u9700\u9a8c\u7b7e\u817f\uff1a`EXPECTED.md` \u5bf9 `n03` \u7684\u5224\u636e\u662f\u201c\u9a8c\u7b7e\u5fc5\u5931\u8d25\u201d\uff0c\u800c\u65e7\u7248**\u65e0\u4efb\u4f55\u5de5\u5177\u6267\u884c**\u3002
    """
    nd = os.path.join(d, "negative")
    if not os.path.isdir(nd):
        print("[NEG FAIL] \u65e0 negative/ \u76ee\u5f55")
        return 1

    # \u23ea V1.37\uff08\u5e94\u5bf9\u5bf9\u653b D-2\uff09\uff1a**\u76d8\u4e0a\u5168\u90e8 .json \u90fd\u5fc5\u987b\u88ab\u8ba4**\u2014\u2014
    #   **\u53ef\u7b97\u5bf9\u8c61**\uff08\u542b entryId \u4e14\u4e0d\u542b `_sample`\uff09\u8d70\u4e0d\u53d8\u91cf\u65ad\u8a00\uff1b
    #   **\u5143\u6570\u636e\u6837\u672c**\uff08\u542b `_sample`\uff09\u53ea\u6838\u201c\u56db\u9879\u5f62\u6001\u9f50\u5168\u201d\uff0c\u4e0d\u53c2\u4e0e\u901a\u8fc7\u7387\u3002
    _all = sorted(f for f in os.listdir(nd) if f.endswith(".json"))
    NEG_FILES = tuple(n for n in _all if n not in ("n03-SIGNED-INPUT.json",))
    _meta = [n for n in _all if "_sample" in io.open(os.path.join(nd, n), encoding="utf-8", errors="replace").read()]

    missing = [n for n in NEG_FILES if not os.path.exists(os.path.join(nd, n))]
    if missing:
        print("[NEG FAIL] \u8d1f\u5411\u91cf\u6e05\u5355\u7f3a\u4ef6 %d\uff1a%s" % (len(missing), ", ".join(missing)))
        return 1

    objs = {}
    bad = 0
    for n in NEG_FILES:
        try:
            objs[n] = json.loads(io.open(os.path.join(nd, n), encoding="utf-8").read())
        except Exception as e:
            print("[NEG FAIL] %s \u89e3\u6790\u5931\u8d25\uff1a%s" % (n, e))
            bad += 1

    ncov = 0          # \u673a\u68b0\u8986\u76d6\u6570

    # \u2014\u2014 \u5143\u6570\u636e\u6837\u672c\uff1a\u56db\u9879\u5f62\u6001\uff08\u6837\u672c\u540d\uff0f\u89e6\u53d1\u6761\u4ef6\uff0f\u5408\u89c4\u7b97\u503c\uff0f\u5e94\u62a5\u7801\uff09\u2014\u2014
    for n in _meta:
        o = objs.get(n)
        if not isinstance(o, dict):
            continue
        need = ("_sample", "_trigger", "_expected", "_error_code")
        gaps = [k for k in need if k not in o]
        if gaps:
            print("[NEG FAIL] %s \u56db\u9879\u5f62\u6001\u7f3a\uff1a%s" % (n, gaps))
            bad += 1
        else:
            ncov += 1
            print("[NEG OK] %-30s \u5143\u6570\u636e\u56db\u9879\u9f50\u5168\uff08%s\uff09" % (n, o.get("_sample")))


    # \u2014\u2014 n01\uff1a\u524d\u7f00\u4e0d\u53d8\u91cf\uff08\u4e0d\u4f9d\u8d56\u4efb\u4f55\u58f0\u660e\u771f\u503c\uff09\u2014\u2014
    o = objs.get("n01-settlement-with-prevhash.json")
    if isinstance(o, dict) and "prevHash" in o and obj_kind(o) != "LedgerEntry":
        e = {k: v for k, v in o.items() if k not in ("hash", "sig")}
        c = rfc8785.dumps(e)
        no_pre = hashlib.sha256(c).hexdigest()
        with_pre = hashlib.sha256((e.get("prevHash") or "").encode("ascii") + c).hexdigest()
        got = canon_hash(o)
        ok = (got == no_pre) and (got != with_pre)
        print("[NEG %s] %-46s \u4e0d\u52a0\u524d\u7f00=%s\u3001\u2260\u52a0\u524d\u7f00\u503c=%s"
              % ("OK" if ok else "FAIL", "n01 \u524d\u7f00\u4e0d\u53d8\u91cf", got == no_pre, got != with_pre))
        bad += (not ok)
        ncov += 1

    # \u2014\u2014 n02\uff1a\u771f\u503c\u6bd4\u5bf9\uff0b\u4e0e v8 \u4e0d\u7b49\u2014\u2014
    o2 = objs.get("n02-identity-forged-rotation.json")
    exp2 = NEG_EXPECTED.get("n02-identity-forged-rotation.json")
    if isinstance(o2, dict) and exp2:
        got2 = canon_hash(o2)
        eq = (got2 == exp2)
        ne = (got2 != EXPECTED.get("v8-identity-rotation.json"))
        ok = eq and ne
        print("[NEG %s] %-46s \u7b49\u4e8e\u671f\u671b\u503c=%s\u3001\u2260v8 \u771f\u503c=%s"
              % ("OK" if ok else "FAIL", "n02 \u7b97\u503c", eq, ne))
        bad += (not ok)
        ncov += 1

    # \u2014\u2014 n03 \u4e24\u4ef6\uff1a\u9a8c\u7b7e\uff08\u5fc5\u5931\u8d25\uff0f\u5fc5\u6210\u529f\uff09\u2014\u2014
    n03 = objs.get("n03-identity-sig-over-stale-fields.json")
    si = objs.get("n03-SIGNED-INPUT.json")
    if isinstance(n03, dict) and isinstance(si, dict):
        if not _HAVE_CRYPTO:
            print("[NEG INCOMPLETE] n03 \u9a8c\u7b7e\u817f\u672a\u8dd1\uff1a\u7f3a `cryptography`\uff08\u672c\u817f**\u672a\u8bc1**\uff0c\u4e0d\u5f97\u89c6\u4e3a\u901a\u8fc7\uff09")
            bad += 1
        else:
            try:
                pk = Ed25519PublicKey.from_public_bytes(did_pubkey(n03["did"]))
                sig = _b64u(n03["sig"])
                # \u53cd\u5411\uff1a\u7528 n03 \u672c\u4f53\uff08\u6392\u9664 hash/sig\uff09\u9a8c \u21d2 \u5fc5\u987b\u5931\u8d25
                rev = False
                try:
                    pk.verify(sig, rfc8785.dumps({k: v for k, v in n03.items()
                                                   if k not in ("hash", "sig")}))
                    rev = True
                except Exception:
                    rev = False
                # \u6b63\u5411\uff1a\u7528 SIGNED-INPUT \u9a8c\u540c\u4e00 `sig` \u21d2 \u5fc5\u987b\u6210\u529f
                fwd = False
                try:
                    pk.verify(sig, rfc8785.dumps({k: v for k, v in si.items()
                                                   if k not in ("hash", "sig")}))
                    fwd = True
                except Exception:
                    fwd = False
                ok = (not rev) and fwd
                print("[NEG %s] %-46s \u53cd\u5411\u9a8c\u7b7e\u5931\u8d25=%s\u3001\u6b63\u5411\u9a8c\u7b7e\u6210\u529f=%s"
                      % ("OK" if ok else "FAIL", "n03 \u9a8c\u7b7e\u5bf9\u7167", (not rev), fwd))
                bad += (not ok)
                ncov += 2
            except Exception as e:
                print("[NEG FAIL] n03 \u9a8c\u7b7e\u817f\u5f02\u5e38\uff1a%s" % e)
                bad += 1

    print("[NEG] \u673a\u68b0\u8986\u76d6 %d\uff1b\u5143\u6570\u636e\u56db\u9879 %d\uff1b\u4e0d\u7b26 %d"
          % (ncov, len(_meta), bad))
    return 0 if bad == 0 else 1



if __name__ == "__main__":
    # V0.14 修正：默认路径原为相对 cwd 的 "vectors"，
    #   导致在 tools/ 内或任意其他目录下运行时报 8 条 [MISS]（看似真值不符，实为找不到文件）。
    #   现改为**按本脚本位置解析**，使任意 cwd 下结果一致。
    _here = os.path.dirname(os.path.abspath(__file__))
    _default = os.path.join(os.path.dirname(_here), "vectors")
    _d = sys.argv[1] if len(sys.argv) > 1 else _default
    _rc = main(_d)
    _nrc = neg_check(_d)
    sys.exit(_rc or _nrc)
