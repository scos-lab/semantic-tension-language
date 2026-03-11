# STL Query STLC Specification

> **Version:** 1.0.0
> **Type:** Base
> **Target:** `stl_parser/query.py` + `stl_parser/models.py` (ParseResult extension)
> **Author:** Syn-claude
> **Date:** 2026-02-12
> **Status:** Draft
> **Priority:** P0-a (first phase of Query roadmap)

---

## 1. Scope Definition

[Query_Module] -> [Scope] ::mod(
  intent="Provide find/filter/select/pointer operations on parsed STL documents",
  boundaries="Read-only query over existing ParseResult; no mutation, no parsing, no I/O",
  confidence=0.95
)

**Included:**
- `find(result, ...)` — return first matching Statement or None
- `find_all(result, ...)` — return all matching Statements
- `filter_statements(result, ...)` — return new ParseResult containing only matches
- `select(result, field)` — extract specific field values from all statements
- `stl_pointer(result, path)` — access arbitrary nested value by path string
- `ParseResult` convenience methods: `.find()`, `.find_all()`, `.filter()`, `.select()`, `__getitem__`
- Django-style field operators: `__gt`, `__gte`, `__lt`, `__lte`, `__ne`, `__contains`, `__startswith`, `__in`

**Excluded:**
- Query language parser (P0-c, future phase)
- CLI query command (P1, future phase)
- Index persistence or caching across calls
- Mutation of source ParseResult or Statements
- File I/O

---

## 2. Architecture Overview

[Query_Module] -> [ParseResult_Model] ::mod(
  rule="causal",
  intent="Query functions accept ParseResult as primary input; convenience methods added to ParseResult",
  confidence=0.95
)

[Query_Module] -> [Statement_Model] ::mod(
  rule="causal",
  intent="Query functions inspect Statement fields (source, target, modifiers) for matching",
  confidence=0.95
)

[Query_Module] -> [Standalone_Functions] ::mod(
  rule="definitional",
  intent="All query logic lives in query.py as standalone functions; ParseResult methods delegate to them",
  confidence=0.95
)

[ParseResult_Methods] -> [Query_Functions] ::mod(
  rule="causal",
  intent="ParseResult.find() calls query.find(self, ...); thin delegation layer",
  confidence=0.95
)

### Design Principle: Separation of Concerns

[Design_Principle] -> [No_Mutation] ::mod(
  rule="definitional",
  intent="All query operations are read-only; they return new objects, never modify inputs",
  confidence=1.0
)

[Design_Principle] -> [Lazy_Index] ::mod(
  rule="definitional",
  intent="Internal index built on first query call, cached on ParseResult instance for reuse",
  confidence=0.90
)

---

## 3. Data Models

### 3.1 FieldCondition (Internal)

[FieldCondition] -> [Model_Definition] ::mod(
  rule="definitional",
  type="model",
  schema="Internal representation of a single field filter condition",
  fields="field_name: str, operator: str ('eq'|'gt'|'gte'|'lt'|'lte'|'ne'|'contains'|'startswith'|'in'), value: Any",
  confidence=0.95
)

### 3.2 Operator Syntax

[Operator_Syntax] -> [Django_Style] ::mod(
  rule="definitional",
  intent="Field lookups use double-underscore operator suffixes",
  confidence=0.95
)

**Operator mapping from kwargs:**

| Kwarg Pattern | Operator | Semantics | Example |
|---------------|----------|-----------|---------|
| `confidence=0.9` | `eq` | Exact equality | `confidence == 0.9` |
| `confidence__gt=0.8` | `gt` | Greater than | `confidence > 0.8` |
| `confidence__gte=0.8` | `gte` | Greater or equal | `confidence >= 0.8` |
| `confidence__lt=0.5` | `lt` | Less than | `confidence < 0.5` |
| `confidence__lte=0.5` | `lte` | Less or equal | `confidence <= 0.5` |
| `confidence__ne=0.0` | `ne` | Not equal | `confidence != 0.0` |
| `rule__contains="caus"` | `contains` | Substring match | `"caus" in rule` |
| `source__startswith="doi:"` | `startswith` | Prefix match | `source.startswith("doi:")` |
| `rule__in=["causal","logical"]` | `in` | Membership test | `rule in ["causal", "logical"]` |

### 3.3 Field Resolution Order

[Field_Resolution] -> [Priority_Chain] ::mod(
  rule="definitional",
  intent="Define how field names in query kwargs map to Statement attributes",
  confidence=0.95
)

**Special fields (resolved from Statement directly):**

| Query Field | Resolves To | Type |
|-------------|-------------|------|
| `source` | `stmt.source.name` | str |
| `target` | `stmt.target.name` | str |
| `source_namespace` | `stmt.source.namespace` | Optional[str] |
| `target_namespace` | `stmt.target.namespace` | Optional[str] |
| `arrow` | `stmt.arrow` | str |

**Modifier fields (resolved from Statement.modifiers):**

All other field names are resolved as modifier fields:
1. Check `stmt.modifiers.{field_name}` (standard Modifier fields)
2. If not found in standard fields, check `stmt.modifiers.custom.get(field_name)` (custom fields)
3. If `stmt.modifiers` is None, the field value is treated as None

This means `confidence=0.9` resolves to `stmt.modifiers.confidence == 0.9` and `type="class"` resolves to `stmt.modifiers.custom.get("type") == "class"`.

---

## 4. Computational Flow

### 4.1 Function: find(result, **kwargs) -> Optional[Statement]

[Entry_find] -> [Input_ParseResult] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="ParseResult — the document to search",
  confidence=1.0
)

[Entry_find] -> [Input_Kwargs] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Dict[str, Any] — field conditions with optional operator suffixes",
  confidence=1.0
)

[Input_Kwargs] -> [Parse_Conditions] ::mod(
  rule="causal",
  type="transformation",
  intent="Convert kwargs to list of FieldCondition objects",
  input="kwargs: Dict[str, Any]",
  output="List[FieldCondition]",
  algorithm="For each kwarg, split key on '__' to get (field_name, operator). Default operator is 'eq'.",
  confidence=0.95
)

[Parse_Conditions] -> [Loop_Statements] ::mod(
  rule="causal",
  type="loop",
  loop_condition="for stmt in result.statements",
  intent="Iterate statements in order, return first match",
  confidence=1.0
)

[Loop_Statements] -> [Match_Statement] ::mod(
  rule="causal",
  type="transformation",
  intent="Test if statement satisfies ALL conditions (AND logic)",
  input="{stmt, conditions}",
  output="bool",
  algorithm="For each condition: resolve field value from stmt, apply operator comparison. ALL must pass.",
  confidence=0.95
)

[Match_Statement] -> [Branch_Matched] ::mod(
  rule="logical",
  type="branching",
  condition="all conditions matched",
  on_success="Return_Statement",
  on_fail="Continue_Loop",
  confidence=1.0
)

[Branch_Matched] -> [Return_Statement] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="Optional[Statement] — first matching statement",
  confidence=1.0
)

[Branch_Matched] -> [Continue_Loop] ::mod(
  rule="causal",
  intent="Try next statement",
  confidence=1.0
)

[Continue_Loop] -> [Loop_Exhausted] ::mod(
  rule="causal",
  type="output",
  format="None",
  intent="No match found, return None",
  confidence=1.0
)

[Return_Statement] -> [Exit_find] ::mod(
  rule="definitional",
  confidence=1.0
)

[Loop_Exhausted] -> [Exit_find] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.2 Function: find_all(result, **kwargs) -> List[Statement]

[Entry_find_all] -> [Input_ParseResult] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="ParseResult",
  confidence=1.0
)

[Entry_find_all] -> [Input_Kwargs] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Dict[str, Any] — field conditions",
  confidence=1.0
)

[Input_Kwargs] -> [Parse_Conditions] ::mod(
  rule="causal",
  type="transformation",
  intent="Same condition parsing as find()",
  confidence=0.95
)

[Parse_Conditions] -> [Loop_All_Statements] ::mod(
  rule="causal",
  type="loop",
  loop_condition="for stmt in result.statements",
  intent="Collect ALL matching statements (not just first)",
  confidence=1.0
)

[Loop_All_Statements] -> [Collect_Matches] ::mod(
  rule="causal",
  type="aggregation",
  input="matching statements",
  output="List[Statement]",
  confidence=1.0
)

[Collect_Matches] -> [Return_List] ::mod(
  rule="definitional",
  type="output",
  format="Array",
  schema="List[Statement] — all matching statements (empty list if none)",
  confidence=1.0
)

[Return_List] -> [Exit_find_all] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.3 Function: filter_statements(result, **kwargs) -> ParseResult

[Entry_filter] -> [Input_ParseResult] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="ParseResult",
  confidence=1.0
)

[Entry_filter] -> [Input_Kwargs] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Dict[str, Any] — field conditions",
  confidence=1.0
)

[Input_Kwargs] -> [Call_find_all] ::mod(
  rule="causal",
  type="transformation",
  intent="Delegate matching logic to find_all()",
  input="{result, kwargs}",
  output="List[Statement]",
  confidence=0.95
)

[Call_find_all] -> [Create_New_ParseResult] ::mod(
  rule="causal",
  type="transformation",
  intent="Wrap matched statements in a new ParseResult",
  input="List[Statement]",
  output="ParseResult(statements=matched, is_valid=result.is_valid, errors=[], warnings=[])",
  confidence=0.95,
  note="Returns NEW ParseResult; original is unmodified"
)

[Create_New_ParseResult] -> [Return_ParseResult] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="ParseResult — filtered copy",
  confidence=1.0
)

[Return_ParseResult] -> [Exit_filter] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.4 Function: select(result, field) -> List[Any]

[Entry_select] -> [Input_ParseResult] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="ParseResult",
  confidence=1.0
)

[Entry_select] -> [Input_Field] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="str — field path to extract (e.g., 'source', 'target', 'confidence', 'custom.type')",
  confidence=1.0
)

[Input_Field] -> [Loop_Extract] ::mod(
  rule="causal",
  type="loop",
  loop_condition="for stmt in result.statements",
  intent="Extract the named field value from each statement",
  algorithm="Use same field resolution as find() — special fields from Statement, others from Modifier/custom",
  confidence=0.95
)

[Loop_Extract] -> [Collect_Values] ::mod(
  rule="causal",
  type="aggregation",
  input="resolved values",
  output="List[Any] — includes None for statements where field is absent",
  confidence=0.95
)

[Collect_Values] -> [Return_Values] ::mod(
  rule="definitional",
  type="output",
  format="Array",
  schema="List[Any]",
  confidence=1.0
)

[Return_Values] -> [Exit_select] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.5 Function: stl_pointer(result, path) -> Any

[Entry_stl_pointer] -> [Input_ParseResult] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="ParseResult",
  confidence=1.0
)

[Entry_stl_pointer] -> [Input_Path] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="str — slash-delimited path (inspired by JSON Pointer RFC 6901)",
  examples="/0/source/name, /0/modifiers/confidence, /2/target/namespace",
  confidence=0.95
)

[Input_Path] -> [Parse_Path_Segments] ::mod(
  rule="causal",
  type="transformation",
  intent="Split path on '/' and resolve each segment",
  input="path string",
  output="List[str] — path segments",
  algorithm="path.strip('/').split('/')",
  confidence=0.95
)

[Parse_Path_Segments] -> [Resolve_Root] ::mod(
  rule="causal",
  type="transformation",
  intent="First segment is statement index (integer)",
  input="segments[0]",
  output="Statement at that index",
  algorithm="result.statements[int(segments[0])]",
  on_fail="Error_Index_Out_Of_Range",
  confidence=0.95
)

[Resolve_Root] -> [Walk_Segments] ::mod(
  rule="causal",
  type="loop",
  loop_condition="for segment in remaining segments",
  intent="Traverse object tree: 'source' -> stmt.source, 'name' -> anchor.name, 'modifiers' -> stmt.modifiers, etc.",
  algorithm="getattr(current, segment) or current.custom.get(segment)",
  confidence=0.90
)

[Walk_Segments] -> [Branch_Resolved] ::mod(
  rule="logical",
  type="branching",
  condition="path fully resolved to a value",
  on_success="Return_Value",
  on_fail="Error_Invalid_Path",
  confidence=0.95
)

[Branch_Resolved] -> [Return_Value] ::mod(
  rule="definitional",
  type="output",
  format="Any",
  schema="The resolved value (str, float, int, Anchor, Modifier, etc.)",
  confidence=0.95
)

[Branch_Resolved] -> [Error_Invalid_Path] ::mod(
  rule="causal",
  type="output",
  error_type="STLQueryError",
  error_message="Invalid pointer path: segment '{segment}' not found",
  confidence=0.90
)

[Return_Value] -> [Exit_stl_pointer] ::mod(
  rule="definitional",
  confidence=1.0
)

[Error_Invalid_Path] -> [Exit_stl_pointer_Error] ::mod(
  rule="definitional",
  confidence=1.0
)

[Resolve_Root] -> [Error_Index_Out_Of_Range] ::mod(
  rule="causal",
  type="output",
  error_type="STLQueryError",
  error_message="Statement index {idx} out of range (document has {n} statements)",
  confidence=0.95
)

[Error_Index_Out_Of_Range] -> [Exit_stl_pointer_Error] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.6 ParseResult Convenience Methods

[ParseResult_Extension] -> [Delegation_Pattern] ::mod(
  rule="definitional",
  intent="Add thin wrapper methods to ParseResult that delegate to query.py functions",
  confidence=0.95
)

**Methods added to ParseResult:**

```
ParseResult.find(**kwargs) -> Optional[Statement]
    → delegates to query.find(self, **kwargs)

ParseResult.find_all(**kwargs) -> List[Statement]
    → delegates to query.find_all(self, **kwargs)

ParseResult.filter(**kwargs) -> ParseResult
    → delegates to query.filter_statements(self, **kwargs)

ParseResult.select(field) -> List[Any]
    → delegates to query.select(self, field)

ParseResult.__getitem__(key) -> Statement | List[Statement]
    → if key is int: return self.statements[key]
    → if key is str: return self.find_all(source=key)
    → if key is slice: return self.statements[key]
```

### 4.7 Internal: _resolve_field(stmt, field_name) -> Any

[Entry_resolve_field] -> [Input_Statement] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Statement",
  confidence=1.0
)

[Entry_resolve_field] -> [Input_Field_Name] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="str — raw field name without operator suffix",
  confidence=1.0
)

[Input_Field_Name] -> [Branch_Special_Field] ::mod(
  rule="logical",
  type="branching",
  condition="field_name in SPECIAL_FIELDS",
  on_success="Resolve_Special",
  on_fail="Resolve_Modifier",
  confidence=0.95
)

[Branch_Special_Field] -> [Resolve_Special] ::mod(
  rule="causal",
  type="transformation",
  intent="Map special field names to statement attributes",
  mapping="source -> stmt.source.name, target -> stmt.target.name, source_namespace -> stmt.source.namespace, target_namespace -> stmt.target.namespace, arrow -> stmt.arrow",
  confidence=1.0
)

[Branch_Special_Field] -> [Resolve_Modifier] ::mod(
  rule="causal",
  type="transformation",
  intent="Look up field in Modifier standard fields, then custom dict",
  confidence=0.95
)

[Resolve_Modifier] -> [Branch_Has_Modifiers] ::mod(
  rule="logical",
  type="branching",
  condition="stmt.modifiers is not None",
  on_success="Check_Standard_Field",
  on_fail="Return_None",
  confidence=1.0
)

[Branch_Has_Modifiers] -> [Check_Standard_Field] ::mod(
  rule="causal",
  type="transformation",
  intent="Try getattr(stmt.modifiers, field_name)",
  on_success="Return_Value",
  on_fail="Check_Custom_Field",
  confidence=0.90
)

[Check_Standard_Field] -> [Check_Custom_Field] ::mod(
  rule="causal",
  type="transformation",
  intent="Try stmt.modifiers.custom.get(field_name)",
  confidence=0.90
)

[Check_Standard_Field] -> [Return_Value] ::mod(
  rule="causal",
  confidence=0.95
)

[Check_Custom_Field] -> [Return_Value] ::mod(
  rule="causal",
  confidence=0.95
)

[Branch_Has_Modifiers] -> [Return_None] ::mod(
  rule="causal",
  type="output",
  format="None",
  confidence=1.0
)

[Resolve_Special] -> [Return_Value] ::mod(
  rule="causal",
  confidence=1.0
)

[Return_Value] -> [Exit_resolve_field] ::mod(
  rule="definitional",
  confidence=1.0
)

[Return_None] -> [Exit_resolve_field] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.8 Internal: _parse_kwargs(**kwargs) -> List[FieldCondition]

[Entry_parse_kwargs] -> [Input_Kwargs] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Dict[str, Any]",
  confidence=1.0
)

[Input_Kwargs] -> [Loop_Each_Kwarg] ::mod(
  rule="causal",
  type="loop",
  loop_condition="for key, value in kwargs.items()",
  confidence=1.0
)

[Loop_Each_Kwarg] -> [Split_Key] ::mod(
  rule="causal",
  type="transformation",
  intent="Split key on '__' to extract field name and operator",
  algorithm="If '__' in key and last part is known operator: field_name = parts before last '__', operator = last part. Else: field_name = key, operator = 'eq'.",
  examples="'confidence__gt' -> ('confidence', 'gt'), 'confidence' -> ('confidence', 'eq'), 'source__startswith' -> ('source', 'startswith')",
  confidence=0.95
)

[Split_Key] -> [Create_Condition] ::mod(
  rule="causal",
  type="transformation",
  output="FieldCondition(field_name, operator, value)",
  confidence=1.0
)

[Create_Condition] -> [Collect_Conditions] ::mod(
  rule="causal",
  type="aggregation",
  output="List[FieldCondition]",
  confidence=1.0
)

[Collect_Conditions] -> [Return_Conditions] ::mod(
  rule="definitional",
  type="output",
  format="Array",
  schema="List[FieldCondition]",
  confidence=1.0
)

[Return_Conditions] -> [Exit_parse_kwargs] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.9 Internal: _apply_operator(field_value, operator, target_value) -> bool

[Entry_apply_operator] -> [Branch_Operator_Type] ::mod(
  rule="logical",
  type="branching",
  intent="Dispatch to correct comparison logic based on operator",
  confidence=1.0
)

[Branch_Operator_Type] -> [Op_EQ] ::mod(
  rule="definitional",
  operator="eq",
  algorithm="field_value == target_value",
  confidence=1.0
)

[Branch_Operator_Type] -> [Op_GT] ::mod(
  rule="definitional",
  operator="gt",
  algorithm="field_value is not None and field_value > target_value",
  confidence=1.0
)

[Branch_Operator_Type] -> [Op_GTE] ::mod(
  rule="definitional",
  operator="gte",
  algorithm="field_value is not None and field_value >= target_value",
  confidence=1.0
)

[Branch_Operator_Type] -> [Op_LT] ::mod(
  rule="definitional",
  operator="lt",
  algorithm="field_value is not None and field_value < target_value",
  confidence=1.0
)

[Branch_Operator_Type] -> [Op_LTE] ::mod(
  rule="definitional",
  operator="lte",
  algorithm="field_value is not None and field_value <= target_value",
  confidence=1.0
)

[Branch_Operator_Type] -> [Op_NE] ::mod(
  rule="definitional",
  operator="ne",
  algorithm="field_value != target_value",
  confidence=1.0
)

[Branch_Operator_Type] -> [Op_CONTAINS] ::mod(
  rule="definitional",
  operator="contains",
  algorithm="field_value is not None and target_value in str(field_value)",
  confidence=0.95
)

[Branch_Operator_Type] -> [Op_STARTSWITH] ::mod(
  rule="definitional",
  operator="startswith",
  algorithm="field_value is not None and str(field_value).startswith(target_value)",
  confidence=0.95
)

[Branch_Operator_Type] -> [Op_IN] ::mod(
  rule="definitional",
  operator="in",
  algorithm="field_value in target_value (target_value must be iterable)",
  confidence=0.95
)

**None handling:** When `field_value` is None (field absent on statement):
- `eq` with `None` → True (explicitly querying for absent fields)
- `ne` with any value → True (absent != any value)
- All other operators → False (absent field cannot satisfy comparison)

---

## 5. Dependencies (Reuse, Not Duplicate)

| Dependency | Module | Purpose |
|------------|--------|---------|
| `Statement` | `models.py` | Statement data model (queried object) |
| `Modifier` | `models.py` | Modifier data model (field resolution) |
| `Anchor` | `models.py` | Anchor data model (source/target resolution) |
| `ParseResult` | `models.py` | Document container (primary input + extended with methods) |
| `STLQueryError` | `errors.py` | Query-specific exceptions (E400-E499) |

**New error codes:**

| Code | Name | Trigger |
|------|------|---------|
| E400 | `E400_QUERY_INVALID_OPERATOR` | Unknown operator suffix in kwargs |
| E401 | `E401_QUERY_INVALID_PATH` | stl_pointer path cannot be resolved |
| E402 | `E402_QUERY_INDEX_OUT_OF_RANGE` | stl_pointer statement index out of bounds |
| E403 | `E403_QUERY_TYPE_ERROR` | Comparison operator applied to incompatible types |

---

## 6. Public API Summary

### Standalone Functions (query.py)

```python
from stl_parser.query import find, find_all, filter_statements, select, stl_pointer

# Find first statement from Theory_X with high confidence
stmt = find(result, source="Theory_X", confidence__gt=0.8)

# Find all causal statements
stmts = find_all(result, rule="causal")

# Filter to high-confidence subset (returns new ParseResult)
filtered = filter_statements(result, confidence__gte=0.8)

# Extract all source anchor names
names = select(result, "source")

# Pointer access
value = stl_pointer(result, "/0/modifiers/confidence")
```

### ParseResult Methods (added to models.py)

```python
result = parse(stl_text)

# Convenience methods (delegate to query.py)
stmt = result.find(source="Theory_X")
stmts = result.find_all(rule="causal")
filtered = result.filter(confidence__gte=0.8)
names = result.select("source")

# Dict-like access
first = result[0]                    # Statement by index
matches = result["Theory_X"]         # All statements with source name
subset = result[1:3]                 # Slice of statements
```

### Exported from __init__.py

```python
from stl_parser import find, find_all, filter_statements, select, stl_pointer
```

---

## 7. Verification Criteria

### 7.1 find()

- [ ] `find(result, source="A")` returns first statement where source.name == "A"
- [ ] `find(result, source="Nonexistent")` returns None
- [ ] `find(result, source="A", target="B")` matches both conditions (AND)
- [ ] `find(result, confidence=0.9)` matches modifier field
- [ ] `find(result, confidence__gt=0.8)` matches with operator
- [ ] `find(result, rule="causal")` matches standard modifier string field
- [ ] `find(result, type="class")` matches custom modifier field
- [ ] `find(result)` with no kwargs returns first statement (vacuous truth)

### 7.2 find_all()

- [ ] `find_all(result, source="A")` returns all matching statements
- [ ] `find_all(result, source="Nonexistent")` returns empty list
- [ ] `find_all(result, confidence__gte=0.5)` returns all with confidence >= 0.5
- [ ] `find_all(result, rule__in=["causal", "logical"])` matches either value

### 7.3 filter_statements()

- [ ] `filter_statements(result, confidence__gt=0.8)` returns new ParseResult
- [ ] Original result is unmodified after filter
- [ ] Filtered result has correct is_valid, empty errors/warnings
- [ ] `filter_statements(result).to_stl()` produces valid STL text

### 7.4 select()

- [ ] `select(result, "source")` returns list of source anchor names
- [ ] `select(result, "target")` returns list of target anchor names
- [ ] `select(result, "confidence")` returns list of confidence values (with None for absent)
- [ ] `select(result, "type")` resolves custom modifier fields

### 7.5 stl_pointer()

- [ ] `stl_pointer(result, "/0/source/name")` returns first statement's source name
- [ ] `stl_pointer(result, "/0/modifiers/confidence")` returns confidence value
- [ ] `stl_pointer(result, "/0/target/namespace")` returns namespace (or None)
- [ ] `stl_pointer(result, "/99/source/name")` raises STLQueryError (index out of range)
- [ ] `stl_pointer(result, "/0/nonexistent")` raises STLQueryError (invalid path)

### 7.6 ParseResult methods

- [ ] `result.find(source="A")` works (delegates to query.find)
- [ ] `result.find_all(rule="causal")` works
- [ ] `result.filter(confidence__gte=0.8)` works
- [ ] `result.select("source")` works
- [ ] `result[0]` returns first Statement
- [ ] `result["A"]` returns list of statements with source "A"
- [ ] `result[1:3]` returns slice of statements

### 7.7 Operator tests

- [ ] `__gt` with float comparison works
- [ ] `__gte` with float comparison works
- [ ] `__lt` with float comparison works
- [ ] `__lte` with float comparison works
- [ ] `__ne` works for string and numeric
- [ ] `__contains` works for substring match
- [ ] `__startswith` works for prefix match
- [ ] `__in` works for membership test
- [ ] Unknown operator raises STLQueryError
- [ ] None field value with `__gt` returns False (not crash)

### 7.8 Edge cases

- [ ] Empty ParseResult (no statements) — all queries return empty/None
- [ ] Statement with no modifiers — modifier field queries return None
- [ ] Chained filter: `result.filter(rule="causal").filter(confidence__gt=0.8)` works
- [ ] Large document (1000+ statements) — no performance regression
