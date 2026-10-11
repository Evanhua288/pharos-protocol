## 2026.11 - admission table, amount bands, operational policies

Specification text unchanged. One layer file changed. No judgement criteria changed.

Added (protocol side):
- `spec/stablecoin-admission.json` - the first admission gate is now decided by an
  externally recorded table with four dimensions (licence type, jurisdiction,
  reserve attestation, redemption party), three profiles, and two hard floors
  (licence type may not be `none`; redemption may not be `third_party`). The table
  is explicitly **not** a statement that any asset is compliant.
- `spec/amount-layering.json` - four bands (`micro`, `normal`, `large`, `offramp`)
  mapping each band to an admission profile and a settlement route, with the
  existing prohibitions copied in verbatim.

Added (operational policy, repository root):
- `POLICY-STABLECOIN-LIST.md` - the concrete token list lives here, not in the
  protocol. All four candidate entries are marked `accepted: no` and `unverified`;
  a blank field stays blank. Reasons: token additions are operational policy and
  must not force a protocol refreeze.
- `POLICY-AMOUNT-BANDS.md` - plain-language companion explaining the bands, why a
  single-transaction ceiling is not a control, and where a threshold may come from.

Changed (layer file):
- `spec/layers/PHAROS-FIN-100-...md` - `FIN-100-023` added: the first gate is
  decided by the external admission table, and the table carries no compliance
  claim. `FIN-100-024` added: per-task amount bands, sharpening the existing
  `FIN-100-052` from cash-out to ordinary deliveries. It changes only which
  profile applies and which route is used. The second gate is untouched, word for
  word.

Withdrawn:
- Two threshold values (a factor of 1 and a factor of 20) were previously written
  into the machine-readable file with no external basis. They have been withdrawn
  and replaced by named pending parameters `T1`, `T2`, `F1`, `A1`. Until they are
  decided, the banding must not be described as in operation.

Rationale: `FIN-100-011` forbids the implementing party from setting a rate
unilaterally, and a per-transaction ceiling without a frequency and a cumulative
limit controls nothing. Both points are now recorded in the file itself.

Verification impact: `CORE-001-V1.2.md` is unchanged, so its hash and all published
vectors and proofs remain valid. The layer set hash is recomputed at build time.

## Unreleased — external-interface and legal minimum

No specification version bump. No judgement criteria changed.

Added (repository root):
- `LICENSE` — dual license: specification text under CC BY 4.0,
  reference implementation and vectors under Apache License 2.0, with an
  explicit excluded set (keys, pipeline, ledgers, customer and pricing data,
  internal records).
- `NOTICE` — attribution for all referenced standards and mechanisms;
  states that no affiliation, endorsement, or certification is claimed, and
  that the protocol name is intentionally not trademarked.
- `SECURITY.md` — private disclosure channel, 72-hour acknowledgement,
  30-day conclusion, coordinated disclosure with pre-fix and post-fix roots,
  safe harbour, and the list of material that must never be shipped.
- `VERSION` — three version series declared; internal snapshot numbers
  must not be cited externally.
- `POLICY-COMPAT.md` — semantic versioning rules, the "always MAJOR" list,
  the backward compatibility promise (C1–C5), and the mapping to the four
  freeze states.

Rationale: during self-assessment we found version numbers had been used as
debug counters (one integer discrepancy consumed eight releases), that the
anchor-exclusion rule was still described as a regex rather than a
whitelist, and that a green internal self-check had been allowed to stand in
for external evidence. This changelog entry records the correction.

Verification impact: none. Published vectors and proofs remain valid.

# 变更日志（CHANGELOG）

> **⚠️ 本表为**历史登记**：**表中哈希为**当时值**，**故意钉死以保追溯**；**现行值一律以包内 `SHA256SUMS` 为准**。

> **本件适用规范版本：`CORE-001-V1.2`**

> **效力档**：**甲 · 协议要求**。
> **本日志只记一件事**：**哪一版改了什么、为什么改、旧实现该怎么办。**
> **它不替代 `spec/CORE-001-*.md` 正文；也不替代 `spec/SPEC-HISTORY.md`（**逐包哈希登记**）。**

---

# 　、★ 先读：版本号怎么读（**三件事**）

| # | 事 |
|---|---|
| **1** | **本协议现为**草案（Draft）****；**版号已进 `V1.x`，但**状态仍是草案****（**版号与状态是两件事**） |
| **2** | **不同版之间，**条款号可能变****——**故不得跨版引用条款号而不写版号** |
| **3** | 🔴 **向量真值**不随版号变****（`CORE-001-120`）：**只在**对象字段或规范化规则改变**时才变。**故凡“未变”类结论，**必须写明与哪一版比较**。 |

---

# 一、现行版：`CORE-001-V1.2`

| 项 | 值 |
|---|---|
| **状态** | **草案（Draft）** |
| **条款** | **107 条定义**（号段至 `CORE-001-124`） |
| **话题数** | **29**（`8+7+6+6+2`） |
| **测试向量** | **10**＋**4 个反面样本** |
| **规范哈希** | **不钉死；请以包内 `SHA256SUMS` 当场核对** |

## 1.1 `V1.2` 改了什么（**本版**）

| # | 变更 | 为什么 |
|---|---|---|
| **1** | **新增 `§〇A` 九条解释原则（序言层）**：**六条地基 ＋ 三条铁律** | 以前它们**一条不在包内**（包内命中 **0/9**）；按 `110`，写在包外者**视为未立** |
| **2** | **新增 `CORE-001-124`**：九条**不单独作为判定依据****；但**条款不得被解释为违反它们** | 防“某条款合规却违反九条”那种争议 |
| **3** | **`FIN-100` 新增 `FIN-100` §4 的 `FIN-030-040`**：**结算周期＝每 7 日**；**变更须走 `OPEN-100-017`～`023` 提案程序** | 原只有“按周期结算”而**无数值**；商户问“何时到账”答不出 |
| **4** | **修正三处正文旧数字**：`044`（“8 个”→“10 个”）；`013`（“八个”→“十个”）；`§七A` 标题（“五个”→“十个”） | 新增判据 `NUM_CLAIM` 抳出的**规范自身矛盾** |

## 1.2 ★ ★ 对旧实现的影响（**这一节是本日志最重要的**）

| 问 | **答** |
|---|---|
| **向量真值变了吗** | ❌ **没变**——**八条原向量**一条都没变**（**与 `V1.1` 逐字节相同**） |
| **我的实现要重写吗** | ❌ **不需**——**字段集、序列化、哈希规则**均未动** |
| **我的一致性声明过期了吗** | ✅ **过期了**——**因为规范哈希变了**；**需改填新哈希** |
| **我该做什么** | ✅ **重跑 `tools/check_vectors.py`**（应 **10/10**）**＋把报告里的规范哈希改成 `f6a6e841…`** |

---

# 二、沿革（**按可告人的粒度**）

> **只列**已对外交付过**的版；**内部中间态不列**（它们不是交付物）。**

| 版 | 规范 | **关键变更** |
|---|---|---|
| **`V0.6`** | `CORE-001-V0.6` | 基础定型：**五对象 ＋ 28 字段 ＋ JCS 哈希 ＋ 三个对账报文** |
| **`V0.7`** | `CORE-001-V0.7` | **`v6` 向量重建**；错误码扩展 |
| **`V0.9`** | `CORE-001-V0.9` | **`CORE-001-028` 改为**强制 `did:key`****；`ALIAS_CONFLICT` 判据入体 |
| **`V0.14`** | `CORE-001-V0.14` | **因 `did:key` 强制，四条向量真值变**（`v1`／`v1b`／`v3-absent`／`v3-null`） |
| **`V1.0`** | （未出包） | **字段 28→29**；**`Identity` 加 `sig`**；**19 件层级规范隨包**；新增 `123` |
| **`V1.1`** | `CORE-001-V1.1` | **修正 JCS 表**（去无依据的“24 条”）；**JCS 官方测试数据入包**；新增 `v7`／`v8` 向量；新增 `120` |
| **`V1.2`** | `CORE-001-V1.2` | **九条序言层 ＋ `124`**；**`FIN-030-040` 结算周期 7 日**；修三处正文旧数字 |

## 2.1 向量真值的变迁（**与 `CORE-001-120` 对应**）

| 向量 | `V0.6` | `V0.7` | `V0.9` | **`V1.1`** | **`V1.2`** |
|---|---|---|---|---|---|
| `v1-minimal` | `1af49e7d…` | 同 | 同 | `94e5dcdf…` | ✅ **未变** |
| `v1b-chained` | `76cc6a7a…` | 同 | 同 | `74893464…` | ✅ **未变** |
| `v2-amount-precision` | `e5dc8a8a…` | 同 | 同 | 同 | ✅ **未变** |
| `v3-absent` | `b513e7e3…` | 同 | 同 | `c7790271…` | ✅ **未变** |
| `v3-null` | `84e1c795…` | 同 | 同 | `41c9f56d…` | ✅ **未变** |
| `v4-cjk` | `c73dafd5…` | 同 | 同 | 同 | ✅ **未变** |
| `v5-negative-zero` | `208e0ed3…` | 同 | 同 | 同 | ✅ **未变** |
| `v6-settlement-clean` | 名为 `v6-settlement-prevhash` | `709d23c5…` | 同 | 同 | ✅ **未变** |
| `v7-identity-minimal` | — | — | — | `050dc1b9…` | ✅ **未变** |
| `v8-identity-rotation` | — | — | — | `75989d9b…` | ✅ **未变** |

> ## **⚠️ 本表的读法**：**“同”=与左侧相邻列相同**；**“未变”=与 `V1.1` 相同**。
> ## **→ 本版（`V1.2`）**一条向量真值都没改**——**而规范哈希改了**。
> ## **→ **这正是 `CORE-001-120` 要求写明“与哪一版比较”的原因**。

---

# 三、不破坏承诺（**从现在起生效**）

| 承诺 | 含义 |
|---|---|
| **字段集不再扩** | **29 字段**为 `V1.x` 内定值**；**若需扩，需 `V2.0` ＋ 迁移说明** |
| **向量只增不改** | **已发布的向量真值不得修改**（`CORE-001-013`）；**新异常只能**新增向量号**** |
| **错误码只增不改** | **`E01`～`E10` 已定**；**新增只能往后排** |
| **版名不得复用** | **已交付版号不得重用**（`XFER-092`） |

---

# 四、已知未完成（**不隐藏**）

| # | 项 | 影响 |
|---|---|---|
| **1** | **对账分歧的收敛规则尚未定义**（`CORE-001-021`） | **未定义前**不得声称“对账解决分歧”**** |
| **2** | **参考实现尚未对外** | **导致部分自验项外部**不可独立复现**** |
| **3** | **“外部人能否在两小时内跑通”仍是假设** | **本仓最需被证伪的一条** |
| **4** | **已发布实现方**：**0** | **本协议尚未被第三方验证** |
| **5** | **完整级（六组全过）**本包尚未覆盖**** | **本包只能自证基础级** |

---

*PHAROS 变更日志 V1.0 · 随包发布。*
