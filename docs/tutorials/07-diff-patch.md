# Tutorial 7: Diff & Patch

Learn how to compare STL documents and apply patches.

**What you'll learn:**
- Compare documents with `stl_diff()`
- Read diff entries and summaries
- Render human-readable diffs with `diff_to_text()`
- Export diffs as JSON with `diff_to_dict()`
- Apply patches with `stl_patch()`

**Prerequisites:** [Tutorial 6: Streaming I/O](06-streaming-io.md)

---

## Step 1: Compute a Diff

```python
from stl_parser import parse, stl_diff

before = parse("""
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85, strength=0.8)
[Wind] -> [Erosion] ::mod(rule="causal", confidence=0.70)
[Sun] -> [Evaporation] ::mod(rule="causal", confidence=0.90)
""")

after = parse("""
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.90, strength=0.85)
[Sun] -> [Evaporation] ::mod(rule="causal", confidence=0.90)
[Heat] -> [Drought] ::mod(rule="causal", confidence=0.75)
""")

diff = stl_diff(before, after)
```

## Step 2: Read the Summary

```python
print(f"Added:     {diff.summary.added}")      # 1 (Heat->Drought)
print(f"Removed:   {diff.summary.removed}")     # 1 (Wind->Erosion)
print(f"Modified:  {diff.summary.modified}")     # 1 (Rain->Flooding)
print(f"Unchanged: {diff.summary.unchanged}")    # 1 (Sun->Evaporation)
print(f"Is empty:  {diff.is_empty}")             # False
```

## Step 3: Inspect Diff Entries

Each `DiffEntry` describes one change:

```python
for entry in diff.entries:
    print(f"[{entry.op.value}] {entry.key}")

    if entry.modifier_changes:
        for change in entry.modifier_changes:
            print(f"  {change.field}: {change.old_value} -> {change.new_value}")
```

Output:

```
[modify] [Rain] -> [Flooding]
  confidence: 0.85 -> 0.9
  strength: 0.8 -> 0.85
[remove] [Wind] -> [Erosion]
[add] [Heat] -> [Drought]
```

### Filter by Operation Type

```python
from stl_parser.diff import DiffOp

added = [e for e in diff.entries if e.op == DiffOp.ADD]
removed = [e for e in diff.entries if e.op == DiffOp.REMOVE]
modified = [e for e in diff.entries if e.op == DiffOp.MODIFY]

# Or use convenience properties
added = diff.added
removed = diff.removed
modified = diff.modified
```

## Step 4: Render as Text

`diff_to_text()` produces a human-readable format with `+`/`-`/`~` markers:

```python
from stl_parser import stl_diff
from stl_parser.diff import diff_to_text

text = diff_to_text(diff)
print(text)
```

Output:

```
~ [Rain] -> [Flooding]
    confidence: 0.85 -> 0.9
    strength: 0.8 -> 0.85
- [Wind] -> [Erosion] ::mod(confidence=0.7, rule="causal")
+ [Heat] -> [Drought] ::mod(confidence=0.75, rule="causal")

1 added, 1 removed, 1 modified, 1 unchanged
```

## Step 5: Export as JSON

```python
from stl_parser.diff import diff_to_dict
import json

d = diff_to_dict(diff)
print(json.dumps(d, indent=2))
```

This produces a JSON-compatible dict with `"entries"` and `"summary"` keys — useful for storing diffs or passing them between systems.

## Step 6: Apply a Patch

`stl_patch()` transforms a document by applying a diff:

```python
from stl_parser import parse, stl_diff, stl_patch

before = parse("""
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.85)
[Wind] -> [Erosion] ::mod(rule="causal", confidence=0.70)
""")

after = parse("""
[Rain] -> [Flooding] ::mod(rule="causal", confidence=0.90)
[Heat] -> [Drought] ::mod(rule="causal", confidence=0.75)
""")

# Compute diff
diff = stl_diff(before, after)

# Apply patch to transform 'before' into 'after'
patched = stl_patch(before, diff)

print(f"Patched statements: {len(patched.statements)}")
for s in patched.statements:
    print(f"  {s}")
```

## Step 7: Ignore Order

By default, `stl_diff()` ignores statement order (`ignore_order=True`). Reordering statements does not generate diff entries:

```python
a = parse("[X] -> [Y]\n[A] -> [B]")
b = parse("[A] -> [B]\n[X] -> [Y]")

diff = stl_diff(a, b)
print(diff.is_empty)  # True — same content, different order
```

To treat order as significant:

```python
diff = stl_diff(a, b, ignore_order=False)
```

## Step 8: CLI Usage

```bash
# Text diff (default)
stl diff before.stl after.stl

# JSON diff (for machine consumption)
stl diff before.stl after.stl --format json

# Summary only
stl diff before.stl after.stl --summary

# Quiet mode (exit code only: 0=identical, 1=different)
stl diff before.stl after.stl --quiet

# Apply a JSON patch
stl diff before.stl after.stl --format json > changes.json
stl patch before.stl changes.json --output patched.stl
```

---

## Complete Example

```python
from stl_parser import parse, stl_diff, stl_patch
from stl_parser.diff import diff_to_text, diff_to_dict
import json

# Version 1 of a knowledge base
v1 = parse("""
[Smoking] -> [Lung_Cancer] ::mod(rule="causal", confidence=0.88, strength=0.80)
[Exercise] -> [Heart_Health] ::mod(rule="causal", confidence=0.85, strength=0.75)
[Sugar] -> [Diabetes] ::mod(rule="causal", confidence=0.75, strength=0.60)
""")

# Version 2 with updates
v2 = parse("""
[Smoking] -> [Lung_Cancer] ::mod(rule="causal", confidence=0.92, strength=0.85)
[Exercise] -> [Heart_Health] ::mod(rule="causal", confidence=0.85, strength=0.75)
[Pollution] -> [Respiratory_Disease] ::mod(rule="causal", confidence=0.80, strength=0.70)
""")

# Compute diff
diff = stl_diff(v1, v2)

# Display
print("=== Knowledge Base Changes ===")
print(diff_to_text(diff))

# Export for version control
with open("v1_to_v2.json", "w") as f:
    json.dump(diff_to_dict(diff), f, indent=2)

# Apply patch to reproduce v2
patched = stl_patch(v1, diff)
print(f"\nPatched document has {len(patched.statements)} statements")
```

---

**Next:** [Tutorial 8: CLI Tools](08-cli-tools.md)
