# -*- coding: utf-8 -*-
r"""sign_sums.py —— **对 `SHA256SUMS` 做 Ed25519 签名**（`PH-REV-001-03`）。

用法：python sign_sums.py <包目录> [--key <私钥文件>]
行为：
  ① 若无私钥，**生成**并保存到 `--key`（默认 `signing-key.pem`）；
  ② 对 `SHA256SUMS` 签名 ⇒ `SHA256SUMS.sig`；
  ③ 写出公钥 `SHA256SUMS.pub`（方便随包）。

依赖：`cryptography`（若未安装，本脚本会**明确报错而非静默跳过**）。
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _patch_manifest_count(pkg):
    """把 MANIFEST.sha256 头部 `files: N = M + ...` 的 N 改为**含自证签名件**。"""
    import re as _re
    mp = os.path.join(pkg, "MANIFEST.sha256")
    if not os.path.isfile(mp):
        return
    t = io.open(mp, encoding="utf-8", errors="replace").read()
    m = _re.search(r"files: (\d+) = (\d+) \+ SHA256SUMS \+ MANIFEST\.sha256", t)
    if not m:
        return
    n, mm = int(m.group(1)), int(m.group(2))
    want = mm + 4
    if n != want:
        t = t.replace(m.group(0), "files: %d = %d + SHA256SUMS + MANIFEST.sha256 + SHA256SUMS.sig + SHA256SUMS.pub" % (want, mm), 1)
        io.open(mp, "w", encoding="utf-8", newline="\n").write(t)
        print("[SIGN] MANIFEST \u4ef6\u6570\u5df2\u4fee\uff1a%d \u2192 %d" % (n, want))


def main(argv):
    if len(argv) < 2:
        print("usage: sign_sums.py <pkg> [--key <pem>]")
        return 2
    pkg = argv[1]
    norw = "--no-rewrite" in argv   # ⭐ 只签不改（保证清单与实件持续一致）
    key = "signing-key.pem"
    if "--key" in argv:
        key = argv[argv.index("--key") + 1]
    su = os.path.join(pkg, "SHA256SUMS")
    if not os.path.isfile(su):
        print("[SIGN] \u65e0 SHA256SUMS\uff0c\u8df3\u8fc7")
        return 2
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
    except Exception as e:
        print("[SIGN] **\u7f3a\u4f9d\u8d56 cryptography**\uff1a%s" % e)
        return 2
    if os.path.isfile(key):
        priv = serialization.load_pem_private_key(io.open(key, "rb").read(), password=None)
    else:
        priv = Ed25519PrivateKey.generate()
        io.open(key, "wb").write(priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()))
        print("[SIGN] \u5df2\u751f\u6210\u79c1\u94a5\uff1a%s（**\u4e0d\u5f97\u968f\u5305\u53d1出**\uff09" % key)
    data = io.open(su, "rb").read()
    sig = priv.sign(data)
    io.open(os.path.join(pkg, "SHA256SUMS.sig"), "wb").write(sig)
    pub = priv.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                         format=serialization.PublicFormat.Raw)
    io.open(os.path.join(pkg, "SHA256SUMS.pub"), "wb").write(pub)
    if "--no-rewrite" not in argv:
        _patch_manifest_count(pkg)
    print("[SIGN] \u5df2\u7b7e\uff1aSHA256SUMS.sig\uff08%d B\uff09\uff1b\u516c\u94a5 SHA256SUMS.pub\uff08%d B\uff09" % (
        len(sig), len(pub)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
