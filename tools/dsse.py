# -*- coding: utf-8 -*-
r"""dsse.py —— **DSSE 的 `PAE` 真实作**（DSSE protocol v1.0.2）。

逐字照拄：
  PAE(t, b) = "DSSEv1" SP LEN(t) SP t SP LEN(b) SP b
  其中 LEN(x) 是 x 的 **ASCII 十进制长度**，SP 是 **单个空格**（`0x20`）。

为何用：**被签字节 = {payloadType, 原始载荷}**，**不依赖任何序列化规范**（故不会因
JSON 键序、空白而漂移）；**`payloadType` 入签** 消除类型混淆。
本模块**只读不写盘**。
"""
import hashlib
import json


def pae(payload_type: str, payload: bytes) -> bytes:
    t = payload_type.encode("utf-8")
    return (b"DSSEv1" + b" " + str(len(t)).encode("ascii") + b" " + t
            + b" " + str(len(payload)).encode("ascii") + b" " + payload)


def envelope(payload_type: str, payload: bytes, sigs) -> dict:
    """sigs：`[(keyid, signature_hex)]`。"""
    return {"payloadType": payload_type,
            "payload": __import__("base64").b64encode(payload).decode("ascii"),
            "signatures": [{"keyid": k, "sig": s} for k, s in sigs]}


def signing_bytes(env: dict) -> bytes:
    """从信封取回被签字节（验签方与签名方必须同法）。"""
    import base64 as _b
    return pae(env["payloadType"], _b.b64decode(env["payload"]))


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
