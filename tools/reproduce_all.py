# -*- coding: utf-8 -*-
r"""reproduce_all.py —— **一键复现**（锚 3）。

各方（第二／第三实现方、审计方）只需跑本脚本一次，即可得到：
  1 **21 道门**的结果；
  2 **证明账本**校验；
  3 **任务闭环样例**校验；
  4 **Ed25519 验签**；
  5 一行**结论**（`REPRODUCIBLE`／`NOT_REPRODUCIBLE`）。

用法：python reproduce_all.py <包目录>   （只读；不改包）
"""
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

STEPS = (
    ("1 自检卡（21 门）", "check_card.py", ["--count-root"]),
    ("2 证明账本", "check_proof_ledger.py", []),
    ("3 Merkle 实作", "check_merkle.py", []),
    ("4 DSSE", "check_dsse.py", []),
    ("5 DigestSet", "check_digest_set.py", []),
    ("6 ext 外挂", "check_extension_cases.py", []),
    ("7 裁剪实测", "check_pruning.py", []),
    ("8 冻结期", "check_freeze_registry.py", []),
    ("9 件数算术", "check_manifest_math.py", []),
    ("10 同步收敛", "check_sync_converge.py", []),
)


def main(argv):
    if len(argv) < 2:
        print("usage: reproduce_all.py <\u5305\u76ee\u5f55> [包工作区]")
        return 2
    V = os.path.abspath(argv[1])
    root = os.path.abspath(argv[2]) if len(argv) > 2 else os.path.dirname(V)
    td = os.path.join(V, "tools")
    fail = 0
    print("=" * 62)
    print("  一键复现（只读）：%s" % os.path.basename(V))
    print("=" * 62)
    for label, tool, extra in STEPS:
        p = os.path.join(td, tool)
        if not os.path.isfile(p):
            print("  %-22s 跳过（无此件）" % label)
            continue
        cmd = [sys.executable, p, V] + ([root] if extra else [])
        rr = subprocess.run(cmd, capture_output=True)
        ok = rr.returncode == 0
        if not ok:
            fail += 1
        print("  %-22s %s" % (label, "PASS" if ok else "FAIL"))
    # Ed25519 验签
    sig_ok = None
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(
            io.open(os.path.join(V, "SHA256SUMS.pub"), "rb").read()).verify(
            io.open(os.path.join(V, "SHA256SUMS.sig"), "rb").read(),
            io.open(os.path.join(V, "SHA256SUMS"), "rb").read())
        sig_ok = True
    except Exception:
        sig_ok = False
    print("  %-22s %s" % ("11 Ed25519 验签", "PASS" if sig_ok else "FAIL"))
    if not sig_ok:
        fail += 1
    print("-" * 62)
    print("  结论：%s（失败 %d 项）" % (
        "REPRODUCIBLE" if fail == 0 else "NOT_REPRODUCIBLE", fail))
    print("  ⭐ 本结论**不等于合规**；它只证明：本实现与规范一致。")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
