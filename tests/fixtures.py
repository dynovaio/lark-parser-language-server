"""Test fixtures and sample data for lark-parser-language-server tests."""

# Sample valid Lark grammar
VALID_GRAMMAR = """
start: expression

expression: term
         | expression "+" term
         | expression "-" term

term: factor
    | term "*" factor
    | term "/" factor

factor: NUMBER
      | "(" expression ")"

NUMBER: /[0-9]+/
"""

# Sample grammar with parse error
INVALID_GRAMMAR = """
start: expression

expression: term
         | expression "+" term   -> add
         | expression "-" term   -> sub

term: factor
    | term "*" factor  -> mul
    | term "/" factor  -> div

factor: NUMBER
      | "(" expression ")"  # Missing closing quote

NUMBER: /[0-9]+/

%import common.WS
%ignore WS
"""

# Sample grammar with undefined references
UNDEFINED_REFERENCES_GRAMMAR = """
start: expr

expr: NUMBER
    | undefined_rule
    | UNDEFINED_TERMINAL

NUMBER: /[0-9]+/
"""

# Simple grammar for basic testing
SIMPLE_GRAMMAR = """
start: greeting

greeting: "hello" NAME

NAME: /[a-zA-Z]+/
"""

# Empty grammar
EMPTY_GRAMMAR = ""

# Grammar with comments
COMMENTED_GRAMMAR = """
// This is a comment
start: expression  // Another comment

// Rule definition
expression: NUMBER

NUMBER: /[0-9]+/
"""

# Grammar with imports
IMPORT_GRAMMAR = """
%import common.WORD
%import common.WS
%ignore WS

start: WORD+
"""

# Grammar with terminals and rules
MIXED_GRAMMAR = """
start: rule_name TERMINAL_NAME

rule_name: "test"

TERMINAL_NAME: /[A-Z]+/

%import common.WS
%ignore WS
"""
