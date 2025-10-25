from typing import Optional, cast

from lark import Token

from lark_parser_language_server.symbol_table.flags import Directives, Kind, Modifiers
from lark_parser_language_server.symbol_table.symbol import Definition, Range, Reference
from lark_parser_language_server.syntax_tree.nodes import (
    AstNode,
    Declare,
    Expansion,
    Expr,
    Extend,
    Ignore,
    Import,
    Maybe,
    Override,
    Rule,
    TemplateUsage,
    Term,
)


def definitions_from_declare(declare: Declare) -> list[Definition]:
    return [
        Definition(
            name=str(symbol),
            kind=Kind.RULE if symbol.type == "RULE" else Kind.TERMINAL,
            range=Range.from_meta(declare.meta),
            selection_range=Range.from_token(cast(Token, symbol)),
            directives=Directives.DECLARED,
            ast_node=declare,
        )
        for symbol in declare.symbols
    ]


def definitions_from_expansions(
    expansions: list[Expansion], container: Definition
) -> list[Definition]:
    return [
        Definition(
            name=str(expansion.alias),
            kind=Kind.RULE,
            range=Range.from_meta(expansion.meta),
            selection_range=Range.from_token(expansion.alias),
            ast_node=container.ast_node,
            container=container,
        )
        for expansion in expansions
        if expansion.alias
    ]


def definitions_from_import(import_: Import) -> list[Definition]:
    if import_.alias:
        import_definition = Definition(
            name=str(import_.alias),
            kind=Kind.RULE if import_.alias.type == "RULE" else Kind.TERMINAL,
            range=Range.from_meta(import_.meta),
            selection_range=Range.from_token(import_.alias),
            directives=Directives.IMPORTED,
            ast_node=import_,
        )

        aliased_definitions = [
            Definition(
                name=str(symbol),
                kind=Kind.RULE if symbol.type == "RULE" else Kind.TERMINAL,
                range=import_definition.range,
                selection_range=Range.from_token(symbol),
                directives=Directives.IMPORTED,
                ast_node=import_,
            )
            for symbol in import_.symbols
        ]

        for definition in aliased_definitions:
            import_definition.append_child(definition)

        return [import_definition]

    return [
        Definition(
            name=str(symbol),
            kind=Kind.RULE if symbol.type == "RULE" else Kind.TERMINAL,
            range=Range.from_meta(import_.meta),
            selection_range=Range.from_token(symbol),
            directives=Directives.IMPORTED,
            ast_node=import_,
        )
        for symbol in import_.symbols
    ]


def definitions_from_rule_params(
    params: list[Token], parent: Definition
) -> list[Definition]:

    return [
        Definition(
            name=str(token),
            kind=Kind.RULE,
            range=parent.range,
            selection_range=Range.from_token(token),
            ast_node=parent.ast_node,
        )
        for token in params
    ]


def definitions_from_rule(rule: Rule) -> list[Definition]:
    rule_definition = Definition(
        name=str(rule.name),
        kind=Kind.RULE,
        range=Range.from_meta(rule.meta),
        selection_range=Range.from_token(rule.name),
        ast_node=rule,
    )

    for parameter_definition in definitions_from_rule_params(
        rule.parameters, rule_definition
    ):
        rule_definition.append_child(parameter_definition)

    for modifier in rule.modifiers:
        rule_definition.modifiers |= Modifiers.from_char(modifier)

    return [
        rule_definition,
        *definitions_from_expansions(
            rule.expansions,
            container=rule_definition,
        ),
    ]


def definitions_from_term(term: Term) -> list[Definition]:
    term_definition = Definition(
        name=str(term.name),
        kind=Kind.TERMINAL,
        range=Range.from_meta(term.meta),
        selection_range=Range.from_token(term.name),
        ast_node=term,
    )

    for modifier in term.modifiers:
        term_definition.modifiers |= Modifiers.from_char(modifier)

    return [
        term_definition,
        *definitions_from_expansions(
            term.expansions,
            container=term_definition,
        ),
    ]


def definitions_from_ast_node(node: AstNode) -> list[Definition]:
    extractor_map = {
        Declare: definitions_from_declare,
        Import: definitions_from_import,
        Rule: definitions_from_rule,
        Term: definitions_from_term,
    }

    extractor = extractor_map.get(type(node), lambda *args, **kwargs: [])  # type: ignore
    return extractor(node)


def references_from_declare(
    declare: Declare, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    if ast_node is None:
        ast_node = declare

    return [
        reference
        for symbol in declare.symbols
        for reference in references_from_ast_node(symbol, ast_node=ast_node)
    ]


def references_from_ignore(
    ignore: Ignore, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    if ast_node is None:
        ast_node = ignore

    return [
        reference
        for expansion in ignore.expansions
        for reference in references_from_ast_node(expansion, ast_node=ast_node)
    ]


def references_from_import(
    import_: Import, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    if ast_node is None:
        ast_node = import_

    return [
        *[
            reference
            for symbol in import_.symbols
            for reference in references_from_ast_node(symbol, ast_node=ast_node)
        ],
        *(
            references_from_ast_node(import_.alias, ast_node=ast_node)
            if import_.alias
            else []
        ),
    ]


def references_from_override(
    override: Override, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    if ast_node is None:
        ast_node = override

    return references_from_ast_node(override.definition, ast_node=ast_node)


def references_from_extend(
    extend: Extend, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    if ast_node is None:
        ast_node = extend

    return references_from_ast_node(extend.definition, ast_node=ast_node)


def references_from_template_usage(
    template_usage: TemplateUsage, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    return [
        *references_from_ast_node(template_usage.rule, ast_node=ast_node),
        *[
            reference
            for argument in template_usage.arguments
            for reference in references_from_ast_node(
                cast(AstNode | Token, argument),
                ast_node=ast_node,
            )
            if isinstance(argument, (AstNode, Token))
        ],
    ]


def references_from_maybe(
    maybe: Maybe, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    return [
        reference
        for expansion in maybe.expansions
        for reference in references_from_ast_node(expansion, ast_node=ast_node)
    ]


def references_from_expr(
    expr: Expr, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    if isinstance(expr.atom, (AstNode, Token)):
        return references_from_ast_node(expr.atom, ast_node=ast_node)

    return []


def references_from_expansion(
    expansion: Expansion, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    return [
        *[
            reference
            for expression in expansion.expressions
            for reference in references_from_ast_node(expression, ast_node=ast_node)
        ],
        *(
            references_from_ast_node(expansion.alias, ast_node=ast_node)
            if expansion.alias
            else []
        ),
    ]


def references_from_term(
    term: Term, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    if ast_node is None:
        ast_node = term
    return [
        *references_from_ast_node(term.name, ast_node=ast_node),
        *[
            reference
            for expansion in term.expansions
            for reference in references_from_ast_node(expansion, ast_node=ast_node)
        ],
    ]


def references_from_rule(
    rule: Rule, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    if ast_node is None:
        ast_node = rule

    return [
        *references_from_ast_node(rule.name, ast_node=ast_node),
        *[
            reference
            for param in rule.parameters
            for reference in references_from_ast_node(param, ast_node=ast_node)
        ],
        *[
            reference
            for expansion in rule.expansions
            for reference in references_from_ast_node(expansion, ast_node=ast_node)
        ],
    ]


def references_from_ast_node(
    node: AstNode | Token, ast_node: Optional[AstNode] = None
) -> list[Reference]:
    if isinstance(node, Token) and node.type in {"RULE", "TERMINAL"}:
        return [Reference.from_token(node, ast_node=ast_node)]

    extractor_map = {
        Declare: references_from_declare,
        Ignore: references_from_ignore,
        Import: references_from_import,
        Override: references_from_override,
        Extend: references_from_extend,
        TemplateUsage: references_from_template_usage,
        Maybe: references_from_maybe,
        Expr: references_from_expr,
        Expansion: references_from_expansion,
        Term: references_from_term,
        Rule: references_from_rule,
    }

    extractor = extractor_map.get(type(node), lambda *args, **kwargs: [])  # type: ignore

    return extractor(node, ast_node=ast_node)
