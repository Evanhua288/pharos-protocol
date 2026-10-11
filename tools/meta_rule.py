# -*- coding: utf-8 -*-
r"""meta_rule.py —— **件数规则唯一常量表**。

为何：下列三表曾在「**门**」与「**算术**」里**各定一份**，两份规则不同
⇒ **一个事实两套算法**，永远对不上。现：**三表只定义在此**，门与算术均 `import` 本模块。

口径（逐字）：
  `SELF`  —— **自证件**：计入声明件数 `N`；**不列入两清单表体**；
  `META`  —— **元数据件**：**不计入 `N`**；**不列入两清单**；
  `SIGS`  —— **签名件**：随包；**不计入 `N`**；**不列入两清单**；
  `RATIO` —— 声明总数：**`N` = 清单表行数 `M` + len(SELF)**。
"""
# 自证件（计入 N）
SELF = ("SHA256SUMS", "MANIFEST.sha256")
# 元数据件（不计入 N）
META = ("_FROZEN", "SELF-CHECK.txt")
# 签名件（随包、不计入 N）
SIGS = ("SHA256SUMS.sig", "SHA256SUMS.pub")
# 常驻件（**真件**：在盘上、不受签名影响、**计入 N**）
CONST = ("SHIP-MANIFEST.md",)
# 不列入两清单的件（SELF + META + CONST）
OFF_LIST = tuple(sorted(set(SELF) | set(META) | set(CONST)))


def declared_total(m):
    """N39 ⭐ 唯一算术：**`N = M + 4 + 1`**（自证 2＋签名 2＋常驻 1）。"""
    return int(m) + len(SELF) + len(SIGS) + len(CONST)


def expect_disk(m):
    """CLEAR_AT_CHECK ⭐ **清点时点**的盘上应有件数。

    口径：清点发生在**两清单与签名件已就位**、**自证与元数据件尚未写**之时
    ⇒ 故 `m + len(SELF) + len(SIGS)`。
    """
    return int(m) + len(SELF) + len(SIGS)


def declared_from_disk(disk_total):
    """FROM_DISK ⭐ **声明总数由盘上反推**（单一事实）。

    口径：盘上每一件都必须被数到；`_FROZEN` 与 `SELF-CHECK.txt`
    也是盘上件，故**一律计入**。清单不列它们（自指），但计数不漏。
    """
    return int(disk_total)
