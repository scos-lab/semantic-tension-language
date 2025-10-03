# Semantic Tension Language (STL)

**Semantic Tension Language (STL)** is a **calculable, universal standard for structuring knowledge**.  
Unlike traditional data formats, STL introduces a **tension-path model** that allows not only storage and retrieval but also **reasoning, verification, and traceability** across domains.

---

##  Key Features
- **Universal Knowledge Structuring**  
  Express concepts, relations, and evidence in a graph-like but human-readable syntax.

- **Calculable & Executable**  
  STL statements are not just annotations — they can be **evaluated, transformed, and reasoned upon**.

- **Evidence-Attached by Design**  
  Every statement can embed source references, timestamps, and confidence levels for verifiable knowledge.

- **Bridging Symbolic & Neural AI**  
  Works alongside LLMs as an **intermediate structured layer** for reasoning and long-term memory.

---

## Documentation

- [STL Core Specification v1.0](./spec/stl-core-spec-v1.0.md)

##  Example

```text
[Clause_A] → [Clause_B] ::mod(source="doc://law/§3.2", t=2025-10-03, confidence=0.92)
```

This example states that Clause A implies Clause B, supported by evidence from a legal document,
with a given timestamp and confidence level.


---

##   Repository Structure (planned)
```
/spec           → STL specifications (core / advanced)
/examples       → Example STL files
/ref-impl       → Reference parsers and exporters
/tests          → Conformance test suite
/docs           → Whitepaper and extended documentation
```
---

##   License

- **Code:** Apache License 2.0  
- **Specification text:** CC BY 4.0  
- **Trademarks:** "Semantic Tension Language" (STL) — usage subject to guidelines.  

---

##   Roadmap

- **v1.0** — Core syntax, AST, JSON-LD/RDF* mapping  
- **v1.1** — Event/temporal extensions, conflict annotations  
- **v1.2** — Execution guidelines, signature and content-addressing support  

---

##   Contributing

STL is intended as an **open standard**.  

We welcome:
- Issues  
- Discussions  
- Contributions  

Future proposals will follow the **STL Improvement Proposal (SIP)** process.  
Please open a pull request or start a discussion if you want to contribute.

---

##   Citation

If you use STL in research or software, please cite as:
> **SCOS-Lab.**  
> *Semantic Tension Language (STL): A Structural Protocol for Provenanced Knowledge.*  
> Preprint, 2025.
