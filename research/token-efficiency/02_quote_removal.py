"""Measure token savings from removing quotes around STL modifier values.

Hypothesis (intuitive): removing the quote pair around string values in
::mod(...) should save tokens because there are fewer characters.

Counter-finding (this script): savings ≈ 0% because BPE has already merged
the high-frequency pattern `="` into a single token. Removing the opening
quote saves nothing; the closing quote may or may not be its own token
depending on neighbouring characters.

Variants tested per sample:
  (A) Current STL — quoted string values: `rule="empirical"`
  (B) Hybrid — only short identifier/enum values unquoted; long free-text
      fields keep quotes
  (C) Fully unquoted — no quotes anywhere

First conducted: 2026-05-13 by Syn-claude (Opus 4.7)
"""
import tiktoken
ENC = tiktoken.get_encoding("cl100k_base")
def t(s: str) -> int:
    return len(ENC.encode(s))

samples = [
    ("Simple typed",
     '[Cat] → [Mammal] ::mod(rule="definitional", confidence=0.99)',
     '[Cat] → [Mammal] ::mod(rule=definitional, confidence=0.99)',
     '[Cat] → [Mammal] ::mod(rule=definitional, confidence=0.99)'),

    ("Causal",
     '[Heavy_Rain] → [Flooding] ::mod(rule="causal", confidence=0.85, strength=0.80, source="NOAA_2024_report")',
     '[Heavy_Rain] → [Flooding] ::mod(rule=causal, confidence=0.85, strength=0.80, source="NOAA_2024_report")',
     '[Heavy_Rain] → [Flooding] ::mod(rule=causal, confidence=0.85, strength=0.80, source=NOAA_2024_report)'),

    ("Empirical lesson",
     '[Refresh_Token] → [Auth_Failure] ::mod(action="causes", rule="empirical", lesson="Testing 模式 OAuth 7 天过期", occurred_time="2026-04-23", confidence=0.95)',
     '[Refresh_Token] → [Auth_Failure] ::mod(action=causes, rule=empirical, lesson="Testing 模式 OAuth 7 天过期", occurred_time=2026-04-23, confidence=0.95)',
     '[Refresh_Token] → [Auth_Failure] ::mod(action=causes, rule=empirical, lesson=Testing 模式 OAuth 7 天过期, occurred_time=2026-04-23, confidence=0.95)'),

    ("Long description",
     '[STGEdge] → [Two_Field_Model] ::mod(rule="definitional", confidence=0.98, description="edge has confidence and salience fields, salience decays but confidence does not")',
     '[STGEdge] → [Two_Field_Model] ::mod(rule=definitional, confidence=0.98, description="edge has confidence and salience fields, salience decays but confidence does not")',
     '[STGEdge] → [Two_Field_Model] ::mod(rule=definitional, confidence=0.98, description=edge has confidence and salience fields, salience decays but confidence does not)'),

    ("CJK heavy",
     '[黄帝内经] → [中医理论基础] ::mod(rule="definitional", confidence=0.95, domain="traditional_chinese_medicine", author="未知_战国时期", description="中医基础理论的奠基之作，涵盖阴阳五行、脏腑经络")',
     '[黄帝内经] → [中医理论基础] ::mod(rule=definitional, confidence=0.95, domain=traditional_chinese_medicine, author=未知_战国时期, description="中医基础理论的奠基之作，涵盖阴阳五行、脏腑经络")',
     '[黄帝内经] → [中医理论基础] ::mod(rule=definitional, confidence=0.95, domain=traditional_chinese_medicine, author=未知_战国时期, description=中医基础理论的奠基之作，涵盖阴阳五行、脏腑经络)'),
]

print(f"{'Sample':<22} {'A:quoted':>10} {'B:hybrid':>10} {'C:none':>8} "
      f"{'B vs A':>8} {'C vs A':>8}")
print("─" * 76)
tA = tB = tC = 0
for label, a, b, c in samples:
    a_t, b_t, c_t = t(a), t(b), t(c)
    tA += a_t; tB += b_t; tC += c_t
    print(f"{label:<22} {a_t:>10} {b_t:>10} {c_t:>8} "
          f"{(b_t-a_t)/a_t*100:>+7.1f}% {(c_t-a_t)/a_t*100:>+7.1f}%")
print("─" * 76)
print(f"{'TOTAL':<22} {tA:>10} {tB:>10} {tC:>8} "
      f"{(tB-tA)/tA*100:>+7.1f}% {(tC-tA)/tA*100:>+7.1f}%")
print()
print(f"Hybrid (only short fields unquoted) saves: {(tA-tB)/tA*100:.1f}%")
print(f"Full no-quotes saves:                      {(tA-tC)/tA*100:.1f}%")

# BPE inspection — why savings are ~0%
print("\n" + "═" * 76)
print("BPE INSPECTION — why removing quotes saves almost nothing")
print("═" * 76)
inspect = [
    'rule="causal"',
    'rule=causal',
    ', confidence=0.95',
    'lesson="Testing 模式 OAuth 7 天过期"',
    'lesson=Testing 模式 OAuth 7 天过期',
]
for s in inspect:
    ids = ENC.encode(s)
    tokens_visible = [ENC.decode([i]) for i in ids]
    print(f"\n  {repr(s)}")
    print(f"    {len(ids)} tokens: {tokens_visible}")
print()
print('Key finding: BPE has merged `="` into a single token (the pattern is')
print('  ubiquitous in JSON/Python/JS training data). Removing the opening')
print('  quote saves zero tokens because there is no separate `"` token to')
print('  drop — it was already part of `="`.')
