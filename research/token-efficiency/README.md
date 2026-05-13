# STL Token-Efficiency Benchmarks

> **Purpose:** Empirical evidence backing the token-efficiency claims in
> `docs/protocols/STL_Operational_Protocol.md` — specifically §0 ("Token-
> efficient — Compact syntax optimized for LLM context windows") and §4.2.5
> ("Empirical Token Savings").
>
> **First run:** 2026-05-13 by Syn-claude (Opus 4.7)
> **Tokenizer:** `tiktoken cl100k_base` (publicly available proxy for modern
> LLM tokenizers; Anthropic's tokenizer is similar in spirit)

---

## Three Experiments

| # | Question | File | Headline result |
|---|----------|------|----------------|
| **01** | Does STL use fewer tokens than equivalent JSON? | `01_stl_vs_json.py` | **STL saves 39.7% vs JSON-pretty, 6.2% vs JSON-minified** |
| **02** | Can we save more by dropping quotes around modifier values? | `02_quote_removal.py` | **No — savings ≈ 0%** (BPE has merged `="` into a single token) |
| **03** | What does §4.2 Default Value Omission actually save? | `03_default_omission.py` | **17.6% average** on representative edge styles |

Full output snapshot: `results_2026-05-13.txt`

---

## 01. STL vs JSON

**6 representative samples** spanning minimal → complex, EN + CN, single edge
→ 3-edge chain. Each sample expressed three equivalent ways:

- **STL** — native syntax (`[A] → [B] ::mod(...)`)
- **JSON-pretty** — `json.dumps(obj, indent=2)`, the form LLMs actually
  produce when asked to emit structured output
- **JSON-minified** — `json.dumps(obj, separators=(",",":"))`, the
  mathematical lower bound for "fair" JSON

Excluded: ultra-minified JSON with 1-char keys (`{"s":"A","t":"B","m":{...}}`)
— unfair comparison since keys lose semantic clarity.

### Headline numbers (6-sample total)

| Format | Tokens | vs STL |
|--------|-------:|-------:|
| STL | 286 | baseline |
| JSON-pretty | 474 | +65.7% (STL saves **39.7%**) |
| JSON-minified | 305 | +6.6% (STL saves **6.2%**) |

### Why STL wins

JSON's "structure tax" is fixed overhead; STL compresses it to the minimum:

| Cost driver | JSON | STL |
|------------|------|-----|
| Quoted keys | `"confidence":0.95` | `confidence=0.95` |
| Nested modifier block | `"modifiers":{...}` | single `::mod(...)` call |
| Directionality | two separate keys (`"source"`/`"target"`) | one arrow token `→` |
| Multi-edge framing | array brackets + per-object braces | newline-separated |

### Caveat

Savings scale with **structural overhead share**. Edges dominated by long
free-text value content (description, lesson) see smaller relative savings
because the text bytes themselves tokenize identically in both formats.

---

## 02. Quote Removal (Counter-Intuitive Null Result)

**Hypothesis:** Removing the quote pair around string values in `::mod(...)`
should save tokens.

**Finding:** Savings ≈ **0%** (−0.4% on 5 samples; effectively noise).

### Why — BPE has already merged `="`

```
'rule="causal"'  → 5 tokens: ['rule', '="', 'ca', 'usal', '"']
'rule=causal'    → 4 tokens: ['rule', '=', 'ca', 'usal']
```

The pattern `="` is ubiquitous in JSON / Python / JS training data, so BPE
learned it as a single token. Removing the opening quote saves zero — there
was no separate `"` token to drop. Removing the closing quote *sometimes*
saves 1 token but is offset by the new ambiguity (free-text values
containing `,`/`=`/`)` would break parsing).

**Lesson:** Character-count intuition does not transfer to token cost.
Always verify with a tokenizer. This null result killed a tempting protocol
change before it was made.

See STG node `BPE_Equals_Quote_Merge_Insight` for the cached insight.

---

## 03. Default Value Omission (§4.2)

Once you accept that `confidence`, `rule`, and `strength` carry well-defined
defaults that a parser can fill back in, you can omit them from the surface
form. Five representative edge styles:

| Edge style | before | after | saving |
|-----------|-------:|------:|-------:|
| Definitional (`is_a`) | 28 | 16 | **−43%** |
| Causal | 34 | 29 | −15% |
| Empirical (with `lesson`) | 53 | 48 | −9% |
| Definitional + `description` | 35 | 30 | −14% |
| Role/spec | 38 | 32 | −16% |
| **TOTAL** | **188** | **155** | **−17.6%** |

This is the headline number cited in `STL_Operational_Protocol.md` §4.2.5.

---

## How to Reproduce

```bash
# Requires tiktoken. STL repo's stg venv has it:
~/.stg/venv/bin/python 01_stl_vs_json.py
~/.stg/venv/bin/python 02_quote_removal.py
~/.stg/venv/bin/python 03_default_omission.py

# Or install fresh:
pip install tiktoken
python 01_stl_vs_json.py
```

All scripts are deterministic — `cl100k_base` is a frozen vocabulary, so
results are reproducible across runs and machines.

---

## File Layout

```
research/token-efficiency/
├── README.md                   # this file
├── 01_stl_vs_json.py           # main STL-vs-JSON benchmark
├── 02_quote_removal.py         # quote-removal null-result experiment
├── 03_default_omission.py      # §4.2 token-savings measurement
└── results_2026-05-13.txt      # full output snapshot of first run
```

---

## Tokenizer Caveats

We use **`cl100k_base`** (GPT-4 family) because:

1. **Publicly available** — no API key required to reproduce
2. **Same BPE family** as modern Claude / GPT tokenizers (all are
   byte-level BPE trained on overlapping web corpora)
3. **Stable** — the vocabulary is frozen; no version drift

Anthropic does not publish Claude's exact tokenizer, so absolute token
counts may differ by ±5%. The **relative ratios** (STL vs JSON, defaults
vs explicit) are stable across BPE families because the same structural
patterns are merged in all of them.

---

## Citation

When citing these numbers in spec changes, STG nodes, or other agent
context, please use:

> "STL saves 39.7% tokens vs JSON-pretty / 6.2% vs JSON-minified;
>  §4.2 default-value omission saves an additional ≈17.6% average.
>  Measured 2026-05-13 with tiktoken cl100k_base. Source:
>  `scos-lab/semantic-tension-language/research/token-efficiency/`."

GitHub:
<https://github.com/scos-lab/semantic-tension-language/tree/main/research/token-efficiency>
