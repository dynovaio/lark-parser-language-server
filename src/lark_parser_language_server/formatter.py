from typing import Any, Callable, cast

from lark import Token

from lark_parser_language_server.syntax_tree.nodes import (
    Ast,
    AstNode,
    Comment,
    Declare,
    Expansion,
    Expr,
    Extend,
    Ignore,
    Import,
    Maybe,
    Override,
    Range,
    Rule,
    TemplateUsage,
    Term,
)

DEFAULT_INDENT = " " * 4


def _format_comment(  # pylint: disable=unused-argument
    comment: Comment,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    return str(comment.content).strip()


def _format_declare(  # pylint: disable=unused-argument
    declare: Declare,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    symbols = " ".join([str(symbol) for symbol in declare.symbols])
    return f"%declare {symbols}"


def _format_expansion(  # pylint: disable=unused-argument
    expansion: Expansion,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    alias = f"-> {str(expansion.alias)}" if expansion.alias else ""
    expressions = " ".join(
        [_format_ast_node(expression).strip() for expression in expansion.expressions]
    )
    return f"{expressions} {alias}".strip()


def _format_expr(  # pylint: disable=unused-argument
    expr: Expr,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    operators = (
        "".join([str(operator) for operator in expr.operators[:2]])
        if expr.operators
        else ""
    )

    if expr.operators and len(expr.operators) == 3:
        operators = f"{operators}..{str(expr.operators[2])}"

    wrap_within_parens = isinstance(expr.atom, list)
    atom_as_list = expr.atom if isinstance(expr.atom, list) else [expr.atom]
    atom = " | ".join([_format_ast_node(cast(AstNode, item)) for item in atom_as_list])
    if wrap_within_parens:
        atom = f"({atom})"

    return f"{atom}{operators}".strip()


def _format_extend(  # pylint: disable=unused-argument
    extend: Extend,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    return f"%extend {_format_ast_node(extend.definition)}".strip()


def _format_ignore(  # pylint: disable=unused-argument
    ignore: Ignore,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    expansions = "\n    | ".join(
        [_format_ast_node(expansion).strip() for expansion in ignore.expansions]
    )
    return f"%ignore {expansions}".strip()


def _format_import(  # pylint: disable=unused-argument
    import_: Import,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    alias = f"-> {str(import_.alias)} " if import_.alias else ""

    symbols = ", ".join([str(symbol) for symbol in import_.symbols])
    symbols = f"({symbols})" if len(import_.symbols) > 1 else symbols

    separator = " " if len(import_.symbols) > 1 else "."

    return f"%import {import_.path}{separator}{symbols} {alias}".strip()


def _format_maybe(  # pylint: disable=unused-argument
    maybe: Maybe,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    expansions = " | ".join(
        [_format_ast_node(expansion).strip() for expansion in maybe.expansions]
    )
    return f"[{expansions}]".strip()


def _format_override(  # pylint: disable=unused-argument
    override: Override,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    return f"%extend {_format_ast_node(override.definition)}".strip()


def _format_range(  # pylint: disable=unused-argument
    range_: Range,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    return f"{range_.start}..{range_.end}"


def _format_rule(  # pylint: disable=unused-argument
    rule: Rule,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    modifiers = "".join([modifier for modifier in rule.modifiers if modifier != "_"])
    name = str(rule.name)
    parameters = (
        ", ".join([str(parameter) for parameter in rule.parameters])
        if rule.parameters
        else ""
    )
    parameters = f"{{{parameters}}}" if parameters else ""
    priority = f".{rule.priority}" if rule.priority else ""
    expansions = f"\n{indent * level}| ".join(
        [_format_ast_node(expansion) for expansion in rule.expansions]
    )
    return f"{modifiers}{name}{parameters}{priority}: {expansions}"


def _format_template_usage(  # pylint: disable=unused-argument
    template_usage: TemplateUsage,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    rule = str(template_usage.rule)
    parameters = ", ".join(
        [
            _format_ast_node(cast(AstNode, argument))
            for argument in template_usage.arguments
        ]
    )
    return f"{rule}{{{parameters}}}"


def _format_term(  # pylint: disable=unused-argument
    term: Term,
    indent: str = DEFAULT_INDENT,
    level: int = 1,
) -> str:
    modifiers = "".join([modifier for modifier in term.modifiers if modifier != "_"])
    name = str(term.name)
    priority = f".{term.priority}" if term.priority else ""
    expansions = f"\n{indent * level}| ".join(
        [_format_ast_node(expansion) for expansion in term.expansions]
    )

    return f"{modifiers}{name}{priority}: {expansions}"


def _format_ast_node(node: Any, indent: str = DEFAULT_INDENT, level: int = 1) -> str:
    formatter_map: dict[Any, Callable[[Any, str, int], str]] = {
        Comment: _format_comment,
        Declare: _format_declare,
        Expansion: _format_expansion,
        Expr: _format_expr,
        Extend: _format_extend,
        Ignore: _format_ignore,
        Import: _format_import,
        Maybe: _format_maybe,
        Override: _format_override,
        Range: _format_range,
        Rule: _format_rule,
        TemplateUsage: _format_template_usage,
        Term: _format_term,
    }

    node_type = type(node)

    if node_type in formatter_map:
        return formatter_map[node_type](node, indent, level)

    if isinstance(node, Token):
        return str(node)

    return f'"{str(node)}"'


class Formatter:
    def format(self, ast: Ast, indent: str = DEFAULT_INDENT) -> str:
        formatted_nodes = [
            _format_ast_node(node, indent=indent).strip() for node in ast.statements
        ]
        return "\n\n".join(formatted_nodes).strip()

    def format_ast_node(self, node: AstNode, indent: str = DEFAULT_INDENT) -> str:
        return _format_ast_node(node, indent=indent)


FORMATTER = Formatter()
