# -*- coding: utf-8 -*-
"""
STL Diff / Patch Module — Semantic difference and patching for STL documents.

Computes semantic differences between two ParseResult documents and applies
patches to transform one document into another.

Example usage::

    from stl_parser import parse, stl_diff, stl_patch, diff_to_text

    a = parse('[A] -> [B] ::mod(confidence=0.8)')
    b = parse('[A] -> [B] ::mod(confidence=0.95)')

    diff = stl_diff(a, b)
    print(diff_to_text(diff))
    # ~ [A] -> [B]
    #     confidence: 0.8 -> 0.95

    patched = stl_patch(a, diff)
    assert patched.statements[0].modifiers.confidence == 0.95
"""

from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from pydantic import BaseModel, Field

from .errors import ErrorCode, STLDiffError

if TYPE_CHECKING:
    from .models import ParseResult, Statement


# ========================================
# DATA MODELS
# ========================================

class DiffOp(str, Enum):
    """Type of diff operation."""
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"


class ModifierChange(BaseModel):
    """A single modifier field change."""
    field: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None


class DiffEntry(BaseModel):
    """One change between two documents."""
    op: DiffOp
    key: str  # Human-readable: "[A] -> [B]"
    statement_a: Optional[Any] = None  # Statement from doc A
    statement_b: Optional[Any] = None  # Statement from doc B
    index_a: Optional[int] = None
    index_b: Optional[int] = None
    modifier_changes: List[ModifierChange] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}


class DiffSummary(BaseModel):
    """Aggregate diff statistics."""
    added: int = 0
    removed: int = 0
    modified: int = 0
    unchanged: int = 0
    total_a: int = 0
    total_b: int = 0


class STLDiff(BaseModel):
    """Result of comparing two STL documents."""
    entries: List[DiffEntry] = Field(default_factory=list)
    summary: DiffSummary = Field(default_factory=DiffSummary)

    model_config = {"arbitrary_types_allowed": True}

    @property
    def is_empty(self) -> bool:
        """True if documents are identical."""
        return len(self.entries) == 0

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.op == DiffOp.ADD]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.op == DiffOp.REMOVE]

    @property
    def modified(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.op == DiffOp.MODIFY]


# ========================================
# INTERNAL HELPERS
# ========================================

def _statement_key(stmt: "Statement") -> Tuple:
    """Compute the identity key for a statement."""
    return (
        stmt.source.namespace,
        stmt.source.name,
        stmt.target.namespace,
        stmt.target.name,
        stmt.arrow,
    )


def _key_label(stmt: "Statement") -> str:
    """Human-readable key label."""
    src = str(stmt.source)
    tgt = str(stmt.target)
    return f"{src} -> {tgt}"


def _modifier_dict(stmt: "Statement") -> Dict[str, Any]:
    """Extract all modifier fields as a flat dict."""
    if stmt.modifiers is None:
        return {}
    d = stmt.modifiers.model_dump(exclude_none=True, exclude={"custom"})
    if stmt.modifiers.custom:
        d.update(stmt.modifiers.custom)
    return d


def _compute_modifier_changes(
    stmt_a: "Statement", stmt_b: "Statement"
) -> List[ModifierChange]:
    """Compare modifiers between two statements at field granularity."""
    dict_a = _modifier_dict(stmt_a)
    dict_b = _modifier_dict(stmt_b)

    changes: List[ModifierChange] = []
    all_keys = sorted(set(dict_a.keys()) | set(dict_b.keys()))

    for key in all_keys:
        val_a = dict_a.get(key)
        val_b = dict_b.get(key)
        if val_a != val_b:
            changes.append(ModifierChange(field=key, old_value=val_a, new_value=val_b))

    # Also check path_type
    if stmt_a.path_type != stmt_b.path_type:
        changes.append(ModifierChange(
            field="path_type",
            old_value=stmt_a.path_type.value if stmt_a.path_type else None,
            new_value=stmt_b.path_type.value if stmt_b.path_type else None,
        ))

    return changes


def _build_key_groups(
    statements: List["Statement"],
) -> Dict[Tuple, List[Tuple[int, "Statement"]]]:
    """Group statements by identity key, preserving index."""
    groups: Dict[Tuple, List[Tuple[int, "Statement"]]] = defaultdict(list)
    for i, stmt in enumerate(statements):
        groups[_statement_key(stmt)].append((i, stmt))
    return groups


# ========================================
# PUBLIC API
# ========================================

def stl_diff(
    a: "ParseResult",
    b: "ParseResult",
    *,
    ignore_order: bool = True,
) -> STLDiff:
    """Compute semantic diff between two STL documents.

    Args:
        a: Source document (before).
        b: Target document (after).
        ignore_order: If True (default), statement order does not generate
            diff entries.

    Returns:
        STLDiff with all changes needed to transform A into B.
    """
    entries: List[DiffEntry] = []
    unchanged = 0

    groups_a = _build_key_groups(a.statements)
    groups_b = _build_key_groups(b.statements)

    all_keys = sorted(set(groups_a.keys()) | set(groups_b.keys()))

    for key in all_keys:
        list_a = groups_a.get(key, [])
        list_b = groups_b.get(key, [])

        # Sort within group by string representation for deterministic matching
        list_a_sorted = sorted(list_a, key=lambda t: str(t[1]))
        list_b_sorted = sorted(list_b, key=lambda t: str(t[1]))

        # Match pairs positionally
        pairs = min(len(list_a_sorted), len(list_b_sorted))

        for j in range(pairs):
            idx_a, stmt_a = list_a_sorted[j]
            idx_b, stmt_b = list_b_sorted[j]

            if stmt_a == stmt_b:
                unchanged += 1
            else:
                mod_changes = _compute_modifier_changes(stmt_a, stmt_b)
                entries.append(DiffEntry(
                    op=DiffOp.MODIFY,
                    key=_key_label(stmt_a),
                    statement_a=stmt_a,
                    statement_b=stmt_b,
                    index_a=idx_a,
                    index_b=idx_b,
                    modifier_changes=mod_changes,
                ))

        # Leftover A → REMOVE
        for j in range(pairs, len(list_a_sorted)):
            idx_a, stmt_a = list_a_sorted[j]
            entries.append(DiffEntry(
                op=DiffOp.REMOVE,
                key=_key_label(stmt_a),
                statement_a=stmt_a,
                index_a=idx_a,
            ))

        # Leftover B → ADD
        for j in range(pairs, len(list_b_sorted)):
            idx_b, stmt_b = list_b_sorted[j]
            entries.append(DiffEntry(
                op=DiffOp.ADD,
                key=_key_label(stmt_b),
                statement_b=stmt_b,
                index_b=idx_b,
            ))

    summary = DiffSummary(
        added=sum(1 for e in entries if e.op == DiffOp.ADD),
        removed=sum(1 for e in entries if e.op == DiffOp.REMOVE),
        modified=sum(1 for e in entries if e.op == DiffOp.MODIFY),
        unchanged=unchanged,
        total_a=len(a.statements),
        total_b=len(b.statements),
    )

    return STLDiff(entries=entries, summary=summary)


def stl_patch(
    doc: "ParseResult",
    diff: STLDiff,
) -> "ParseResult":
    """Apply a diff to produce a new document.

    Args:
        doc: Original document (should match diff's source).
        diff: Diff to apply.

    Returns:
        New ParseResult equivalent to the diff's target.

    Raises:
        STLDiffError: If patch cannot be applied.
    """
    from .models import ParseResult as _ParseResult

    # Work with a mutable list copy
    result = list(doc.statements)

    # Track indices to remove (process in reverse to avoid shifting)
    indices_to_remove = set()

    # Process REMOVE entries
    for entry in diff.entries:
        if entry.op == DiffOp.REMOVE:
            if entry.index_a is not None and entry.index_a < len(result):
                if result[entry.index_a] == entry.statement_a:
                    indices_to_remove.add(entry.index_a)
                    continue
            # Fallback: search by content
            found = False
            for i, stmt in enumerate(result):
                if i not in indices_to_remove and stmt == entry.statement_a:
                    indices_to_remove.add(i)
                    found = True
                    break
            if not found:
                raise STLDiffError(
                    code=ErrorCode.E951_PATCH_STATEMENT_NOT_FOUND,
                    message=f"Cannot remove statement: {entry.key} (not found in document)",
                )

    # Process MODIFY entries (replace in-place)
    for entry in diff.entries:
        if entry.op == DiffOp.MODIFY:
            if entry.index_a is not None and entry.index_a < len(result):
                if result[entry.index_a] == entry.statement_a:
                    result[entry.index_a] = entry.statement_b
                    continue
            # Fallback: search by content
            found = False
            for i, stmt in enumerate(result):
                if i not in indices_to_remove and stmt == entry.statement_a:
                    result[i] = entry.statement_b
                    found = True
                    break
            if not found:
                raise STLDiffError(
                    code=ErrorCode.E951_PATCH_STATEMENT_NOT_FOUND,
                    message=f"Cannot modify statement: {entry.key} (not found in document)",
                )

    # Remove marked indices (reverse order)
    for i in sorted(indices_to_remove, reverse=True):
        result.pop(i)

    # Process ADD entries (append; insertion position is best-effort)
    add_entries = sorted(
        [e for e in diff.entries if e.op == DiffOp.ADD],
        key=lambda e: e.index_b if e.index_b is not None else len(result),
    )
    for entry in add_entries:
        idx = entry.index_b if entry.index_b is not None else len(result)
        idx = min(idx, len(result))
        result.insert(idx, entry.statement_b)

    return _ParseResult(
        statements=result,
        is_valid=doc.is_valid,
    )


def diff_to_text(diff: STLDiff) -> str:
    """Render diff as human-readable text.

    Format::

        + [A] -> [B] ::mod(confidence=0.95)
        - [C] -> [D] ::mod(rule="causal")
        ~ [E] -> [F]
            confidence: 0.8 -> 0.95

    Returns:
        Multi-line string with diff markers.
    """
    if diff.is_empty:
        return "No differences."

    lines: List[str] = []

    for entry in diff.entries:
        if entry.op == DiffOp.ADD:
            lines.append(f"+ {entry.statement_b}")
        elif entry.op == DiffOp.REMOVE:
            lines.append(f"- {entry.statement_a}")
        elif entry.op == DiffOp.MODIFY:
            lines.append(f"~ {entry.key}")
            for mc in entry.modifier_changes:
                old = mc.old_value if mc.old_value is not None else "(none)"
                new = mc.new_value if mc.new_value is not None else "(none)"
                lines.append(f"    {mc.field}: {old} -> {new}")

    # Summary line
    s = diff.summary
    lines.append(f"\n{s.added} added, {s.removed} removed, {s.modified} modified, {s.unchanged} unchanged")

    return "\n".join(lines)


def diff_to_dict(diff: STLDiff) -> dict:
    """Serialize diff as a JSON-compatible dict.

    Returns:
        Dict with "entries" and "summary" keys.
    """
    entries = []
    for entry in diff.entries:
        d: Dict[str, Any] = {
            "op": entry.op.value,
            "key": entry.key,
        }
        if entry.statement_a is not None:
            d["statement_a"] = str(entry.statement_a)
        if entry.statement_b is not None:
            d["statement_b"] = str(entry.statement_b)
        if entry.index_a is not None:
            d["index_a"] = entry.index_a
        if entry.index_b is not None:
            d["index_b"] = entry.index_b
        if entry.modifier_changes:
            d["modifier_changes"] = [
                {"field": mc.field, "old_value": mc.old_value, "new_value": mc.new_value}
                for mc in entry.modifier_changes
            ]
        entries.append(d)

    return {
        "entries": entries,
        "summary": diff.summary.model_dump(),
    }
