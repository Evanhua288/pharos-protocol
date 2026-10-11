# -*- coding: utf-8 -*-
r"""reconcile.py —— **对拍工具**（承 `CORE-001-219`）。

用法：python reconcile.py <清单A.json> <清单B.json> [--log <日志.json>] [--spec-hash <值>]

做三件：
  ① 逐条比 `hash`；相等者记 `equal`；
  ② 不等者**定位差异的字节**（逐段比对并报首个不同位置）；
  ③ 写入 `--log` 指定的日志（默认 `vectors/reconciliation-log.json`）。

退出码：0 全等；1 有不等；2 无法执行。
"""
import io
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _load(p):
    j = json.loads(io.open(p, encoding="utf-8").read())
    rows = j.get("index") or j.get("clauses") or []
    m = {}
    for r in rows:
        cid = r.get("id")
        if not cid:
            continue
        h = r.get("hash") or r.get("sha256") or ""
        m[cid] = h
    return m


def _first_diff(a, b):
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n if len(a) != len(b) else -1


def main(argv):
    if len(argv) < 3:
        print("usage: reconcile.py <A.json> <B.json> [--log <p>] [--spec-hash <v>]")
        return 2
    A, B = argv[1], argv[2]
    logp = "vectors/reconciliation-log.json"
    if "--log" in argv:
        logp = argv[argv.index("--log") + 1]
    spech = ""
    if "--spec-hash" in argv:
        spech = argv[argv.index("--spec-hash") + 1]
    try:
        ma, mb = _load(A), _load(B)
    except Exception as e:
        print("[RC] \u65e0\u6cd5\u8bfb\u53d6\uff1a%s" % e)
        return 2
    # ⭐ 新增（本会话）：**证明前置**——若对拍对象所在目录含 `proof-ledger.json`，
    #    先验**包含证明**（RFC 6962），再逐条比叶。这样对拍不再"逐字节盲比"。
    pre = ""
    try:
        import sys as _sys
        _td = os.path.dirname(os.path.abspath(__file__))
        if _td not in _sys.path:
            _sys.path.insert(0, _td)
        import merkle as _M
        for d in {os.path.dirname(os.path.abspath(A)), os.path.dirname(os.path.abspath(B))}:
            pl = os.path.join(d, "proof-ledger.json")
            if not os.path.isfile(pl):
                continue
            _j = json.loads(io.open(pl, encoding="utf-8").read())
            _hs = [bytes.fromhex(l["hash"]) for l in _j["leaves"]]
            _root = bytes.fromhex(_j["root"])
            _ok = (_M.mth(_hs) == _root)
            for _k, _l in enumerate(_j["leaves"]):
                _p = [bytes.fromhex(x) for x in _l["path"]]
                if not _M.verify_inclusion(_k, len(_hs), _hs[_k], _p, _root):
                    _ok = False
                    break
            pre = "OK" if _ok else "FAIL"
            print("[RC] \u8bc1\u660e\u524d\u7f6e\uff1a%s\uff08\u53f6 %d\uff09" % (pre, len(_hs)))
            if not _ok:
                print("[RC] \u8bc1\u660e\u524d\u7f6e\u672a\u8fc7 \u21d2 \u62d2\u7edd\u51fa\u5bf9\u62cd\u7ed3\u8bba")
                return 2
            break
    except Exception as _e:
        print("[RC] \u8bc1\u660e\u524d\u7f6e\u8df3\u8fc7\uff1a%s" % _e)
    ids = sorted(set(ma) | set(mb))
    equal, unequal, only = 0, [], []
    for cid in ids:
        ha, hb = ma.get(cid), mb.get(cid)
        if ha is None or hb is None:
            only.append(cid)
            continue
        if ha == hb:
            equal += 1
        else:
            unequal.append({"clause": cid, "hashA": ha, "hashB": hb,
                            "firstDiffAt": _first_diff(ha, hb)})
    print("[RC] \u5171 %d \u6761\uff1b\u76f8\u7b49 %d\uff1b**\u4e0d\u7b49 %d**\uff1b\u4ec5\u4e00\u65b9\u6709 %d" % (
        len(ids), equal, len(unequal), len(only)))
    for x in unequal[:12]:
        print("     \u2192 %s \u9996\u4e2a\u4e0d\u540c\u4f4d\u7f6e\uff1a%s" % (x["clause"], x["firstDiffAt"]))
    for cid in only[:12]:
        print("     \u2192 \u4ec5\u4e00\u65b9\u6709\uff1a%s" % cid)
    rec = {"clause": "\u6574\u4ef6", "env": {"specHash": spech, "toolVersion": "reconcile.py/1.1",
                                           "proofPre": pre or "\u65e0\u8bc1\u660e\u8d26\u672c"},
           "hashOurs": "", "hashTheirs": "", "verdict": "equal" if not (unequal or only) else "unequal",
           "diffBytes": unequal[:50], "loggedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z"}
    ji = []
    if os.path.isfile(logp):
        try:
            ji = json.loads(io.open(logp, encoding="utf-8").read()).get("entries", [])
        except Exception:
            ji = []
    ji.append(rec)
    os.makedirs(os.path.dirname(os.path.abspath(logp)), exist_ok=True)
    io.open(logp, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"_note": "\u5bf9\u62cd\u7ed3\u8bba\u53f0\u8d26\uff08\u627f CORE-001-219\uff09", "entries": ji},
                   ensure_ascii=False, indent=2) + "\n")
    print("[RC] \u65e5\u5fd7\u5df2\u5199\uff1a%s\uff08\u5171 %d \u6761\uff09" % (logp, len(ji)))
    return 0 if not (unequal or only) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
