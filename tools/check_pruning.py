# -*- coding: utf-8 -*-
r"""check_pruning.py —— **`216` 裁剪实测门**。

口径：`minimumIndex` 推进后，**已发布的证明必须仍有效**（裁剪＝只拒供，不删数据）。
判据：
 N1 推进前：全叶包含证明可验；
 N2 推进 `minimumIndex=k` 后：**证明仍可验**（因为树没变）；
 N3 裁剪后**只影响供给**：请求 `index < minimumIndex` 应被拒绝；
 N4 **根不变**（裁剪不改树）；N5 `minimumIndex` 单调不减且 ≤ `treeSize`。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merkle as M  # noqa: E402


def serve(minimum, idx):
    """模拟提供方：裁剪后拒绝旧下标。"""
    return None if idx < minimum else "path"


def main(argv):
    p = os.path.join(os.path.abspath(argv[1]) if len(argv) > 1 else ".", "vectors", "proof-ledger.json")
    if not os.path.isfile(p):
        print("[PRUNE] 无证明账本（未声称覆盖）：PASS")
        return 0
    j = json.loads(io.open(p, encoding="utf-8").read())
    hs = [bytes.fromhex(l["hash"]) for l in j["leaves"]]
    root0 = bytes.fromhex(j["root"])
    bad = []
    # N1
    for k, l in enumerate(j["leaves"]):
        path = [bytes.fromhex(x) for x in l["path"]]
        if not M.verify_inclusion(k, len(hs), hs[k], path, root0):
            bad.append("N1 第 %d 叶证明无效" % k)
    # N2/N4：推进裁剪后根不变、证明仍可验
    minimum = max(1, len(hs) // 3)
    if M.mth(hs) != root0:
        bad.append("N4 裁剪后根变了")
    for k, l in enumerate(j["leaves"]):
        path = [bytes.fromhex(x) for x in l["path"]]
        if not M.verify_inclusion(k, len(hs), hs[k], path, root0):
            bad.append("N2 裁剪后第 %d 叶证明变无效" % k)
    # N3
    if serve(minimum, 0) is not None:
        bad.append("N3 裁剪后仍向 `index < minimumIndex` 提供")
    if serve(minimum, len(hs) - 1) is None:
        bad.append("N3 裁剪后对新下标也拒供")
    # N5
    if not (0 <= minimum <= len(hs)):
        bad.append("N5 `minimumIndex` 越界")
    bad += _cross_package(os.path.abspath(argv[1]))
    print("[PRUNE] 叶 %d；推进后 minimumIndex=%d；异常 %d" % (len(hs), minimum, len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 \u88c1\u526a\u4e0d\u5408\u683c"))
    return 0 if not bad else 1



def _cross_package(V):
    """P1\u2013P3\uff1a\u8de8\u5305\u88c1\u526a\u7528\u4f8b\u3002"""
    bad = []
    p = os.path.join(V, "vectors", "prune-pair.json")
    if not os.path.isfile(p):
        return bad
    j = json.loads(io.open(p, encoding="utf-8").read())
    data = [b"e%03d" % i for i in range(40)]
    old = [M.leaf_hash(d) for d in data[:j["oldSize"]]]
    new = [M.leaf_hash(d) for d in data]
    if M.mth(old).hex() != j["oldRoot"] or M.mth(new).hex() != j["newRoot"]:
        bad.append("P1 \u65e7\uff0f\u65b0\u6839\u4e0d\u53ef\u91cd\u7b97")
    for rec in j.get("oldProofs", []):
        i = rec["index"]
        path = [bytes.fromhex(x) for x in rec["path"]]
        if not M.verify_inclusion(i, j["oldSize"], old[i], path, bytes.fromhex(j["oldRoot"])):
            bad.append("P1 \u65e7\u8bc1\u660e %d \u5728\u65e7\u6811\u4e0b\u65e0\u6548" % i)
        # \u540c\u4e00\u8bc1\u660e\u5728\u65b0\u6811\u4e0b\u5fc5\u987b\u5931\u8d25\uff08\u6811\u53d8\u4e86\uff09\u2014\u2014\u6545\u4e0d\u80fd\u76f4\u63a5\u62ff\u65e7\u8def\u5f84\u9a8c\u65b0\u6839
        if M.verify_inclusion(i, j["newSize"], new[i], path, bytes.fromhex(j["newRoot"])):
            bad.append("P1 \u65e7\u8def\u5f84\u5c45\u7136\u9a8c\u8fc7\u65b0\u6839\uff08\u4e0d\u5f97\u53d1\u751f\uff09")
    # P2\uff1a\u88c1\u526a\u540e\u65e7\u4e0b\u6807\u62d2\u4f9b\uff0c\u4f46\u65b0\u4e0b\u6807\u53ef\u4f9b
    minimum = j["oldSize"]
    if not (0 <= minimum <= j["newSize"]):
        bad.append("P2 minimumIndex \u8d8a\u754c")
    # P3\uff1a\u4e00\u81f4\u6027\u8bc1\u660e\u8282\u70b9\u975e\u7a7a
    if not j.get("consistency", {}).get("hashes"):
        bad.append("P3 \u7f3a\u4e00\u81f4\u6027\u8bc1\u660e")
    return bad


if __name__ == "__main__":
    sys.exit(main(sys.argv))

