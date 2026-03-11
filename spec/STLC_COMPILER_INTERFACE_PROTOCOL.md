# STLC v1.0 — Compiler Interface Protocol

> **Protocol Type:** Compiler Interface Protocol for Semantic Code Generation
> **Purpose:** Standard interface for LLMs to compile STLC semantic specifications into concrete programming language implementations
> **Specification Base:** STL Core Specification v1.0 + Computational Semantics Extensions
> **Target:** LLMs acting as semantic compilers, code generation tools, automated development systems
> **Analogy:** Similar to LLVM IR enabling multi-language → multi-platform compilation, STLC enables semantic specifications → multi-language code generation

---

## 0. What is STLC

**STLC (Semantic Tension Language for Code)** is a **compiler interface protocol** that enables **language-agnostic code generation** from semantic specifications.

### The Compiler Interface Model

STLC serves as an **intermediate representation (IR)** in a multi-stage compilation process:

```
┌─────────────────────────────────────────────────────────────┐
│                   STLC Compilation Pipeline                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Input Layer]                                              │
│  Natural Language Requirements / High-Level Intent          │
│                     ↓                                        │
│  ┌──────────────────────────────────────────────┐          │
│  │         Phase 1: Semantic Compiler           │          │
│  │         (LLM or Analysis Tool)               │          │
│  └──────────────────────────────────────────────┘          │
│                     ↓                                        │
│  [Intermediate Representation]                              │
│  STLC Specification (Language-Agnostic Semantics)          │
│                     ↓                                        │
│  ┌──────────────────────────────────────────────┐          │
│  │      Phase 2: Target Language Compiler       │          │
│  │      (LLM Code Generator)                    │          │
│  └──────────────────────────────────────────────┘          │
│                     ↓                                        │
│  [Output Layer]                                             │
│  Concrete Code (Python/JavaScript/Go/Rust/Java/...)        │
│                     ↓                                        │
│  ┌──────────────────────────────────────────────┐          │
│  │   Phase 3: Traditional Compiler (Optional)   │          │
│  │   (GCC/LLVM/JVM)                             │          │
│  └──────────────────────────────────────────────┘          │
│                     ↓                                        │
│  [Executable]                                               │
│  Machine Code / Bytecode                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Analogy: STLC as "LLVM IR for Semantics"

| Traditional Compilation | STLC Semantic Compilation |
|------------------------|---------------------------|
| **Multiple Source Languages** → LLVM IR → Multiple Target Platforms | **Natural Language Intent** → STLC → Multiple Programming Languages |
| C/C++/Rust → IR → x86/ARM/WASM | Requirements → STLC → Python/JS/Go/Rust |
| Language-neutral intermediate representation | Semantics-preserving intermediate representation |
| Enables compiler optimizations | Enables semantic verification & multi-language generation |

### Core Principles
- **Compiler Interface Standard** - STLC is the formal contract between semantic analysis and code generation
- **Language-agnostic** - Express algorithms without committing to specific syntax or paradigms
- **Semantically complete** - Include intent, constraints, side effects, error handling, performance requirements
- **Human-readable yet machine-executable** - AI agents can parse and compile STLC to concrete code
- **Verifiable** - Logic can be validated for correctness, completeness, and security before compilation
- **Higher than pseudocode** - Pure computational intent, not implementation hints

### Design Philosophy
STLC introduces a **computational tension model** where:
- **Data flows** from input to output through transformations (functional semantics)
- **Control flows** branch and loop based on conditions (imperative semantics)
- **Side effects** are explicitly marked and constrained (purity tracking)
- **Intentions** are preserved alongside mechanics (documentation as specification)
- **Constraints** define valid execution space (contract programming)

### Why a Compiler Interface?

**Traditional Problem:**
```
Requirements (English) → Developer (Human Compiler) → Code (Python/JS/Go)
                           ↑
                    Ambiguity, inconsistency, information loss
```

**STLC Solution:**
```
Requirements → LLM → STLC (Precise Semantics) → LLM Compiler → Code
                            ↑
                    Unambiguous, verifiable, reproducible
```

**Benefits:**
1. **Separation of Concerns** - Intent (STLC) decoupled from implementation (target language)
2. **Multi-Target Compilation** - One STLC spec → Many language implementations
3. **Semantic Preservation** - Security, performance, correctness requirements preserved across compilation
4. **Verification** - Validate logic once at STLC level, not per-language
5. **Optimization** - Semantic-level optimizations before code generation

### STLC vs. Traditional Approaches

| Approach | Abstraction | Semantics | Language-Agnostic | AI-Friendly |
|----------|-------------|-----------|-------------------|-------------|
| **Pseudocode** | Medium | Low | Partial | Medium |
| **Flowcharts** | Medium | Low | Yes | Low |
| **UML** | Medium | Medium | Yes | Low |
| **IDL (Interface Definition)** | High | Medium | Yes | Medium |
| **STLC** | **High** | **High** | **Yes** | **High** |

---

## 1. Fundamental Syntax

### 1.1 Basic Form (Extends STL)

```stl
[Source_Node] -> [Target_Node] ::mod(
  // === Core STL fields ===
  rule="computational_rule_type",
  confidence=0.0-1.0,
  necessity="Necessary|Sufficient|Possible",

  // === STLC computational fields ===
  type="computation_type",
  input="data_source",
  output="data_destination",
  constraint="validation_or_constraint",
  on_success="success_path",
  on_fail="failure_path",
  intent="human_readable_explanation"
)
```

### 1.2 Syntax Rules (Same as STL)

**Nodes:**
- Use `[NodeName]` format
- PascalCase or snake_case
- Descriptive of computational step

**Arrows:**
- `→` or `->` indicates data/control flow direction
- Direction matters: `[A] → [B]` means A feeds into B

**Modifiers:**
- Always prefixed with `::`
- Format: `::mod(key=value, key=value, ...)`

---

## 2. Node System (Computational Nodes)

### 2.1 Node Type Selection Matrix

**COMPUTATIONAL LAYER** (Core code constructs)

| Type | When to Use | Examples | Naming Pattern |
|------|-------------|----------|----------------|
| **Input** | Function parameters, user input, API request | `[Input_Email]`, `[Request_Body]` | `[Input_*]` |
| **Output** | Return values, responses, side effects | `[Output_Success]`, `[Response_JSON]` | `[Output_*]`, `[Response_*]` |
| **Validation** | Data validation, precondition checks | `[Validate_Email]`, `[Check_Auth]` | `[Validate_*]`, `[Check_*]` |
| **Transformation** | Pure data transformations | `[Hash_Password]`, `[Parse_JSON]` | `[Transform_*]`, `[Parse_*]`, `[Hash_*]` |
| **Query** | Database reads, API calls (no mutation) | `[Query_User]`, `[Fetch_Data]` | `[Query_*]`, `[Fetch_*]`, `[Get_*]` |
| **Mutation** | Database writes, state changes | `[Create_User]`, `[Update_Record]` | `[Create_*]`, `[Update_*]`, `[Delete_*]` |
| **Branch** | Conditional logic, if/else | `[Branch_Auth_Valid]`, `[Check_Role]` | `[Branch_*]`, `[If_*]` |
| **Loop** | Iteration, recursion | `[Loop_Array]`, `[Iterate_Users]` | `[Loop_*]`, `[Iterate_*]` |
| **Error** | Error states, exceptions | `[Error_Invalid_Email]`, `[Exception_DB]` | `[Error_*]`, `[Exception_*]` |
| **Aggregation** | Reduce, sum, collect | `[Aggregate_Total]`, `[Reduce_Sum]` | `[Aggregate_*]`, `[Reduce_*]` |

**CONTROL FLOW LAYER**

| Type | When to Use | Examples | Naming Pattern |
|------|-------------|----------|----------------|
| **Entry** | Function/algorithm start | `[Entry_RegisterUser]`, `[Start]` | `[Entry_*]`, `[Start_*]` |
| **Exit** | Function/algorithm end | `[Exit_Success]`, `[Return]` | `[Exit_*]`, `[Return_*]` |
| **Checkpoint** | Intermediate state, assertion | `[Checkpoint_Validated]`, `[Assert_NotNull]` | `[Checkpoint_*]`, `[Assert_*]` |

---

## 3. Path Expression Types (Computational Paths)

### 3.1 Path Type Selection

| Path Type | Semantic Function | When to Use | Example |
|-----------|-------------------|-------------|---------|
| **Data Flow** | Data transformation pipeline | Pure data transformations | `[Input] → [Parse] → [Validate] → [Transform]` |
| **Control Flow** | Branching, conditionals | If/else, switch/case | `[Condition] → [Branch_True]`, `[Condition] → [Branch_False]` |
| **Side Effect** | State mutation, I/O | Database writes, API calls | `[Data] → [Mutation_DB]` |
| **Validation Flow** | Input validation chain | Preconditions, guards | `[Input] → [Validate_Type] → [Validate_Range]` |
| **Error Flow** | Exception handling | Try/catch, error propagation | `[Operation] → [Error_Handler]` |
| **Iterative Flow** | Loops, recursion | For/while loops, map/reduce | `[Collection] → [Loop_Iterator] → [Process_Item]` |

### 3.2 Path Composition Rules

**Linear Flow (Sequential):**
```stl
[Step_1] -> [Step_2] -> [Step_3]
```

**Branching Flow (Conditional):**
```stl
[Condition] -> [Branch_True] ::mod(condition="x > 0", on_true="continue")
[Condition] -> [Branch_False] ::mod(condition="x <= 0", on_true="continue")
```

**Error Handling Flow:**
```stl
[Operation] -> [Success_Path] ::mod(on_success="return_result")
[Operation] -> [Error_Path] ::mod(on_fail="handle_error")
```

**Loop Flow:**
```stl
[Collection] -> [Loop_Start] -> [Process_Item] -> [Loop_Condition] -> [Loop_Start]
[Loop_Condition] -> [Exit_Loop] ::mod(condition="no_more_items")
```

---

## 4. Modifier System (STLC Extensions)

### 4.1 Core STL Modifiers (Inherited)

From STL Core Specification:
- `rule` - causal, logical, empirical, definitional
- `confidence` - 0.0 to 1.0
- `necessity` - Necessary, Sufficient, Possible
- `value` - Good, Neutral, Bad, Critical
- `priority` - High, Medium, Low
- `intent` - Human-readable explanation

### 4.2 STLC Computational Modifiers

#### 4.2.1 Type Classification

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `type` | Enum | `validation`, `transformation`, `query`, `mutation`, `branching`, `loop`, `aggregation`, `output` | `::mod(type="validation")` |

**Type Definitions:**
- **validation** - Check data correctness (preconditions, guards)
- **transformation** - Pure function (no side effects)
- **query** - Read operation (database SELECT, API GET)
- **mutation** - Write operation (database INSERT/UPDATE/DELETE, state change)
- **branching** - Conditional logic (if/else, switch)
- **loop** - Iteration (for, while, map, reduce)
- **aggregation** - Combine multiple values (sum, count, collect)
- **output** - Return value or response

#### 4.2.2 Data Flow Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `input` | String/List | Data source identifier(s) | `::mod(input="user_email")` |
| `output` | String/List | Data destination identifier(s) | `::mod(output="hashed_password")` |
| `format` | Enum | `JSON`, `XML`, `String`, `Integer`, `Boolean`, `Array`, `Object`, `Binary` | `::mod(format="JSON")` |
| `schema` | String | Data structure definition | `::mod(schema="{id, email, name}")` |

#### 4.2.3 Control Flow Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `condition` | String | Boolean expression | `::mod(condition="age >= 18")` |
| `on_success` | String | Next node on success | `::mod(on_success="Return_Success")` |
| `on_fail` | String | Next node on failure | `::mod(on_fail="Error_Handler")` |
| `on_timeout` | String | Timeout handler | `::mod(on_timeout="Return_Cached")` |
| `loop_condition` | String | Loop continuation condition | `::mod(loop_condition="i < n")` |
| `break_condition` | String | Early exit condition | `::mod(break_condition="found == true")` |

#### 4.2.4 Algorithm & Constraint Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `algorithm` | String | Specific algorithm name | `::mod(algorithm="bcrypt_cost_10")` |
| `constraint` | String | Validation rule or invariant | `::mod(constraint="min_8_chars")` |
| `complexity_time` | String | Big-O time complexity | `::mod(complexity_time="O(log n)")` |
| `complexity_space` | String | Big-O space complexity | `::mod(complexity_space="O(1)")` |
| `deterministic` | Boolean | Always same output for input | `::mod(deterministic=true)` |

#### 4.2.5 Side Effect Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `operation` | Enum | `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `HTTP_GET`, `HTTP_POST`, etc. | `::mod(operation="INSERT")` |
| `table` | String | Database table name | `::mod(table="users")` |
| `fields` | String/List | Database fields | `::mod(fields="{email, password, created_at}")` |
| `idempotent` | Boolean | Safe to retry | `::mod(idempotent=true)` |
| `transaction` | Boolean | Requires atomic transaction | `::mod(transaction=true)` |
| `cache` | Boolean | Result can be cached | `::mod(cache=true)` |
| `cache_ttl` | String | Cache time-to-live | `::mod(cache_ttl="300s")` |

#### 4.2.6 HTTP/API Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `http_method` | Enum | `GET`, `POST`, `PUT`, `PATCH`, `DELETE` | `::mod(http_method="POST")` |
| `http_status` | Integer | HTTP status code | `::mod(http_status=201)` |
| `endpoint` | String | API endpoint path | `::mod(endpoint="/api/users")` |
| `auth_required` | Boolean | Authentication needed | `::mod(auth_required=true)` |
| `rate_limit` | String | Rate limit constraint | `::mod(rate_limit="100/hour")` |

#### 4.2.7 Performance Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `max_time` | String | Maximum execution time | `::mod(max_time="500ms")` |
| `max_memory` | String | Maximum memory usage | `::mod(max_memory="10MB")` |
| `async` | Boolean | Asynchronous execution | `::mod(async=true)` |
| `parallel` | Boolean | Can execute in parallel | `::mod(parallel=true)` |

#### 4.2.8 Security Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `security_critical` | Boolean | Security-sensitive operation | `::mod(security_critical=true)` |
| `sanitization` | Enum | `SQL_escape`, `HTML_escape`, `XSS_prevent`, `CSRF_token` | `::mod(sanitization="SQL_escape")` |
| `encryption` | Enum | `AES256`, `RSA`, `bcrypt`, `argon2` | `::mod(encryption="bcrypt")` |
| `authorization` | String | Required permission | `::mod(authorization="admin_role")` |

#### 4.2.9 Error Handling Modifiers

| Key | Type | Values | Example |
|-----|------|--------|---------|
| `error_type` | Enum | `ValidationError`, `DatabaseError`, `NetworkError`, `AuthError` | `::mod(error_type="ValidationError")` |
| `error_message` | String | Error message template | `::mod(error_message="Invalid email format")` |
| `retry` | Boolean | Retryable operation | `::mod(retry=true)` |
| `retry_count` | Integer | Max retry attempts | `::mod(retry_count=3)` |
| `fallback` | String | Fallback value/action | `::mod(fallback="return_default")` |

---

## 5. LLM Generation Guidelines

### 5.1 Decision Tree for STLC Generation

```
START
│
├─ Is this INPUT/OUTPUT?
│  ├─ INPUT → Use [Input_*] node, specify format and schema
│  └─ OUTPUT → Use [Output_*] or [Response_*] node, specify format
│
├─ Is this DATA VALIDATION?
│  └─ YES → Use [Validate_*] node, specify constraint, on_fail
│
├─ Is this PURE TRANSFORMATION?
│  └─ YES → Use type="transformation", specify algorithm if applicable
│
├─ Is this DATABASE/API OPERATION?
│  ├─ READ → Use type="query", operation="SELECT|HTTP_GET"
│  └─ WRITE → Use type="mutation", operation="INSERT|UPDATE|DELETE|HTTP_POST"
│
├─ Is this CONDITIONAL LOGIC?
│  └─ YES → Use [Branch_*] nodes, specify condition, on_success, on_fail
│
├─ Is this ITERATION?
│  └─ YES → Use [Loop_*] node, specify loop_condition, break_condition
│
├─ Is this ERROR HANDLING?
│  └─ YES → Use [Error_*] node, specify error_type, error_message
│
└─ Is this COMPLEX COMPUTATION?
   └─ YES → Break into smaller steps, connect with arrows
```

### 5.2 Completeness Checklist

Before finalizing STLC, LLM must verify:

```
□ ENTRY/EXIT DEFINED?
  → Every function/algorithm has [Entry_*] and [Exit_*] nodes

□ ALL INPUTS VALIDATED?
  → Every [Input_*] has corresponding [Validate_*] before use

□ ERROR PATHS DEFINED?
  → Every mutation/query has on_fail path

□ SIDE EFFECTS MARKED?
  → All mutations have type="mutation", idempotent flag

□ SECURITY CRITICAL STEPS?
  → Password hashing, auth checks have security_critical=true

□ PERFORMANCE CONSTRAINTS?
  → API calls have max_time, cache settings if needed

□ INTENT DOCUMENTED?
  → All complex nodes have intent="..." explanation
```

### 5.3 Confidence Calibration for Code

**Confidence Scores for STLC:**

| Confidence | When to Use |
|------------|-------------|
| **0.95-1.0** | Standard library functions, proven algorithms |
| **0.85-0.94** | Well-established patterns, common implementations |
| **0.70-0.84** | Domain-specific logic, moderate complexity |
| **0.50-0.69** | Heuristic approaches, optimization trade-offs |
| **0.30-0.49** | Experimental approaches, edge cases |

### 5.4 Best Practices for LLMs

#### DO:
✅ **Break complex logic into atomic steps** - Each node = one clear operation
✅ **Explicitly mark side effects** - Use `type="mutation"` for all writes
✅ **Define error paths** - Every operation has `on_fail`
✅ **Use descriptive node names** - `[Hash_Password_Bcrypt]` not `[Step_3]`
✅ **Include intent for non-obvious steps** - `intent="Security: prevent timing attacks"`
✅ **Specify constraints** - `constraint="min_8_chars_alphanumeric"`
✅ **Mark security-critical operations** - `security_critical=true`

#### DON'T:
❌ **Don't bundle multiple operations in one node** - Keep atomic
❌ **Don't omit validation steps** - Every input must be validated
❌ **Don't forget idempotency flags** - Critical for retries
❌ **Don't use vague node names** - `[Process]` is too generic
❌ **Don't skip error handling** - Even "impossible" errors
❌ **Don't hardcode values** - Use `input="config.max_retry"` not `retry_count=3`
❌ **Don't ignore performance** - Specify `max_time` for external calls

---

## 6. Validation Checklist

### 6.1 Structural Validation

```
□ Nodes
  ✓ All nodes have valid names (no special chars except _ and :)
  ✓ Node types are descriptive ([Validate_Email] not [Node_1])
  ✓ Entry and Exit nodes present

□ Paths
  ✓ All arrows have clear direction
  ✓ No dangling nodes (all connected)
  ✓ Cyclic paths have break conditions (loops)

□ Modifiers
  ✓ All required fields present for type
    - type="validation" → constraint, on_fail required
    - type="mutation" → operation, idempotent required
    - type="branching" → condition, on_success, on_fail required
  ✓ Enum values match specification
  ✓ Confidence scores in range [0.0, 1.0]
```

### 6.2 Semantic Validation

```
□ Data Flow
  ✓ All inputs validated before use
  ✓ Outputs defined for all exit paths
  ✓ Transformations are pure (no side effects unless type="mutation")

□ Control Flow
  ✓ All branches have both success and fail paths
  ✓ Loops have termination conditions
  ✓ No unreachable code paths

□ Side Effects
  ✓ All mutations marked with type="mutation"
  ✓ Idempotency specified for all mutations
  ✓ Transactions marked where needed

□ Security
  ✓ Sensitive operations have security_critical=true
  ✓ User inputs have sanitization specified
  ✓ Authentication/authorization checks present

□ Error Handling
  ✓ All operations have on_fail paths
  ✓ Error types are specific (not generic)
  ✓ Fallback values/actions defined
```

### 6.3 Completeness Validation

```
□ Business Logic
  ✓ All requirements captured in STLC
  ✓ Edge cases handled
  ✓ Invariants documented as constraints

□ Non-Functional Requirements
  ✓ Performance constraints specified (max_time)
  ✓ Scalability considerations (parallel, cache)
  ✓ Reliability features (retry, idempotent)
```

---

## 7. Examples (Best Practices)

### 7.1 Simple Function: Email Validation

```stl
## Function: Validate Email Format

[Entry_ValidateEmail] -> [Input_Email] ::mod(
  rule="definitional",
  type="input",
  format="String",
  confidence=1.0
)

[Input_Email] -> [Validate_Email_Format] ::mod(
  rule="logical",
  type="validation",
  constraint="RFC5322_email_regex",
  confidence=0.88,
  on_success="Return_Valid",
  on_fail="Return_Invalid",
  necessity="Necessary",
  intent="Email must match standard format"
)

[Validate_Email_Format] -> [Return_Valid] ::mod(
  rule="causal",
  type="output",
  output="true",
  format="Boolean",
  confidence=0.90
)

[Validate_Email_Format] -> [Return_Invalid] ::mod(
  rule="causal",
  type="output",
  output="false",
  format="Boolean",
  confidence=0.90
)

[Return_Valid] -> [Exit_Success] ::mod(
  rule="definitional",
  confidence=1.0
)

[Return_Invalid] -> [Exit_Failure] ::mod(
  rule="definitional",
  confidence=1.0
)
```

**Any language implementation possible:**
- Python: `re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)`
- JavaScript: `/^[\w.-]+@[\w.-]+\.\w+$/.test(email)`
- Go: `regexp.MatchString("^[\\w.-]+@[\\w.-]+\\.\\w+$", email)`

---

### 7.2 User Registration (Complex Flow)

```stl
## API Endpoint: POST /api/register

[Entry_RegisterUser] -> [Input_Request_Body] ::mod(
  rule="definitional",
  type="input",
  format="JSON",
  schema="{email: String, password: String}",
  http_method="POST",
  endpoint="/api/register",
  confidence=1.0
)

[Input_Request_Body] -> [Extract_Email] ::mod(
  rule="causal",
  type="transformation",
  input="request.body.email",
  output="email",
  format="String",
  confidence=1.0
)

[Input_Request_Body] -> [Extract_Password] ::mod(
  rule="causal",
  type="transformation",
  input="request.body.password",
  output="password",
  format="String",
  confidence=1.0
)

[Extract_Email] -> [Validate_Email_Format] ::mod(
  rule="logical",
  type="validation",
  constraint="RFC5322_email_regex",
  on_success="Validate_Email_Unique",
  on_fail="Error_Invalid_Email",
  necessity="Necessary",
  confidence=0.88
)

[Validate_Email_Format] -> [Validate_Email_Unique] ::mod(
  rule="logical",
  type="query",
  operation="SELECT",
  table="users",
  fields="email",
  condition="email = ?",
  on_success="Validate_Password_Strength",
  on_fail="Error_Email_Exists",
  necessity="Necessary",
  intent="Prevent duplicate registrations"
)

[Extract_Password] -> [Validate_Password_Strength] ::mod(
  rule="logical",
  type="validation",
  constraint="min_8_chars_alphanumeric_special",
  on_success="Hash_Password",
  on_fail="Error_Weak_Password",
  necessity="Necessary",
  security_critical=true,
  confidence=0.90
)

[Validate_Password_Strength] -> [Hash_Password] ::mod(
  rule="causal",
  type="transformation",
  algorithm="bcrypt_cost_10",
  input="password",
  output="hashed_password",
  format="String",
  deterministic=false,
  security_critical=true,
  necessity="Necessary",
  confidence=0.95,
  intent="Security: Never store plaintext passwords"
)

[Hash_Password] -> [Create_User_Record] ::mod(
  rule="causal",
  type="mutation",
  operation="INSERT",
  table="users",
  fields="{email, hashed_password, created_at}",
  idempotent=false,
  transaction=true,
  on_success="Return_Success_201",
  on_fail="Error_Database",
  necessity="Necessary",
  confidence=0.95
)

[Create_User_Record] -> [Return_Success_201] ::mod(
  rule="causal",
  type="output",
  format="JSON",
  schema="{success: true, user_id: Integer, email: String}",
  http_status=201,
  confidence=1.0
)

[Error_Invalid_Email] -> [Return_Error_400] ::mod(
  rule="causal",
  type="output",
  format="JSON",
  schema="{success: false, error: String}",
  error_message="Invalid email format",
  http_status=400,
  confidence=1.0
)

[Error_Email_Exists] -> [Return_Error_409] ::mod(
  rule="causal",
  type="output",
  format="JSON",
  error_message="Email already registered",
  http_status=409,
  confidence=1.0
)

[Error_Weak_Password] -> [Return_Error_400] ::mod(
  rule="causal",
  type="output",
  error_message="Password must be at least 8 characters with letters, numbers, and symbols",
  http_status=400,
  confidence=1.0
)

[Error_Database] -> [Return_Error_500] ::mod(
  rule="causal",
  type="output",
  error_message="Server error, please try again",
  http_status=500,
  confidence=1.0,
  intent="Don't expose internal error details to user"
)

[Return_Success_201] -> [Exit_Success] ::mod(
  rule="definitional",
  confidence=1.0
)

[Return_Error_400] -> [Exit_Client_Error] ::mod(
  rule="definitional",
  confidence=1.0
)

[Return_Error_409] -> [Exit_Conflict] ::mod(
  rule="definitional",
  confidence=1.0
)

[Return_Error_500] -> [Exit_Server_Error] ::mod(
  rule="definitional",
  confidence=1.0
)
```

---

### 7.3 Algorithm: Binary Search

```stl
## Algorithm: Binary Search in Sorted Array

[Entry_BinarySearch] -> [Input_Array] ::mod(
  rule="definitional",
  type="input",
  format="Array",
  schema="[Integer]",
  confidence=1.0
)

[Entry_BinarySearch] -> [Input_Target] ::mod(
  rule="definitional",
  type="input",
  format="Integer",
  confidence=1.0
)

[Input_Array] -> [Validate_Array_Sorted] ::mod(
  rule="logical",
  type="validation",
  constraint="array_must_be_sorted_ascending",
  on_success="Initialize_Pointers",
  on_fail="Error_Unsorted_Array",
  necessity="Necessary",
  confidence=1.0,
  intent="Binary search requires sorted input"
)

[Validate_Array_Sorted] -> [Initialize_Pointers] ::mod(
  rule="causal",
  type="transformation",
  input="none",
  output="{left: 0, right: array.length - 1}",
  confidence=1.0
)

[Initialize_Pointers] -> [Loop_Search] ::mod(
  rule="causal",
  type="loop",
  loop_condition="left <= right",
  on_true="Calculate_Middle",
  on_false="Return_Not_Found",
  confidence=1.0
)

[Loop_Search] -> [Calculate_Middle] ::mod(
  rule="causal",
  type="transformation",
  algorithm="floor((left + right) / 2)",
  input="{left, right}",
  output="mid",
  deterministic=true,
  confidence=1.0
)

[Calculate_Middle] -> [Compare_Target] ::mod(
  rule="logical",
  type="branching",
  condition="array[mid] == target",
  on_success="Return_Found",
  on_fail="Branch_Left_Or_Right",
  confidence=1.0
)

[Compare_Target] -> [Branch_Left_Or_Right] ::mod(
  rule="logical",
  type="branching",
  condition="array[mid] > target",
  on_success="Update_Right",
  on_fail="Update_Left",
  confidence=1.0,
  intent="Target is in left half if mid > target, else right half"
)

[Branch_Left_Or_Right] -> [Update_Right] ::mod(
  rule="causal",
  type="transformation",
  input="{mid}",
  output="right = mid - 1",
  confidence=1.0
)

[Branch_Left_Or_Right] -> [Update_Left] ::mod(
  rule="causal",
  type="transformation",
  input="{mid}",
  output="left = mid + 1",
  confidence=1.0
)

[Update_Right] -> [Loop_Search] ::mod(
  rule="causal",
  confidence=1.0,
  intent="Continue search in narrowed range"
)

[Update_Left] -> [Loop_Search] ::mod(
  rule="causal",
  confidence=1.0,
  intent="Continue search in narrowed range"
)

[Compare_Target] -> [Return_Found] ::mod(
  rule="causal",
  type="output",
  output="mid",
  format="Integer",
  confidence=1.0
)

[Loop_Search] -> [Return_Not_Found] ::mod(
  rule="causal",
  type="output",
  output="-1",
  format="Integer",
  confidence=1.0,
  intent="Convention: -1 indicates element not found"
)

[Return_Found] -> [Exit_Success] ::mod(
  rule="definitional",
  confidence=1.0
)

[Return_Not_Found] -> [Exit_Not_Found] ::mod(
  rule="definitional",
  confidence=1.0
)

[Error_Unsorted_Array] -> [Exit_Error] ::mod(
  rule="causal",
  type="output",
  error_type="PreconditionError",
  error_message="Array must be sorted for binary search",
  confidence=1.0
)

## Complexity Analysis

[Algorithm_BinarySearch] -> [Complexity_Time] ::mod(
  rule="empirical",
  complexity_time="O(log n)",
  confidence=1.0,
  intent="Logarithmic time due to halving search space each iteration"
)

[Algorithm_BinarySearch] -> [Complexity_Space] ::mod(
  rule="empirical",
  complexity_space="O(1)",
  confidence=1.0,
  intent="Constant space for iterative version (no recursion stack)"
)
```

---

### 7.4 API Call with Retry Logic

```stl
## External API Call: Fetch User Data with Retry

[Entry_FetchUserData] -> [Input_User_ID] ::mod(
  rule="definitional",
  type="input",
  format="Integer",
  confidence=1.0
)

[Input_User_ID] -> [API_Call_External_Service] ::mod(
  rule="causal",
  type="query",
  operation="HTTP_GET",
  endpoint="https://api.example.com/users/{user_id}",
  http_method="GET",
  auth_required=true,
  max_time="2000ms",
  on_success="Parse_Response",
  on_fail="Check_Retry_Count",
  on_timeout="Check_Retry_Count",
  cache=true,
  cache_ttl="300s",
  confidence=0.85,
  intent="External service may be slow or unavailable"
)

[API_Call_External_Service] -> [Parse_Response] ::mod(
  rule="causal",
  type="transformation",
  input="response.body",
  output="user_data",
  format="JSON",
  on_success="Return_User_Data",
  on_fail="Error_Invalid_Response",
  confidence=0.90
)

[API_Call_External_Service] -> [Check_Retry_Count] ::mod(
  rule="logical",
  type="branching",
  condition="retry_count < 3",
  on_success="Increment_Retry",
  on_fail="Return_Cached_Or_Error",
  confidence=1.0
)

[Check_Retry_Count] -> [Increment_Retry] ::mod(
  rule="causal",
  type="transformation",
  input="retry_count",
  output="retry_count + 1",
  confidence=1.0
)

[Increment_Retry] -> [Wait_Exponential_Backoff] ::mod(
  rule="causal",
  type="transformation",
  algorithm="exponential_backoff_2^retry_count_seconds",
  input="retry_count",
  output="wait_time",
  confidence=0.95,
  intent="Avoid overwhelming failing service"
)

[Wait_Exponential_Backoff] -> [API_Call_External_Service] ::mod(
  rule="causal",
  confidence=1.0,
  intent="Retry with backoff"
)

[Check_Retry_Count] -> [Return_Cached_Or_Error] ::mod(
  rule="logical",
  type="branching",
  condition="cache_exists",
  on_success="Return_Cached_Data",
  on_fail="Return_Error_Service_Unavailable",
  confidence=0.85
)

[Return_Cached_Or_Error] -> [Return_Cached_Data] ::mod(
  rule="causal",
  type="output",
  output="cached_user_data",
  format="JSON",
  confidence=0.80,
  intent="Stale data better than no data"
)

[Return_Cached_Or_Error] -> [Return_Error_Service_Unavailable] ::mod(
  rule="causal",
  type="output",
  error_type="ServiceUnavailableError",
  error_message="User service is temporarily unavailable",
  http_status=503,
  confidence=1.0
)

[Parse_Response] -> [Return_User_Data] ::mod(
  rule="causal",
  type="output",
  output="user_data",
  format="JSON",
  confidence=1.0
)

[Return_User_Data] -> [Exit_Success] ::mod(
  rule="definitional",
  confidence=1.0
)
```

---

### 7.5 Database Transaction with Rollback

```stl
## Database Operation: Transfer Money Between Accounts

[Entry_TransferMoney] -> [Input_From_Account] ::mod(
  rule="definitional",
  type="input",
  format="Integer",
  confidence=1.0
)

[Entry_TransferMoney] -> [Input_To_Account] ::mod(
  rule="definitional",
  type="input",
  format="Integer",
  confidence=1.0
)

[Entry_TransferMoney] -> [Input_Amount] ::mod(
  rule="definitional",
  type="input",
  format="Decimal",
  confidence=1.0
)

[Input_Amount] -> [Validate_Amount_Positive] ::mod(
  rule="logical",
  type="validation",
  constraint="amount > 0",
  on_success="Start_Transaction",
  on_fail="Error_Invalid_Amount",
  necessity="Necessary",
  confidence=1.0
)

[Validate_Amount_Positive] -> [Start_Transaction] ::mod(
  rule="causal",
  type="mutation",
  operation="BEGIN_TRANSACTION",
  transaction=true,
  on_success="Check_Balance",
  on_fail="Error_Transaction_Failed",
  necessity="Necessary",
  confidence=1.0,
  intent="Ensure atomicity: both debit and credit must succeed or both fail"
)

[Start_Transaction] -> [Check_Balance] ::mod(
  rule="causal",
  type="query",
  operation="SELECT",
  table="accounts",
  fields="balance",
  condition="id = from_account",
  on_success="Validate_Sufficient_Funds",
  on_fail="Rollback_Transaction",
  confidence=1.0
)

[Check_Balance] -> [Validate_Sufficient_Funds] ::mod(
  rule="logical",
  type="validation",
  constraint="balance >= amount",
  on_success="Debit_From_Account",
  on_fail="Rollback_Insufficient_Funds",
  necessity="Necessary",
  confidence=1.0
)

[Validate_Sufficient_Funds] -> [Debit_From_Account] ::mod(
  rule="causal",
  type="mutation",
  operation="UPDATE",
  table="accounts",
  fields="balance = balance - amount",
  condition="id = from_account",
  idempotent=false,
  transaction=true,
  on_success="Credit_To_Account",
  on_fail="Rollback_Transaction",
  confidence=1.0
)

[Debit_From_Account] -> [Credit_To_Account] ::mod(
  rule="causal",
  type="mutation",
  operation="UPDATE",
  table="accounts",
  fields="balance = balance + amount",
  condition="id = to_account",
  idempotent=false,
  transaction=true,
  on_success="Commit_Transaction",
  on_fail="Rollback_Transaction",
  confidence=1.0
)

[Credit_To_Account] -> [Commit_Transaction] ::mod(
  rule="causal",
  type="mutation",
  operation="COMMIT_TRANSACTION",
  transaction=true,
  on_success="Return_Success",
  on_fail="Rollback_Transaction",
  necessity="Necessary",
  confidence=1.0
)

[Commit_Transaction] -> [Return_Success] ::mod(
  rule="causal",
  type="output",
  format="JSON",
  schema="{success: true, transaction_id: String}",
  confidence=1.0
)

[Rollback_Insufficient_Funds] -> [Rollback_Transaction] ::mod(
  rule="causal",
  error_type="InsufficientFundsError",
  confidence=1.0
)

[Rollback_Transaction] -> [Execute_Rollback] ::mod(
  rule="causal",
  type="mutation",
  operation="ROLLBACK_TRANSACTION",
  transaction=true,
  on_success="Return_Error",
  necessity="Necessary",
  confidence=1.0,
  intent="Undo all changes on any failure"
)

[Execute_Rollback] -> [Return_Error] ::mod(
  rule="causal",
  type="output",
  format="JSON",
  error_message="Transfer failed, no changes made",
  confidence=1.0
)

[Return_Success] -> [Exit_Success] ::mod(
  rule="definitional",
  confidence=1.0
)

[Return_Error] -> [Exit_Failure] ::mod(
  rule="definitional",
  confidence=1.0
)
```

---

## 8. Anti-Patterns (What NOT to Do)

### 8.1 Vague Node Names
```stl
❌ BAD:
[Step_1] -> [Step_2] -> [Step_3]

✅ GOOD:
[Validate_Input] -> [Hash_Password] -> [Save_To_Database]
```

### 8.2 Missing Error Handling
```stl
❌ BAD:
[API_Call] -> [Process_Response]

✅ GOOD:
[API_Call] -> [Process_Response] ::mod(on_success="Return_Data", on_fail="Handle_Error")
[API_Call] -> [Handle_Error] ::mod(on_fail="Return_Error_Response")
```

### 8.3 Unmarked Side Effects
```stl
❌ BAD:
[User_Data] -> [Database] ::mod(type="transformation")

✅ GOOD:
[User_Data] -> [Database_Insert] ::mod(
  type="mutation",
  operation="INSERT",
  idempotent=false,
  transaction=true
)
```

### 8.4 Missing Validation
```stl
❌ BAD:
[Input_Email] -> [Save_To_Database]

✅ GOOD:
[Input_Email] -> [Validate_Email_Format] -> [Validate_Email_Unique] -> [Save_To_Database]
```

### 8.5 Hardcoded Values
```stl
❌ BAD:
::mod(retry_count=3, max_time="500ms")

✅ GOOD:
::mod(
  retry_count="config.max_retries",
  max_time="config.api_timeout"
)
```

### 8.6 Insufficient Security Marking
```stl
❌ BAD:
[Password] -> [Hash] ::mod(type="transformation")

✅ GOOD:
[Password] -> [Hash_Bcrypt] ::mod(
  type="transformation",
  algorithm="bcrypt_cost_10",
  security_critical=true,
  necessity="Necessary",
  value="Critical",
  intent="Security: Never store plaintext passwords"
)
```

### 8.7 Bundling Multiple Operations
```stl
❌ BAD:
[Input] -> [Validate_Transform_Save] ::mod(
  type="transformation",
  operations="validate,hash,insert"
)

✅ GOOD:
[Input] -> [Validate] -> [Hash] -> [Save]
```

### 8.8 Missing Idempotency Flag
```stl
❌ BAD:
[Data] -> [Create_Record] ::mod(
  type="mutation",
  operation="INSERT"
)

✅ GOOD:
[Data] -> [Create_Record] ::mod(
  type="mutation",
  operation="INSERT",
  idempotent=false,
  transaction=true
)
```

---

## 9. Quick Reference Card

### Minimal Valid Statement
```stl
[Source] -> [Target]
```

### Recommended Statement (Computational)
```stl
[Source] -> [Target] ::mod(
  type="validation|transformation|mutation|query|branching|loop|output",
  input="data_source",
  output="data_destination",
  on_success="next_step",
  on_fail="error_handler",
  confidence=0.XX,
  intent="explanation"
)
```

### Complete Statement (All Dimensions)
```stl
[Source] -> [Target] ::mod(
  // Core computation
  type="mutation",
  input="user_data",
  output="user_id",

  // Control flow
  on_success="Return_Success",
  on_fail="Handle_Error",

  // Algorithm
  algorithm="bcrypt_cost_10",
  constraint="min_8_chars",

  // Side effects
  operation="INSERT",
  table="users",
  fields="{email, password, created_at}",
  idempotent=false,
  transaction=true,

  // Security
  security_critical=true,
  sanitization="SQL_escape",

  // Performance
  max_time="500ms",
  cache=true,

  // STL core
  rule="causal",
  confidence=0.95,
  necessity="Necessary",
  value="Critical",
  intent="Create user account with secure password storage"
)
```

---

## 10. LLM Checklist Before Generating STLC

Before writing STLC, confirm:

- [ ] I understand the computational intent (what the code should do)
- [ ] I have identified all inputs and outputs
- [ ] I have identified all validation requirements
- [ ] I have identified all side effects (mutations)
- [ ] I have identified all error cases
- [ ] I have identified all security-critical operations
- [ ] I will use descriptive node names
- [ ] I will specify error handling for all operations
- [ ] I will mark all mutations with type="mutation" and idempotent flag
- [ ] I will include intent for non-obvious steps

**If all checked → Generate STLC! 🚀**

---

## Appendix A: Type System Summary

| Type | Use Case | Required Modifiers | Optional Modifiers |
|------|----------|-------------------|-------------------|
| `validation` | Input checks | `constraint`, `on_fail` | `on_success`, `security_critical` |
| `transformation` | Pure functions | `input`, `output` | `algorithm`, `deterministic` |
| `query` | Read operations | `operation` | `table`, `fields`, `cache`, `max_time` |
| `mutation` | Write operations | `operation`, `idempotent` | `table`, `fields`, `transaction` |
| `branching` | Conditionals | `condition`, `on_success`, `on_fail` | `intent` |
| `loop` | Iteration | `loop_condition` | `break_condition`, `complexity_time` |
| `aggregation` | Reduce/combine | `input`, `output` | `algorithm` |
| `output` | Return values | `format` | `schema`, `http_status` |

---

## Appendix B: Common Algorithms Reference

**Hashing:**
- `bcrypt_cost_10`, `bcrypt_cost_12`
- `argon2id`
- `SHA256`, `SHA512`

**Encoding:**
- `base64_encode`, `base64_decode`
- `URL_encode`, `URL_decode`
- `JWT_sign`, `JWT_verify`

**Sanitization:**
- `SQL_escape`
- `HTML_escape`
- `XSS_prevent`
- `CSRF_token_generate`

**Search:**
- `binary_search`
- `linear_search`
- `depth_first_search`
- `breadth_first_search`

**Sort:**
- `quicksort`
- `mergesort`
- `heapsort`

**Math:**
- `floor`, `ceil`, `round`
- `exponential_backoff_2^n`

---

## Appendix C: Error Types Reference

**Validation Errors:**
- `ValidationError` - Invalid input data
- `FormatError` - Wrong data format
- `ConstraintViolationError` - Business rule violated

**Database Errors:**
- `DatabaseError` - Generic DB error
- `UniqueConstraintError` - Duplicate key
- `ForeignKeyError` - Referential integrity violated
- `TransactionError` - Transaction failed

**Network Errors:**
- `NetworkError` - Network connectivity issue
- `TimeoutError` - Operation timed out
- `ServiceUnavailableError` - External service down

**Security Errors:**
- `AuthenticationError` - Invalid credentials
- `AuthorizationError` - Insufficient permissions
- `TokenExpiredError` - Auth token expired

**Business Logic Errors:**
- `InsufficientFundsError` - Not enough balance
- `ResourceNotFoundError` - Entity doesn't exist
- `ConflictError` - State conflict (409)

---

## Document Metadata

**Document Status:** ✅ Complete
**Protocol Version:** 1.0
**Protocol Type:** Compiler Interface Protocol
**Target Audience:** LLMs, code generation tools, automated development systems
**Prerequisite:** STL Core Specification v1.0 understanding
**Purpose:** Define standard interface for compiling semantic specifications into concrete programming language code

---

## For LLM Implementers

**After reading this Compiler Interface Protocol, you can:**

1. ✅ **Generate STLC specifications** from natural language requirements
2. ✅ **Compile STLC to code** in any programming language (Python, JavaScript, Go, Rust, Java, etc.)
3. ✅ **Verify semantic correctness** before code generation
4. ✅ **Preserve security and performance constraints** across compilation
5. ✅ **Generate multi-language implementations** from a single STLC spec
6. ✅ **Validate implementations** against STLC specifications

**You now act as a semantic compiler with STLC as your intermediate representation.**

---

## Version History

**v1.0 (2025-11-26)**
- Initial release as "Compiler Interface Protocol"
- Defined 10 computational node types
- Specified 50+ computational modifiers across 9 categories
- Established compilation pipeline model
- Provided 5 complete reference examples
- Documented anti-patterns and validation checklists

---

**⭐ STLC v1.0 — The Standard Compiler Interface for Semantic Code Generation**
