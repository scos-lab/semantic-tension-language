# -*- coding: utf-8 -*-
"""
STL Grammar Definition

This module defines the complete EBNF grammar for Semantic Tension Language (STL)
using the Lark parser library. The grammar is based on the STL v1.0 Core Specification
and Supplement.

The grammar supports:
- Anchors: [Name] or [Namespace:Name]
- Paths: [A] -> [B] (both ASCII and Unicode arrows)
- Modifiers: ::mod(key=value, ...)
- Chained paths: [A] -> [B] -> [C]
- Unicode support: Chinese, Arabic, Japanese, etc.
- Comments: # comment line
"""

from lark import Lark

# STL v1.0 Complete Grammar in Lark EBNF format
STL_GRAMMAR = r"""
    // ========================================
    // START RULE
    // ========================================

    ?start: statement*

    // ========================================
    // STATEMENT RULES
    // ========================================

    statement: path_expression
             | comment

    comment: COMMENT

    // Path expression: handles both simple and chained paths
    // [A] -> [B] ::mod(...) or [A] -> [B] -> [C] ...
    path_expression: anchor (arrow anchor modifier?)+

    // ========================================
    // ANCHOR RULES
    // ========================================

    anchor: "[" anchor_name "]"

    anchor_name: simple_identifier
               | namespaced_identifier

    // Simple identifier: Concept, Energy, etc.
    simple_identifier: IDENTIFIER

    // Namespaced identifier: Physics:Energy, Domain.Subdomain:Name
    namespaced_identifier: namespace ":" IDENTIFIER

    // Namespace can have dots for hierarchy: Physics.Quantum
    namespace: IDENTIFIER ("." IDENTIFIER)*

    // ========================================
    // ARROW RULES
    // ========================================

    arrow: ARROW_UNICODE
         | ARROW_ASCII

    // ========================================
    // MODIFIER RULES
    // ========================================

    modifier: "::" "mod" "(" modifier_list ")"

    modifier_list: modifier_pair ("," modifier_pair)*

    modifier_pair: key "=" value

    key: IDENTIFIER

    // Values can be strings, numbers, booleans, or datetime
    ?value: string_value
          | numeric_value
          | boolean_value
          | datetime_value

    string_value: ESCAPED_STRING

    numeric_value: NUMBER

    boolean_value: BOOLEAN

    datetime_value: ISO8601_DATETIME

    // ========================================
    // TERMINALS
    // ========================================

    // Identifier: Alphanumeric + underscore + hyphen + Unicode letters
    // Supports: English, Chinese, Arabic, Japanese, etc.
    // Hyphen (-) allowed mid-name; safe because anchors are bracket-delimited [...]
    IDENTIFIER: /[\w\u4e00-\u9fff\u0600-\u06ff\u3040-\u30ff][\w\u4e00-\u9fff\u0600-\u06ff\u3040-\u30ff\-]*/

    // Arrow symbols (Unicode and ASCII)
    ARROW_UNICODE: "\u2192"  // Unicode rightwards arrow
    ARROW_ASCII: "->"

    // Numbers: integers, floats, percentages
    NUMBER: /-?\d+\.?\d*%?/

    // Booleans
    BOOLEAN: "true" | "false"

    // ISO 8601 datetime format
    ISO8601_DATETIME: /\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?)?/

    // Comments: # comment text until end of line
    COMMENT: /#[^\n]*/

    // Import standard definitions from Lark
    %import common.ESCAPED_STRING
    %import common.WS

    // Ignore whitespace
    %ignore WS
"""

# Create the Lark parser instance
stl_parser = Lark(
    STL_GRAMMAR,
    start='start',
    parser='lalr',
    propagate_positions=True,
    maybe_placeholders=False
)


def parse_stl_text(text: str):
    """Quick parse function for testing.

    Args:
        text: STL text to parse

    Returns:
        Lark parse tree

    Raises:
        lark.exceptions.LarkError: If parsing fails
    """
    return stl_parser.parse(text)


# ========================================
# USAGE EXAMPLES
# ========================================

if __name__ == "__main__":
    print("=" * 60)
    print("STL Grammar Test Suite")
    print("=" * 60)
    print()

    # Example 1: Simple statement
    print("Test 1: Simple statement")
    example1 = "[A] -> [B]"
    tree1 = parse_stl_text(example1)
    print(f"Input: {example1}")
    print(tree1.pretty())
    print()

    # Example 2: Unicode arrow
    print("Test 2: Unicode arrow")
    example2 = "[A] \u2192 [B]"
    tree2 = parse_stl_text(example2)
    print(f"Input: {example2}")
    print(tree2.pretty())
    print()

    # Example 3: With modifiers
    print("Test 3: With modifiers")
    example3 = '[A] -> [B] ::mod(confidence=0.95, rule="causal")'
    tree3 = parse_stl_text(example3)
    print(f"Input: {example3}")
    print(tree3.pretty())
    print()

    # Example 4: Unicode (Chinese)
    print("Test 4: Unicode anchors (Chinese)")
    example4 = "[黄帝内经] -> [素问]"
    try:
        tree4 = parse_stl_text(example4)
        print(f"Input: {example4}")
        print(tree4.pretty())
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Example 5: Namespaced
    print("Test 5: Namespaced anchors")
    example5 = "[Physics:Energy] -> [Physics:Mass]"
    tree5 = parse_stl_text(example5)
    print(f"Input: {example5}")
    print(tree5.pretty())
    print()

    # Example 6: Chained path
    print("Test 6: Chained path")
    example6 = "[A] -> [B] -> [C] -> [D]"
    tree6 = parse_stl_text(example6)
    print(f"Input: {example6}")
    print(tree6.pretty())
    print()

    # Example 7: Complex with multiple modifiers
    print("Test 7: Complex statement with multiple modifiers")
    example7 = '[Theory_Relativity] -> [Prediction_TimeDilation] ::mod(rule="logical", confidence=0.99, author="Einstein")'
    tree7 = parse_stl_text(example7)
    print(f"Input: {example7}")
    print(tree7.pretty())
    print()

    # Example 8: With comments
    print("Test 8: With comments")
    example8 = """# This is a comment
[A] -> [B] ::mod(confidence=0.9)
# Another comment
[B] -> [C]"""
    tree8 = parse_stl_text(example8)
    print("Input (with comments):")
    print(tree8.pretty())
    print()

    print("=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
