# STL Builder STLC Specification

> **Version:** 1.0.0
> **Type:** Base
> **Target:** `stl_parser/builder.py`
> **Author:** Syn-claude
> **Date:** 2026-02-11
> **Status:** Draft

---

## 1. Scope Definition

[Builder_Module] -> [Scope] ::mod(
  intent="Programmatic STL statement construction via fluent API",
  boundaries="Build Statement/ParseResult objects without parsing text",
  confidence=0.95
)

**Included:**
- `stl(source, target)` factory function
- `StatementBuilder` fluent builder class
- `stl_doc(*builders)` batch document builder
- Anchor string parsing (brackets, namespaces)
- Modifier accumulation and separation (standard vs custom)
- Build-time validation via existing `validator.validate_statement()`

**Excluded:**
- Text parsing (handled by parser.py)
- Serialization (handled by serializer.py)
- File I/O

---

## 2. Architecture Overview

[Factory_stl] -> [StatementBuilder] ::mod(
  rule="definitional",
  intent="Factory creates builder, builder accumulates state, build() produces Statement"
)

[StatementBuilder] -> [Statement_Model] ::mod(
  rule="causal",
  intent="Builder compiles accumulated state into existing Pydantic model",
  confidence=0.95
)

[Factory_stl_doc] -> [ParseResult_Model] ::mod(
  rule="causal",
  intent="Batch factory builds multiple statements into ParseResult",
  confidence=0.95
)

---

## 3. Computational Flow

### 3.1 Function: stl(source, target) -> StatementBuilder

[Entry_stl_factory] -> [Input_Source_String] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="anchor string: '[Obs:X]' | 'Obs:X' | '[X]' | 'X'",
  confidence=1.0
)

[Entry_stl_factory] -> [Input_Target_String] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="anchor string: same formats as source",
  confidence=1.0
)

[Input_Source_String] -> [Parse_Anchor_Source] ::mod(
  rule="causal",
  type="transformation",
  intent="Parse anchor string into Anchor model",
  input="source_str",
  output="Anchor",
  confidence=0.95
)

[Input_Target_String] -> [Parse_Anchor_Target] ::mod(
  rule="causal",
  type="transformation",
  input="target_str",
  output="Anchor",
  confidence=0.95
)

[Parse_Anchor_Source] -> [Create_Builder] ::mod(
  rule="causal",
  type="transformation",
  output="StatementBuilder",
  confidence=1.0
)

[Parse_Anchor_Target] -> [Create_Builder] ::mod(
  rule="causal",
  confidence=1.0
)

[Create_Builder] -> [Return_Builder] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="StatementBuilder",
  confidence=1.0
)

[Return_Builder] -> [Exit_stl_factory] ::mod(
  rule="definitional",
  confidence=1.0
)

### 3.2 Function: _parse_anchor_str(s) -> Anchor

[Entry_Parse_Anchor] -> [Input_Anchor_String] ::mod(
  rule="definitional",
  type="input",
  format="String",
  confidence=1.0
)

[Input_Anchor_String] -> [Strip_Brackets] ::mod(
  rule="causal",
  type="transformation",
  intent="Remove surrounding [] if present",
  input="raw_str",
  output="stripped_str",
  confidence=1.0
)

[Strip_Brackets] -> [Branch_Has_Namespace] ::mod(
  rule="logical",
  type="branching",
  condition="':' in stripped_str",
  on_success="Split_Namespace",
  on_fail="Create_Simple_Anchor",
  confidence=0.95
)

[Branch_Has_Namespace] -> [Split_Namespace] ::mod(
  rule="causal",
  type="transformation",
  intent="Split on first ':' to get namespace and name",
  input="stripped_str",
  output="{namespace, name}",
  confidence=0.95
)

[Split_Namespace] -> [Create_Namespaced_Anchor] ::mod(
  rule="causal",
  type="transformation",
  output="Anchor(name=name, namespace=namespace)",
  confidence=0.95,
  intent="Reuses existing models.Anchor with Pydantic validation"
)

[Branch_Has_Namespace] -> [Create_Simple_Anchor] ::mod(
  rule="causal",
  type="transformation",
  output="Anchor(name=stripped_str)",
  confidence=1.0
)

[Create_Namespaced_Anchor] -> [Return_Anchor] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="models.Anchor",
  confidence=1.0
)

[Create_Simple_Anchor] -> [Return_Anchor] ::mod(
  rule="definitional",
  confidence=1.0
)

[Return_Anchor] -> [Exit_Parse_Anchor] ::mod(
  rule="definitional",
  confidence=1.0
)

### 3.3 Method: .mod(**kwargs) -> StatementBuilder

[Entry_Mod] -> [Input_Kwargs] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Dict[str, Any]",
  confidence=1.0
)

[Input_Kwargs] -> [Accumulate_Modifiers] ::mod(
  rule="causal",
  type="transformation",
  intent="Merge kwargs into internal modifier dict (later calls override earlier)",
  input="self._modifiers + kwargs",
  output="self._modifiers (updated)",
  deterministic=true,
  confidence=1.0
)

[Accumulate_Modifiers] -> [Return_Self] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="StatementBuilder (self)",
  intent="Enable method chaining: .mod(a=1).mod(b=2)",
  confidence=1.0
)

[Return_Self] -> [Exit_Mod] ::mod(
  rule="definitional",
  confidence=1.0
)

### 3.4 Method: .build() -> Statement

[Entry_Build] -> [Separate_Standard_Custom] ::mod(
  rule="causal",
  type="transformation",
  intent="Split accumulated kwargs into standard Modifier fields vs custom fields",
  input="self._modifiers",
  output="{standard_fields: Dict, custom_fields: Dict}",
  confidence=0.90,
  algorithm="Check each key against Modifier model_fields"
)

[Separate_Standard_Custom] -> [Create_Modifier] ::mod(
  rule="causal",
  type="transformation",
  intent="Construct Modifier object from standard fields + custom dict",
  input="{standard_fields, custom_fields}",
  output="Modifier(**standard_fields, custom=custom_fields)",
  confidence=0.95,
  intent="Reuses existing models.Modifier with Pydantic validation"
)

[Create_Modifier] -> [Create_Statement] ::mod(
  rule="causal",
  type="transformation",
  input="{self._source, self._target, modifier}",
  output="Statement(source=..., target=..., modifiers=...)",
  confidence=0.95
)

[Create_Statement] -> [Branch_Should_Validate] ::mod(
  rule="logical",
  type="branching",
  condition="self._validate is True",
  on_success="Validate_Statement",
  on_fail="Return_Statement",
  confidence=1.0
)

[Branch_Should_Validate] -> [Validate_Statement] ::mod(
  rule="causal",
  type="validation",
  intent="Validate built statement using existing validator.validate_statement()",
  constraint="All Pydantic + semantic validations must pass",
  on_success="Return_Statement",
  on_fail="Error_Validation_Failed",
  confidence=0.90
)

[Validate_Statement] -> [Return_Statement] ::mod(
  rule="causal",
  type="output",
  format="Object",
  schema="models.Statement",
  confidence=0.95
)

[Branch_Should_Validate] -> [Return_Statement] ::mod(
  rule="causal",
  confidence=1.0
)

[Return_Statement] -> [Exit_Build] ::mod(
  rule="definitional",
  confidence=1.0
)

[Validate_Statement] -> [Error_Validation_Failed] ::mod(
  rule="causal",
  type="output",
  error_type="STLBuilderError",
  error_message="Builder validation failed: {details}",
  confidence=0.90
)

[Error_Validation_Failed] -> [Exit_Build_Error] ::mod(
  rule="definitional",
  confidence=1.0
)

### 3.5 Function: stl_doc(*builders) -> ParseResult

[Entry_stl_doc] -> [Input_Builders] ::mod(
  rule="definitional",
  type="input",
  format="Array",
  schema="List[StatementBuilder | Statement]",
  confidence=1.0
)

[Input_Builders] -> [Loop_Build_Each] ::mod(
  rule="causal",
  type="loop",
  loop_condition="for each builder in builders",
  intent="Build each builder if not already a Statement",
  confidence=0.95
)

[Loop_Build_Each] -> [Branch_Is_Builder] ::mod(
  rule="logical",
  type="branching",
  condition="isinstance(item, StatementBuilder)",
  on_success="Call_Build",
  on_fail="Use_Statement_Directly",
  confidence=1.0
)

[Branch_Is_Builder] -> [Call_Build] ::mod(
  rule="causal",
  type="transformation",
  input="builder",
  output="Statement",
  confidence=0.95
)

[Branch_Is_Builder] -> [Use_Statement_Directly] ::mod(
  rule="causal",
  confidence=1.0
)

[Call_Build] -> [Collect_Statements] ::mod(
  rule="causal",
  type="aggregation",
  input="Statement",
  output="List[Statement]",
  confidence=1.0
)

[Use_Statement_Directly] -> [Collect_Statements] ::mod(
  rule="causal",
  confidence=1.0
)

[Collect_Statements] -> [Create_ParseResult] ::mod(
  rule="causal",
  type="transformation",
  output="ParseResult(statements=collected, is_valid=True)",
  confidence=0.95
)

[Create_ParseResult] -> [Return_ParseResult] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="models.ParseResult",
  confidence=1.0
)

[Return_ParseResult] -> [Exit_stl_doc] ::mod(
  rule="definitional",
  confidence=1.0
)

---

## 4. Dependencies (Reuse, Not Duplicate)

| Dependency | Module | Purpose |
|------------|--------|---------|
| `Anchor` | `models.py` | Anchor data model |
| `Modifier` | `models.py` | Modifier data model with 30+ fields |
| `Statement` | `models.py` | Statement data model |
| `ParseResult` | `models.py` | Multi-statement container |
| `validate_statement()` | `validator.py` | Statement validation |
| `to_stl()` | `serializer.py` | Statement.__str__ already handles this |
| `STLBuilderError` | `errors.py` | Error class (E500-E599) |

---

## 5. Verification Criteria

- [ ] `stl("[A]", "[B]").build()` returns valid Statement
- [ ] `stl("Obs:X", "Act:Y")` parses namespace correctly
- [ ] `stl("[A]", "[B]").mod(confidence=0.9).mod(rule="causal").build()` accumulates modifiers
- [ ] Non-standard modifier keys go to `modifier.custom` dict
- [ ] `confidence=2.0` raises STLBuilderError (Pydantic validation)
- [ ] `.no_validate().build()` skips validation
- [ ] `stl_doc(stl("[A]", "[B]"), stl("[C]", "[D]"))` returns ParseResult with 2 statements
- [ ] Roundtrip: `build() -> str(stmt) -> parse() -> compare` preserves semantics
- [ ] `stl("A", "B")` and `stl("[A]", "[B]")` produce identical results
