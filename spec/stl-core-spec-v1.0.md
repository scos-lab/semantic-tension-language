# STL Core Specification v1.0

## 1. Introduction
This document defines the **core syntax** and **computational model** of the Semantic Tension Language (STL).  
STL is a universal, calculable language designed for structuring, reasoning, and verifying knowledge across domains.  

Key goals:
- Provide a **human-readable yet machine-executable** representation of knowledge.
- Support **traceability and provenance** of statements.
- Bridge symbolic logic with neural systems by acting as an **intermediate structured layer**.

---

## 2. Core Syntax

### 2.1 Basic Units
- **Node**: Represents an entity, concept, or state.  
  Example: `[Clause_A]`

- **Path**: Directed relation between nodes.  
  Example: `[Clause_A] → [Clause_B]`

- **Modifier**: Metadata attached to a path, enclosed by `::mod(...)`.  
  Example:  
  ```text
  [Clause_A] → [Clause_B] ::mod(source="doc://law/§3.2", confidence=0.92)
  ```

### 2.2 General Form
   ```text
   [Node_A] → [Node_B] ::mod(key=value, ...)
   ```
 - Node_A (origin)
 - Node_B (target)
 - ::mod (optional modifiers: provenance, temporal info, confidence, etc.)

---

## 3. Semantics

1. **Structural Authenticity**  
   Every STL statement must be structurally valid: nodes must be well-formed, paths must be directional.

2. **Provenance**  
   Each statement can embed:
   - `source` (e.g., document URI, dataset reference)
   - `t` (timestamp)
   - `confidence` (0–1 float)

3. **Computability**  
   STL is **not just a markup** — modifiers and relations are computable and can be used in:
   - Reasoning
   - Verification
   - Graph-based transformation
 ## 4. Example Statements

 ### 4.1 Legal Reference
  ```text
  [Clause_A] -> [Clause_B] ::mod(source="doc://law/§3.2", t=2025-10-03, confidence=0.92)
  ```

Meaning: Clause A implies Clause B, supported by evidence from a legal document, with timestamp and confidence.

 ### 4.2 Knowledge Graph Style
 ```text
[Einstein] -> [Author] ::mod(work="Relativity", year=1905)
 ```

Meaning: Einstein is the author of the work "Relativity", dated 1905.

---

 ## 5. Compliance Guidelines

A conformant STL parser/engine must:

 - Parse node-path-modifier structures.  
 - Validate syntax correctness.  
 - Support at least the following modifiers:
   - `source`
   - `t` (timestamp)
   -    - `confidence`

Future versions may extend these requirements with temporal/event structures and conflict annotations.
