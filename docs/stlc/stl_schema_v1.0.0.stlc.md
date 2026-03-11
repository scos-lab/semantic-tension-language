# STL Schema STLC Specification

> **Version:** 1.0.0
> **Type:** Base
> **Target:** `stl_parser/schema.py`
> **Author:** Syn-claude
> **Date:** 2026-02-11
> **Status:** Draft

---

## 1. Scope Definition

[Schema_Module] -> [Scope] ::mod(
  intent="Schema definition, loading, and validation for STL documents",
  boundaries="Define .stl.schema format, parse schemas, validate ParseResult against schemas, bidirectional Pydantic conversion",
  confidence=0.90
)

**Included:**
- `.stl.schema` file format (Lark grammar)
- `load_schema(filepath_or_text)` loader function
- `STLSchema` Pydantic model representing a parsed schema
- `validate_against_schema(parse_result, schema)` validation function
- `to_pydantic(schema)` → dynamic Pydantic model generation
- `from_pydantic(model_class)` → STLSchema extraction
- Schema constraint types: namespace, field types, ranges, required/optional, cardinality

**Excluded:**
- Text parsing of STL statements (handled by parser.py)
- Statement-level validation (handled by validator.py)
- File I/O beyond schema loading

---

## 2. Architecture Overview

[Schema_File] -> [Schema_Grammar] ::mod(
  rule="definitional",
  intent="Schema files parsed by dedicated Lark grammar into AST"
)

[Schema_Grammar] -> [STLSchema_Model] ::mod(
  rule="causal",
  intent="Grammar parse tree transformed into STLSchema Pydantic model",
  confidence=0.90
)

[STLSchema_Model] -> [Validate_ParseResult] ::mod(
  rule="causal",
  intent="Schema model used to validate ParseResult documents",
  confidence=0.95
)

[STLSchema_Model] -> [Dynamic_Pydantic] ::mod(
  rule="causal",
  intent="Schema can generate dynamic Pydantic models for typed access",
  confidence=0.85
)

---

## 3. Schema File Format (.stl.schema)

### 3.1 Schema Syntax Definition

The `.stl.schema` format uses a declarative syntax for defining constraints on STL documents.

```
schema EventLog v1.0 {
  namespace "Events"

  anchor source {
    namespace: required("Events")
    pattern: /^Event_/
  }

  anchor target {
    namespace: optional
    pattern: /^(Result|State|Action)_/
  }

  modifier {
    required: [confidence, rule, timestamp]
    optional: [source, author, domain, location]

    confidence: float(0.5, 1.0)
    rule: enum("causal", "empirical", "logical")
    timestamp: datetime
    domain: string
  }

  constraints {
    max_chain_length: 5
    allow_cycles: false
    min_statements: 1
    max_statements: 1000
  }
}
```

---

## 4. Computational Flow

### 4.1 Data Models

[SchemaAnchorConstraint] -> [Schema_Model_Component] ::mod(
  rule="definitional",
  type="model",
  schema="SchemaAnchorConstraint(namespace_required: Optional[str], namespace_optional: bool, pattern: Optional[str])",
  confidence=0.90
)

[SchemaModifierConstraint] -> [Schema_Model_Component] ::mod(
  rule="definitional",
  type="model",
  schema="SchemaModifierConstraint(required_fields: List[str], optional_fields: List[str], field_constraints: Dict[str, FieldConstraint])",
  confidence=0.90
)

[FieldConstraint] -> [Schema_Model_Component] ::mod(
  rule="definitional",
  type="model",
  schema="FieldConstraint(type: str, min_value: Optional[float], max_value: Optional[float], enum_values: Optional[List[str]], pattern: Optional[str])",
  confidence=0.90
)

[SchemaConstraints] -> [Schema_Model_Component] ::mod(
  rule="definitional",
  type="model",
  schema="SchemaConstraints(max_chain_length: Optional[int], allow_cycles: Optional[bool], min_statements: Optional[int], max_statements: Optional[int])",
  confidence=0.90
)

[STLSchema] -> [Schema_Top_Level_Model] ::mod(
  rule="definitional",
  type="model",
  schema="STLSchema(name: str, version: str, namespace: Optional[str], source_anchor: SchemaAnchorConstraint, target_anchor: SchemaAnchorConstraint, modifier: SchemaModifierConstraint, constraints: SchemaConstraints)",
  confidence=0.90
)

[SchemaValidationResult] -> [Output_Model] ::mod(
  rule="definitional",
  type="model",
  schema="SchemaValidationResult(is_valid: bool, errors: List[SchemaError], warnings: List[SchemaWarning], schema_name: str, schema_version: str)",
  confidence=0.90
)

### 4.2 Function: load_schema(source) -> STLSchema

[Entry_load_schema] -> [Input_Source] ::mod(
  rule="definitional",
  type="input",
  format="String",
  schema="filepath (str) or raw schema text (str)",
  confidence=1.0
)

[Input_Source] -> [Branch_Is_File] ::mod(
  rule="logical",
  type="branching",
  condition="source ends with '.stl.schema' or file exists at path",
  on_success="Read_File",
  on_fail="Use_Raw_Text",
  confidence=0.95
)

[Branch_Is_File] -> [Read_File] ::mod(
  rule="causal",
  type="transformation",
  intent="Read schema file content",
  input="filepath",
  output="raw_text: str",
  confidence=1.0
)

[Branch_Is_File] -> [Use_Raw_Text] ::mod(
  rule="causal",
  type="transformation",
  input="source",
  output="raw_text: str",
  confidence=1.0
)

[Read_File] -> [Parse_Schema_Grammar] ::mod(
  rule="causal",
  confidence=1.0
)

[Use_Raw_Text] -> [Parse_Schema_Grammar] ::mod(
  rule="causal",
  confidence=1.0
)

[Parse_Schema_Grammar] -> [Lark_Parse] ::mod(
  rule="causal",
  type="transformation",
  intent="Parse schema text using schema-specific Lark grammar",
  input="raw_text",
  output="Lark parse tree",
  algorithm="Lark LALR parser with schema grammar",
  confidence=0.90
)

[Lark_Parse] -> [Branch_Parse_Success] ::mod(
  rule="logical",
  type="branching",
  condition="parse succeeded without errors",
  on_success="Transform_To_Model",
  on_fail="Error_Schema_Parse",
  confidence=0.90
)

[Branch_Parse_Success] -> [Transform_To_Model] ::mod(
  rule="causal",
  type="transformation",
  intent="Transform Lark tree into STLSchema Pydantic model using SchemaTransformer",
  input="Lark parse tree",
  output="STLSchema",
  algorithm="Lark Transformer (same pattern as STLTransformer in parser.py)",
  confidence=0.90
)

[Transform_To_Model] -> [Return_Schema] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="STLSchema",
  confidence=0.95
)

[Return_Schema] -> [Exit_load_schema] ::mod(
  rule="definitional",
  confidence=1.0
)

[Branch_Parse_Success] -> [Error_Schema_Parse] ::mod(
  rule="causal",
  type="output",
  error_type="STLSchemaError",
  error_message="Schema parse failed: {details}",
  confidence=0.90
)

[Error_Schema_Parse] -> [Exit_load_schema_Error] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.3 Function: validate_against_schema(parse_result, schema) -> SchemaValidationResult

[Entry_validate_against_schema] -> [Input_ParseResult] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="models.ParseResult",
  confidence=1.0
)

[Entry_validate_against_schema] -> [Input_Schema] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="STLSchema",
  confidence=1.0
)

[Input_ParseResult] -> [Init_Result] ::mod(
  rule="causal",
  type="transformation",
  output="SchemaValidationResult(is_valid=True, errors=[], warnings=[])",
  confidence=1.0
)

[Input_Schema] -> [Init_Result] ::mod(
  rule="causal",
  confidence=1.0
)

[Init_Result] -> [Check_Document_Constraints] ::mod(
  rule="causal",
  type="validation",
  intent="Validate document-level constraints (min/max statements, cycles)",
  input="parse_result.statements, schema.constraints",
  constraint="Statement count within bounds, cycle policy respected",
  on_success="Loop_Validate_Statements",
  on_fail="Accumulate_Errors",
  confidence=0.90
)

[Check_Document_Constraints] -> [Loop_Validate_Statements] ::mod(
  rule="causal",
  type="loop",
  loop_condition="for each statement in parse_result.statements",
  intent="Validate each statement against schema anchor and modifier constraints",
  confidence=0.95
)

[Loop_Validate_Statements] -> [Validate_Source_Anchor] ::mod(
  rule="causal",
  type="validation",
  intent="Check source anchor against schema.source_anchor constraints",
  constraint="namespace match, name pattern match",
  on_success="Validate_Target_Anchor",
  on_fail="Accumulate_Errors",
  confidence=0.90
)

[Validate_Source_Anchor] -> [Validate_Target_Anchor] ::mod(
  rule="causal",
  type="validation",
  intent="Check target anchor against schema.target_anchor constraints",
  constraint="namespace match, name pattern match",
  on_success="Validate_Modifiers",
  on_fail="Accumulate_Errors",
  confidence=0.90
)

[Validate_Target_Anchor] -> [Validate_Modifiers] ::mod(
  rule="causal",
  type="validation",
  intent="Check modifier fields against schema.modifier constraints",
  constraint="Required fields present, field types match, values in range/enum",
  on_success="Continue_Loop",
  on_fail="Accumulate_Errors",
  confidence=0.90
)

[Validate_Modifiers] -> [Validate_Required_Fields] ::mod(
  rule="causal",
  type="validation",
  intent="Check all required modifier fields are present and non-None",
  input="statement.modifiers, schema.modifier.required_fields",
  constraint="All required fields must have non-None values",
  on_fail="Accumulate_Errors",
  confidence=0.95
)

[Validate_Required_Fields] -> [Validate_Field_Types] ::mod(
  rule="causal",
  type="validation",
  intent="Check each present field matches its declared type constraint",
  input="modifier field values, schema.modifier.field_constraints",
  algorithm="For each field: check type (float, string, enum, datetime), check range (min/max), check enum membership, check pattern",
  on_fail="Accumulate_Errors",
  confidence=0.90
)

[Validate_Field_Types] -> [Continue_Loop] ::mod(
  rule="causal",
  confidence=1.0
)

[Continue_Loop] -> [Loop_Validate_Statements] ::mod(
  rule="causal",
  type="loop",
  intent="Continue to next statement",
  confidence=1.0
)

[Accumulate_Errors] -> [Continue_Loop] ::mod(
  rule="causal",
  intent="Errors accumulated but validation continues for all statements",
  confidence=1.0
)

[Loop_Validate_Statements] -> [Build_Result] ::mod(
  rule="causal",
  type="transformation",
  intent="Compile accumulated errors/warnings into SchemaValidationResult",
  output="SchemaValidationResult(is_valid=len(errors)==0, errors=errors, warnings=warnings)",
  confidence=0.95
)

[Build_Result] -> [Return_Result] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="SchemaValidationResult",
  confidence=1.0
)

[Return_Result] -> [Exit_validate_against_schema] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.4 Function: to_pydantic(schema) -> Type[BaseModel]

[Entry_to_pydantic] -> [Input_Schema] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="STLSchema",
  confidence=1.0
)

[Input_Schema] -> [Build_Field_Definitions] ::mod(
  rule="causal",
  type="transformation",
  intent="Convert schema field constraints to Pydantic Field definitions",
  input="schema.modifier.field_constraints",
  output="Dict[str, Tuple[type, FieldInfo]]",
  algorithm="Map schema types to Python types: float→float, string→str, enum→Literal[...], datetime→str with validator. Apply ge/le for ranges.",
  confidence=0.85
)

[Build_Field_Definitions] -> [Create_Dynamic_Model] ::mod(
  rule="causal",
  type="transformation",
  intent="Use pydantic.create_model() to generate dynamic model class",
  input="field_definitions, schema.name",
  output="Type[BaseModel]",
  algorithm="pydantic.create_model(schema.name + 'Modifier', **field_definitions)",
  confidence=0.85
)

[Create_Dynamic_Model] -> [Return_Model_Class] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="Type[BaseModel] (dynamic Pydantic model class)",
  confidence=0.85
)

[Return_Model_Class] -> [Exit_to_pydantic] ::mod(
  rule="definitional",
  confidence=1.0
)

### 4.5 Function: from_pydantic(model_class) -> STLSchema

[Entry_from_pydantic] -> [Input_Model_Class] ::mod(
  rule="definitional",
  type="input",
  format="Object",
  schema="Type[BaseModel]",
  confidence=1.0
)

[Input_Model_Class] -> [Introspect_Fields] ::mod(
  rule="causal",
  type="transformation",
  intent="Extract field names, types, constraints from Pydantic model_fields",
  input="model_class.model_fields",
  output="Dict[str, FieldConstraint]",
  algorithm="For each field: infer schema type from annotation (float→float, str→string, Literal→enum), extract ge/le from Field kwargs",
  confidence=0.85
)

[Introspect_Fields] -> [Classify_Required_Optional] ::mod(
  rule="causal",
  type="transformation",
  intent="Separate fields into required vs optional based on default values",
  input="model_fields",
  output="{required_fields: List[str], optional_fields: List[str]}",
  algorithm="Fields with no default and not Optional → required; others → optional",
  confidence=0.90
)

[Classify_Required_Optional] -> [Build_Schema] ::mod(
  rule="causal",
  type="transformation",
  intent="Construct STLSchema from extracted field info",
  output="STLSchema",
  confidence=0.85
)

[Build_Schema] -> [Return_Schema] ::mod(
  rule="definitional",
  type="output",
  format="Object",
  schema="STLSchema",
  confidence=0.85
)

[Return_Schema] -> [Exit_from_pydantic] ::mod(
  rule="definitional",
  confidence=1.0
)

---

## 5. Schema Grammar (Lark EBNF)

[Schema_Grammar] -> [Grammar_Definition] ::mod(
  rule="definitional",
  intent="Lark grammar for .stl.schema format",
  confidence=0.90,
  algorithm="LALR parser, same pattern as grammar.py"
)

The schema grammar will be defined as a separate Lark grammar string within schema.py, following the same pattern used by `grammar.py` for the main STL grammar. Key grammar rules:

- `schema_def`: `"schema" NAME VERSION "{" schema_body "}"`
- `schema_body`: `(namespace_decl | anchor_block | modifier_block | constraints_block)*`
- `anchor_block`: `"anchor" ("source"|"target") "{" anchor_rules "}"`
- `modifier_block`: `"modifier" "{" modifier_rules "}"`
- `constraints_block`: `"constraints" "{" constraint_rules "}"`
- `field_type`: `"float" "(" MIN "," MAX ")"` | `"enum" "(" values ")"` | `"string"` | `"datetime"` | `"boolean"` | `"integer"`

---

## 6. Dependencies (Reuse, Not Duplicate)

| Dependency | Module | Purpose |
|------------|--------|---------|
| `Anchor` | `models.py` | Anchor model for constraint checking |
| `Modifier` | `models.py` | Modifier model_fields for field introspection |
| `Statement` | `models.py` | Statement model for validation loop |
| `ParseResult` | `models.py` | Document-level validation target |
| `ParseError` | `models.py` | Error reporting format |
| `STLSchemaError` | `errors.py` | Schema-specific exceptions |
| `ErrorCode.E600-E603` | `errors.py` | Schema error codes |
| `Lark` | `lark` (external) | Schema grammar parsing |
| `pydantic.create_model` | `pydantic` (external) | Dynamic model generation |

---

## 7. Verification Criteria

- [ ] `load_schema("events.stl.schema")` returns valid STLSchema
- [ ] `load_schema(raw_text)` parses inline schema text
- [ ] Invalid schema syntax raises STLSchemaError(E600)
- [ ] `validate_against_schema(result, schema)` returns SchemaValidationResult
- [ ] Missing required modifier fields detected (E601)
- [ ] Out-of-range values detected (E603)
- [ ] Enum constraint violations detected (E603)
- [ ] Anchor namespace mismatch detected (E601)
- [ ] Anchor pattern mismatch detected (E601)
- [ ] Document-level constraints (min/max statements) enforced
- [ ] `to_pydantic(schema)` returns dynamic BaseModel subclass
- [ ] `from_pydantic(DynamicModel)` roundtrips to equivalent STLSchema
- [ ] Schema with all constraint types parses and validates correctly
