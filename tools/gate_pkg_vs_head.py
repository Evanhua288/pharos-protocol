# -*- coding: utf-8 -*-
r"""gate_pkg_vs_head.py —— **包 vs HEAD 门**（F-03 闭合门）。

检什么：交付包内**每一件** 与 `git show HEAD:<同路径>`（即 HEAD blob 的**原始字节**）**逐字节比**。
报两个数：**缺失**（包内有、HEAD 树内无）／**字节不同**。

判定：
  PASS ⇔ **字节不同 ＝ 0** 且 **缺失 ⊆ 允许清单**（包内自生成锚件，本来就不在 Git 树里）。
  允许清单默认＝`MANIFEST.sha256, SELF-CHECK.txt, SHA256SUMS, SHA256SUMS.pub, SHA256SUMS.sig,
  SHIP-MANIFEST.md, _FROZEN`（7 件；可用 `--allow-missing a,b` 覆盖）。
  ★ 任何**不在**允许清单内的缺失 ⇒ FAIL（不得靠"反正 HEAD 没有"放过）。

附（**不计入 PASS/FAIL**，只报事实）：
  · `git status --porcelain` 是否为空（`--require-clean` 可把它升为硬门）；
  · HEAD 树内有、包内无的件（仅信息：包由白名单构建，本就不含全部仓内件）。

纪律：**只读**（`git cat-file` 不写对象库；不写任何文件）。退出码 0＝PASS，1＝FAIL，2＝无法执行。

用法：
    python tools/gate_pkg_vs_head.py .                       # 在包目录内，自动找 ../pharos-core
    python tools/gate_pkg_vs_head.py <包目录> --repo <仓目录>
"""
import hashlib
import io
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ALLOW_MISSING_DEFAULT = {
    "MANIFEST.sha256", "SELF-CHECK.txt", "SHA256SUMS", "SHA256SUMS.pub",
    "SHA256SUMS.sig", "SHIP-MANIFEST.md", "_FROZEN",
}


def git(repo, args, binary=False):
    p = subprocess.run(["git", "-C", repo] + args, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError("git %s 失败：%s" % (" ".join(args), (p.stderr or b"").decode("utf-8", "replace")[:200]))
    return p.stdout if binary else p.stdout.decode("utf-8", "replace")


def head_tree(repo):
    """返回 {relpath: blob_sha}（-z：不做路径引号转义，中文路径安全）。"""
    out = git(repo, ["ls-tree", "-r", "-z", "HEAD"], binary=True)
    d = {}
    for rec in out.split(b"\0"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        mode, typ, sha = meta.split(b" ")
        if typ == b"blob":
            d[path.decode("utf-8")] = sha.decode("ascii")
    return d


def cat_blobs(repo, shas):
    """一次 `git cat-file --batch` 取回多个 blob 原始字节。"""
    if not shas:
        return {}
    p = subprocess.run(["git", "-C", repo, "cat-file", "--batch"],
                       input=("\n".join(shas) + "\n").encode("ascii"), capture_output=True)
    out = p.stdout
    res, i = {}, 0
    while i < len(out):
        nl = out.find(b"\n", i)
        if nl < 0:
            break
        header = out[i:nl].split(b" ")
        if len(header) < 3:
            break
        sha, typ, size = header[0].decode(), header[1].decode(), int(header[2])
        start = nl + 1
        res[sha] = out[start:start + size]
        i = start + size + 1
    return res


def main(argv):
    if len(argv) < 2:
        print("usage: gate_pkg_vs_head.py <包目录> [--repo <仓目录>] [--allow-missing a,b] [--require-clean]")
        return 2
    pkg = os.path.abspath(argv[1])
    repo = None
    if "--repo" in argv:
        repo = os.path.abspath(argv[argv.index("--repo") + 1])
    allow = set(ALLOW_MISSING_DEFAULT)
    if "--allow-missing" in argv:
        allow = set(x.strip() for x in argv[argv.index("--allow-missing") + 1].split(",") if x.strip())
    require_clean = "--require-clean" in argv
    if repo is None:
        # ⭐ 多候选定位（第三方 G-4）：原写法**只在 `dirname(pkg)/pharos-core` 找一个候选** ⇒
        #   对"包副本"（如在临时目录里复验）跑必然找不到仓，返回 rc=2 而**易被误读为 FAIL**。
        #   改为**按顺序找多个候选**，并把"有没有找到"与"找到哪个"都打出来。
        cands = []
        cands.append(os.path.join(os.path.dirname(pkg), "pharos-core"))
        # ① 从包目录与其各级父目录找 `pharos-core`
        d = pkg
        for _ in range(6):
            d = os.path.dirname(d)
            if not d or d == os.path.dirname(d):
                break
            cands.append(os.path.join(d, "pharos-core"))
        # ② 从当前工作目录往各级父目录找 `pharos-core`
        d = os.getcwd()
        for _ in range(6):
            cands.append(os.path.join(d, "pharos-core"))
            nd = os.path.dirname(d)
            if not nd or nd == d:
                break
            d = nd
        # ③ 包内自带 `tools/` 时，其父目录也可能是仓（**包＝仓**的情况）
        cands.append(os.path.dirname(pkg))
        seen = set()
        for c in cands:
            c = os.path.abspath(c)
            if c in seen:
                continue
            seen.add(c)
            if os.path.isdir(os.path.join(c, ".git")):
                repo = c
                break
    if not repo or not os.path.isdir(os.path.join(repo, ".git")):
        print("  [无法执行] 找不到 Git 仓 —— 这不等于 FAIL（是「没得比」）")
        print("             已试候选：%s" % "、".join(sorted(seen)[:8]))
        print("             ⭐ 请显式指定：python tools/gate_pkg_vs_head.py <包目录> --repo <仓目录>")
        return 2
    if not os.path.isdir(pkg):
        print("[RESULT] FAIL -- 包目录不存在：%s" % pkg)
        return 2

    print("== gate_pkg_vs_head：包=%s" % pkg)
    print("   repo=%s  HEAD=%s" % (repo, git(repo, ["rev-parse", "--short", "HEAD"]).strip()))
    ht = head_tree(repo)
    files = []
    for dp, dn, fn in os.walk(pkg):
        if "__pycache__" in dp:
            continue
        for f in fn:
            full = os.path.join(dp, f)
            files.append(os.path.relpath(full, pkg).replace("\\", "/"))
    files.sort()

    missing = [r for r in files if r not in ht]
    common = [r for r in files if r in ht]
    blobs = cat_blobs(repo, sorted(set(ht[r] for r in common)))
    diff = []
    for r in common:
        b = io.open(os.path.join(pkg, r.replace("/", os.sep)), "rb").read()
        hb = blobs.get(ht[r])
        if hb is None:
            diff.append((r, len(b), -1, "HEAD blob 读取失败"))
        elif b != hb:
            off = next((i for i in range(min(len(b), len(hb))) if b[i] != hb[i]), min(len(b), len(hb)))
            diff.append((r, len(b), len(hb), "首个不同 offset=%d" % off))

    print("   包内件＝%d；HEAD 树内件＝%d" % (len(files), len(ht)))
    print("   ⭐ 缺失（包内有、HEAD 无）＝%d" % len(missing))
    print("   ⭐ 字节不同＝%d" % len(diff))
    for r, a, b, why in diff[:20]:
        print("      [不同] %-52s 包=%d B HEAD=%d B %s" % (r, a, b, why))
    if len(diff) > 20:
        print("      … 共 %d 件不同" % len(diff))
    bad_missing = [r for r in missing if r not in allow]
    if missing:
        print("   缺失明细：")
        for r in missing:
            print("      %-52s %s" % (r, "允许（包内自生成锚件）" if r in allow else "★ 不在允许清单 ⇒ FAIL"))
    head_only = [r for r in ht if r not in files]
    # ⭐ 双向门（第三方 G-3）：**"HEAD 有、包内无"必须报 FAIL**。
    #   为何：本门原先只查"包内件 ∈ HEAD"，反向仅打 [INFO] ⇒
    #   **仓里新加的件没进包，门照样 PASS**。第三方复验正是据此外加实测：
    #   删掉包副本内一件在 HEAD 树中的件，门仍 PASS。
    #   后果不是洁癖：`POLICY-FINANCE-ANCHOR.md`（T5 移出内容的落点）
    #   就这样**在仓、不在包**，而**收件方拿到的是包**。
    if head_only:
        print("   [FAIL] ⭐ HEAD 有、包内无＝%d 件（**白名单/打包器漏件**）：" % len(head_only))
        for r in head_only[:12]:
            print("      %s" % r)
    else:
        print("   [PASS] HEAD 有、包内无＝0 件")
    porcelain = git(repo, ["status", "--porcelain"]).strip()
    if porcelain:
        print("   [INFO] git status --porcelain 非空（%d 行）%s" % (len(porcelain.split("\n")),
              "；--require-clean 时计为硬门" if require_clean else "（本门默认不计入 PASS/FAIL）"))
        for l in porcelain.split("\n")[:5]:
            print("      %s" % l[:110])
    else:
        print("   [PASS] git status --porcelain 为空")

    print("-" * 68)
    ok = (not diff) and (not bad_missing) and (not head_only)
    if require_clean and porcelain:
        ok = False
        print("  [FAIL] --require-clean：工作树不干净")
    for r in head_only:
        print("  [FAIL] HEAD 有、包内无（**漏件**）：%s" % r)
    for r in bad_missing:
        print("  [FAIL] 缺失且不在允许清单：%s" % r)
    for r, a, b, why in diff[:10]:
        print("  [FAIL] 字节不同：%s（%s）" % (r, why))
    print("  [RESULT] %s（缺失 %d／漏件 %d／字节不同 %d）"
          % ("PASS -- 双向一致" if ok else "FAIL -- 包与 HEAD 不一致", len(missing), len(head_only), len(diff)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
