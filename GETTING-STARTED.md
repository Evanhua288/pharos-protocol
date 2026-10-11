> ⚠️ **中文 Windows 控制台先设编码**：**`set PYTHONIOENCODING=utf-8`**（（否则 `tools/` 脚本输出的特殊字符会让控制台报错并返非零**）**。

# 快速开始

> **本件适用规范版本：`CORE-001-V1.2`**（**无版本标注者视为无效结论**）。**规范内容哈希以 `SHA256SUMS` 中 `spec/CORE-001-V1.2.md` 一行为唯一**（**本件不钉死其值；请以该行**当场核对****）**锚**。

> **效力档**：**甲 · 协议要求**。

> **目标**：**让一个不认识本项目的人，在**两小时内**跑出第一个通过测试的基础级实现。**
> **⚠️ 这个目标是**假设**，尚未被验证。若你跑不通，请在 Issues 里告诉我们卡在哪一步——**那比什么都重要。**

---

## 第 0 步 · 你需要知道的三件事

| # | 事 |
|---|---|
| **1** | **PHAROS 是协议，不是产品。** 它只规定"怎么互相认"。 |
| **2** | **基础级＝只做账本与凭证**，不涉资产、不涉计量轨对外。 |
| **3** | **测试自己会说话**——不需要任何人批准你。 |

---

## 第 1 步 · 装对库（**这一步最容易错**）

```bash
pip install rfc8785==0.1.4
```

**⚠️ 不要装 `canonicaljson`。**

| 库 | RFC 8785 官方向量 | 结论 |
|---|---|---|
| `rfc8785` 0.1.4 | **6/6 文件（合 25 条）** | ✅ |
| `canonicaljson` 2.0.0 | 🔴 **不合格** | 🔴 数字序列化全错 |

**npm**：`npm i canonicalize@4.0.0`（**勿用 5.x，它要 Node ≥ 22**）。

---

## 第 2 步 · 跑测试向量

```bash
git clone <repo-url>
cd pharos-core
python tools/check_vectors.py vectors/
```

**期望输出**：

```
[OK] v1-minimal         94e5dcdf...  MATCH
[OK] v1b-chained        74893464...  MATCH
[OK] v2-amount-precision e5dc8a8a...  MATCH
[OK] v3-absent          c7790271...  MATCH
[OK] v3-null            41c9f56d...  MATCH
[OK] v4-cjk             c73dafd5...  MATCH
[OK] v5-negative-zero   208e0ed3...  MATCH
[OK] v6-settlement-clean 709d23c5...  MATCH
[OK] v7-identity-minimal 050dc1b9...  MATCH
[OK] v8-identity-rotation 75989d9b...  MATCH
[PASS] 10/10 vectors

> ## **⚠️ 以上是**示例输出**（**手写摘要，非程序实跑转录**）。**
> ## **判据一律以**包内 `vectors/EXPECTED.md`**与**你自己跑出的结果**为准**；
> ## **本段若与实跑不符，**以实跑为准**。
```

**若 `v1-minimal` 不 MATCH，八成是库选错了（回第 1 步）。**

---

## 第 3 步 · 写你的第一个条目

**最小合法条目**（`LedgerEntry`，7 字段中的 5 个必填）：

```json
{
  "entryId": "01920000-0000-7000-8000-000000000001",
  "subject": "did:key:z7QEP3xWeQbW3hgmJP-6cLMyQIVJrk5U7UVLVvRxtrQ7OhQ",
  "what": "delivered task T-001",
  "when": "2026-10-06T12:00:00Z",
  "prevHash": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

**哈希规则（**唯一的硬规则**）**：

```
hash = SHA-256( ASCII(prevHash) ‖ UTF-8(JCS(条目，不含 hash 字段)) )
```

**⚠️ 三条口径**：

| # | 口径 |
|---|---|
| **1** | **`prevHash` 是 64 个**小写十六进制 ASCII 字符****，不是 32 字节原始值 |
| **2** | **首条为 64 个 `0`（字符）** |
| **3** | **无分隔符**——ASCII 文本直接拼 UTF-8 字节 |

**算出**：

```bash
python -c "
import rfc8785, hashlib
e={'entryId':'01920000-0000-7000-8000-000000000001','subject':'did:key:z7QEP3xWeQbW3hgmJP-6cLMyQIVJrk5U7UVLVvRxtrQ7OhQ','what':'delivered task T-001','when':'2026-10-06T12:00:00Z','prevHash':'0'*64}
c=rfc8785.dumps(e)
print(hashlib.sha256('0'.encode()*64 + c).hexdigest())
"
```

**期望**：`94e5dcdfdd2c6ada2e6f2930624df958137fc4e4e0e21019c8291f67348d378e`

---

## 第 4 步 · 跑一致性测试

```bash
python tools/tcore1.py .              # 禁止字段扫描
python tools/tcore2.py routes.example.json    # 禁止端点扫描
python tools/tcore3.py <entries.json> <engine.py>   # 两参缺一不可；engine.py 需自供
```

### `T-CORE-1` · 禁止字段扫描

**扫描键名 ＋ 枚举值 ＋ 自由文本中的等价词**：

```
score grade level percentile rank composite weight points badge title
tier tiering grading rating rating_score completionDegree 成型期 完成度
```

**命中数必须为 0。**

**⚠️ 边界**：**它只挡字段名，不挡语义。`{"completionDegree":87}` 会被挡；**
**但若你换个我们没想到的词，它挡不住。语义检查必须人工或模型复核。**

### `T-CORE-2` · 禁止端点扫描

**遍历你的 API 清单（`routes.json`），跨人排序端点必须为 0。**

**`routes.json` 格式**：

```json
{"routes": [{"method": "GET", "path": "/entries/{id}", "returns": "LedgerEntry"}]}
```

### `T-CORE-3` · 置空对照实验

**把所有等级类字段置空，`Settlement` 的结果**不得变化**。**

**⚠️ 你需要先自造一个"最小结算引擎"**——`FIN-100 §6` 是空标题，没有接口定义。

---

## 第 5 步 · 出一份一致性报告

**用 [`CONFORMANCE.md`](CONFORMANCE.md) 模板。**

**必须包含**：

| # | 内容 |
|---|---|
| **1** | **规范版本号 ＋ 哈希** |
| **2** | **JCS **官方测试数据**（**6 文件／25 条**）通过证明** |
| **3** | **十条测试向量的原始输出** |
| **4** | **未覆盖范围**（如未扫描合约／BI／内部台账） |

**⚠️ 第 4 项是硬要求（`VAL-400-020`）**：

> **凡声称"红线扫描通过"，必须附一句"本扫描未覆盖：＿＿～＿＿"。**

---

## 卡住了怎么办

| 症状 | 八成原因 |
|---|---|
| **`v1-minimal` 不 MATCH** | **库选错了（用了 `canonicaljson`）** |
| **哈希对不上但库没错** | **键名排序——JCS 按 UTF-16 码元，Python 默认按码点。**→ **本协议建议键名限 ASCII** |
| **`amount` 校验不过** | **`"1.0"`／`"1.00"` 不合法；写 `"1"`** |
| **`T-CORE-2` 报错** | **没有 `routes.json`——须自造** |
| **`T-CORE-3` 跑不了** | **须先自造最小结算引擎** |

---

## 诚实边界

- **本文件描述的"两小时跑通"是**目标**，不是承诺**；
- **基础级不承诺互认**；
- **对账分歧的收敛规则尚未定义**；
- **若你发现本文件有任何地方写得不清楚，那是我们的问题，不是你的。**

---

*PHAROS PROTOCOL · GETTING-STARTED*
