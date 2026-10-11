# Stablecoin admission list


> **上位**：`PHAROS-FIN-100`；**本件为**经营层政策**，**非协议判据**。

**编号**：PHAROS-POL-001-V1.0
**名称**：稳定币准入清单（经营层政策）
**上位**：PHAROS-FIN-100-V1.0
**状态**：草案
**批准人**：协议维护者
**日期**：2026-10-11
**持有方**：协议维护者


---
> **This file is operational policy, not protocol.** It can be updated without rebuilding

> the specification package. The protocol only fixes **which four dimensions** are recorded

> and **which profiles** exist; the concrete list lives here.

> **本件为经营层政策，非协议判据**；**更新它不需重建包**。
> **协议只固定“记哪四个维度”与“有哪几档”**；**具体币种在本件**。

## What this file does not say

> **It does not state that any asset is compliant.** Compliance is defined by regulators.

> This file states only **what we are willing to accept**, and **by what evidence**.

> **它不声明任何资产“合规”**；**只说明我方接受范围与凭据**。

## Dimensions

| id | 维度 | 档位 |
|---|---|---|
| `license_type` | **牌照类型** | `bank` / `payment` / `msb_mtl` / `none` |
| `jurisdiction` | **法域** | `admitted` / `major_other` / `unknown` |
| `reserve_attestation` | **储备鉴证** | `audited_1to1` / `attested_monthly` / `attested_less` |
| `redemption` | **兑付主体** | `issuer_licensed` / `issuer_unlicensed` / `third_party` |

## Profiles

| profile | 用于 | 取值 |
|---|---|---|
| `strict` | **大额与出金** | **三项均最严** |
| `standard` | **常规交付** | **支付类牌照＋月度鉴证以上＋主要法域** |
| `broad` | **小额 A2A** | **接受事实标准，但不接受无牌照** |

## Hard floor

| # | 硬底 |
|---|---|
| 1 | **`license_type` 不得为 `none`** |
| 2 | **`redemption` 不得为 `third_party`** |

## Candidate list

| 币 | 发行主体 | license_type | jurisdiction | reserve_attestation | redemption | profile | accepted | verification |
|---|---|---|---|---|---|---|---|---|
| **`USDT`** | Tether | `msb_mtl` | `unknown` | `attested_less` | `未证` | `broad` | **❌** | 未证 |
| **`USDC`** | Circle | `payment` | `major_other` | `attested_monthly` | `issuer_licensed` | `standard` | **❌** | 未证 |
| **`EURC`** | Circle | `payment` | `major_other` | `attested_monthly` | `issuer_licensed` | `standard` | **❌** | 未证 |
| **`PYUSD`** | Paxos | `bank` | `major_other` | `未证` | `未证` | `strict` | **❌** | 未证 |

> ⭐ **`accepted` 全为 `❌` 是正确状态**：**证据尚在核实**，**白名单不能凭公开报道收紧**。

## Open questions per entry

### `USDT`（Tether）
- **发行主体到底是哪一实体**（`Tether` 下多实体）
- **萨尔瓦多许可的类别与范围**
- **储备鉴证的频率与出具方**
- **RGB 上发行的稳定币主体是否与上述同一实体**
- 证据：[https://tether.io/news/tether-licensed-in-el-salvador-streng](https://tether.io/news/tether-licensed-in-el-salvador-strengthening-focus-on-emerging-markets-and-innovation/)

### `USDC`（Circle）
- **`MiCA` 授权的具体实体与法域**（如法国）
- **储备鉴证的出具方与频率**
- **是否满足 1:1 可审计**
- 证据：[https://www.circle.com/blog/one-year-of-mica-momentum-confid](https://www.circle.com/blog/one-year-of-mica-momentum-confidence-and-the-road-to-global-alignment)

### `EURC`（Circle）
- **欧元账户在我方市场可用性**
- **兑付与出金路径**
- 证据：[https://developers.circle.com/stablecoins/what-is-eurc](https://developers.circle.com/stablecoins/what-is-eurc)

### `PYUSD`（Paxos）
- **`OCC` 特许的生效日与业务范围**
- **储备鉴证方式**
- **在我方市场的可用性**
- 证据：[https://blockchain.news/postamp?id=paxos-occ-charter-stablec](https://blockchain.news/postamp?id=paxos-occ-charter-stablecoins)

## Rule for adding an entry

1. **Four dimensions must each be filled**; **a blank stays blank and is marked 未证**.

2. **`as_of` must carry a real date**; **if no date can be evidenced, the entry is not accepted**.

3. **`accepted_by_us` is set only after the evidence is read**, not after a press release is read.

4. **Removing an entry is always allowed** and needs no protocol change.

## 关于“待裁参数”的一句说明

> ⭐ **待裁参数**，不是**未取数****：**参数已定义（名称与含义），只是**数值尚未裁定**。按 `000-070-001`，**未裁定的数值不得作为实测值引用**。
