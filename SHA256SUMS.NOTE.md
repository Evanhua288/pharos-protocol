# NOTE

> **本件适用规范版本：`CORE-001-V1.2`**（**无版本标注者视为无效结论**）。**规范内容哈希以 `SHA256SUMS` 中 `spec/CORE-001-V1.2.md` 一行为唯一**（**本件不钉死其值；请以该行**当场核对****）**锚**。

SHA256SUMS lists every file EXCEPT itself and MANIFEST.sha256.
A checksum list cannot contain its own hash (self-reference).
This exclusion is declared here on purpose: an undeclared exclusion
would make `sha256sum -c` look green while hiding files.

---

# ⚠️ 诚实边界（**本包内证据链能证什么、不能证什么**）

| 本包内可自行验证的 | 经由 |
|---|---|
| **已列出的每一件内容未被篡改** | `sha256sum -c SHA256SUMS`；`tools/check_integrity.py` |
| **清单与磁盘一致**（**无幽灵行、无未列件、无哈希不符**） | `tools/check_integrity.py` |
| **件数算术成立**（`files: N = M + SHA256SUMS + MANIFEST.sha256`） | `tools/check_integrity.py` |

> ## **而本包内**无法自行验证**的，只有一条**：**
> ## **“磁盘上这些，就是全部应交付件。”**
> ## **→ **因为两份清单是由同一个**打包器**生成的**；**
> ## **→ **若打包器漏了一件，**清单与磁盘会一起漏**，**判据看不见**。**
> ## **→ **故：本包内只能证**“清单 ↔ 磁盘 一致”**，**
> ## **　　**不能证**“清单本身完整”**。**

**要证那一条，只能由包外手段**：**签发方的源目录白名单**、
**源目录与包目录逐件对表**、**或第三方签名**。**本包**不含**这三种中的任何一种**。**

**本包内有一份**元数据件**可供交叉参照**：
`spec/layers/PHAROS-000-060-当前有效版本清单`——**但它只管“哪些版本算现行”，不管“件数完整”**。
