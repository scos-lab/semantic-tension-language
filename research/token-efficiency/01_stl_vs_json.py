"""STL vs JSON token-efficiency benchmark.

Hypothesis: For equivalent semantic content, STL uses fewer tokens than JSON.

Method:
  - 6 representative samples spanning simple → complex, EN + CN, single edge
    → 3-edge chain
  - For each sample, three equivalent representations:
      (A) STL — native syntax
      (B) JSON-pretty — human-readable JSON with indent=2 (the form LLMs
          naturally produce when generating structured output)
      (C) JSON-minified — same JSON serialized without whitespace
  - Tokenize with tiktoken cl100k_base (publicly available proxy for modern
    LLM tokenizers; Anthropic's tokenizer is similar in spirit)
  - Report tokens, characters, and ratios per sample + total

Note: ultra-minified JSON with 1-char keys (e.g. {"s":"A","t":"B","m":{...}})
is excluded — that's an unfair comparison because the keys lose semantic
clarity. The point is to compare *equally readable* representations.

First conducted: 2026-05-13 by Syn-claude (Opus 4.7)
"""

import json
import tiktoken

ENC = tiktoken.get_encoding("cl100k_base")

def toks(s: str) -> int:
    return len(ENC.encode(s))

# ─────────────────────────────────────────────────────────────────────────
# SAMPLES — each tuple is (label, stl_text, json_obj_equivalent)
# ─────────────────────────────────────────────────────────────────────────

samples = []

# 1. Minimal edge (no modifier)
samples.append((
    "1. Minimal edge",
    "[Cat] → [Mammal]",
    {"source": "Cat", "target": "Mammal"},
))

# 2. Edge with confidence + rule
samples.append((
    "2. Simple typed edge",
    '[Cat] → [Mammal] ::mod(rule="definitional", confidence=0.99)',
    {
        "source": "Cat",
        "target": "Mammal",
        "modifiers": {"rule": "definitional", "confidence": 0.99},
    },
))

# 3. Causal claim with strength + source
samples.append((
    "3. Causal claim",
    '[Heavy_Rain] → [Flooding] ::mod(rule="causal", confidence=0.85, '
    'strength=0.80, source="NOAA_2024_report")',
    {
        "source": "Heavy_Rain",
        "target": "Flooding",
        "modifiers": {
            "rule": "causal",
            "confidence": 0.85,
            "strength": 0.80,
            "source": "NOAA_2024_report",
        },
    },
))

# 4. Empirical lesson with longer description
samples.append((
    "4. Empirical lesson",
    '[OAuth_Refresh_Token] → [Auth_Failure] ::mod(rule="empirical", '
    'confidence=0.95, lesson="Testing-mode refresh tokens expire after 7 days; '
    'must publish app to Production", occurred_time="2026-04-23")',
    {
        "source": "OAuth_Refresh_Token",
        "target": "Auth_Failure",
        "modifiers": {
            "rule": "empirical",
            "confidence": 0.95,
            "lesson": "Testing-mode refresh tokens expire after 7 days; must publish app to Production",
            "occurred_time": "2026-04-23",
        },
    },
))

# 5. Chinese anchors + mixed content
samples.append((
    "5. CJK anchors",
    '[黄帝内经] → [中医理论基础] ::mod(rule="definitional", confidence=0.95, '
    'domain="traditional_chinese_medicine", author="未知_战国时期")',
    {
        "source": "黄帝内经",
        "target": "中医理论基础",
        "modifiers": {
            "rule": "definitional",
            "confidence": 0.95,
            "domain": "traditional_chinese_medicine",
            "author": "未知_战国时期",
        },
    },
))

# 6. Chain of 3 statements (multi-edge graph fragment)
stl_chain = (
    '[Density_Field_Rho] → [Universal_Substrate] ::mod(rule="definitional", '
    'confidence=0.98, description="ρ is the unique fundamental entity")\n'
    '[Universal_Substrate] → [Consciousness] ::mod(rule="causal", '
    'confidence=0.90, strength=0.85, description="self-organizing modes of ρ")\n'
    '[Consciousness] → [Density_Field_Rho] ::mod(rule="empirical", '
    'confidence=0.92, description="inner experience of the same substrate")'
)
json_chain = [
    {
        "source": "Density_Field_Rho",
        "target": "Universal_Substrate",
        "modifiers": {
            "rule": "definitional",
            "confidence": 0.98,
            "description": "ρ is the unique fundamental entity",
        },
    },
    {
        "source": "Universal_Substrate",
        "target": "Consciousness",
        "modifiers": {
            "rule": "causal",
            "confidence": 0.90,
            "strength": 0.85,
            "description": "self-organizing modes of ρ",
        },
    },
    {
        "source": "Consciousness",
        "target": "Density_Field_Rho",
        "modifiers": {
            "rule": "empirical",
            "confidence": 0.92,
            "description": "inner experience of the same substrate",
        },
    },
]
samples.append(("6. 3-edge chain", stl_chain, json_chain))


# ─────────────────────────────────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────────────────────────────────

print(f"{'Sample':<22} {'STL tok':>8} {'JSON-pretty':>12} {'JSON-min':>10} "
      f"{'Δ pretty':>10} {'Δ min':>8}")
print("─" * 78)

total_stl = total_pretty = total_min = 0
for label, stl, obj in samples:
    json_pretty = json.dumps(obj, indent=2, ensure_ascii=False)
    json_min    = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)

    t_stl    = toks(stl)
    t_pretty = toks(json_pretty)
    t_min    = toks(json_min)

    d_pretty = (t_pretty - t_stl) / t_stl * 100
    d_min    = (t_min    - t_stl) / t_stl * 100

    print(f"{label:<22} {t_stl:>8} {t_pretty:>12} {t_min:>10} "
          f"{d_pretty:>+9.1f}% {d_min:>+7.1f}%")

    total_stl    += t_stl
    total_pretty += t_pretty
    total_min    += t_min

print("─" * 78)
d_pretty_tot = (total_pretty - total_stl) / total_stl * 100
d_min_tot    = (total_min    - total_stl) / total_stl * 100
print(f"{'TOTAL':<22} {total_stl:>8} {total_pretty:>12} {total_min:>10} "
      f"{d_pretty_tot:>+9.1f}% {d_min_tot:>+7.1f}%")

print()
print(f"STL uses {total_stl} tokens.")
print(f"JSON-pretty uses {total_pretty} ({d_pretty_tot:+.1f}% vs STL) "
      f"→ STL saves {(total_pretty - total_stl)/total_pretty*100:.1f}%")
print(f"JSON-min    uses {total_min} ({d_min_tot:+.1f}% vs STL) "
      f"→ STL saves {(total_min - total_stl)/total_min*100:.1f}%")

# Audit: full text of one sample side-by-side
print("\n" + "═" * 78)
print("AUDIT: full text of sample #4 (empirical lesson)")
print("═" * 78)
_, stl, obj = samples[3]
print("\n── STL ──")
print(stl)
print(f"[{toks(stl)} tokens, {len(stl)} chars]")
print("\n── JSON (pretty) ──")
jp = json.dumps(obj, indent=2, ensure_ascii=False)
print(jp)
print(f"[{toks(jp)} tokens, {len(jp)} chars]")
print("\n── JSON (minified) ──")
jm = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
print(jm)
print(f"[{toks(jm)} tokens, {len(jm)} chars]")
