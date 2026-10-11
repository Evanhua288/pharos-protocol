#!/usr/bin/env python3
"""pharos-verify - verify a CORE-001 package without trusting the package.

Zero third-party dependencies. One file. Nothing is written to the package.

Usage:
    python pharos_verify.py check-sums   <package-dir>
    python pharos_verify.py check-sig    <package-dir>
    python pharos_verify.py reproduce    <package-dir> [workspace-dir]
    python pharos_verify.py manifest     <package-dir>
    python pharos_verify.py all          <package-dir> [workspace-dir]

Exit codes: 0 pass, 1 mismatch, 2 cannot run.

A pass means the implementation agrees with the published specification.
It does NOT mean any party is compliant with any law or certification scheme.
"""
import hashlib
import os
import subprocess
import sys

VERSION = "1.0.0"


def _walk(pkg):
    for dp, dn, fn in os.walk(pkg):
        dn[:] = [d for d in dn if d not in ("__pycache__", ".git")]
        for f in fn:
            yield os.path.relpath(os.path.join(dp, f), pkg).replace("\\", "/")


def cmd_check_sums(pkg):
    su = os.path.join(pkg, "SHA256SUMS")
    if not os.path.isfile(su):
        print("no SHA256SUMS in %s" % pkg)
        return 2
    want, bad, missing = {}, [], []
    for ln in open(su, encoding="utf-8", errors="replace").read().split("\n"):
        if "  " not in ln:
            continue
        h, rel = ln.split("  ", 1)
        want[rel.strip()] = h.strip()
    for rel, h in sorted(want.items()):
        p = os.path.join(pkg, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            missing.append(rel)
            continue
        got = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if got != h:
            bad.append(rel)
    print("[check-sums] listed %d; mismatched %d; missing %d" % (len(want), len(bad), len(missing)))
    for x in bad[:10]:
        print("   MISMATCH %s" % x)
    for x in missing[:10]:
        print("   MISSING  %s" % x)
    return 0 if not bad and not missing else 1


def cmd_check_sig(pkg):
    sig = os.path.join(pkg, "SHA256SUMS.sig")
    pub = os.path.join(pkg, "SHA256SUMS.pub")
    if not (os.path.isfile(sig) and os.path.isfile(pub)):
        print("[check-sig] no .sig/.pub pair in this package")
        print("            the pair is produced at release time and published alongside the release")
        print("            to verify: openssl pkeyutl -verify -pubin -inkey SHA256SUMS.pub \\")
        print("                       -rawin -in SHA256SUMS -sigfile SHA256SUMS.sig")
        return 2
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except Exception:
        print("[check-sig] the 'cryptography' module is not installed here")
        print("            verify with any Ed25519 tool over the raw bytes of SHA256SUMS:")
        print("            openssl pkeyutl -verify -pubin -inkey %s -rawin -in %s -sigfile %s"
              % (pub, os.path.join(pkg, "SHA256SUMS"), sig))
        return 2
    raw = open(os.path.join(pkg, "SHA256SUMS"), "rb").read()
    sigb = open(sig, "rb").read()
    pubb = open(pub, "rb").read()
    if pubb.startswith(b"-----BEGIN"):
        from cryptography.hazmat.primitives import serialization
        key = serialization.load_pem_public_key(pubb)
    else:
        key = Ed25519PublicKey.from_public_bytes(pubb)
    try:
        key.verify(sigb, raw)
        print("[check-sig] Ed25519: OK")
        return 0
    except Exception as e:
        print("[check-sig] Ed25519: FAIL (%s)" % e)
        return 1


def cmd_reproduce(pkg, ws):
    tool = os.path.join(pkg, "tools", "reproduce_all.py")
    if not os.path.isfile(tool):
        print("[reproduce] tools/reproduce_all.py not present in this package")
        return 2
    cmd = [sys.executable, tool, pkg] + ([ws] if ws else [])
    print("[reproduce] running the package's own one-click check (read-only)")
    r = subprocess.run(cmd)
    print("[reproduce] exit code %d" % r.returncode)
    return r.returncode


def cmd_manifest(pkg):
    for name in ("VERSION", "SELF-CHECK.txt", "_FROZEN"):
        p = os.path.join(pkg, name)
        if os.path.isfile(p):
            body = open(p, encoding="utf-8", errors="replace").read().strip().split("\n")
            print("--- %s ---" % name)
            for ln in body[:20]:
                print("  " + ln)
    su = os.path.join(pkg, "SHA256SUMS")
    if os.path.isfile(su):
        n = len([x for x in open(su, encoding="utf-8", errors="replace").read().split("\n") if "  " in x])
        print("--- SHA256SUMS ---")
        print("  listed files: %d" % n)
    print("--- on disk ---")
    allf = list(_walk(pkg))
    print("  total files: %d" % len(allf))
    return 0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    sub, pkg = argv[1], os.path.abspath(argv[2])
    ws = os.path.abspath(argv[3]) if len(argv) > 3 else None
    if not os.path.isdir(pkg):
        print("not a directory: %s" % pkg)
        return 2
    if sub == "check-sums":
        return cmd_check_sums(pkg)
    if sub == "check-sig":
        return cmd_check_sig(pkg)
    if sub == "reproduce":
        return cmd_reproduce(pkg, ws)
    if sub == "manifest":
        return cmd_manifest(pkg)
    if sub == "all":
        rc = 0
        for fn in (lambda: cmd_manifest(pkg), lambda: cmd_check_sums(pkg),
                   lambda: cmd_check_sig(pkg), lambda: cmd_reproduce(pkg, ws)):
            rc = max(rc, fn())
        print("\n[all] worst exit code: %d" % rc)
        return rc
    print("unknown subcommand: %s" % sub)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
