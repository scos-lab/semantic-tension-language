# Error Code Reference

Complete reference for all STL parser error codes (E001-E962) and warning codes (W001-W009).

**Module:** `stl_parser.errors`
**Import:** `from stl_parser.errors import ErrorCode, WarningCode, STLParseError, STLValidationError`

---

## Error Code Ranges

| Range | Category | Exception Class |
|-------|----------|-----------------|
| E001-E011 | Parse errors | `STLParseError` |
| E100-E115 | Validation errors | `STLValidationError` |
| E200-E207 | Serialization errors | `STLSerializationError` |
| E300-E304 | Graph errors | `STLGraphError` |
| E400-E404 | File I/O errors | `STLFileError` |
| E450-E453 | Query errors | `STLQueryError` |
| E500-E502 | Builder errors | `STLBuilderError` |
| E600-E603 | Schema errors | `STLSchemaError` |
| E700-E702 | LLM errors | `STLLLMError` |
| E800-E801 | Emitter errors | `STLEmitterError` |
| E900-E901 | Decay errors | `STLDecayError` |
| E950-E953 | Diff/Patch errors | `STLDiffError` |
| E960-E962 | Reader errors | `STLReaderError` |
| W001-W009 | Warnings | `STLWarning` |

All exception classes inherit from `STLError`, which inherits from `Exception`.

---

## Parse Errors (E001-E011)

Raised during lexing and parsing of STL text.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E001 | Unexpected token | Parser encountered a token it didn't expect | Check syntax near the reported position |
| E002 | Invalid syntax | General syntax error | Verify statement follows `[A] -> [B] ::mod(...)` pattern |
| E003 | Auto-extraction detected syntax errors | Auto-extraction mode found unparseable content | Review the input text for non-STL content |
| E004 | Unclosed bracket | `[Anchor` without closing `]` | Add closing bracket: `[Anchor]` |
| E005 | Invalid arrow syntax | Arrow is malformed | Use `->` or `→` between anchors |
| E006 | Invalid modifier syntax | `::mod(...)` block is malformed | Check parentheses, commas, and key=value pairs |
| E007 | Malformed namespace | Namespace syntax is invalid | Use `Namespace:Name` or `A.B:Name` format |
| E008 | Invalid string value | String literal is malformed | Ensure strings are properly quoted: `"value"` |
| E009 | Invalid number format | Numeric literal can't be parsed | Use standard number format: `0.85`, `42` |
| E010 | Invalid datetime format | DateTime doesn't match ISO 8601 | Use `"2025-01-15"` or `"2025-01-15T10:00:00Z"` |
| E011 | Unexpected end of file | Input ends mid-statement | Complete the statement or remove trailing arrow |

**Example:**

```python
from stl_parser import parse

try:
    result = parse('[Unclosed -> [B]')
except Exception as e:
    print(e)  # E004: Unclosed bracket
```

---

## Validation Errors (E100-E115)

Raised during semantic validation of parsed statements.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E100 | Invalid anchor name | Anchor contains invalid characters | Use only letters, digits, underscores |
| E101 | Reserved name used | Anchor uses a reserved name (NULL, NONE, etc.) | Choose a different name |
| E102 | Anchor name too long | Name exceeds 64 characters | Shorten the anchor name |
| E103 | Invalid namespace format | Namespace contains invalid characters | Use letters, digits, underscores, dots |
| E104 | Invalid modifier key | Modifier key is not a valid identifier | Use alphanumeric keys with underscores |
| E105 | Invalid modifier value type | Value type doesn't match expected type | Check the modifier reference for correct types |
| E106 | Confidence value out of range | `confidence` or `certainty` is not in [0.0, 1.0] | Use a value between 0.0 and 1.0 |
| E107 | Invalid rule type | `rule` value is not recognized | Use `"causal"`, `"logical"`, `"empirical"`, `"definitional"`, or `"correlative"` |
| E108 | Invalid anchor type | Anchor type is not one of the 9 canonical types | Use a valid AnchorType value |
| E109 | Invalid path type | Path type is not recognized | Use a valid PathType value |
| E110 | Missing required modifier | A required modifier is absent | Add the required modifier field |
| E111 | Conflicting modifiers | Two modifiers contradict each other | Remove one (e.g., `time="Past"` + `tense="Future"`) |
| E112 | Invalid datetime format | Modifier datetime value is malformed | Use ISO 8601: `"2025-01-15T10:00:00Z"` |
| E113 | Semantic inconsistency | Statement is semantically inconsistent | Review modifier combinations |
| E114 | Circular reference detected | Statement graph contains unexpected cycle | Break the cycle or mark as intentional |
| E115 | Dangling reference | Anchor referenced but never defined as source or target | Connect the anchor or remove the reference |

---

## Serialization Errors (E200-E207)

Raised during JSON/RDF/dict serialization and deserialization.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E200 | Serialization failed | General serialization error | Check the ParseResult structure |
| E201 | Invalid JSON format | JSON string is malformed | Validate the JSON syntax |
| E202 | Invalid JSON-LD format | JSON-LD structure is invalid | Check `@context` and `@type` fields |
| E203 | Invalid RDF format | RDF serialization failed | Verify RDF format parameter (`"turtle"`, `"xml"`, `"nt"`, `"json-ld"`) |
| E204 | Deserialization failed | Cannot reconstruct ParseResult from data | Ensure the input matches the expected schema |
| E205 | Missing JSON-LD context | JSON-LD `@context` is missing | Add the required context object |
| E206 | Incompatible version | Serialized data version mismatch | Re-serialize with current parser version |
| E207 | Encoding error | Character encoding issue | Ensure UTF-8 encoding |

---

## Graph Errors (E300-E304)

Raised during graph construction and analysis.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E300 | Graph construction failed | Cannot build graph from ParseResult | Check that ParseResult contains valid statements |
| E301 | Invalid edge | Edge references a non-existent node | Ensure both source and target anchors exist |
| E302 | Invalid node | Node identifier is invalid | Check anchor name validity |
| E303 | Graph cycle detected | Unexpected cycle in graph | Review the cycle; break it or handle intentionally |
| E304 | Disconnected graph | Graph has isolated components | Connect components or analyze separately |

---

## File I/O Errors (E400-E404)

Raised during file reading and writing operations.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E400 | File not found | Specified file does not exist | Check the file path |
| E401 | File read error | Cannot read the file | Check file permissions and encoding |
| E402 | File write error | Cannot write to the file | Check directory permissions and disk space |
| E403 | Permission denied | Insufficient file permissions | Run with appropriate permissions |
| E404 | Invalid file format | File content is not valid STL | Check the file contains STL syntax |

---

## Query Errors (E450-E453)

Raised during query, filter, and pointer operations.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E450 | Invalid query operator | Operator not recognized | Use valid operators: `__gt`, `__gte`, `__lt`, `__lte`, `__ne`, `__contains`, `__startswith`, `__in` |
| E451 | Invalid pointer path | STL pointer path is malformed | Use format `/index/field/subfield` |
| E452 | Statement index out of range | Pointer index exceeds statement count | Check the number of statements in the document |
| E453 | Query type error | Value type incompatible with operator | Ensure numeric operators are used with numeric fields |

---

## Builder Errors (E500-E502)

Raised by the programmatic builder API.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E500 | Builder validation error | Built statement fails validation | Check anchor names and modifier values |
| E501 | Builder configuration error | Builder is misconfigured | Ensure source and target are set before `.build()` |
| E502 | Builder type error | Incorrect type passed to builder | Use correct types for `.mod()` parameters |

---

## Schema Errors (E600-E603)

Raised during schema loading and validation.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E600 | Schema parse error | Cannot parse `.stl.schema` file | Check schema syntax |
| E601 | Schema validation error | Document fails schema validation | Fix statements to conform to schema constraints |
| E602 | Schema not found | Schema file does not exist | Check the schema file path |
| E603 | Schema conflict | Schema rules conflict with each other | Review and fix conflicting schema rules |

---

## LLM Errors (E700-E702)

Raised during LLM output cleaning and repair.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E700 | LLM clean error | Cannot clean the input text | Check that input contains STL-like content |
| E701 | LLM repair error | Repair operation failed | Review the repair actions and input |
| E702 | LLM validation error | Cleaned output fails validation | Apply additional manual fixes |

---

## Emitter Errors (E800-E801)

Raised by the STLEmitter during streaming output.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E800 | Emitter write error | Cannot write to output file/stream | Check file permissions and path |
| E801 | Emitter format error | Statement cannot be formatted for output | Check the statement structure |

---

## Decay Errors (E900-E901)

Raised during confidence decay calculations.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E900 | Invalid decay configuration | `half_life_days` is <= 0 | Use a positive number for half-life |
| E901 | Decay calculation error | Cannot compute effective confidence | Check that statement has `confidence` and `timestamp` modifiers |

---

## Diff/Patch Errors (E950-E953)

Raised during document comparison and patching.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E950 | Diff type error | Cannot compare the given inputs | Ensure both inputs are valid ParseResult objects |
| E951 | Patch statement not found | Patch references a statement that doesn't exist in the target | Verify the patch matches the target document |
| E952 | Patch conflict | Patch operation conflicts with current state | Resolve the conflict manually |
| E953 | Invalid patch operation | Patch operation type is not recognized | Use valid operations from `stl_diff()` output |

---

## Reader Errors (E960-E962)

Raised during streaming input parsing.

| Code | Message | Cause | Fix |
|------|---------|-------|-----|
| E960 | Reader source error | Cannot read from the input source | Check file path or stream validity |
| E961 | Reader parse error | Cannot parse a line from the stream | Check STL syntax in the input stream |
| E962 | Multi-line continuation overflow | Multi-line statement exceeds buffer limit | Break the statement into smaller parts |

---

## Warning Codes (W001-W009)

Warnings are non-fatal. They appear in `ParseResult.warnings` but do not prevent parsing.

| Code | Message | Cause | Recommendation |
|------|---------|-------|----------------|
| W001 | Deprecated syntax | Using an outdated syntax form | Update to current syntax |
| W002 | Unusual anchor name | Anchor name doesn't follow conventions | Review naming; consider PascalCase or underscore_case |
| W003 | Low confidence value | `confidence` < 0.3 | Verify the claim or rephrase |
| W004 | Missing recommended modifier | Statement lacks commonly expected modifiers | Add `source`, `confidence`, or `time` as appropriate |
| W005 | Inconsistent style | Mixed naming or formatting styles | Standardize style across the document |
| W006 | Duplicate statement | Same statement appears more than once | Remove the duplicate |
| W007 | Unused anchor | Anchor appears only once (no connections) | Connect it to the graph or remove it |
| W008 | Complex namespace hierarchy | Namespace has 3+ levels of dots | Simplify to 1-2 levels |
| W009 | Performance warning | Document is very large or complex | Consider splitting into multiple files |

---

## Handling Errors in Code

```python
from stl_parser import parse
from stl_parser.errors import STLParseError, STLValidationError, ErrorCode

try:
    result = parse('[Invalid!] -> [B]')
except STLParseError as e:
    print(f"Parse error: {e}")
except STLValidationError as e:
    print(f"Validation error: {e}")

# Check warnings after successful parse
result = parse('[A] -> [B]')
for warning in result.warnings:
    print(f"Warning {warning.code}: {warning.message}")
```

---

## Error Class Hierarchy

```
Exception
└── STLError (base for all STL errors)
    ├── STLParseError        (E001-E011)
    ├── STLValidationError   (E100-E115)
    ├── STLSerializationError (E200-E207)
    ├── STLGraphError        (E300-E304)
    ├── STLFileError         (E400-E404)
    ├── STLQueryError        (E450-E453)
    ├── STLBuilderError      (E500-E502)
    ├── STLSchemaError       (E600-E603)
    ├── STLLLMError          (E700-E702)
    ├── STLEmitterError      (E800-E801)
    ├── STLDecayError        (E900-E901)
    ├── STLDiffError         (E950-E953)
    └── STLReaderError       (E960-E962)

STLWarning (W001-W009)  — not an exception, stored in ParseResult.warnings
```
