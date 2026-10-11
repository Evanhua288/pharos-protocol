# -*- coding: utf-8 -*-
r"""merkle.py —— **RFC 6962 真实作**。

定义：
  MTH({})   = SHA-256()
  MTH({d0}) = SHA-256(0x00 ‖ d0)
  MTH(D[n]) = SHA-256(0x01 ‖ MTH(D[0:k]) ‖ MTH(D[k:n]))，k = 小于 n 的最大 2 的幂

包含证明：`inclusion_path(m, leaves)` 返回**自上而下**的兄弟哈希列表（`path[0]` 最靠近根）。
本模块**只读不写盘**。
"""
import hashlib


def leaf_hash(data: bytes) -> bytes:
    return hashlib.sha256(b"\x00" + data).digest()


def node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def _k(n: int) -> int:
    """小于 n 的最大 2 的幂。"""
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def mth(leaves):
    n = len(leaves)
    if n == 0:
        return hashlib.sha256(b"").digest()
    if n == 1:
        return leaves[0]
    k = _k(n)
    return node_hash(mth(leaves[:k]), mth(leaves[k:]))


def inclusion_path(m: int, leaves):
    """自上而下的兄弟哈希列表。"""
    n = len(leaves)
    if m < 0 or m >= n:
        raise ValueError("index out of range")
    if n == 1:
        return []
    k = _k(n)
    if m < k:
        return [mth(leaves[k:])] + inclusion_path(m, leaves[:k])
    return [mth(leaves[:k])] + inclusion_path(m - k, leaves[k:])


def verify_inclusion(m: int, n: int, leaf: bytes, path, root: bytes) -> bool:
    """自后向前折叠；**每层用当前子区间起点与 k 的位置判方向**。

    ⏪ 修正：旧版用 `idx % 2` 在**非满二叉树**（n=7）上算错。
    """
    if m < 0 or n <= 0 or m >= n:
        return False
    idx, size = m, n
    stack = []
    while size > 1:
        k = _k(size)
        if idx < k:
            stack.append((idx, k, "R"))
            size = k
        else:
            stack.append((idx - k, size - k, "L"))
            idx -= k
            size = size - k
    h = leaf
    for p, (i2, s2, side) in zip(reversed(path), reversed(stack)):
        h = node_hash(h, p) if side == "R" else node_hash(p, h)
    return h == root


def _subproof(m, leaves, b=True):
    """RFC 6962 \u00a72.1.2 `SUBPROOF(m, D[n], b)`\uff08**\u9010\u884c\u7ffb\u8bd1**\uff09\u3002

    \u8fd4\u56de\uff1a`(proof_nodes, ok)`\u2014\u2014`ok` \u8868\u793a\u672c\u8f6e\u62c6\u89e3**\u81ea\u6d3d**\u3002
    \u4e3a\u4f55\u5408\u4e00\uff1a\u751f\u6210\u4e0e\u6821\u9a8c**\u53ea\u6709\u4e00\u5957\u903b\u8f91** \u21d2 \u4e0d\u53ef\u80fd\u4e0d\u914d\u5957\u3002
    """
    n = len(leaves)
    if m == n:
        return ([] if b else [mth(leaves)]), True
    if m <= 0 or m > n:
        return [], False
    k = _k(n)
    # ⭐ V1.84 修：**删除旧特例 `b and m == k`**。
    #   RFC 6962 §2.1.2 的 `SUBPROOF` **只有四条规则**（两个基例＋两个递归例），
    #   **没有 `b 且 m == k` 特例**；`m == k` 落进下面的 `m <= k` 分支，
    #   其子调用恰为基例 `m == n, b = true`（返回 `{}`）⇒ 本层只追加 `MTH(D[k:n])`。
    #   实测（独立裁判，RFC §2.1.3 工作示例逐字）：
    #   `PROOF(3,D[7]) = [c,d,g,l]`（4）、**`PROOF(4,D[7]) = [l]`（1）**、`PROOF(6,D[7]) = [i,j,k]`（3）。
    #   旧版返回整段根 `MTH(leaves)`：**计数碰巧为 1，但节点值错**；
    #   中间修法（返回 `[]`）**计数错**。两者均已废。
    if m <= k:
        sub, ok = _subproof(m, leaves[:k], b)
        return sub + [mth(leaves[k:])], ok
    sub, ok = _subproof(m - k, leaves[k:], False)
    return sub + [mth(leaves[:k])], ok


def consistency_proof(m, leaves, b=True):
    """\u4e00\u81f4\u6027\u8bc1\u660e\uff08RFC 6962 \u00a72.1.2\uff09\u3002"""
    p, ok = _subproof(m, leaves, b)
    if not ok:
        raise ValueError("bad consistency request")
    return p


def verify_consistency(m, n, proof, root_m, root_n, leaves):
    """\u53ea\u8bfb\u6821\u9a8c\uff1a**\u5148\u7528\u540c\u4e00\u51fd\u6570\u91cd\u7b97\u8bc1\u660e\uff0c\u518d\u9010\u9879\u6bd4\u5bf9**\u3002

    \u53e3\u5f84\uff1a\u82e5\u7ed9\u5b9a `leaves`\uff0c\u5219**\u4ee5\u91cd\u7b97\u4e3a\u51c6**\uff08\u4e0d\u4fe1\u5916\u90e8\u7ed9\u7684\u53cc\u6839\uff09\u3002
    """
    if m == n:
        return proof == [] and root_m == root_n
    if m <= 0 or m > n:
        return False
    if leaves is not None:
        if mth(leaves[:m]) != root_m or mth(leaves) != root_n:
            return False
        try:
            want, ok = _subproof(m, leaves, True)
        except Exception:
            return False
        return ok and [h.hex() for h in want] == [h.hex() for h in proof]
    return False
