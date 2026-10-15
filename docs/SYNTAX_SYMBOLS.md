# 模板符號盤點與新語法衝突分析

> 本文盤點 `dynamicprompts` 模板語法目前使用的全部符號，並評估**還能新增哪些符號與語法**，而不會與既有語法、YAML 或 Jinja 衝突。
>
> 本文以**中文為主**；僅在譯名不唯一或易生歧義的技術術語處保留英文原詞，以便跨語言檢索與比對。所有程式碼引用皆以專案內原始碼為準，並附行號。

---

## 0. 術語約定：`Wildcard` / Terminology

> [!IMPORTANT]
> 本文件**一律保留 `Wildcard` 英文原詞**（首字大寫），不譯為「萬用字元」。

原因是本專案中同時存在兩種 wildcard 語意，以中文統稱會無法區分：

| 意義 | 本文寫法 | 說明 |
| :--- | :--- | :--- |
| **本專案的 Wildcard** | `Wildcard`（保留英文，首字大寫） | 具名的值集合，由 `__name__` 引用，儲存於 YAML / JSON / `.txt` 檔案 |
| **一般運算的萬用字元** | `` `*` ``（以符號標記） | globbing metacharacter，用於 Wildcard **名稱**的模式比對 |

`Wildcard` 名稱本身即支援 glob，因此兩者會在同一個 codebase 內並存。既有英文文件 `docs/SYNTAX.md:250` 則以小寫 `wildcard` 通稱兩者 —— 寫作「an asterisk `*` as a wildcard」，即以符號 `*` 指稱真正的萬用字元。

若將本專案的 `Wildcard` 譯為「萬用字元」，讀者無法判斷指的是具名值集合、還是 `*` 比對語意。依術語規則「譯名不唯一 → 僅保留英文」，此處採用僅英文並首字大寫，以便與程式碼識別字（`wildcard_manager.py`、`sort_wildcards` 等一律小寫）及英文原文的通稱用法區隔。

---

## 1. 範圍與方法 / Scope & Method

| 項目 | 內容 |
| :--- | :--- |
| 依據來源 | 僅專案內原始碼，不含外部文件或依賴套件之行為推測 |
| 權威檔案 | `src/dynamicprompts/parser/parse.py`、`src/dynamicprompts/parser/config.py`、`src/dynamicprompts/generators/jinjagenerator.py`、`src/dynamicprompts/samplers/utils.py` |
| YAML 行為 | 以專案已鎖定的 PyYAML 實測取得，非依記憶推斷（見第 5 節與附錄） |

---

## 2. 作用層級模型 / Layer Model

> [!IMPORTANT]
> **這是全文的前提。** 討論任何符號之前，必須先釐清「它在哪一層生效」。
> 既有文件分散於 `TEMPLATE_SYNTAX.md` 與 `YAML_SYNTAX.md`，但**從未說明 Jinja 的作用範圍**，因而產生「Jinja 語法能否寫進 YAML」的常見誤解。

### 2.1 三層求值模型 / Three Evaluation Layers

| 層級 | 內容 | 由誰解析 | Jinja 是否作用 |
| :--- | :--- | :--- | :--- |
| **模板層** (Template Layer) | 傳入 generator 的主字串 | **二選一**：dynamicprompts 解析器，或 Jinja2 | **僅** Jinja 模式 |
| **路徑層** (Path Layer) | `__...__` 之間的 Wildcard 路徑 | 僅 dynamicprompts Wildcard 路徑解析器 | **絕不** |
| **值層** (Value Layer) | YAML / JSON / `.txt` 的 Wildcard 值 | 僅 dynamicprompts 解析器 | **絕不** |

### 2.2 核心事實：Jinja 與 YAML 無交集 / Jinja Never Touches YAML

**YAML 內容一律由 dynamicprompts 解析器處理，與所選 generator 無關。**

| 位置 | 原始碼 | 說明 |
| :--- | :--- | :--- |
| 模板層 | `jinjagenerator.py:84` | `env.from_string(template)` —— `template` 是**函式參數**，不是 YAML 內容 |
| 值層 | `samplers/utils.py:35` | `VariantOption(parse(v, parser_config=...))` —— `v` 是 YAML 值，**一律**經 dynamicprompts 解析器 |
| Jinja 模式下 | `jinja_extensions.py:41-51` | `wildcard()` 呼叫 `CombinatorialPromptGenerator.generate()`，回傳 `[str(r) ...]` 為**資料**；Jinja 不會重新解析函式回傳值 |

> **依賴是單向的**：Jinja 模板可以「呼叫」 Wildcard 取得資料，但 Wildcard 值**永遠不會流入 Jinja**。

### 2.3 實務結論 / Practical Consequences

| 情境 | 結果 |
| :--- | :--- |
| 在 YAML 值中寫 `{{ x }}`、`{% if %}` | ❌ **不會被 Jinja 求值**，會被 dynamicprompts 解析器當作字面量 (Literal) 輸出（`{` 另會觸發變體解析而報錯） |
| 在 YAML 值中寫 `{a\|b}`、`${x=1}`、`__wc__` | ✅ 正常運作，由 dynamicprompts 解析器求值 |
| 在 `JinjaGenerator` 的模板中寫 `{a\|b}` | ❌ **不會**被 dynamicprompts 求值（該路徑不經過 `parse()`） |
| 在 `JinjaGenerator` 的模板中呼叫 `wildcard('name')` | ✅ 回傳該 collection 的**已求值**結果 |

換言之，兩套模板語法**互斥**，且僅在模板層競爭；值層與路徑層永遠只有 dynamicprompts 一套。

---

## 3. 現有符號盤點 / Existing Symbol Inventory

> 下表「作用層級」欄位採第 2 節定義。**所有 dynamicprompts 符號同時適用於模板層與值層**，因為兩者共用同一個解析器。

### 3.1 可配置分隔符 / Configurable Delimiters

定義於 `parser/config.py:6-14`，為 `frozen=True` 的 `dataclass`。

> **注意**：該類別必須維持不可變，因為 `get_cached_parser` 將它當作 `WeakKeyDictionary` 的鍵（`parse.py:554`）。

| 欄位 | 預設值 | 用途 | 作用層級 |
| :--- | :--- | :--- | :--- |
| `variant_start` / `variant_end` | `{` / `}` | 變體 (Variant) | 模板＋值層 |
| `wildcard_wrap` | `__` | `Wildcard` 包裹 | 模板＋值層 |
| `variable_start` / `variable_end` | `${` / `}` | 變數指派與存取 | 模板＋值層＋路徑層 |
| `wrap_start` / `wrap_end` | `%{` / `}` | 包裹指令 (Wrap Command)，內部分隔符為 `$$` | 模板＋值層 |

### 3.2 文法硬編碼符號 / Hard-coded Grammar Symbols

這些符號**無法**透過 `ParserConfig` 調整。

| 符號 | 定義位置 | 用途 | 作用層級 |
| :--- | :--- | :--- | :--- |
| `\|` | `parse.py:206` | 變體選項分隔 | 模板＋值層 |
| `::` | `parse.py:187` | 權重分隔 (Weight Delimiter) | 模板＋值層 |
| `$$` | `parse.py:68` | 界限式 (Bound Expression) 與包裹分隔 | 模板＋值層 |
| `-` | `parse.py:82` | 範圍界限，如 `1-5` | 模板＋值層 |
| `~` | `parse.py:63` | 隨機取樣 (Random Sampler) | 模板＋值層 |
| `!` | `parse.py:64`、`:249` | 組合取樣 (Combinatorial)；以及 `=!` 立即求值 | 模板＋值層 |
| `@` | `parse.py:65` | 循環取樣 (Cyclical Sampler) | 模板＋值層 |
| `:` | `parse.py:231` | 變數預設值分隔 | 模板＋值層＋路徑層 |
| `=` | `parse.py:248`、`:343` | 變數指派；`key=value` 配對 | 模板＋值層＋路徑層 |
| `?` | `parse.py:247` | 保留既有變數值 | 模板＋值層＋路徑層 |
| `(` `)` | `parse.py:118,120`、`:527` | Wildcard 的變數規格 (Variable Spec) | 模板＋值層 |
| `,` | `parse.py:336` | 變數規格的配對分隔 | 模板＋值層 |
| `0-9`、`.` | `parse.py:57-60` | 數值與權重 | 模板＋值層 |

> **關於 `...`**：省略號**並非**解析器符號。包裹指令的分隔符是 `$$`（`parse.py:68` `variant_delim`）；`...` 僅是包裹指令左側的**內容標記**，由 `WrapCommand` 於執行期置換。設計新語法時不應將 `...` 視為已佔用符號，也不建議取用它（易與使用者常見的省略號文字混淆）。

> **關於 `*`**：`*` **不是**解析器符號，而是 Wildcard **名稱**內的 globbing metacharacter —— 由 `tree/tree.py:46` 以 `fnmatch` 比對（路徑層），**不經** `parse.py` 處理。這是第 0 節「兩種 wildcard 語意」的技術來源：同一 codebase 內， `` `*` `` 指真正的萬用字元，而 `Wildcard` 指具名值集合。
>
> 設計新語法時需注意： Wildcard 路徑的字元集為 `[^(${}#]`（`parse.py:140`），**允許 `*`**。因此若新增與 `*` 相關的語法，將直接干擾既有 glob 解析。

### 3.3 註解 / Comments

定義於 `parse.py:530-532`，以 `ignore()` 實作，作用層級為**模板＋值層**：

| 樣式 | 形式 |
| :--- | :--- |
| Python 風格 | `#` 行註解 |
| C++ 風格 | `//` 行註解 |
| C 風格 | `/* ... */` 區塊註解 (C-style Comment) |

> **兩套 `#` 容易混淆**：模板層的 `#` 由本解析器處理；YAML 檔的 `#` 則在載入階段就被 PyYAML 消化，兩者時機與作用範圍完全不同。詳見 `YAML_SYNTAX.md#comments`。
>
> **推論**：因 `//` 為行註解， Wildcard 路徑不可開頭為 `//`；任何新語法若採 `//` 系開頭將與註解衝突。

### 3.4 Jinja 模式：僅限模板層的另一分支 / Jinja Mode Is Template-layer Only

> [!WARNING]
> **此節所有符號僅存在於模板層，且僅在使用 `JinjaGenerator` 時生效。**
> **它們完全不適用於 YAML、JSON 或 `.txt` Wildcard 值**（見第 2.2 節）。

`JinjaGenerator._build_jinja_template`（`jinjagenerator.py:61-88`）**不經過** dynamicprompts 解析器，於 `:84` 直接呼叫 `env.from_string(template)`。

| Jinja2 分隔符 | 用途 | 作用層級 |
| :--- | :--- | :--- |
| `{{ ... }}` | 表達式 (Expression) | 僅模板層（Jinja 模式） |
| `{% ... %}` | 陳述 (Statement) | 僅模板層（Jinja 模式） |
| `{# ... #}` | 註解 | 僅模板層（Jinja 模式） |

此外 `jinja_extensions.py:98-107` 注入了全域函式，同樣**僅模板層**可用：

`choice`、`weighted_choice`、`random`、`randint`、`permutations`、`wildcard`、`random_sample`、`all_combinations`，以及自訂區塊標籤 (Block Tag) `{% prompt %}...{% endprompt %}`（`PromptExtension`）。

> **設計意涵**：任何以 `{` 開頭的新語法，會同時與變體（軸①）、Jinja（軸④）、YAML 純量（軸③）三重衝突，無討論空間。

### 3.5 字面量禁入字元 / Characters Banned in Literals

`_configure_literal_sequence`（`parse.py:146-183`）依上下文動態組出字面量 (Literal) 不可含有的字元：

| 上下文 | 禁入字元 | 原因（原始碼註解） |
| :--- | :--- | :--- |
| 頂層 literal | `#`、`{`、`${`、`%{` | 註解與各構造的開頭 |
| 變體 literal（`:167`） | 追加 `\|`、`$`、`}` | 選項分隔、界限式終止、變體結束 |
| Wildcard literal（`:173`） | 追加 `(`、`)` | 變數規格的起訖 |

另有兩處獨立限制：

- Wildcard 路徑（`:140`）：`[^(${}#]`，且需避開 `wildcard_wrap`
- 界限式分隔（`:89`）：`exclude_chars="${}"`

> **設計意涵**：加入禁入清單代表「畸形構造**直接報錯**」（嚴格模式）；不加入則代表「降級 (Fallback) 為字面量」（向後相容 (Backward Compatibility)）。兩者不可兼得，詳見第 7 節。

---

## 4. 衝突判斷的四個層面 / Four Axes of Conflict

判斷新符號是否「不衝突」，實際上有四個**彼此獨立**的軸：

| 軸 | 判斷問題 | 判斷方法 |
| :--- | :--- | :--- |
| ① 文法內部 (Grammar-internal) | 是否與既有 token 開頭撞車？ | 比對第 3.2 節 |
| ② 向後相容 (Backward Compatibility) | 既有 prompt 中當作**字面文字**使用的字元，會否被重新解釋？ | 該字元目前是否允許出現在 literal 中（第 3.5 節） |
| ③ YAML 純量安全 (Plain Scalar Safety) | 值的**開頭**能否不加引號？ | 第 5 節實測 |
| ④ Jinja 模式 (Jinja Mode) | `--jinja` 模式下是否撞 Jinja2？ | 是否以 `{` 開頭 |

> **②是最容易被忽略的一軸。** `^`、`;`、`<`、`>`、`+` 目前**都允許**出現在 literal 中（皆不在第 3.5 節清單內），因此一旦取用為開頭符號，`1<2`、`red+blue`、`a^b^c` 這類既有文字的語意就會改變。

> **④的影響範圍**：僅模板層。由於 Jinja 不作用於 YAML（第 2.2 節），軸④對「能否寫進 YAML」毫無影響 —— 這是分層之後才看得清的重點。

---

## 5. YAML 純量安全實測 / Plain Scalar Safety Test

以專案已鎖定的 PyYAML，測試「值以該符號開頭且未加引號」的結果：

| 結果 | 符號 |
| :--- | :--- |
| ✅ 可作純量 (Plain Scalar) 開頭 | `$`、`${`、`__`、`(`、`~`、`<`、`^`、`;`、`+`、`=`、`:`、`?`、`-`、`.`、`/`、`\`、`<<`、`++`、`^^` |
| ❌ 解析錯誤 | `%{`（ScannerError）、`{`（ParserError）、`!`（標籤 Tag）、`*`（別名 Alias）、`[`、`]`、`` ` ``、`>`、`>>`、`\|`、`@`、`&&`、`\|\|` |
| ⚠️ **靜默產生錯誤值** | `#` → 值變 `None`（整段被當註解）、`&` → 值變 `None`（被當錨 Anchor） |

### 5.1 對既有語法的印證 / Confirmation on Existing Syntax

| 既有開頭 | 實測結果 | 文件要求 |
| :--- | :--- | :--- |
| `${a}` | ✅ 不需引號 | 與現況一致 |
| `__a__` | ✅ 不需引號 | 與現況一致 |
| `{a\|b}` | ❌ ParserError | 必須加引號 |
| `%{x$$y}` | ❌ ScannerError | 必須加引號 |

這正是既有文件要求變體與包裹指令加引號的**根本原因**：`{` 是流式映射 (Flow Mapping) 起始，`%` 是指令 (Directive) 指示符 (Indicator)。

### 5.2 值內的間接干擾 / Interference Inside a Value

| 寫法 | 實測結果 |
| :--- | :--- |
| `key: a # b` | 被截斷為 `'a'`（`空格 + #` 觸發註解） |
| `key: a# b` | 完整保留 `'a# b'` |
| `key: a: b` | ScannerError（`冒號 + 空格`） |
| `key: a:- b` | 完整保留 `'a:- b'` |

> **陷阱**：`#` 與 `&` 雖回傳 `OK` 卻產生 `None`，**不拋錯**。除錯成本極高，屬最應避免的開頭符號。

---

## 6. 可用符號評級 / Availability Rating

同時通過軸①與軸③，並評估軸②風險後的結果：

| 符號 | 文法占用 | YAML 開頭 | 既有 prompt 出現頻率 | 評級 |
| :--- | :--- | :--- | :--- | :--- |
| `^` | 未使用 | ✅ | 極低 | **★★★ 最佳** |
| `;` | 未使用 | ✅ | 低 | **★★★ 最佳** |
| `<<` | 未使用 | ✅ | 極低 | **★★★ 最佳（多字元）** |
| `++` | 未使用 | ✅ | 極低 | ★★★ 佳 |
| `^^` | 未使用 | ✅ | 極低 | ★★★ 佳 |
| `<` | 未使用 | ✅ | 低（比較式偶見） | ★★★ 佳（建議只作開頭） |
| `>` | 未使用 | ❌ | 低 | ✗ 必須引號，且慣用於閉合 |
| `>>` | 未使用 | ❌ | 極低 | ✗ 同上 |
| `+` | 未使用 | ✅ | **高**（`red+blue`、`5+2`） | ★★ 保守備案 |
| `.` | 僅數字相鄰 | ✅ | **極高** | ✗ 無法與小數、句點區隔 |
| `&` `#` | — | ⚠️ 靜默錯誤 | — | ✗ 靜默產生 `None` |
| `\|` `>` `@` `` ` `` `[` `]` `!` `*` `%` | 已占用或 YAML 限制 | ❌ | — | ✗ |
| `$` `=` `~` `?` `:` `-` `,` `_` `/` `{` `}` `(` `)` | 已占用 | — | — | ✗ |

### 6.1 明確避免的三個陷阱 / Three Pitfalls to Avoid

1. **`&` 與 `#`** — YAML 實測**靜默**變 `None`，不拋錯，除錯極度困難。
2. **任何 `{` 開頭** — 軸①（變體已占用）、軸③（YAML ParserError）、軸④（Jinja `{{`/`{%`/`{#`）三重撞車，無討論空間。
3. **`.`** — 與小數（`parse.py:57-60`）、句點、省略號完全無法區隔，不具備分隔符 (Delimiter) 資格。

### 6.2 新語法建議 / Recommendations

| 目標功能類型 | 建議符號 | 理由 |
| :--- | :--- | :--- |
| 條件、過濾、轉換 | `<...>` | 最符合既有使用者的直覺，軸③安全 |
| 區塊、多行構造 | `<<...>>` | 撞車機率最低；`<<` 在 YAML 僅於**鍵位置**為 merge key，值位置無礙（已實測） |
| 修飾子、語法擴充 | `^...^` | 軸①②③④全數通過，風險最低 |
| 緊急備案 | `++...++` | `+` 的風險僅來自軸②，配對後仍可接受 |

---

## 7. 新增語法實作要點 / Implementation Notes

1. **加入 `ParserConfig`**：沿用 `variant_start` 等欄位的模式，使新分隔符可配置。務必維持 `frozen=True`，否則 `get_cached_parser` 的快取鍵會失效。

2. **`chunk` 選單插入位置**（`parse.py:507-514`）：必須置於 `literal_sequence` **之前**。
   pyparsing 的 `|` 為 `MatchFirst`，依序嘗試各分支。因此只要新規則**要求完整配對的閉合符號**，不完整的 `^abc` 會失敗並交棒給 literal —— 這是向後相容的關鍵保護機制。

3. **`non_literal_chars`（`parse.py:156-160`）的取捨**：

   | 做法 | 行為 | 適用情境 |
   | :--- | :--- | :--- |
   | **不加入** | 未配對的開頭降級 (Fallback) 為字面量 | **建議初期採用**，向後相容 |
   | **加入** | 畸形構造直接報錯 | 嚴格模式，與既有 `#`／`{`／`${`／`%{` 一致 |

   兩者不可兼得，屬刻意的設計選擇，建議在文件中明確揭露。

4. **層級宣告**：新語法一旦加入 dynamicprompts 解析器，即**自動同時**生效於模板層與值層（兩者共用解析器），並自動**不**作用於 Jinja 模式。這是分層模型帶來的可預期性 —— 不需額外實作即可推得。

5. **Wildcard 路徑**：若新符號可能出現於路徑中，需一併處理 `parse.py:140` 的 `wildcard_path_literal_re`，以及 `:89` 界限式分隔的 `exclude_chars`。

6. **YAML 層建議**：開頭符號選 `^`、`;`、`<`、`<<`、`++`、`^^` 之一，可讓新語法**不加引號**即生效，相較既有的 `{` 與 `%{` 更為好用。長模板仍建議使用區塊標量 (Block Scalar) `>-`。

7. **避免 `...`**：省略號並非解析器符號（見第 3.2 節註記），取用它會與使用者常見的省略號文字混淆。

---

## 附錄 A：YAML 符號實測腳本 / Appendix A: Test Script

以下腳本可用於重現第 5 節結果：

```python
import yaml

candidates = [
    "${", "__", "%{", "{", "(", "~", "!", "@",
    "|", ">", "<", "^", ";", "+", "=", "#", ":",
    "-", "?", "&", "*", "[", "]", "`", "\\", "/",
    ".", "$", "<<", "++", "^^", ">>", "&&", "||",
]

for tok in candidates:
    try:
        val = yaml.safe_load(f"key: {tok}REST")["key"]
        print(f"{tok!r:<8} OK   {val!r}")
    except Exception as e:
        print(f"{tok!r:<8} {type(e).__name__}")

for doc, label in [
    ("key: a # b", "space-hash (comment)"),
    ("key: a# b", "no-space-hash"),
    ("key: a: b", "colon-space"),
    ("key: a:- b", "dash-space mid"),
]:
    try:
        print(f"{label:<20} -> {yaml.safe_load(doc)!r}")
    except Exception as e:
        print(f"{label:<20} -> {type(e).__name__}")
```

---

## 附錄 B：層級判斷速查 / Appendix B: Layer Quick Reference

懷疑某語法能否用在某處時，依此表判斷：

| 你想寫的位置 | 該處由誰解析 | 可用語法 |
| :--- | :--- | :--- |
| 主 prompt（非 Jinja 模式） | dynamicprompts 解析器 | 變體、Wildcard、變數、包裹指令、模板註解 |
| 主 prompt（Jinja 模式） | Jinja2 | `{{ }}`、`{% %}`、`{# #}`、全域函式、`{% prompt %}` |
| YAML / JSON 的值 | dynamicprompts 解析器 | 同「主 prompt（非 Jinja 模式）」，**無 Jinja** |
| `.txt` 的值（每行一項） | dynamicprompts 解析器 | 同上，**無 Jinja**，且不可含換行 |
| `__...__` 內的路徑 | Wildcard 路徑解析器 | 變體、變數、Wildcard；不可含 `(`、`)`、`#`、`{`、`}`、`$` |
| YAML 鍵名 | 不解析 | 僅作為路徑字串，正規化 `/` |
