# STL 工具功能特征总览

> **文档类型：** 面向人类的功能说明
> **适用版本：** stl_parser v1.7.0
> **更新日期：** 2026-02-16

---

## 一、STL 是什么

STL（Semantic Tension Language，语义张力语言）是一种结构化知识表达语言。它用一种简洁、人类可读且机器可执行的语法，将知识表达为"从哪里指向哪里，并附带元数据"的方向性语义关系。

一条典型的 STL 语句长这样：

```
[理论_相对论] -> [预测_时间膨胀] ::mod(confidence=0.99, rule="logical", author="Einstein")
```

它的含义是：「相对论 → 时间膨胀预测」，置信度 0.99，推理规则为逻辑推导，作者是 Einstein。

`stl_parser` 是 STL 的 Python 工具包，提供了从解析到生成、从验证到分析的完整工具链。

---

## 二、核心功能

### 1. 文本解析（Parser）

**做什么：** 将 STL 文本转换为结构化的 Python 对象。

**能力：**
- 解析单条或多条 STL 语句
- 支持全 Unicode（中文、阿拉伯文等完全兼容）
- 自动处理多行语句（跨行的修饰符块自动合并）
- 从混合文本中智能提取 STL 内容（支持 Markdown 代码块、混杂的散文等）
- 解析文件或字符串
- 错误恢复能力——遇到无效行也能继续解析，不会整体崩溃

**使用场景：**
- 读取 `.stl` 文件并获取其中的所有语义关系
- 从 AI 生成的混合文本中提取 STL 数据
- 在 Python 程序中直接操作 STL 数据结构

```python
from stl_parser import parse, parse_file

# 解析字符串
result = parse('[知识] -> [理解] ::mod(confidence=0.85, rule="causal")')
print(result.statements[0].source.name)  # "知识"
print(result.statements[0].modifiers.confidence)  # 0.85

# 解析文件
result = parse_file("knowledge_base.stl")
print(f"共 {len(result.statements)} 条语句，有效性：{result.is_valid}")
```

---

### 2. 语法与语义验证（Validator）

**做什么：** 检查 STL 语句的正确性，既检查语法结构，也检查语义一致性。

**能力：**
- **语法验证**——锚点名称格式、箭头是否存在、修饰符是否有 `::` 前缀
- **类型验证**——数值范围（confidence 必须在 0.0–1.0 之间）、枚举值是否合法
- **语义一致性**——检测矛盾的修饰符（如同时标记 `time="Past"` 和 `tense="Future"`）
- **溯源完整性**——高置信度语句是否附带了 source、author 等溯源信息
- **清晰的错误报告**——每个错误附带错误码、行号、修复建议

**使用场景：**
- CI/CD 流水线中自动校验 STL 文件
- 在写入知识库前确保数据质量
- 发现语义层面的逻辑矛盾

```python
from stl_parser import parse, validate_parse_result

result = parse('[A] -> [B] ::mod(confidence=1.5)')  # 范围超限
validated = validate_parse_result(result)
for error in validated.errors:
    print(f"[{error.code}] {error.message}")
    # → [E104] Range violation: confidence=1.5 is outside [0.0, 1.0]
```

---

### 3. 多格式序列化（Serializer）

**做什么：** 将解析结果在多种数据格式间双向转换。

**支持的格式：**

| 格式 | 方向 | 用途 |
|------|------|------|
| **JSON** | 双向 | 通用数据交换，API 传输，数据库存储 |
| **Python Dict** | 双向 | 程序内部使用 |
| **RDF/Turtle** | 导出 | 语义网、知识图谱、链接数据 |
| **RDF/XML** | 导出 | W3C 标准交换格式 |
| **N-Triples** | 导出 | 大规模 RDF 批量处理 |
| **JSON-LD** | 导出 | 语义化的 JSON，搜索引擎友好 |
| **STL 文本** | 导出 | 还原为人类可读的 STL 格式 |

**使用场景：**
- 将知识图谱导出为 RDF 格式供 SPARQL 查询
- 以 JSON 格式存入数据库或通过 API 传输
- 从 JSON 反序列化回 STL 对象继续处理

```python
from stl_parser import parse, to_json
from stl_parser.serializer import to_rdf

result = parse('[知识] -> [应用] ::mod(rule="causal", confidence=0.9)')

# 导出为 JSON
json_str = to_json(result, indent=2)

# 导出为 RDF Turtle
rdf_str = to_rdf(result, format="turtle")
```

---

### 4. 知识图谱构建（Graph）

**做什么：** 将 STL 文档自动转换为有向多重图（directed multigraph），进行图论分析。

**能力：**
- 自动从语句构建 NetworkX 有向图（节点=锚点，边=关系）
- **路径发现**——查找两个概念之间的所有连接路径
- **环路检测**——发现推理中的循环引用（如 A→B→C→A 的反馈回路）
- **中心性分析**——找到知识网络中最关键的节点
- **语义冲突检测**——发现同一源节点对同一关系有矛盾目标的情况
- **张力度量**——量化知识网络中的语义冲突总量
- **子图提取**——按领域（domain）筛选出特定知识子网络

**使用场景：**
- 分析知识体系的结构——哪些概念是枢纽？
- 检测推理链中的循环依赖
- 发现知识库中的语义矛盾
- 按学科领域切分知识图谱

```python
from stl_parser import parse, STLGraph

result = parse("""
[问题_意识] -> [理论_整合信息]
[理论_整合信息] -> [实验_神经关联]
[实验_神经关联] -> [观测_Phi值]
[观测_Phi值] -> [问题_意识]
""")

graph = STLGraph(result)
print(f"节点数: {graph.summary['nodes']}")       # 4
print(f"边数: {graph.summary['edges']}")           # 4
print(f"环路: {graph.find_cycles()}")               # 发现 1 个循环
print(f"中心性: {graph.get_node_centrality()}")     # 每个节点的中心度
```

---

### 5. 统计分析（Analyzer）

**做什么：** 对 STL 文档进行全面的统计报告。

**分析维度：**
- **元素计数**——语句总数、唯一锚点数、去重语句数
- **锚点类型分布**——Concept/Entity/Event/Agent 等 9 种类型各有多少
- **路径类型分布**——因果、逻辑、语义、认知等路径的比例
- **修饰符使用统计**——哪些修饰符最常用？数值型修饰符的最小/最大/均值
- **置信度分析**——confidence 和 certainty 值的分布情况
- **溯源缺失识别**——找出高置信度但缺少 source/author/timestamp 的语句

**使用场景：**
- 评估知识库的质量——溯源覆盖率、置信度分布是否合理
- 了解知识体系的结构特征——以哪种类型的关系为主？
- 数据质量审计

```python
from stl_parser import parse, STLAnalyzer

result = parse_file("research_notes.stl")
analyzer = STLAnalyzer(result)
report = analyzer.get_full_analysis_report()

print(f"语句总数: {report['counts']['total_statements']}")
print(f"置信度均值: {report['confidence_metrics']['confidence']['mean']:.2f}")
print(f"缺少溯源的高置信语句: {len(report['missing_provenance_high_confidence'])} 条")
```

---

### 6. 命令行工具（CLI）

**做什么：** 在终端直接使用 STL 工具，无需编写代码。

**可用命令：**

| 命令 | 功能 |
|------|------|
| `stl validate input.stl` | 验证文件语法和语义正确性 |
| `stl convert input.stl --to json` | 转换为 JSON 格式 |
| `stl convert input.stl --to turtle` | 转换为 RDF/Turtle 格式 |
| `stl convert input.stl --to json-ld` | 转换为 JSON-LD 格式 |
| `stl convert input.stl --to json -o out.json` | 转换并写入文件 |
| `stl analyze input.stl` | 图分析——节点/边数、环路、冲突、中心性排名 |
| `stl build "[A]" "[B]" --mod "confidence=0.9"` | 从命令行参数构建 STL 语句 |
| `stl clean llm_output.txt --show-repairs` | 清洗和修复 LLM 输出文件 |
| `stl schema-validate input.stl --schema events.stl.schema` | 校验文件是否符合 Schema |
| `stl query input.stl --where "confidence__gt=0.8"` | 按条件查询和过滤 |
| `stl query input.stl --select "source,confidence" -f json` | 投影字段并输出为 JSON |
| `stl query input.stl --pointer "/0/source/name"` | 按指针路径精确寻址 |
| `stl query input.stl --where "rule=causal" --count` | 计数匹配语句 |
| `stl diff a.stl b.stl` | 比较两份文档的语义差异 |
| `stl diff a.stl b.stl -f json` | 以 JSON 格式输出差异 |
| `stl diff a.stl b.stl --summary` | 仅显示差异统计摘要 |
| `stl diff a.stl b.stl --quiet` | 静默模式（仅返回退出码：0=相同，1=不同） |
| `stl patch input.stl diff.json` | 将 JSON 差异补丁应用到文档 |
| `stl patch input.stl diff.json -o out.stl` | 应用补丁并写入文件 |

输出使用 Rich 库渲染，在终端中有彩色高亮和表格格式。查询命令支持 4 种输出格式：`table`（默认）、`json`、`csv`、`stl`。差异比较命令支持 `text`（默认）和 `json` 两种输出格式。

---

## 三、扩展工具（Priority 1 Tooling）

### 7. 程序化构建器（Builder）

**做什么：** 用 Python 代码直接构造 STL 语句，无需拼接文本字符串。

**为什么需要它：**
在程序中动态生成 STL 时，手动拼字符串既容易出错又难以维护。Builder 提供了类型安全的流式 API——写错了会在构建时立即报错，而不是等到解析时才发现。

**能力：**
- **流式 API**——`stl().mod().mod().build()` 链式调用
- **自动字段分类**——标准修饰符字段（如 confidence）和自定义字段自动分离
- **构建时验证**——默认对生成的语句进行验证，可通过 `.no_validate()` 关闭
- **锚点解析**——支持 `"[Ns:Name]"`、`"Name"`、`"[Name]"` 等多种输入格式
- **批量文档**——`stl_doc()` 一次构建多条语句组成的文档

**使用场景：**
- 后端服务根据业务逻辑动态生成知识表示
- 将数据库查询结果转化为 STL 格式
- 测试和原型开发

```python
from stl_parser import stl, stl_doc

# 构建单条语句
stmt = stl("[症状_发热]", "[诊断_感染]").mod(
    confidence=0.85,
    rule="causal",
    strength=0.80,
    domain="medicine"
).build()

# 构建文档（多条语句）
doc = stl_doc(
    stl("[A]", "[B]").mod(confidence=0.9, rule="causal"),
    stl("[B]", "[C]").mod(confidence=0.85, rule="logical"),
    stl("[C]", "[D]").mod(confidence=0.80),
)
print(f"共 {len(doc.statements)} 条语句")
```

---

### 8. 模式验证（Schema）

**做什么：** 定义"一份合格的 STL 文档应该长什么样"，然后自动校验文档是否符合要求。

**为什么需要它：**
不同领域对 STL 的使用规范不同。医学领域可能要求每条语句必须有 `confidence` 和 `source`；事件日志可能要求锚点名必须以 `Event_` 开头。Schema 让这些规则可以声明式定义，并自动执行。

**Schema 可定义的约束：**
- **必填修饰符**——哪些字段必须存在（如 `required: [confidence, rule]`）
- **字段类型与范围**——`confidence: float(0.5, 1.0)` 限制取值范围
- **枚举约束**——`rule: enum("causal", "empirical", "logical")` 限制可选值
- **锚点命名模式**——`pattern: /^Event_/` 要求锚点名以特定前缀开头
- **命名空间要求**——`namespace "Events"` 强制使用特定命名空间
- **文档级约束**——最少/最多语句数、是否允许循环引用

**额外能力：**
- **动态 Pydantic 模型生成**——从 Schema 自动生成对应的 Pydantic 模型类
- **双向转换**——Pydantic 模型 ↔ STL Schema 互相转换

**Schema 文件格式示例：**
```
schema MedicalRecords v1.0 {
  namespace "Med"

  anchor source {
    pattern: /^Symptom_|^Drug_|^Diagnosis_/
  }

  modifier {
    required: [confidence, rule, source]
    confidence: float(0.5, 1.0)
    rule: enum("causal", "empirical", "definitional")
  }

  constraints {
    min_statements: 1
  }
}
```

```python
from stl_parser import load_schema, validate_against_schema, parse

schema = load_schema("""
schema EventLog v1.0 {
  modifier {
    required: [confidence, rule]
    confidence: float(0.5, 1.0)
    rule: enum("causal", "empirical", "logical")
  }
}
""")

result = parse('[A] -> [B] ::mod(confidence=0.9, rule="causal")')
validation = validate_against_schema(result, schema)
print(f"是否合规: {validation.is_valid}")   # True
print(f"错误数: {len(validation.errors)}")  # 0
```

---

### 9. LLM 输出清洗与修复（LLM Pipeline）

**做什么：** 自动清理和修复大语言模型（LLM）生成的 STL 输出中的常见错误。

**为什么需要它：**
LLM 生成的 STL 几乎不可能一次完美。它们会忘记方括号、用错箭头符号、不加引号、数值超范围、拼错修饰符名……LLM Pipeline 通过三阶段处理自动修复这些问题，使 LLM 生成的文本变成合法的 STL。

**三阶段处理流程：**

| 阶段 | 功能 | 修复的问题类型 |
|------|------|----------------|
| **Clean（清洗）** | 去噪 | 去除 Markdown 代码块、过滤散文和注释、合并跨行语句、规范化箭头符号（`=>`, `➔`, `—>` 等 10+ 种变体统一为 `->`）、修复多余空白 |
| **Repair（修复）** | 纠错 | 补全缺失的方括号、添加 `::mod(` 前缀、给字符串值加引号、将超范围数值钳位到合法区间、修正 15 种常见拼写错误（如 `confience` → `confidence`） |
| **Parse（解析）** | 校验 | 标准解析 + 可选 Schema 验证 |

**完整审计追踪：** 每一步修复都被记录为 `RepairAction`，包含修复类型、原始文本、修复后文本和描述。

**辅助功能：**
- `prompt_template(schema)` — 生成教 LLM 正确使用 STL 的提示词模板

**使用场景：**
- LLM Agent 的输出后处理管线
- 将 ChatGPT/Claude 的非结构化输出转化为合法 STL
- 自动化的 LLM 输出质量保证

```python
from stl_parser import validate_llm_output

# 一段典型的 LLM "脏输出"
raw = """
Here is the STL analysis:
```stl
A => B mod(confience=1.5, rule=causal)
C —> D ::mod(strenth=0.8)
```
"""

result = validate_llm_output(raw)
print(f"有效: {result.is_valid}")
print(f"修复操作: {len(result.repairs)} 次")
for r in result.repairs:
    print(f"  [{r.type}] {r.description}")
    # [strip_fence] Extracted content from ```stl code fence
    # [normalize_arrow] Replaced '=>' with '->'
    # [add_brackets] Added brackets: A → [A]
    # [fix_mod_prefix] Added :: prefix to mod(...)
    # [fix_typo] Fixed modifier key: confience → confidence
    # [clamp_value] Clamped confidence from 1.5 to 1.0
    # [quote_string] Quoted unquoted string value: rule=causal → rule="causal"
    # [normalize_arrow] Replaced '—>' with '->'
    # [fix_typo] Fixed modifier key: strenth → strength
```

---

### 10. 结构化事件发射器（Emitter）

**做什么：** 将程序运行时的事件以 STL 格式写入日志文件或流。

**为什么需要它：**
当系统运行时会产生大量事件（状态变更、决策过程、因果触发等），Emitter 用标准的 STL 格式记录这些事件。这意味着事件日志本身就是一份可解析、可查询、可分析的知识图谱。

**能力：**
- **文件输出**——追加写入 `.stl` 文件
- **流输出**——写入标准输出、StringIO 等任意流对象
- **双重输出**——同时写入文件和流
- **自动时间戳**——每条记录自动注入 ISO 8601 时间戳
- **命名空间前缀**——自动为锚点添加统一的命名空间前缀
- **线程安全**——内置互斥锁，多线程并发写入不会混乱
- **上下文管理器**——`with` 语句自动管理文件生命周期
- **可验证输出**——可开启 `auto_validate` 在写入前自动校验

**输出格式保证：** 生成的 `.stl` 文件可以直接被 `parse_file()` 解析，形成完整的工具链闭环。

**使用场景：**
- AI Agent 决策过程的结构化日志
- 系统状态变迁的因果关系记录
- 事件溯源（Event Sourcing）
- 实时监控系统的知识图谱构建

```python
from stl_parser import STLEmitter

# 记录一段 AI Agent 的决策过程
with STLEmitter(log_path="agent_decisions.stl", namespace="Agent") as emitter:
    emitter.emit("[Observe_Input]",   "[Classify_Intent]",  confidence=0.92, rule="causal")
    emitter.emit("[Classify_Intent]", "[Select_Action]",    confidence=0.88, rule="logical")
    emitter.emit("[Select_Action]",   "[Execute_Response]", confidence=0.95, rule="causal")
    emitter.emit("[Execute_Response]","[Verify_Outcome]",   confidence=0.90, rule="empirical")

# 生成的 agent_decisions.stl 内容（每行自动附带时间戳）：
# [Agent:Observe_Input] -> [Agent:Classify_Intent] ::mod(confidence=0.92, rule="causal", timestamp="2026-02-11T10:30:00Z")
# [Agent:Classify_Intent] -> [Agent:Select_Action] ::mod(confidence=0.88, rule="logical", timestamp="2026-02-11T10:30:00Z")
# ...

# 之后可以直接分析这份日志
from stl_parser import parse_file, STLGraph
result = parse_file("agent_decisions.stl")
graph = STLGraph(result)
print(f"决策链长度: {graph.summary['edges']} 步")
```

---

### 11. 置信度衰减（Confidence Decay）

**做什么：** 基于语句的时间戳，在查询时计算有效置信度——越旧的语句，置信度越低。

**为什么需要它：**
知识会随时间变得过时。一年前置信度 0.95 的声明，今天可能不再可靠。Decay 模块通过指数半衰期模型，在读取时（而非写入时）动态计算有效置信度，保持原始数据不变。

**核心公式：** `effective = confidence × 0.5^(age_days / half_life_days)`

**设计原则：** **只读**——从不修改原始 Statement 数据，仅计算派生值。

**能力：**
- **单条计算** `effective_confidence(stmt)` —— 返回衰减后的有效置信度
- **批量报告** `decay_report(result)` —— 生成完整的衰减分析报告（含统计摘要：均值、中位数、最小/最大值）
- **过滤** `filter_by_confidence(result, min_confidence=0.5)` —— 只保留有效置信度高于阈值的语句
- **可配置** `DecayConfig` —— 半衰期天数、最低阈值、参考时间
- **优雅降级** —— 无时间戳返回原始置信度；格式错误的时间戳返回原始置信度

**使用场景：**
- 知识图谱查询时自动过滤过时信息
- 评估知识库的"新鲜度"
- 根据时效性对搜索结果排序

```python
from stl_parser import parse, effective_confidence, decay_report, filter_by_confidence, DecayConfig

result = parse("""
[Theory_A] -> [Prediction_B] ::mod(confidence=0.95, timestamp="2025-06-01T00:00:00Z")
[Study_X] -> [Finding_Y] ::mod(confidence=0.85, timestamp="2026-02-01T00:00:00Z")
""")

# 单条衰减
eff = effective_confidence(result.statements[0], half_life_days=30)
print(f"有效置信度: {eff:.3f}")  # 很老的语句，大幅衰减

# 批量报告
config = DecayConfig(half_life_days=60)
report = decay_report(result, config)
print(f"总语句: {report.total_statements}")
print(f"已衰减: {report.statements_decayed}")
print(f"均值: {report.summary['mean']:.3f}")

# 过滤出仍然可信的语句
fresh = filter_by_confidence(result, min_confidence=0.5, half_life_days=30)
print(f"保留 {len(fresh.statements)} / {len(result.statements)} 条")
```

---

### 12. 查询与过滤（Query）

**做什么：** 在解析后的 STL 文档中查找、过滤、提取和精确定位数据。

**为什么需要它：**
之前开发者要找到特定语句，必须手动遍历 `result.statements` 并逐一检查字段。Query 模块提供了类似数据库查询的高级 API——一行代码就能找到你要的数据。这对标了 JSON 生态中 JSON Pointer (RFC 6901) 和 JSONPath (RFC 9535) 的能力。

**能力：**
- **查找** `find()` — 返回第一个匹配的语句
- **批量查找** `find_all()` — 返回所有匹配的语句
- **过滤** `filter_statements()` — 返回新的 ParseResult（原文档不变）
- **提取** `select()` — 从所有语句中提取某个字段的值列表
- **指针访问** `stl_pointer()` — 按路径精确寻址（对标 JSON Pointer）
- **Django-style 操作符** — `__gt`, `__gte`, `__lt`, `__lte`, `__ne`, `__contains`, `__startswith`, `__in`
- **ParseResult 便捷方法** — `result.find()`, `result.filter()`, `result[0]`, `result["Name"]`

**字段解析规则：**
- `source` → 源锚点名称（`stmt.source.name`）
- `target` → 目标锚点名称（`stmt.target.name`）
- `confidence`, `rule` 等 → 标准修饰符字段
- `type`, `line` 等 → 自定义修饰符字段（`stmt.modifiers.custom`）

**使用场景：**
- 从大型知识库中查找特定语句
- 按置信度、规则类型等条件筛选数据
- 提取所有源锚点名称做统计
- 在程序中精确访问嵌套数据

```python
from stl_parser import parse, find, find_all, filter_statements, select, stl_pointer

result = parse("""
[Theory_X] -> [Prediction_A] ::mod(confidence=0.95, rule="logical")
[Theory_X] -> [Prediction_B] ::mod(confidence=0.70, rule="causal")
[Study_Y] -> [Finding_Z] ::mod(confidence=0.85, rule="empirical", source="doi:10.1234")
""")

# 查找第一个匹配
stmt = result.find(source="Theory_X", confidence__gt=0.8)
print(stmt.target.name)  # "Prediction_A"

# 查找所有因果关系
causal = result.find_all(rule="causal")
print(f"因果语句数: {len(causal)}")  # 1

# 过滤为新文档（支持链式调用）
high_conf = result.filter(confidence__gte=0.8)
print(high_conf.to_stl())  # 只包含 confidence >= 0.8 的语句

# 提取所有源锚点名称
names = result.select("source")  # ["Theory_X", "Theory_X", "Study_Y"]

# 指针访问
val = stl_pointer(result, "/0/modifiers/confidence")  # 0.95

# 字典式访问
first = result[0]             # 第一条语句
matches = result["Theory_X"]  # 源为 Theory_X 的所有语句
```

---

### 13. 差异比较与补丁（Diff / Patch）

**做什么：** 计算两份 STL 文档之间的语义差异，并支持将差异作为补丁应用到文档上。

**为什么需要它：**
知识库需要版本管理。当两份文档不同时，你需要知道"具体哪些语句变了？哪些修饰符被修改了？"——不是文本行级别的差异，而是语义级别的差异。Diff/Patch 对标 JSON Patch (RFC 6902)，为 STL 文档提供了语义化的版本比较和增量更新能力。

**核心概念：**
- **语义匹配**——基于语句的身份键（源锚点 + 目标锚点 + 箭头类型）进行匹配，而非文本行比较
- **修饰符粒度**——精确报告每个修改语句中哪些修饰符字段发生了变化（字段名、旧值、新值）
- **三种操作**——`ADD`（新增）、`REMOVE`（删除）、`MODIFY`（修改）

**能力：**
- **语义差异** `stl_diff(a, b)` — 计算从文档 A 到文档 B 的所有变化
- **补丁应用** `stl_patch(doc, diff)` — 将差异应用到文档，生成新文档
- **文本渲染** `diff_to_text(diff)` — 人类可读的差异输出（`+` 新增 / `-` 删除 / `~` 修改）
- **JSON 序列化** `diff_to_dict(diff)` — 可存储/传输的 JSON 格式差异
- **往返保证** — `stl_patch(a, stl_diff(a, b))` 产生与 `b` 等价的文档
- **重复键处理** — 相同源→目标的多条语句正确匹配和比较

**使用场景：**
- 知识库版本管理——比较不同版本间的语义变化
- 协作编辑——识别并合并不同编辑者的修改
- 增量同步——只传输变化部分而非整个文档
- 审计追踪——记录知识库的演变历史

```python
from stl_parser import parse, stl_diff, stl_patch, diff_to_text

a = parse("""
[Theory_X] -> [Prediction_A] ::mod(confidence=0.80, rule="logical")
[Study_Y] -> [Finding_Z] ::mod(confidence=0.85, rule="empirical")
""")

b = parse("""
[Theory_X] -> [Prediction_A] ::mod(confidence=0.95, rule="logical")
[Theory_X] -> [Prediction_B] ::mod(confidence=0.70, rule="causal")
""")

# 计算差异
diff = stl_diff(a, b)
print(diff_to_text(diff))
# ~ [Theory_X] -> [Prediction_A]
#     confidence: 0.8 -> 0.95
# - [Study_Y] -> [Finding_Z] ::mod(confidence=0.85, rule="empirical")
# + [Theory_X] -> [Prediction_B] ::mod(confidence=0.7, rule="causal")
#
# 1 added, 1 removed, 1 modified, 0 unchanged

# 应用补丁
patched = stl_patch(a, diff)
assert len(patched.statements) == 2
assert patched.statements[0].modifiers.confidence == 0.95

# 往返验证
roundtrip = stl_patch(a, stl_diff(a, b))
assert stl_diff(roundtrip, b).is_empty  # 完全等价
```

---

### 14. 流式读取器（Streaming Reader）

**做什么：** 逐行读取 STL 文件，以生成器方式按需返回语句对象——不需要将整个文件加载到内存中。

**为什么需要它：**
`STLEmitter` 解决了"写入"问题：将程序事件追加写入 `.stl` 文件。但"读取"端一直缺失——现有的 `parse_file()` 会一次性加载整个文件到内存，对于大型知识库或持续增长的日志文件来说不可行。Reader 模块补齐了这个缺口，形成了完整的流式 I/O 闭环。

**核心设计：** **Generator-based** —— 使用 Python 生成器逐行解析，每次只有一个 Statement 对象在内存中。

**能力：**
- **流式解析** `stream_parse(source)` — 从文件、StringIO 或字符串列表逐行解析
- **内置过滤** `where={"confidence__gt": 0.8}` — 复用 Query 模块的 Django-style 操作符
- **多行合并** — 自动处理跨行的 `::mod(...)` 块（括号深度追踪）
- **上下文管理器** `STLReader` — 资源自动管理 + 运行统计
- **尾部追踪** `tail=True` — 类似 `tail -f` 的实时监控模式，监听 Emitter 持续写入的新内容
- **批量转换** `read_all()` — 流式过滤后转为 ParseResult，方便接入现有批量 API
- **错误策略** — `on_error="skip"` 静默跳过无效行（默认），`on_error="raise"` 立即报错

**Emitter ↔ Reader 闭环：**
```
STLEmitter (写入)                          STLReader (读取)
    │                                           │
    ▼                                           ▼
emit("[A]", "[B]", confidence=0.9)     for stmt in reader:
    │                                       process(stmt)
    ▼                                           ▲
  events.stl ──────────────────────────────────┘
```

**使用场景：**
- 大型知识库的内存高效处理（百万级语句）
- 实时监控 AI Agent 的决策日志（tail 模式）
- ETL 管线中的流式 STL 数据处理
- 从大文件中按条件提取子集

```python
from stl_parser import stream_parse, STLReader

# 流式解析 + 过滤（内存高效）
for stmt in stream_parse("huge_kb.stl", where={"rule": "causal", "confidence__gt": 0.7}):
    print(f"{stmt.source.name} → {stmt.target.name}")

# 上下文管理器 + 统计
with STLReader("events.stl") as reader:
    for stmt in reader:
        process(stmt)
    print(f"已处理: {reader.stats.statements_yielded} 条")
    print(f"跳过错误: {reader.stats.errors_skipped} 条")

# 实时监控（配合 Emitter 使用）
with STLReader("agent_log.stl", tail=True, tail_interval=0.1) as reader:
    for stmt in reader:  # 持续等待新内容
        if stmt.modifiers and stmt.modifiers.confidence and stmt.modifiers.confidence < 0.5:
            alert(f"低置信度: {stmt}")

# 流式过滤后转为批量结果
with STLReader("data.stl", where={"confidence__gte": 0.8}) as reader:
    result = reader.read_all()  # 只有匹配的语句被加载
    graph = STLGraph(result)    # 后续批量分析
```

---

## 四、错误处理体系

整个工具链使用统一的错误码体系，每个错误包含：
- **错误码**（如 `E104`）——用于程序化分类处理
- **错误消息**——人类可读的问题描述
- **行号和列号**——精确定位问题位置
- **修复建议**——告诉你怎么改

| 错误码范围 | 所属模块 |
|------------|----------|
| E001–E099 | 解析错误 |
| E100–E199 | 验证错误 |
| E200–E299 | 序列化错误 |
| E300–E399 | 图构建错误 |
| E400–E449 | 文件 I/O 错误 |
| E450–E499 | 查询错误 |
| E500–E599 | Builder 错误 |
| E600–E699 | Schema 错误 |
| E700–E799 | LLM 管线错误 |
| E800–E899 | Emitter 错误 |
| E900–E949 | Decay 错误 |
| E950–E959 | Diff/Patch 错误 |
| E960–E969 | Reader 错误 |
| W001–W099 | 警告 |

---

## 五、工具链闭环

这些工具不是孤立的，它们形成了一个完整的闭环：

```
                    ┌─────────────────────────┐
                    │   LLM 生成的原始文本      │
                    └──────────┬──────────────┘
                               ▼
                    ┌─────────────────────────┐
                    │  LLM Pipeline (清洗/修复) │
                    └──────────┬──────────────┘
                               ▼
        ┌──────────────────────────────────────────────┐
        │               Parser (解析)                   │
        └──────────┬───────────────────────────────────┘
                   ▼
        ┌──────────────────────┐     ┌──────────────────┐
        │  Schema (模式验证)    │     │ Validator (校验)  │
        └──────────┬───────────┘     └─────────┬────────┘
                   ▼                           ▼
        ┌──────────────────────┐     ┌──────────────────┐
        │  Graph (图谱构建)     │     │ Analyzer (分析)   │
        └──────────┬───────────┘     └──────────────────┘
                   ▼
        ┌──────────────────────────────────────────────┐
        │  Query (查找/过滤/指针)  │  Serializer (导出)  │
        └──────────┬──────────────────────────────────┘
                   ▼
        ┌──────────────────────────────────────────────┐
        │  Diff/Patch (版本比较与补丁)                   │
        └──────────────────────────────────────────────┘

                    Builder (代码生成) ─────→ Emitter (事件写入)
                         │                        │
                         └────── .stl 文件 ←──────┘
                                   │
                                   ▼
                    Reader (流式读取) ←──── tail 模式实时监控
                                   │
                                   ▼
                            回到 Parser 继续处理
```

**关键闭环路径：**
- **LLM → 清洗 → 解析 → 验证 → 图谱** ——从 AI 输出到知识图谱
- **Builder → Emitter → 文件 → Parser** ——从程序事件到可分析的日志
- **解析 → Schema 验证 → 序列化** ——从文本到合规的结构化数据

---

## 六、安装与运行

```bash
pip install stl-parser

# 或从源码安装
cd parser
pip install -e ".[dev]"

# 命令行使用
stl validate input.stl
stl convert input.stl --to json
stl analyze input.stl

# Python 中使用
from stl_parser import parse, stl, validate_llm_output, STLEmitter
```

**依赖：**
- Python 3.9+
- lark（语法解析）
- pydantic v2（数据建模）
- rdflib（RDF 序列化）
- networkx（图分析）
- typer + rich（命令行界面）

---

## 七、技术指标

| 指标 | 数值 |
|------|------|
| 代码总量 | ~3,100 行（19个模块） |
| 测试数量 | 530 通过 |
| 代码覆盖率 | 89% |
| 文档 | 34 个文档文件，~6,860 行（见下方） |
| 支持的 Python 版本 | 3.9, 3.10, 3.11, 3.12 |
| 许可证 | Apache 2.0（代码）+ CC BY 4.0（语言规范） |

### 文档库

项目配备了完整的英文文档库（`docs/` 目录），面向人类开发者，为后续迁移到 stl-lang.org 做准备。

| 类别 | 目录 | 文件数 | 行数 | 内容 |
|------|------|--------|------|------|
| 入门指南 | `docs/getting-started/` | 4 | ~675 | 安装、快速开始、核心概念 |
| 教程 | `docs/tutorials/` | 8 | ~2,055 | 8 个从零开始的分步教程，覆盖全部主要 API |
| API 参考 | `docs/reference/api/` | 12 | ~1,280 | 每个模块一份，含签名、参数、返回值、示例 |
| 独立参考 | `docs/reference/` | 5 | ~600 | CLI 命令、修饰符、锚点类型、语法速查、错误码 |
| 实用指南 | `docs/guides/` | 5 | ~1,294 | 自定义 Schema、LLM 集成、知识图谱管线、事件日志、置信度衰减 |

入口页面：[`docs/index.md`](index.md)

---

## 七-b、Schema 生态（领域约束库）

Schema 生态是 STL 工具链的**协议层**——定义各领域知识的结构约束，确保不同 AI 和人类产生的 STL 文档符合领域规范。

### 已有领域 Schema

| Schema 文件 | 领域 | 必填字段 | 特殊约束 |
|-------------|------|----------|----------|
| `tcm.stl.schema` | 中医学 | confidence, rule, domain | Unicode 锚点名、confidence 0.5-1.0 |
| `scientific.stl.schema` | 科学研究 | confidence, rule, source | 来源必填、confidence 0.3-1.0 |
| `causal.stl.schema` | 因果推理 | confidence, rule, strength | strength 必填、禁止循环 |
| `historical.stl.schema` | 历史知识 | confidence, time, source | 时间必填、Unicode 多语种 |
| `medical.stl.schema` | 医学/临床 | confidence, rule, source, domain | 前缀锚点名（Symptom_、Drug_等）、confidence 0.5-1.0 |
| `legal.stl.schema` | 法律推理 | confidence, rule, source | 前缀锚点名（Law_、Regulation_等）、confidence 0.7-1.0 |

### 使用方式

```python
from stl_parser import load_schema, validate_against_schema, parse

# 加载领域 schema
schema = load_schema("docs/schemas/tcm.stl.schema")

# 验证文档是否符合 TCM 规范
doc = parse('[TCM:湿邪] -> [TCM:苦味药] ::mod(confidence=0.85, rule="causal", domain="TCM")')
result = validate_against_schema(doc, schema)

if not result.is_valid:
    for err in result.errors:
        print(f"  {err.code}: {err.message}")
```

### 创建新领域 Schema

1. 复制 `docs/schemas/_template.stl.schema`
2. 填入领域特定的锚点模式、必填字段、值范围
3. 用 `load_schema()` + `validate_against_schema()` 测试
4. 添加到 `docs/schemas/README.md` 索引

### Bug 修复记录

- **`re.match` → `re.fullmatch`** (schema.py:524): 锚点名模式验证原来只检查前缀匹配，`"Not Valid!"` 会通过 `/[A-Za-z_]+/` 模式（匹配到 `"Not"`）。已修复为全字符串匹配。

---

## 八、未来开发路线图

STL 工具链的目标是达到与 JSON 生态同等成熟度的工具支持。以下是对标 JSON 已有工具能力的差距分析和优先级规划。

### JSON 生态对标分析

| 能力层 | JSON 生态 | STL 现状 (v1.7.0) | 差距 |
|--------|-----------|-------------------|------|
| **解析/序列化** | `json.loads/dumps` (内置) | `parse()` / `to_json()` / `to_stl()` | 已具备 |
| **数据模型** | 无（JSON 是纯数据） | Pydantic v2 强类型模型 | STL 更强 |
| **Schema 验证** | JSON Schema (RFC draft) | `load_schema()` / `validate_against_schema()` | 已具备 |
| **构建器** | 无需（dict 即可） | `stl()` / `stl_doc()` 流式 API | 已具备 |
| **LLM 修复** | 无标准工具 | `clean()` / `repair()` / `validate_llm_output()` | STL 领先 |
| **图分析** | 无内置 | `STLGraph` / `STLAnalyzer` | STL 特有 |
| **时效衰减** | 无标准工具 | `effective_confidence()` / `decay_report()` | STL 特有 |
| **指针/寻址** | JSON Pointer (RFC 6901) | `stl_pointer()` | **已具备 (v1.4.0)** |
| **查询 API** | JSONPath (RFC 9535) | `find()` / `find_all()` / `filter()` / `select()` | **已具备 (v1.4.0)** |
| **查询语言** | JSONPath 表达式语法 | 无（目前用 Django-style kwargs） | 部分缺失 |
| **CLI 查询** | jq（事实标准） | `stl query` (--where/--select/--pointer/--format/--count/--limit) | **已具备 (v1.5.0)** |
| **差异比较** | JSON Patch (RFC 6902) | `stl_diff()` / `stl_patch()` / `diff_to_text()` | **已具备 (v1.6.0)** |
| **合并补丁** | JSON Merge Patch (RFC 7396) | 通过 `stl_patch()` 实现 | **已具备 (v1.6.0)** |
| **IDE 支持** | 成熟（VS Code 内置高亮、IntelliSense） | 无 | **缺失** |
| **流式处理** | JSON Lines / ndjson | `STLEmitter`（写入端）+ `STLReader`/`stream_parse`（读取端） | **已具备 (v1.7.0)** |
| **事件发射** | 无标准工具 | `STLEmitter` 线程安全发射器 | STL 特有 |
| **领域 Schema 库** | JSON Schema Store | 6 个领域 schema（TCM、科学、因果、历史、医学、法律） | **已具备 (v1.7.0+)** |
| **数据绑定/映射** | ORM / Marshmallow / Pydantic 序列化 | 无（`to_json()` 输出 STL 结构 JSON，无法映射到应用自定义 JSON 结构） | **缺失** |

### 优先级路线图

#### P0-a：STL Pointer + Query API（指针与查询）— 已完成 v1.4.0

**目标：** 让开发者可以像 `jq '.statements[0].source.name'` 一样直接定位和查询 STL 数据。

**已实现：**
- `stl_pointer(result, "/0/source/name")` — 按路径精确寻址（对标 JSON Pointer RFC 6901）
- `find(result, source="X", confidence__gt=0.8)` — 查找第一个匹配
- `find_all(result, rule="causal")` — 查找所有匹配
- `filter_statements(result, confidence__gte=0.8)` — 过滤为新 ParseResult
- `select(result, "source")` — 提取字段值列表
- `result.find()`, `result.filter()`, `result[0]`, `result["Name"]` — ParseResult 便捷方法
- 9 种操作符：`eq`, `gt`, `gte`, `lt`, `lte`, `ne`, `contains`, `startswith`, `in`

**STLC 规范：** `docs/stlc/stl_query_v1.0.0.stlc.md`

#### P0-b/c：查询表达式语言（未来）

**目标：** 提供类似 JSONPath 的字符串表达式查询语法。

**计划实现：**
- `stl_query(result, "source.name == 'Theory_X'")` — 按条件查询语句集（对标 JSONPath RFC 9535）

#### P1：CLI 查询工具（`stl query`）— 已完成 v1.5.0

**目标：** 提供类似 `jq` 的命令行查询能力。

**已实现：**
- `stl query input.stl --where "confidence__gt=0.8"` — Django-style 条件过滤
- `stl query input.stl --select "source,confidence" --format json` — 字段投影 + 多格式输出
- `stl query input.stl --pointer "/0/source/name"` — 指针精确寻址
- `stl query input.stl --where "rule=causal" --count` — 计数模式
- `stl query input.stl --limit 5` — 结果限制
- 输出格式：`table`（Rich 表格）、`json`、`csv`、`stl`
- `--where` 支持 `__in` 操作符（`rule__in=causal|logical`）

**STLC 规范：** `docs/stlc/stl_cli_query_v1.0.0.stlc.md`

#### P2：STL Diff / Patch（差异比较与补丁）— 已完成 v1.6.0

**目标：** 对比两份 STL 文档的差异，并生成/应用补丁。

**已实现：**
- `stl_diff(a, b)` — 基于身份键（源锚点 + 目标锚点 + 箭头）的语义差异比较
- `stl_patch(doc, diff)` — 应用差异补丁，生成新文档
- `diff_to_text(diff)` — 人类可读的差异输出（`+`/`-`/`~` 标记）
- `diff_to_dict(diff)` — JSON 可序列化的差异格式
- `stl diff a.stl b.stl` — CLI 差异比较（支持 `--format`、`--summary`、`--quiet`）
- `stl patch input.stl diff.json` — CLI 补丁应用（支持 `--output`）
- 修饰符粒度变化追踪（字段、旧值、新值）
- 往返保证：`stl_patch(a, stl_diff(a, b))` ≡ `b`

**STLC 规范：** `docs/stlc/stl_diff_v1.0.0.stlc.md`

#### P2-b：流式读取器（Streaming Reader）— 已完成 v1.7.0

**目标：** 补齐 `STLEmitter`（写入端）缺失的读取端，支持内存高效的逐行解析和文件监控。

**已实现：**
- `stream_parse(source, where=, on_error=)` — 生成器逐行解析，内存高效
- `STLReader(source, where=, tail=)` — 上下文管理器 + 运行统计
- `ReaderStats` — 行数、语句数、错误数、注释数等统计
- tail 模式 — 类似 `tail -f`，轮询检测文件新内容
- 多行语句合并 — 括号深度追踪，20行安全限制
- 与 query 模块集成 — `where` 参数复用 Django-style 操作符

**STLC 规范：** `docs/stlc/stl_reader_v1.0.0.stlc.md`

#### Schema 生态 — 已完成 v1.7.0+

**目标：** 创建领域 Schema 库，为不同知识领域提供标准化约束模板。

**已实现：**
- 审计 schema.py 能力边界，修复 `re.fullmatch` bug
- 6 个领域 schema：TCM、科学研究、因果推理、历史知识、医学/临床、法律推理
- 空白模板 `_template.stl.schema` 用于创建新领域
- README 索引文档（使用指南、命名规范、版本管理）

#### P3：Schema Projection — STL → 应用 JSON 数据绑定

**目标：** 扩展 Schema 系统，使其不仅能验证 STL 文档，还能定义 STL 结构到应用自定义 JSON 结构的映射规则，实现 STL 作为通用数据存储层。

**动机：** 当前 `to_json()` 输出的是 STL 自身的结构化 JSON（`{statements: [{source, target, modifiers}]}`），无法直接映射到应用所需的自定义 JSON 格式（如 `{id, title, items: [...]}`）。每个应用都需要手写一个定制的转换层。如果 Schema 能声明式定义映射规则，就可以通过一个通用转换器实现 **STL 存储 → 自动转化 JSON → API 层直接读取** 的完整管线。

**设想的 Schema 扩展语法：**
```
schema SharedBoard v1.0 {
    namespace "Board"

    projection "board" {
        # 从 STL statements 映射到应用 JSON 结构
        root.id       <- source.name          # Board_xxx → id
        root.title    <- source.modifier.title
        root.items[]  <- target {              # 每个 target 映射为一个 item
            id        <- target.name
            type      <- modifier.type
            content   <- modifier.content
            checked   <- modifier.checked
            notes     <- modifier.notes
        }
    }
}
```

**计划实现：**
- Schema 内新增 `projection` 块，声明式定义 STL 字段到应用 JSON 字段的映射
- `project(result, schema, projection_name)` — 根据映射规则将 ParseResult 转换为应用 JSON
- `stl convert input.stl --to json --projection board` — CLI 支持投影转换
- 双向支持（未来）：应用 JSON → STL 的反向映射，实现完整的数据绑定闭环

**价值：**
- STL 可以作为真正的 **通用数据存储格式**，不仅限于知识图谱
- AI agent 用 STL 原生语法生成数据，应用层自动获得所需的 JSON 结构
- 对标 ORM / Marshmallow / Pydantic 序列化器在 JSON 生态中的角色
- 消除每个应用手写映射层的重复劳动

**起源：** Shared Board 项目（2026-02-21）— 探索 STL 替代 JSON 作为协作面板数据格式时，发现的 feature gap。

**状态：** 未开始 | 高价值 | 等待排期

---

#### P4：IDE 与编辑器支持

**目标：** 为主流编辑器提供 STL 语言支持。

**计划实现：**
- VS Code 扩展：语法高亮、自动补全、悬停信息、错误诊断
- Language Server Protocol (LSP) 实现
- `.stl` 文件关联和图标
- TextMate 语法定义（兼容 Sublime Text、Atom 等）

**价值：** 降低 STL 的使用门槛，提升开发体验。

---

**STL 工具链的设计理念：** 让知识的表达、验证、传输和分析形成一个无缝的流水线。从 LLM 的自由文本到可计算的知识图谱，从程序事件到结构化的因果日志——STL 工具链是这座桥梁。
