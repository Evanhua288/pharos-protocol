> ⚠️ **中文 Windows 控制台先设编码**：**`set PYTHONIOENCODING=utf-8`**（（否则 `tools/` 脚本输出的特殊字符会让控制台报错并返非零**）**。


## Using this, and being listed

Download and use are **not gated**. No registration is required and
not registering is fully compliant.

If you do build an implementation, you are welcome to be listed in
[`CONTRIBUTORS-REGISTRY.md`](CONTRIBUTORS-REGISTRY.md) in exchange for a
reproduction record. That is voluntary, not an admission condition.

For why the specification is free while metering is billed, see
[`PLAN-FREE-VS-FEE.md`](PLAN-FREE-VS-FEE.md).

## Status of this repository

| Item | Status |
|---|---|
| Specification version | **0.9.0** — revised continuously until 1.0.0 is declared |
| Package release | date-based (for example `2026.10`); internal snapshot numbers are never cited externally |
| Judgement criteria (`tools/`) | **authoritative** — the published checks and vectors decide |
| Test vectors (`vectors/`) | **authoritative** — reproducible by anyone |
| Policy and fascicle files (`spec/layers/`) | **mostly drafts and pending public comment** — they are **intent, not rules in force** |
| Normative requirements | the specification text plus the published checks |

If a policy file and a published check disagree, the check decides. If this
README and a published check disagree, the check decides.

A passing check means an implementation agrees with the published
specification. It does **not** mean any party is compliant with any law,
regulation, standard, or certification scheme.

# PHAROS PROTOCOL · Core Interface Specification

> **本件适用规范版本：`CORE-001-V1.2`**（**无版本标注者视为无效结论**）。**规范内容哈希以 `SHA256SUMS` 中 `spec/CORE-001-V1.2.md` 一行为唯一**（**本件不钉死其值；请以该行**当场核对****）**锚**。

> **效力档**：**甲 · 协议要求**。

> **PHAROS 是一份让两个互相不认识的实现能对上同一本账的接口最小规范：**
> **30 个字段、5 个对象、10 条可自跑的测试向量；**
> **它还包括一份能写成 CI lint 的禁止字段清单。**

**状态**：**草案（Draft）** ｜ **版本**：`CORE-001-V1.2`
**许可**：`Apache-2.0`（**SPDX-License-Identifier: Apache-2.0**）
**协议名使用**：**任何通过一致性测试的实现，可无偿使用 `PHAROS` 协议名**
**日期**：2026-10-06

---

## 这是什么

`CORE-001` 是 PHAROS 协议的**互操作下限**：它只规定"一个实现要与另一个实现对账，最少必须做什么"。

**它不规定**：怎么做（实现自由）、界面、模块选型、商业模式、节点规模、硬件形态。

> **一句话**：**协议不规定怎么做，只规定怎么互相认。**

---

## 快速开始

**三步**（完整版见 [`GETTING-STARTED.md`](GETTING-STARTED.md)）：

```bash
# 1. 安装 JCS 参考库（注意：见下方"已知陷阱"）
pip install rfc8785==0.1.4

# 2. 跑测试向量
python tools/check_vectors.py vectors/

# 3. 跑一致性测试
python tools/tcore1.py .              # 默认作用域：代码类扩展名        # 禁止字段扫描
python tools/tcore2.py routes.example.json   # 禁止端点扫描
python tools/tcore3.py <entries.json> <engine.py>   # 置空对照（两参缺一不可，用法见 SELFCHECK.md §二）
```

---

## ⚠️ 已知陷阱（**请先读这一节**）

**Python 里名字最像"规范 JSON"的库 `canonicaljson` 不合 RFC 8785。**

| 库 | 版本 | JCS 官方测试数据（**6 文件／25 条**） | 结论 |
|---|---|---|---|
| `rfc8785` | 0.1.4 | **6/6 文件（合 25 条）** | ✅ 推荐 |
| `canonicaljson` | 2.0.0 | 🔴 **不合格**（**原记载 14/24，分母已废**） | 🔴 **禁用** |
| `python-json-canonicalization` | — | PyPI 404 | 不存在 |

> **用错库的后果**：**永久不互认，而且查不出原因。**

**npm 用户**：用 `canonicalize@4.0.0`（**5.x 要求 Node ≥ 22**）。

---

## 仓库结构

```
.
├── README.md                 ← 你在这里
├── GETTING-STARTED.md        ← 三步跑通
├── CONTRIBUTING.md           ← 贡献指南
├── DCO                       ← 开发者原创声明
├── LICENSE                   ← Apache-2.0
├── spec/
│   └── CORE-001-V1.2.md      ← 规范正文（≤ 20 页）
├── vectors/                  ← 测试向量（真值）
│   ├── v1-minimal.json
│   ├── v1b-chained.json
│   ├── v2-amount-precision.json
│   ├── v3-absent-vs-null.json
│   └── EXPECTED.md
├── tools/                    ← 自跑工具
│   ├── check_vectors.py
│   ├── tcore1.py
│   ├── tcore2.py
│   └── tcore3.py
└── CONFORMANCE.md            ← 一致性报告模板
```

---

## 三个对象（**规范正文见 `spec/`**）

**五个对象、30 个字段**：

| 对象 | 字段数 | 用途 |
|---|---|---|
| `Identity` | 8 | 身份与密钥 |
| `LedgerEntry` | 7 | 账本条目 |
| `Settlement` | 6 | 结算 |
| `Attestation` | 6 | 履约事实 |
| `Node` | 2 | 节点 |

---

## 一致性等级

| 级 | 内容 | 适合 |
|---|---|---|
| **基础级** | **L／S＋M；只做账本与凭证** | 小团队、试点、单个社区 |
| **完整级** | **六组全过** | 规模运营、跨社区互认 |

**⚠️ 本仓库当前只覆盖基础级。**

---

## 三条自跑测试

| 测试 | 测什么 | 判据 |
|---|---|---|
| `T-CORE-1` | 禁止字段扫描 | 命中数 = 0 |
| `T-CORE-2` | 禁止端点扫描（无跨人排序） | 命中数 = 0 |
| `T-CORE-3` | 置空对照（等级类字段置空后结算结果不变） | 结果不变 |

### ⚠️ `T-CORE-1` 的边界（**明写，免得被误读**）

> **它只挡字段名，不挡语义。**
> **`{"completionDegree":87}` 可以完美通过三条测试。**

**→ 语义级检查必须人工或模型复核（承 `CORE-001-017`）。**

---

## 贡献

**任何实现方（含新加入者）均可提案。** 见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

**关键规则**：

- **提案必须写成**可测目标****（`OPEN-100-018`）
- **公开评论期 14 日**（`OPEN-100-019`）；涉红线 30 日
- **只涉可测目标：达标即并版；未达标自动失效，不追溯**（`OPEN-100-022`）
- **涉红线或铁律：走甲级程序**（`OPEN-100-023`）

---

## 协议名与商标

| 名称 | 规则 |
|---|---|
| **`PHAROS` / `光明塔`（协议名）** | ✅ **任何合规实现无偿使用** |
| **其它层位名称** | 🟡 **保留；与协议隔离；不构成实现门槛** |

**⚠️ 通过六组测试者，可用协议名；未通过者须改称"基于 PHAROS 规范的实验性实现，尚未通过测试"。**

**不得使用"PHAROS 认证""官方 PHAROS""经 PHAROS 认可"——本协议不设认证机构。**

---

## 许可

**规范文本与参考实现一律 `Apache-2.0`。**

**⚠️ 不用 `CC BY 4.0`**：CC 许可明确**不授予专利权**，而规范文本正是实现方最需要专利保护的地方。

---

## 诚实边界

- **本规范为草案，不构成技术标准**；
- **`CORE-001-018` 要求实现方自行附 JCS **官方测试数据**（**6 文件／25 条**）的通过证明**；
- **对账分歧的收敛规则尚未定义**（`CORE-001-021`）——**未定义前不得声称"对账解决分歧"**；
- **本仓库的"基础级"不承诺互认**；
- **外部人是否能在两周内跑通，是本仓库最需要被证伪的假设。**

---

*PHAROS PROTOCOL · Core Interface Specification · CORE-001-V1.2*

> **`T-CORE-1` 作用域（`V1.2` 补注）**：`tcore1.py .` 默认**只扫代码类扩展名**；**`CORE-001-014` 要求的“自由文本中的等价词”口径需加 `--include-md`**：
> `python tools/tcore1.py . --include-md`。**本包在该口径下会命中**（**规范与向量**必须引用禁用词表**），**这类命中需在 `CONFORMANCE.md` §4 逐条申报为“规范文本引用”**，**不构成实现方违规**。

## Repository and releases

- Source repository: https://github.com/Evanhua288/pharos-protocol
- Latest signed release: https://github.com/Evanhua288/pharos-protocol/releases/latest
- Security and conduct contacts: see SECURITY.md
