"""Measure token savings from §4.2 Default Value Omission (Protocol v1.1+).

When `confidence`, `rule`, and `strength` match their canonical defaults
(§4.2.1) they may be omitted from the surface form. A post-parse layer fills
them back in, so downstream consumers see no behavioural difference.

This script measures the token-cost reduction on five representative edge
styles (definitional / causal / empirical / role-spec).

Results (cl100k_base, 2026-05-13):
  Definitional (is_a)            −43%
  Causal                         −15%
  Empirical (with lesson)         −9%
  Definitional + description     −14%
  Role/spec                      −16%
  Average                       −17.6%

Savings scale with structural density: edges dominated by free-text fields
(long `lesson`, `description`) see smaller relative savings; short type/role
edges see the largest gains.

First conducted: 2026-05-13 by Syn-claude (Opus 4.7)
"""
import tiktoken
e = tiktoken.get_encoding("cl100k_base")
def t(s): return len(e.encode(s))

cases = [
    ("Definitional (typical)",
     '[Cat] -> [Mammal] ::mod(is_a="taxonomy", rule="definitional", confidence=1.0)',
     '[Cat] -> [Mammal] ::mod(is_a="taxonomy")'),
    ("Causal (typical)",
     '[Heavy_Rain] -> [Flooding] ::mod(action="triggers", rule="causal", strength=0.8, confidence=0.85)',
     '[Heavy_Rain] -> [Flooding] ::mod(action="triggers", strength=0.8, confidence=0.85)'),
    ("Empirical (typical)",
     '[Refresh_Token] -> [Auth_Failure] ::mod(action="causes", rule="empirical", lesson="Testing 模式 OAuth 7 天过期", occurred_time="2026-04-23", confidence=0.95)',
     '[Refresh_Token] -> [Auth_Failure] ::mod(action="causes", lesson="Testing 模式 OAuth 7 天过期", occurred_time="2026-04-23", confidence=0.95)'),
    ("Definitional w/ description",
     '[STGEdge] -> [Two_Field_Model] ::mod(rule="definitional", confidence=0.98, description="edge has confidence and salience fields")',
     '[STGEdge] -> [Two_Field_Model] ::mod(confidence=0.98, description="edge has confidence and salience fields")'),
    ("Role/spec",
     '[Phase12] -> [Spec:Phase12_STLC] ::mod(role="specification", rule="definitional", confidence=0.99, path="dev/spec.md")',
     '[Phase12] -> [Spec:Phase12_STLC] ::mod(role="specification", confidence=0.99, path="dev/spec.md")'),
]

print(f"{'Case':<32} {'before':>8} {'after':>8} {'save':>8}")
print("-" * 60)
total_b = total_a = 0
for name, b, a in cases:
    tb, ta = t(b), t(a)
    total_b += tb; total_a += ta
    print(f"{name:<32} {tb:>8} {ta:>8} {(tb-ta)/tb*100:>+7.1f}%")
print("-" * 60)
print(f"{'TOTAL':<32} {total_b:>8} {total_a:>8} {(total_b-total_a)/total_b*100:>+7.1f}%")
