# STL LLM STLC Specification

> **Version:** 1.0.0
> **Type:** Base
> **Target:** `stl_parser/llm.py`
> **Author:** Syn-claude
> **Date:** 2026-02-11
> **Status:** Draft

---

## 1. Scope Definition

[LLM_Module] -> [Scope] ::mod(
  intent="Clean, repair, and validate raw LLM-generated STL output",
  boundaries="Text cleaning, auto-repair, validation pipeline, prompt template generation",
  confidence=0.90
)

**Included:**
- `clean(raw_text)` — strip markdown fences, normalize arrows, fix whitespace
- `repair(text)` — fix common LLM mistakes (brackets, quoting, clamping)
- `validate_llm_output(raw_text, schema=None)` — full pipeline: clean → repair → parse → validate
- `prompt_template(schema=None)` — generate STL teaching prompt for LLMs
- `RepairAction` model to track all repairs applied
- `LLMValidationResult` model extending ParseResult with repair metadata

**Excluded:**
- Schema definition (handled by schema.py)
- Statement-level parsing (handled by parser.py)
- Builder API (handled by builder.py)

---

## 2. Architecture Overview

[Raw_LLM_Text] -> [Clean_Stage] ::mod(
  rule="causal",
  intent="Remove non-STL artifacts (markdown, code fences, prose)",
  confidence=0.95
)

[Clean_Stage] -> [Repair_Stage] ::mod(
  rule="causal",
  intent="Fix common structural errors in STL syntax",
  confidence=0.90
)

[Repair_Stage] -> [Parse_Stage] ::mod(
  rule="causal",
  intent="Parse cleaned+repaired text using existing parser.parse()",
  confidence=0.95
)

[Parse_Stage] -> [Schema_Validate_Stage] ::mod(
  rule="logical",
  type="branching",
  condition="schema is not None",
  intent="Optional schema validation after parsing",
  confidence=0.90
)

---

## 3. Data Models

[RepairAction] -> [Model_Definition] ::mod(
  rule="definitional",
  type="model",
  schema="RepairAction(type: str, line: Optional[int], original: str, repaired: str, description: str)",
  intent="Records each individual repair applied to the text",
  confidence=0.95
)

[LLMValidationResult] -> [Model_Definition] ::mod(
  rule="definitional",
  type="model",
  schema="LLMValidationResult(statements: List[Statement], errors: List[ParseError], warnings: List[ParseWarning], is_valid: bool, repairs: List[RepairAction], cleaned_text: str, original_text: str, schema_result: Optional[SchemaValidationResult])",
  intent="Extends ParseResult concept with LLM-specific metadata",
  confidence=0.90
)

---

## 4. Computational Flow

### 4.1 Function: clean(raw_text) -> Tuple[str, List[RepairAction]]

[Entry_clean] -> [Input_Raw_Text] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="Raw LLM output text (may contain markdown, prose, malformed STL)",
  confidence=1.0
)

[Input_Raw_Text] -> [Strip_Code_Fences] ::mod(
  rule="causal",
  type="transformation",
  intent="Extract STL from ```stl ... ``` or ``` ... ``` blocks if present",
  input="raw_text",
  output="text with fences removed",
  algorithm="Reuse _utils.extract_stl_fences() if fences detected, otherwise pass through",
  confidence=0.95
)

[Strip_Code_Fences] -> [Normalize_Arrows] ::mod(
  rule="causal",
  type="transformation",
  intent="Normalize arrow variants to standard → or ->",
  input="text",
  output="text with normalized arrows",
  algorithm="Replace common LLM arrow variants: '—>', '=>', '- >', '→' (fullwidth), '➜', '➡' with '->'",
  confidence=0.95
)

[Normalize_Arrows] -> [Fix_Whitespace] ::mod(
  rule="causal",
  type="transformation",
  intent="Normalize whitespace issues",
  input="text",
  output="text with fixed whitespace",
  algorithm="Collapse multiple spaces to single, strip trailing whitespace per line, normalize line endings to \\n",
  confidence=0.95
)

[Fix_Whitespace] -> [Merge_Multiline] ::mod(
  rule="causal",
  type="transformation",
  intent="Merge multi-line statements into single lines",
  input="text",
  output="text with merged statements",
  algorithm="Reuse _utils.merge_multiline_statements()",
  confidence=0.95
)

[Merge_Multiline] -> [Strip_Prose_Lines] ::mod(
  rule="causal",
  type="transformation",
  intent="Remove lines that are clearly not STL (natural language prose)",
  input="text",
  output="text with only STL-like lines",
  algorithm="Use _utils.is_stl_line() on each line; keep lines detected as STL or comments; discard natural language and markdown lines",
  confidence=0.90
)

[Strip_Prose_Lines] -> [Return_Cleaned] ::mod(
  rule="definitional",
  type="output",
  format="Tuple",
  schema="(cleaned_text: str, repairs: List[RepairAction])",
  intent="Return cleaned text and list of cleaning actions taken",
  confidence=0.95
)

[Return_Cleaned] -> [Exit_clean] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.2 Function: repair(text) -> Tuple[str, List[RepairAction]]

[Entry_repair] -> [Input_Cleaned_Text] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="Cleaned STL text (may still have structural errors)",
  confidence=1.0
)

[Input_Cleaned_Text] -> [Fix_Missing_Brackets] ::mod(
  rule="causal",
  type="transformation",
  intent="Add missing brackets around anchor names",
  input="text",
  output="text with brackets fixed",
  algorithm="Detect patterns like 'AnchorName -> [Target]' or '[Source] -> AnchorName' and wrap bare anchors in brackets. Use regex: line starts with word chars followed by space+arrow, or arrow followed by space+word chars without brackets.",
  confidence=0.85
)

[Fix_Missing_Brackets] -> [Fix_Unquoted_Strings] ::mod(
  rule="causal",
  type="transformation",
  intent="Quote unquoted string values in modifiers",
  input="text",
  output="text with string values quoted",
  algorithm="Inside ::mod(...), find key=value pairs where value is not quoted, not numeric, not boolean. Wrap in quotes. Regex: within ::mod() context, match key=([A-Za-z_][\\w]*) that is not true/false/number.",
  confidence=0.85
)

[Fix_Unquoted_Strings] -> [Fix_Modifier_Prefix] ::mod(
  rule="causal",
  type="transformation",
  intent="Fix missing :: prefix on mod()",
  input="text",
  output="text with ::mod() prefix fixed",
  algorithm="Replace 'mod(' not preceded by '::' with '::mod('. Careful not to match inside strings.",
  confidence=0.90
)

[Fix_Modifier_Prefix] -> [Clamp_Numeric_Values] ::mod(
  rule="causal",
  type="transformation",
  intent="Clamp out-of-range numeric values to valid ranges",
  input="text",
  output="text with clamped values",
  algorithm="For known [0.0, 1.0] fields (confidence, certainty, strength, intensity), detect values >1.0 or <0.0 and clamp. Record as RepairAction.",
  confidence=0.85
)

[Clamp_Numeric_Values] -> [Fix_Common_Typos] ::mod(
  rule="causal",
  type="transformation",
  intent="Fix common LLM typos in modifier keys",
  input="text",
  output="text with typos fixed",
  algorithm="Map common typos: 'confience'→'confidence', 'strenght'→'strength', 'timestap'→'timestamp', 'authro'→'author', 'soruce'→'source'. Only within ::mod() context.",
  confidence=0.80
)

[Fix_Common_Typos] -> [Return_Repaired] ::mod(
  rule="definitional",
  type="output",
  format="Tuple",
  schema="(repaired_text: str, repairs: List[RepairAction])",
  confidence=0.90
)

[Return_Repaired] -> [Exit_repair] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.3 Function: validate_llm_output(raw_text, schema=None) -> LLMValidationResult

[Entry_validate_llm_output] -> [Input_Raw_Text] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="Raw LLM output text",
  confidence=1.0
)

[Entry_validate_llm_output] -> [Input_Schema] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Optional[STLSchema]",
  confidence=1.0
)

[Input_Raw_Text] -> [Call_Clean] ::mod(
  rule="causal",
  type="transformation",
  intent="Apply clean() pipeline",
  input="raw_text",
  output="(cleaned_text, clean_repairs)",
  confidence=0.95
)

[Call_Clean] -> [Call_Repair] ::mod(
  rule="causal",
  type="transformation",
  intent="Apply repair() pipeline on cleaned text",
  input="cleaned_text",
  output="(repaired_text, repair_repairs)",
  confidence=0.90
)

[Call_Repair] -> [Call_Parse] ::mod(
  rule="causal",
  type="transformation",
  intent="Parse repaired text using existing parser.parse()",
  input="repaired_text",
  output="ParseResult",
  algorithm="parser.parse(repaired_text)",
  confidence=0.95
)

[Call_Parse] -> [Branch_Has_Schema] ::mod(
  rule="logical",
  type="branching",
  condition="schema is not None",
  on_success="Call_Schema_Validate",
  on_fail="Build_LLM_Result",
  confidence=1.0
)

[Branch_Has_Schema] -> [Call_Schema_Validate] ::mod(
  rule="causal",
  type="transformation",
  intent="Validate parse result against provided schema",
  input="parse_result, schema",
  output="SchemaValidationResult",
  algorithm="schema.validate_against_schema(parse_result, schema)",
  confidence=0.90
)

[Call_Schema_Validate] -> [Build_LLM_Result] ::mod(
  rule="causal",
  confidence=1.0
)

[Branch_Has_Schema] -> [Build_LLM_Result] ::mod(
  rule="causal",
  confidence=1.0
)

[Build_LLM_Result] -> [Compile_Result] ::mod(
  rule="causal",
  type="transformation",
  intent="Assemble LLMValidationResult from all pipeline stages",
  input="{parse_result, all_repairs, cleaned_text, raw_text, schema_result}",
  output="LLMValidationResult",
  algorithm="Merge clean_repairs + repair_repairs into repairs list. Copy statements/errors/warnings from parse_result. Attach schema_result if present.",
  confidence=0.95
)

[Compile_Result] -> [Return_LLM_Result] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="LLMValidationResult",
  confidence=0.95
)

[Return_LLM_Result] -> [Exit_validate_llm_output] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.4 Function: prompt_template(schema=None) -> str

[Entry_prompt_template] -> [Input_Schema] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Optional[STLSchema]",
  confidence=1.0
)

[Input_Schema] -> [Build_Base_Template] ::mod(
  rule="causal",
  type="transformation",
  intent="Construct base STL syntax instruction template",
  output="base_template: str",
  algorithm="Static template covering: basic syntax, anchor format, arrow format, modifier syntax, value types. Based on STL Operational Protocol quick reference.",
  confidence=0.95
)

[Build_Base_Template] -> [Branch_Has_Schema] ::mod(
  rule="logical",
  type="branching",
  condition="schema is not None",
  on_success="Append_Schema_Constraints",
  on_fail="Return_Template",
  confidence=1.0
)

[Branch_Has_Schema] -> [Append_Schema_Constraints] ::mod(
  rule="causal",
  type="transformation",
  intent="Append schema-specific constraints to template",
  input="schema, base_template",
  output="enriched_template: str",
  algorithm="Add: required fields, allowed values for enum fields, valid ranges for numeric fields, namespace requirements, anchor patterns. Format as structured instructions.",
  confidence=0.85
)

[Append_Schema_Constraints] -> [Return_Template] ::mod(
  rule="causal",
  confidence=1.0
)

[Branch_Has_Schema] -> [Return_Template] ::mod(
  rule="causal",
  confidence=1.0
)

[Return_Template] -> [Output_Template] ::mod(
  rule="definitional",
  type="output",
  format="String",
  schema="Prompt template text suitable for LLM system/user message",
  confidence=0.95
)

[Output_Template] -> [Exit_prompt_template] ::mod(
  rule="definitional",
  confidence=1.0
)

---

## 5. Repair Type Taxonomy

[RepairType_Taxonomy] -> [Repair_Types] ::mod(
  rule="definitional",
  intent="Enumeration of all repair action types",
  confidence=0.90
)

| Repair Type | Description | Example |
|-------------|-------------|---------|
| `strip_fence` | Removed markdown code fence | ````stl` → (removed) |
| `normalize_arrow` | Replaced non-standard arrow | `=>` → `->` |
| `fix_whitespace` | Fixed whitespace issue | Multiple spaces → single |
| `merge_multiline` | Merged multi-line statement | 3 lines → 1 line |
| `strip_prose` | Removed non-STL line | "Here is the output:" → (removed) |
| `add_brackets` | Added missing brackets | `A -> [B]` → `[A] -> [B]` |
| `quote_string` | Quoted unquoted string value | `rule=causal` → `rule="causal"` |
| `fix_mod_prefix` | Added :: prefix to mod() | `mod(...)` → `::mod(...)` |
| `clamp_value` | Clamped out-of-range value | `confidence=1.5` → `confidence=1.0` |
| `fix_typo` | Fixed modifier key typo | `confience` → `confidence` |

---

## 6. Dependencies (Reuse, Not Duplicate)

| Dependency | Module | Purpose |
|------------|--------|---------|
| `parse()` | `parser.py` | Core STL parsing |
| `is_stl_line()` | `_utils.py` | Line-level STL detection |
| `extract_stl_fences()` | `_utils.py` | Code fence extraction |
| `merge_multiline_statements()` | `_utils.py` | Multi-line merging |
| `Statement` | `models.py` | Statement model |
| `ParseResult` | `models.py` | Parse result container |
| `ParseError` | `models.py` | Error model |
| `ParseWarning` | `models.py` | Warning model |
| `validate_against_schema()` | `schema.py` | Optional schema validation |
| `STLSchema` | `schema.py` | Schema model (optional input) |
| `STLLLMError` | `errors.py` | LLM-specific exceptions |
| `ErrorCode.E700-E702` | `errors.py` | LLM error codes |

---

## 7. Verification Criteria

- [ ] `clean("```stl\n[A] -> [B]\n```")` extracts STL from fences
- [ ] `clean("Here is STL:\n[A] -> [B]")` strips prose line
- [ ] `clean("[A] => [B]")` normalizes arrow to `->`
- [ ] `repair("A -> [B]")` adds brackets → `[A] -> [B]`
- [ ] `repair('[A] -> [B] ::mod(rule=causal)')` quotes string → `rule="causal"`
- [ ] `repair('[A] -> [B] mod(confidence=0.9)')` fixes prefix → `::mod(...)`
- [ ] `repair('[A] -> [B] ::mod(confidence=1.5)')` clamps → `confidence=1.0`
- [ ] `validate_llm_output(raw_text)` returns LLMValidationResult with repairs list
- [ ] `validate_llm_output(raw_text, schema=schema)` includes SchemaValidationResult
- [ ] `prompt_template()` returns valid instruction text with STL syntax guide
- [ ] `prompt_template(schema)` appends schema-specific constraints
- [ ] All RepairActions have type, original, repaired, and description fields
- [ ] Roundtrip: LLM output → clean → repair → parse → str(stmt) preserves semantics
