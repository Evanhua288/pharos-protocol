# -*- coding: utf-8 -*-
r"""check_card.py —— **交接自检卡**：一条命令打印**八门结果**。

用法：python check_card.py <包目录> [--count-root <交付包目录>]
输出：**逐门结果 + 锚 + 验签 + 晚写数 + 取数时点**。
本工具**只读**；不改被检验对象。
"""
import hashlib
import io
import os
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def run(cmd, cwd=None):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True)
    o = (r.stdout or r.stderr).decode("utf-8", "replace")
    last = [x.strip() for x in o.split("\n") if x.strip()]
    return r.returncode == 0, (time.time() - t0), (last[-1] if last else "")


def main(argv):
    if len(argv) < 2:
        print("usage: check_card.py <\u5305\u76ee\u5f55> [--count-root <\u4ea4\u4ed8\u5305\u76ee\u5f55>]")
        return 2
    V = os.path.abspath(argv[1])
    root = argv[argv.index("--count-root") + 1] if "--count-root" in argv else os.path.dirname(V)
    pre = "--pre-freeze" in argv   # ⏪ 冻结前生成：跳过需签名后才能判的两项
    T = os.path.join(V, "tools")
    PY = sys.executable
    GATES = [
        ("1 \u5305\u5185\u5b8c\u6574\u6027", [PY, os.path.join(T, "check_integrity.py"), V], None),
        ("2 \u51bb\u7ed3\u95e8 V2", [PY, os.path.join(T, "check_frozen_immutable.py"), V], None),
        ("3 \u989d\u5916\u5ba1\u8ba1 E1\u2013E4", [PY, os.path.join(T, "audit_extra.py"), V], None),
        ("4 \u5f15\u7528\u95e8", [PY, os.path.join(T, "gen_clauses.py"), "spec/CORE-001-V1.2.md", "--check", "--no-write"], V),
        ("5 \u5411\u91cf\u7ec4", [PY, os.path.join(T, "check_vectors.py"), "vectors"], V),
        ("6 \u5bf9\u62cd\u767b\u8bb0\u95e8", [PY, os.path.join(T, "check_reconcile_log.py"), "vectors"], V),
        ("7 `159` \u56de\u663e\u95e8", [PY, os.path.join(T, "check_echoed_unknown.py"), "vectors"], V),
        ("9 \u6761\u53f7\u522b\u540d\u95e8", [PY, os.path.join(T, "check_alias_map.py"), V], None),
        ("15 DSSE \u95e8", [PY, os.path.join(T, "check_dsse.py"), V], None),
        ("24 \u51bb\u7ed3\u6269\u5c55\u95e8", [PY, os.path.join(T, "check_freeze_extension.py"), V], None),
        ("26 \u8fc1\u79fb\u56db\u6001\u95e8", [PY, os.path.join(T, "check_migration_states.py"), V], None),
        ("25 \u951a\u5254\u9664\u767d\u540d\u5355\u95e8", [PY, os.path.join(T, "check_anchor_whitelist.py"), V], None),
        ("23 \u4e94\u9879\u5f85\u63a5\u95e8", [PY, os.path.join(T, "check_pending_five.py"), V], None),
        ("22 \u4e00\u952e\u590d\u73b0\u95e8", [PY, os.path.join(T, "check_reproduce.py"), V], None),
        ("21 \u4ef6\u6570\u7b97\u672f\u540c\u6e90\u95e8", [PY, os.path.join(T, "check_manifest_math.py"), V], None),
        ("20 \u51bb\u7ed3\u671f\u673a\u68c0\u95e8", [PY, os.path.join(T, "check_freeze_registry.py"), V], None),
        ("19 \u540c\u6b65\u6536\u655b\u95e8", [PY, os.path.join(T, "check_sync_converge.py"), V], None),
        ("18 \u88c1\u526a\u5b9e\u6d4b\u95e8", [PY, os.path.join(T, "check_pruning.py"), V], None),
        ("17 `223` \u53d8\u66f4\u95e8", [PY, os.path.join(T, "check_change_cases.py"), V], None),
        ("16 DigestSet \u95e8", [PY, os.path.join(T, "check_digest_set.py"), V], None),
        ("14 `ext` \u5916\u6302\u95e8", [PY, os.path.join(T, "check_extension_cases.py"), V], None),
        ("13 \u8bc1\u660e\u8d26\u672c\u95e8", [PY, os.path.join(T, "check_proof_ledger.py"), V], None),
        ("12 Merkle \u5b9e\u4f5c\u95e8", [PY, os.path.join(T, "check_merkle.py"), V], None),
        ("11 \u951a\u5957\u4ef6\u95e8", [PY, os.path.join(T, "check_anchor_set.py"), V], None),
        ("10 \u7b97\u6cd5\u6ce8\u518c\u95e8", [PY, os.path.join(T, "check_algorithm_registry.py"), V], None),
        ("8 \u6743\u5a01\u8ba1\u6570", [PY, os.path.join(T, "count_authority.py"), root], None),
    ]
    print("=" * 66)
    print("  PHAROS \u4ea4\u63a5\u81ea\u68c0\u5361  |  \u5305\uff1a%s" % os.path.basename(V))
    print("=" * 66)
    ok_n = 0
    for name, cmd, cwd in GATES:
        ok, dt, last = run(cmd, cwd)
        ok_n += 1 if ok else 0
        print("  %s %-22s %5.1fs  %s" % ("[PASS]" if ok else "[FAIL]", name, dt, last[:64]))
    sp = os.path.join(V, "spec", "CORE-001-V1.2.md")
    h = hashlib.sha256(io.open(sp, "rb").read()).hexdigest() if os.path.isfile(sp) else "\uff08\u65e0 spec\uff09"
    sigok = False
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey as K
        K.from_public_bytes(io.open(os.path.join(V, "SHA256SUMS.pub"), "rb").read()).verify(
            io.open(os.path.join(V, "SHA256SUMS.sig"), "rb").read(),
            io.open(os.path.join(V, "SHA256SUMS"), "rb").read())
        sigok = True
    except Exception:
        sigok = False
    t0 = os.path.getmtime(os.path.join(V, "_FROZEN")) if os.path.isfile(os.path.join(V, "_FROZEN")) else 0
    late = 0
    for dp, dn, fn in os.walk(V):
        for f in fn:
            if f != "_FROZEN" and os.path.getmtime(os.path.join(dp, f)) > t0 + 1:
                late += 1
    print("-" * 66)
    print("  specHash     : %s" % h)
    if pre:
        print("  Ed25519 \u9a8c\u7b7e : \uff08\u51bb\u7ed3\u524d\uff0c\u5f85\u7b7e\u540d\u540e\u9a8c\uff09")
        print("  \u51bb\u7ed3\u540e\u665a\u5199   : \uff08\u5f85\u51bb\u7ed3\uff09")
    else:
        print("  Ed25519 \u9a8c\u7b7e : %s" % ("OK" if sigok else "FAIL"))
        print("  \u51bb\u7ed3\u540e\u665a\u5199   : %d \u4ef6" % late)
    print("  \u51bb\u7ed3\u540e\u665a\u5199   : %d \u4ef6" % late)
    print("  \u53d6\u6570\u65f6\u70b9     : \u672c\u6b21\u8fd0\u884c\uff08\u4e0d\u4f5c\u5bf9\u62cd\u4f9d\u636e\uff09")
    try:
        import json as _jj
        _pl = os.path.join(V, "vectors", "proof-ledger.json")
        if os.path.isfile(_pl):
            _p = _jj.loads(io.open(_pl, encoding="utf-8").read())
            print("  \u8bc1\u660e\u8d26\u672c\uff1a\u53f6 %d\uff1b\u6839 %s" % (len(_p["leaves"]), _p["root"][:16]))
        else:
            print("  \u8bc1\u660e\u8d26\u672c\uff1a\uff08\u65e0\uff09")
    except Exception:
        pass
    # BASELINE-LINE ⭐ 随包自证里带"本次基线一行"
    try:
        import json as _j3, re as _r3
        _sp3 = os.path.join(V, "spec", "CORE-001-V1.2.md")
        _t3 = io.open(_sp3, encoding="utf-8", errors="replace").read()
        _vs = [int(a) * 100 + int(b) for a, b in
               _r3.findall(r"[*][*]`?V(1[.][0-9]+)`?[*][*]", _t3)]
        _mv = type("M", (), {"group": lambda self, i, _v=max(_vs or [0]): "%d.%d" % divmod(_v, 100)})()
        _cl = _j3.loads(io.open(os.path.join(V, "spec", "clauses.json"), encoding="utf-8").read())
        _td3 = os.path.join(V, "tools")
        _nt = len([f for f in os.listdir(_td3)
                   if os.path.isfile(os.path.join(_td3, f)) and not f.endswith(".pyc")])
        print("  \u57fa\u7ebf\uff1a\u5185\u5bb9 V%s\uff1b\u6761\u6587\u5757 %s\uff1b\u552f\u4e00\u6761\u53f7 %s\uff1b\u5de5\u5177 %d" % (_mv.group(1) if _mv else "?", _cl.get("clauses"), _cl.get("clauseIds"), _nt))
    except Exception:
        pass
    print("=" * 66)
    if pre:
        print("  \u7ed3\u8bba\uff1a%d/26 \u95e8\u901a\u8fc7\uff08\u51bb\u7ed3\u524d\u9884\u68c0\uff09%s" % (ok_n, "" if ok_n == 26 else "  \u2190 \u6709\u5f02\u5e38"))
    else:
        print("  \u7ed3\u8bba\uff1a%d/26 \u95e8\u901a\u8fc7%s" % (ok_n, "" if (ok_n == 26 and sigok and late == 0) else "  \u2190 \u6709\u5f02\u5e38"))
    if pre:
        return 0 if ok_n == 26 else 1
    return 0 if (ok_n == 26 and sigok and late == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
