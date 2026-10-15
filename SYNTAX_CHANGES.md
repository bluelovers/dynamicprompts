# 語法新增與變更記錄 / New & Changed Syntax

本文件**專門記錄新增或已變更的模板語法**，每項包含語法形式、語意、範例與相容性說明。

- 想了解**既有完整語法** → [docs/TEMPLATE_SYNTAX.md](docs/TEMPLATE_SYNTAX.md)
- 想了解 **YAML Wildcard 檔案格式** → [docs/YAML_SYNTAX.md](docs/YAML_SYNTAX.md)
- 想了解**符號佔用與衝突分析**（設計新語法時參考） → [docs/SYNTAX_SYMBOLS.md](docs/SYNTAX_SYMBOLS.md)
- 想看**發佈版本摘要** → [CHANGELOG.md](CHANGELOG.md)

記錄順序為新在上。本文件為中文為主，僅在譯名不唯一或易生歧義的技術術語處保留英文原詞。

### 術語約定 / Terminology

**`Wildcard` 一律保留英文且首字大寫，不譯為「萬用字元」。** 因為本專案的 `Wildcard` 指「具名的值集合」（由 `__name__` 引用），而一般運算意義的萬用字元是 globbing metacharacter `` `*` ``，兩者會在同一個 codebase 內並存（`Wildcard` 名稱本身支援 glob）。以中文統稱將無法區分，故依術語規則採用僅英文；真正的萬用字元一律以符號 `` `*` `` 標記。首字大寫則用以與程式碼識別字（`wildcard_manager.py`、`sort_wildcards` 等一律小寫）區隔。詳見 [docs/SYNTAX_SYMBOLS.md](docs/SYNTAX_SYMBOLS.md#0-術語約定wildcard--terminology)。

---

## 目錄 / Contents

1. [`^` 修飾符：隨機挑選但保留宣告順序](#-修飾符隨機挑選但保留宣告順序)

---

## `^` 修飾符：隨機挑選但保留宣告順序 / Preserve Declaration Order

> 狀態：已實作，尚未發佈
> 參考提交：`7cf553b`

### 背景 / Motivation

變體 (Variant) 指定多個選項數量時，例如 `{~2$$a|b|c|d}`，取樣器會挑出 2 個選項。但**輸出順序是「選取順序」**而非「宣告順序」：

```
{~2$$a|b|c|d}   挑到 c 與 a  →  輸出 "c,a"
```

對多數提示詞用途而言，這個順序是無意義的隨機結果。`^` 修飾符 (Modifier) 讓挑選仍保持隨機，但**輸出一律按選項的宣告順序**：

```
{~^2$$a|b|c|d}  挑到 c 與 a  →  輸出 "a,c"
```

### 語法 / Syntax

`^` 放在取樣器符號 (Sampler Symbol) 之後、界限式 (Bound Expression) 之前：

```
{^ 選項}          搭配 generator 的預設取樣器
{~^ 選項}         隨機取樣 + 保留宣告順序
{!^ 選項}         組合取樣 + 保留宣告順序
{@^ 選項}         循環取樣 + 保留宣告順序
```

完整文法位置：

```
<variants> ::= <variant_start> <sampling_method>? "^"? (<bound><separator>?)? <variants_list>? <variant_end>
```

### 範例 / Examples

| 寫法 | 輸出特性 |
| :--- | :--- |
| `{~3$$a\|b\|c\|d\|e}` | `'d,e,c'`、`'c,a,d'` —— 選取順序，每次不同 |
| `{~^3$$a\|b\|c\|d\|e}` | `'a,b,c'`、`'a,c,e'`、`'b,c,d'` —— 一律遞增 |
| `{!2$$a\|b\|c\|d}` | 12 筆，含 `a,b` 與 `b,a` 兩種排列 |
| `{!^2$$a\|b\|c\|d}` | 6 筆，僅 `a,b`、`a,c`、`a,d`、`b,c`、`b,d`、`c,d` |

分隔符 (Separator) 照常可用：

```
{!^2$$ and $$a|b|c}   →  "a and b", "a and c", "b and c"
```

### 對組合取樣的額外效果 / Extra Effect on Combinatorial Sampling

這是 `^` 相對其他排序方案的額外價值。

未加 `^` 時，`{!N$$...}` 窮舉的是**排列 (Permutation)**，因此 `a,b` 與 `b,a` 會各出現一次 —— 對提示詞而言兩者通常是冗餘的。

加上 `^` 後改為窮舉**組合 (Combination)**：

| 寫法 | 結果數 | 數學意義 |
| :--- | :--- | :--- |
| `{!2$$a\|b\|c\|d}` | 12 | P(4,2) = 4 × 3 |
| `{!^2$$a\|b\|c\|d}` | 6 | C(4,2) = 4 × 3 ÷ 2 |

因此 `^` 在組合取樣下會**同時縮減輸出總量**，不只是調整順序。

### 相容性 / Compatibility

| 情境 | 行為 |
| :--- | :--- |
| 未使用 `^` | **完全不變**，已由回歸測試守住 |
| 既有選項內含 `^`（如 `{a^b\|c}`） | 不受影響，`^` 仍為字面量 (Literal) |
| 既有選項**以 `^` 開頭**（如 `{^a\|b}`） | **語意改變** —— `^` 被讀為修飾符，選項變為 `a` |

最後一項是已評估的取捨。此類寫法在實際提示詞中極少見，且原本沒有其他語意，故風險評為低。

### 作用範圍 / Scope

`^` 加入 dynamicprompts 解析器，因此**自動同時**生效於：

- 主模板（非 Jinja 模式）
- YAML / JSON / `.txt` 的 Wildcard 值
- Wildcard 轉變體的路徑（例如 `{!^2$$__colours__}`）

**不**生效於 Jinja 模式（Jinja 只作用於模板層，不處理 Wildcard 值，詳見 [docs/SYNTAX_SYMBOLS.md](docs/SYNTAX_SYMBOLS.md#2-作用層級模型--layer-model)）。

### 與 `Wildcard` 搭配時的順序來源 / Order Source With Wildcards

`{~^2$$__a/b/c__}` 這類寫法完全可用，但有一個**容易誤解**之處：

> `^` 遵循的是 collection 的**儲存順序 (Stored Order)**，而非 YAML 鍵的書寫順序。

`WildcardManager` 在載入時預設會**排序**（`wildcard_manager.py:237`），因此「宣告順序」實際上是字母序：

| YAML 書寫順序 | 預設儲存順序 | `{~^2$$__a/b/c__}` 輸出 |
| :--- | :--- | :--- |
| `zebra`、`apple`、`mango` | `apple`、`mango`、`zebra` | `apple,mango`、`apple,zebra`、`mango,zebra` |

若要 `^` 真正遵循 YAML 書寫順序，需關閉排序：

```python
wm = WildcardManager(path=...)
wm.sort_wildcards = False
```

關閉後儲存順序回為 `zebra`、`apple`、`mango`，`^` 也隨之輸出 `zebra,apple`、`zebra,mango`、`apple,mango`。

#### 與 `shuffle_wildcards` 不相容 / Incompatible With Shuffling

> [!WARNING]
> `^` 與 `shuffle_wildcards=True` **不相容**，請勿同時使用。

原因：`_get_values()` 會排序並快取結果（`:206-240`），但 `get_values()` 在快取**之後**每次呼叫都重新洗牌（`:182-183`）。順序因此永不穩定，`^` 無法產生可預期的輸出。

實測確認 —— 同一個 collection 連續呼叫 15 次 `get_values()`：

| 設定 | 產生的不同順序數 |
| :--- | :--- |
| `shuffle_wildcards=False` | **1**（穩定） |
| `shuffle_wildcards=True` | **6**（3 個元素的全部排列） |

這是既有設計的行為，非 `^` 的缺陷；但在 `^` 加入前，此不穩定不會被注意到，因為原本沒有任何語法依賴順序。

### 實作位置 / Implementation

| 檔案 | 內容 |
| :--- | :--- |
| `src/dynamicprompts/parser/parse.py` | `^` 的語法定義與 `preserve_order` 欄位擷取 |
| `src/dynamicprompts/commands/variant_command.py` | `VariantCommand.preserve_order` 欄位；`get_value_combinations` 的組合模式 |
| `src/dynamicprompts/utils.py` | `choose_without_replacement` 依索引追蹤並還原宣告順序 |
| `src/dynamicprompts/samplers/` | Random / Combinatorial / Cyclical 三個取樣器，及 Wildcard→variant 路徑 |
