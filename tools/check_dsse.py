# -*- coding: utf-8 -*-
r"""check_dsse.py —— **DSSE 门**。

判据：
 D1 **`PAE` 格式逐字**：`DSSEv1 SP len(t) SP t SP len(b) SP b`（自造向量）；
 D2 **往返**：信封 → 被签字节 → 与直接 `pae` 一致；
 D3 **`payloadType` 入签**：只改 `payloadType` 而载荷不变 ⇒ 被签字节**必变**；
 D4 **签名叠加**：两签名的被签字节相同；
 D5 **`keyid` 不作安全判定**：改 `keyid` 不影响被签字节。
退出码：0 通过；1 违反；2 无法执行。**只读**。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsse as D  # noqa: E402


def main(argv):
    bad = []
    # D1 格式
    got = D.pae("application/vnd.test+json", b"ab")
    want = b"DSSEv1 25 application/vnd.test+json 2 ab"
    if got != want:
        bad.append("D1 PAE 不符：%r" % got[:40])
    # D2 往返
    env = D.envelope("application/vnd.test+json", b"ab", [("k1", "00")])
    if D.signing_bytes(env) != got:
        bad.append("D2 信封往返不一致")
    # D3 payloadType 入签
    b1 = D.pae("t1", b"x")
    b2 = D.pae("t2", b"x")
    if b1 == b2:
        bad.append("D3 `payloadType` 未入签")
    # D4 叠加
    env2 = D.envelope("application/vnd.test+json", b"ab", [("k1", "00"), ("k2", "11")])
    if D.signing_bytes(env2) != D.signing_bytes(env):
        bad.append("D4 叠加后被签字节变了")
    # D5 keyid 不入签
    env3 = D.envelope("application/vnd.test+json", b"ab", [("OTHER", "00")])
    if D.signing_bytes(env3) != D.signing_bytes(env):
        bad.append("D5 `keyid` 影响了被签字节")
    # 边界：空载荷
    if D.pae("t", b"") != b"DSSEv1 1 t 0 ":
        bad.append("D6 空载荷 PAE 不符")
    print("[DSSE] PAE %s；异常 %d" % (got[:24].decode("ascii", "replace"), len(bad)))
    for x in bad[:10]:
        print("     \u2192 %s" % x)
    print("[RESULT] %s" % ("PASS" if not bad else "FAIL \u2014 DSSE PAE \u4e0d\u5408\u683c"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
