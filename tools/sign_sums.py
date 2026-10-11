# -*- coding: utf-8 -*-
r"""sign_sums.py —— 对 `SHA256SUMS` 做 Ed25519 签名（PH-REV-001-03）。
 *
 * 本版**实现发布规范 C3**（此前缺失，审计判定为 P0）：
 *   C3：**签名前必须先证明私钥能导出已发布公钥**；否则**拒绝签名**——
 *        静默发布一个"无人能验证"的包，比不签名更坏。
 *
 * 本版行为（与旧版的三点差别）：
 *   ① **不自动生成私钥**。找不到私钥即**报错退出**（exit 3）。
 *      若确需在开发环境新生成，必须显式 `--allow-generate`，并在同一次运行里
 *      把新公钥指纹打印出来，供人工登记。
 *   ② **C3 门**：若包内已有 `SHA256SUMS.pub`，则**要求**本次私钥导出的公钥
 *      与其**逐字节相同**；不同即**拒绝签名**（exit 4）。
 *   ③ **默认不改 `MANIFEST.sha256`**（只签不改）。确需改写件数时显式
 *      `--rewrite-manifest`。
 *
 * 用法：
 *   python tools/sign_sums.py <包目录> --key <私钥.pem> [--no-rewrite] [--allow-generate] [--rewrite-manifest]
 *
 * 依赖：`cryptography`（未安装时**明确报错**，不静默跳过）。
"""
import hashlib
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _patch_manifest_count(pkg):
    """把 MANIFEST.sha256 头部 `files: N = M + ...` 的 N 改为含自证签名件。"""
    import re as _re
    mp = os.path.join(pkg, "MANIFEST.sha256")
    if not os.path.isfile(mp):
        return False
    t = io.open(mp, encoding="utf-8", errors="replace").read()
    m = _re.search(r"files: (\d+) = (\d+) \+ SHA256SUMS \+ MANIFEST\.sha256", t)
    if not m:
        return False
    n, mm = int(m.group(1)), int(m.group(2))
    want = mm + 4
    if n != want:
        t = t.replace(m.group(0),
                      "files: %d = %d + SHA256SUMS + MANIFEST.sha256 + SHA256SUMS.sig + SHA256SUMS.pub"
                      % (want, mm), 1)
        io.open(mp, "w", encoding="utf-8", newline="\n").write(t)
        print("[SIGN] MANIFEST 件数已修：%d → %d" % (n, want))
        return True
    return False


def main(argv):
    if len(argv) < 2 or "--key" not in argv:
        print("usage: sign_sums.py <pkg> --key <pem> [--no-rewrite] [--allow-generate] [--rewrite-manifest]")
        print("  C3 要求显式给出私钥；**本工具不替你生成密钥**。")
        return 2
    pkg = argv[1]
    key = argv[argv.index("--key") + 1]
    allow_gen = "--allow-generate" in argv
    rewrite_manifest = "--rewrite-manifest" in argv
    su = os.path.join(pkg, "SHA256SUMS")
    if not os.path.isfile(su):
        print("[SIGN] 无 SHA256SUMS，跳过")
        return 2
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
        from cryptography.hazmat.primitives import serialization
    except Exception as e:
        print("[SIGN] **缺依赖 cryptography**：%s" % e)
        return 2

    # ---- 载入或（仅显式允许时）生成私钥
    generated = False
    if os.path.isfile(key):
        raw = io.open(key, "rb").read()
        try:
            priv = serialization.load_pem_private_key(raw, password=None)
        except Exception as e:
            print("[SIGN] **私钥无法解析**：%s" % e)
            return 3
    elif allow_gen:
        priv = Ed25519PrivateKey.generate()
        io.open(key, "wb").write(priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()))
        os.chmod(key, 0o600)
        generated = True
        print("[SIGN] ⚠️ **已按 `--allow-generate` 新生成私钥**：%s" % key)
        print("[SIGN] ⚠️ **该私钥不得随包发；新公钥指纹须人工登记后才能用于发布**。")
    else:
        print("[SIGN] **拒绝签名：找不到私钥 `%s`**。" % key)
        print("  C3：**签名前必须先证明私钥能导出已发布公钥**；")
        print("  本工具**不自动生成密钥**（旧版会静默生成并覆写，属审计 P0）。")
        print("  开发环境确需新密钥时，显式加 `--allow-generate`。")
        return 3

    derived = priv.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                             format=serialization.PublicFormat.Raw)
    fp = hashlib.sha256(derived).hexdigest()

    # ---- C3 门：与已发布公钥逐字节比对
    pub_path = os.path.join(pkg, "SHA256SUMS.pub")
    if os.path.isfile(pub_path):
        published = io.open(pub_path, "rb").read()
        if published != derived:
            print("[SIGN] **拒绝签名：C3 门不通过**。")
            print("  已发布公钥 sha256 = %s" % hashlib.sha256(published).hexdigest())
            print("  本次私钥导出   sha256 = %s" % fp)
            print("  ⇒ 二者不同。**若强行签名，将产出一个无人能按已发布公钥验证的包**。")
            return 4
        print("[SIGN] C3 门通过：私钥导出的公钥与包内已发布公钥**逐字节相同**（%s）" % fp[:24])
    else:
        if generated:
            print("[SIGN] 未发现已发布公钥；**新公钥指纹 = %s**（发布前须人工登记）" % fp)
        else:
            print("[SIGN] ⚠️ 未发现包内已发布公钥 `SHA256SUMS.pub`；本次将以新公钥 %s 落盘。" % fp[:24])
            print("[SIGN] ⚠️ **C3 的完整形态要求与「已发布公钥」比对**；无已发布公钥时**该门无法生效**。")

    data = io.open(su, "rb").read()
    sig = priv.sign(data)
    io.open(os.path.join(pkg, "SHA256SUMS.sig"), "wb").write(sig)
    io.open(pub_path, "wb").write(derived)
    if rewrite_manifest:
        _patch_manifest_count(pkg)
    else:
        print("[SIGN] 未改写 MANIFEST.sha256（本版默认只签不改；如需改写加 `--rewrite-manifest`）")
    print("[SIGN] 已签：SHA256SUMS.sig（%d B）；公钥 SHA256SUMS.pub（%d B）" % (len(sig), len(derived)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
