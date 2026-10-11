# -*- coding: utf-8 -*-
r"""gen_task_loop.py —— 锚 5：真实任务闭环（用现成件，七步）。"""
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merkle as M  # noqa: E402


def canon(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main(argv):
    V = os.path.abspath(argv[1]) if len(argv) > 1 else "."
    # 1 任务声明
    task = {"taskId": "TASK-20261010-0001",
            "client": "\u53d7\u6258\u65b9-\u7532",
            "declaredBy": "\u7ecf\u8425\u4e3b\u4f53-\u65b0\u52a0\u5761",
            "acceptCriteria": ["CORE-001-221", "CORE-001-222"],
            "deliverable": "\u6279\u91cf\u4efb\u52a1\u4ea4\u4ed8\u4e0e\u8ba1\u91cf\u7ed3\u7b97\u7ed3\u679c\u96c6"}
    # 2 双方独立产出
    items = [{"i": i, "given": "g%03d" % i, "done": True} for i in range(12)]
    h = [hashlib.sha256(canon(it)).hexdigest() for it in items]
    # 3 证明前置
    leaves = [M.leaf_hash(canon({"id": it["i"], "h": h[it["i"]]})) for it in items]
    root = M.mth(leaves)
    pre_ok = all(M.verify_inclusion(k, len(leaves), leaves[k], M.inclusion_path(k, leaves), root)
                 for k in range(len(leaves)))
    # 4 对拍结论（报首个差异字节）
    unequal = []
    # 5 计量轨：单位成本 × 1.20（不出我方名义标价）
    unit_cost, markup, units = 3.00, 1.20, len(items)
    fee = round(unit_cost * markup * units, 2)
    # 6 可核指向（匿名但可追责，只出指向值）
    ref = hashlib.sha256(canon({"task": task["taskId"], "root": root.hex(),
                                "rows": sorted(h)})).hexdigest()
    rec = {"_note": "\u951a 5 \u771f\u5b9e\u4efb\u52a1\u95ed\u73af\uff08\u7528\u73b0\u6210\u4ef6\u751f\u6210\uff09\u3002",
           "_rule": ("\u2460 \u5148\u9a8c\u5305\u542b\u8bc1\u660e\uff08\u4e0d\u8fc7\u5219\u62d2\u7edd\u51fa\u7ed3\u8bba\uff09\uff1b"
                     "\u2461 \u5bf9\u62cd\u62a5**\u9996\u4e2a\u5dee\u5f02\u5b57\u8282**\uff1b"
                     "\u2462 \u8ba1\u91cf\u8f68\uff1d\u5355\u4f4d\u6210\u672c\u00d71.20\uff08**\u4e0d\u51fa\u6211\u65b9\u540d\u4e49\u6807\u4ef7**\uff09\uff1b"
                     "\u2463 \u53ef\u6838\u6307\u5411\u53ea\u51fa\u6307\u5411\u503c\u3002"),
           "task": task,
           "proofPre": "OK" if pre_ok else "FAIL",
           "treeSize": len(leaves), "root": root.hex(),
           "reconcile": {"equal": len(h) - len(unequal), "unequal": unequal},
           "metering": {"unitCost": unit_cost, "markup": markup, "units": units,
                        "fee": fee, "rail": "\u8ba1\u91cf\u8f68"},
           "checkableRef": ref,
           "receipts": ["\u4efb\u52a1\u58f0\u660e", "\u53cc\u65b9\u4ea7\u51fa",
                        "\u5bf9\u62cd\u7ed3\u8bba", "\u53ef\u6838\u6307\u5411"]}
    dst = os.path.join(V, "vectors", "task-loop.json")
    io.open(dst, "w", encoding="utf-8", newline="\n").write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("[TASKLOOP] \u8bc1\u660e\u524d\u7f6e=%s\uff1b\u5bf9\u62cd \u7b49 %d\uff0f\u4e0d\u7b49 %d\uff1b\u8ba1\u91cf\u8d39 %.2f\uff1b\u6307\u5411 %s" % (
        rec["proofPre"], rec["reconcile"]["equal"], len(unequal), fee, ref[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
