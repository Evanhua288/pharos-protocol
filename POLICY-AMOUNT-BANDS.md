# Amount bands


> **上位**：`PHAROS-FIN-100`；**本件为**经营层政策**，**非协议判据**。

**编号**：PHAROS-POL-002-V1.0
**名称**：额度分层说明（经营层政策＀
**上位**：PHAROS-FIN-100-V1.0
**状态**：草案
**批准人**：协议维护者
**日期**：2026-10-11
**持有方**：协议维护者


---
> This file explains, in plain language, how per-task amount bands work.
> It repeats no threshold number: **the numbers are not decided yet.**
> **本件不写任何阈值数字：因为那些数字尚未裁定。**

## 1. Why there are bands at all

Machine-to-machine tasks are small and fast. If every one of them went through
a licensed settlement channel with per-transaction checks, the cost of the check
would exceed the value of the task, and the channel would become the bottleneck.

Large amounts and any conversion back into ordinary money are the opposite case:
the amount is worth a slower, heavier path.

`FIN-100-024` therefore splits by **per-task amount** and applies a different
admission profile and a different settlement route to each band. The clause is a
sharpening of the existing `FIN-100-052` (export limits), extended from
cash-out to ordinary deliveries.

## 2. The four bands

| Band | What it is | Admission profile | Settlement route | Per-transaction check |
|---|---|---|---|---|
| `micro` | machine-speed small tasks | `broad` | whitelisted stablecoin, pre-charged | no |
| `normal` | ordinary deliveries | `standard` | whitelisted stablecoin or licensed channel | no |
| `large` | large amounts | `strict` | licensed channel, mandatory | yes |
| `offramp` | converting back into ordinary money | `strict` | licensed channel, mandatory | yes |

## 3. What the bands do not change

Bands change **which profile applies** and **which route is used**. They change
nothing else. In particular these remain in force, word for word:

| Clause | Still in force |
|---|---|
| `FIN-100-010` | no convertible money circulates inside the world |
| `FIN-100-013` | user funds may not be used, commingled, or advanced |
| `FIN-100-014` | no external claim of convertibility, appreciation, or yield |
| `FIN-100-021` | no fund pool may be formed |
| `FIN-100` §3.3 | the four forbidden actions |

## 4. Where a threshold may come from

A threshold may **not** be invented by the implementing party: `FIN-100-011`
forbids unilateral price-setting. Every threshold must trace to one of these:

| # | Source | Note |
|---|---|---|
| 1 | the licensed party's own rules | the `KYC-KYT` free-check ceiling is set by the licensed party, not by us |
| 2 | payment-network practice | small-amount no-challenge ceilings are an existing industry fact; we only publish them |
| 3 | a regulatory reporting line | we adopt the line that exists in the jurisdiction where we operate |

## 5. A single-transaction ceiling is not a control

A small per-transaction limit that is not paired with a **frequency** and a
**cumulative** limit controls nothing: many small transactions in a day
aggregate into a large one. Both limits are therefore required:

| Limit | Meaning |
|---|---|
| per-transaction ceiling | the largest single task |
| per-day transaction count | how many tasks per day |
| per-day cumulative amount | total value per day |

## 6. Current status of the numbers

| Item | Status |
|---|---|
| `T1` micro per-transaction ceiling | **pending** |
| `T2` normal per-transaction ceiling | **pending** |
| `F1` micro per-day count | **pending** |
| `A1` micro per-day cumulative amount | **pending** |

Values that were previously written into the machine-readable file (a factor of
1 and a factor of 20) had **no external basis and have been withdrawn**. Until
the four items above are decided, this file and `spec/amount-layering.json`
**must not be used to claim that banding is in operation**.

## 7. What a threshold would have to carry when it is set

1. the source (one of the three above), with a link or a document reference;
2. the date the value was taken;
3. whether it is expressed per transaction, per day, or cumulatively;
4. who may change it, and how a change is published.

## 关于“待裁参数”的一句说明

> ⭐ **待裁参数**，不是**未取数****：**参数已定义（名称与含义），只是**数值尚未裁定**。按 `000-070-001`，**未裁定的数值不得作为实测值引用**。
