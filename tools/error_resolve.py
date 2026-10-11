# -*- coding: utf-8 -*-
r"""error_resolve.py（V1.63 规则表化）—— 错误码分派的**确定性对照**。

**能证什么**：给定输入形态与基准时钟，**本工具按规范算出"应报哪些码"**，
             并与 `vectors/error-codes.json` 的期望逐条比对。
**不能证什么**：不证"你的实现与规范一致"；不替代两方对拍。
**依据**：`CORE-001-155`／`156`／`157`／`167`／`185`／`191`／`195`／`200`／`204`。

⏪ V1.63 规则表化（应对安全深审）：
  · `E02`–`E09` 各有触发面（旧版六码**永不可产出**）；
  · `also_format_error` **真被读取**（旧版从未读 ⇒ 用例恒真）；
  · `E05` 补**四触发面**；`E06` 取 `reason` 六值；`E01` 三义；
  · 时效阈值引 `067` 常量；去掉死代码 `discard("E01")`。

用法：python tools/error_resolve.py vectors/error-codes.json
退出码：0 = 全与期望一致；1 = 有不符；2 = 无法执行。
"""
import io
import json
import sys

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

STALE_LIMIT_MIN = 15                       # CORE-001-067
REASONS_E06 = ("FORBIDDEN_FIELD", "MISSING_REQUIRED", "MISSING_ATTESTATION",
               "DUP_SETTLE_ID", "SELF_ATTESTATION", "FIELD_RANGE")     # 200
FACES_E05 = ("RAIL_MIX", "BIOMETRIC", "NEGATIVE_NET", "REVERSAL_OVER_LIMIT")  # 204

ORDER = ["E10", "E01", "E02", "E03", "E04", "E11", "E05", "E06", "E07", "E08", "E09"]
CLASS = {"E10": "E", "E01": "A", "E02": "A", "E03": "B", "E04": "B",
         "E11": "B", "E05": "C", "E06": "C", "E07": "D", "E08": "D", "E09": "D"}


def _pre(case):
    """把用例字段规范化为内部标记（集中一处，便于机检）。"""
    d = dict(case)
    at, vf, vt = case.get("at"), case.get("validFrom"), case.get("validTo")
    d["_sig_out_of_window"] = bool(at and vf and vt and not (vf <= at < vt))
    face = None
    if case.get("also_rail_currency_conflict"):
        face = "RAIL_MIX"
    elif case.get("biometric"):
        face = "BIOMETRIC"
    elif case.get("net_negative"):
        face = "NEGATIVE_NET"
    elif case.get("reversal_over_limit"):
        face = "REVERSAL_OVER_LIMIT"
    elif case.get("kind") == "forbidden_field" and case.get("text_face"):
        face = "RAIL_MIX"
    d["_e05_face"] = face
    r = case.get("reason")
    if r not in REASONS_E06:
        r = None
    # ⏪ V1.63：只在**字段层**（`layer == "field"`／`kind == "forbidden_field"`）才归 E06；
    #   `layer == "bytes"` 归 E01；`layer == "text"`（E05 文本面）**不归 E06**。
    if r is None:
        _lay = case.get("layer")
        if case.get("kind") == "bad_format":
            if _lay == "field":
                r = "MISSING_REQUIRED" if case.get("field") == "required" else "FIELD_RANGE"
            # _lay == "bytes" ⇒ 不设（归 E01）
        elif case.get("kind") == "forbidden_field" and not case.get("text_face"):
            r = "FORBIDDEN_FIELD"
    if case.get("kind") == "dup_entry":
        # 191：when 与 entryId 全同 ⇒ 字节层 E01
        d["bad_canonical"] = True
        r = None
    d["_e06_reason"] = r
    return d


RULES = [
    ("E10", lambda c: c.get("age_min", 0) > STALE_LIMIT_MIN,
     "067：Δ > 15 分钟 ⇒ E10（只看 age_min，不要求 stale 标志）"),
    ("E01", lambda c: (c.get("bad_canonical") or c.get("input_hash_present")
                       or c.get("also_format_error") or c.get("layer") == "bytes"),
     "8785／字节层"),
    ("E02", lambda c: c.get("hash_mismatch_strict"), "E02：哈希不一致（严格口径）"),
    ("E03", lambda c: c.get("bad_signature"), "E03：签名不可验"),
    ("E04", lambda c: c.get("unknown_did"), "E04：身份不可解析"),
    ("E11", lambda c: c.get("_sig_out_of_window"), "012-B：签名窗口外"),
    ("E05", lambda c: c.get("_e05_face") is not None, "204：E05 四触发面"),
    ("E06", lambda c: c.get("_e06_reason") is not None, "200：E06 六值 reason"),
    ("E07", lambda c: c.get("capability_missing"), "E07：能力缺失"),
    ("E08", lambda c: c.get("capability_conflict"), "E08：能力冲突"),
    ("E09", lambda c: c.get("negotiation_timeout"), "E09：协商超时"),
]


def resolve(case):
    """返回该用例应报的码（按 §6.1 顺序；多类可并存）。"""
    c = _pre(case)
    hits = set()
    for code, pred, _why in RULES:
        try:
            if pred(c):
                hits.add(code)
        except Exception:
            pass
    for code, pred, _why in RULES:
        try:
            if pred(c):
                hits.add(code)
        except Exception:
            pass
    return sorted(hits, key=lambda x: ORDER.index(x))


def main(path):
    data = json.loads(io.open(path, encoding="utf-8").read())
    cases = data.get("cases", data)
    bad = 0
    print("[ERRORS] 用例 %d 条；判定顺序：%s" % (len(cases), " → ".join(ORDER)))
    for c in cases:
        got = resolve(c)
        want = c.get("expect", [])
        ok = got == want
        if not ok:
            bad += 1
        print("  [%s] %-22s 得 %-12s 期望 %-12s%s" % (
            "OK" if ok else "NG", c.get("id", "?"), ",".join(got) or "-",
            ",".join(want) or "-", "" if ok else "  <-- %s" % c.get("why", "")))
    if bad:
        print("[FAIL] 不符 %d 条" % bad)
        return 1
    print("[PASS] 全部与期望一致（%d 条）" % len(cases))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python tools/error_resolve.py vectors/error-codes.json")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
