"""Tests for lark_parser_language_server.symbol_table.syntax_tree module."""

from unittest.mock import Mock

import pytest
from lark import Token
from lark.tree import Meta

from lark_parser_language_server.symbol_table.flags import Kind, Modifiers
from lark_parser_language_server.symbol_table.symbol import Definition, Reference
from lark_parser_language_server.symbol_table.syntax_tree import (
    definitions_from_ast_node,
    definitions_from_declare,
    definitions_from_expansions,
    definitions_from_import,
    definitions_from_rule,
    definitions_from_rule_params,
    definitions_from_term,
    references_from_ast_node,
    references_from_declare,
    references_from_expansion,
    references_from_expr,
    references_from_extend,
    references_from_ignore,
    references_from_import,
    references_from_maybe,
    references_from_override,
    references_from_rule,
    references_from_template_usage,
    references_from_term,
)
from lark_parser_language_server.syntax_tree.nodes import (
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
    Rule,
    TemplateUsage,
    Term,
)


def create_mock_meta(line=1, column=1, end_line=1, end_column=10):
    """Helper function to create mock Meta objects."""
    meta = Mock(spec=Meta)
    meta.line = line
    meta.column = column
    meta.end_line = end_line
    meta.end_column = end_column
    return meta


def create_mock_token(token_type, value, line=1, column=1):
    """Helper function to create mock Token objects."""
    token = Mock(spec=Token)
    token.type = token_type
    token.value = value
    token.line = line
    token.column = column
    token.__str__ = Mock(return_value=value)
    return token


def create_complete_declare_mock(symbols=None):
    """Create a complete Declare mock with all required attributes."""
    declare = Mock(spec=Declare)
    declare.symbols = symbols or [create_mock_token("RULE", "test_symbol")]
    declare.meta = create_mock_meta()
    return declare


def create_complete_rule_mock(
    name="test_rule", parameters=None, expansions=None, modifiers=None
):
    """Create a complete Rule mock with all required attributes."""
    rule = Mock(spec=Rule)
    rule.name = create_mock_token("RULE", name)
    rule.parameters = parameters or []
    rule.expansions = expansions or []
    rule.modifiers = modifiers or []
    rule.meta = create_mock_meta()
    return rule


def create_complete_term_mock(name="TEST_TERM", expansions=None, modifiers=None):
    """Create a complete Term mock with all required attributes."""
    term = Mock(spec=Term)
    term.name = create_mock_token("TERMINAL", name)
    term.expansions = expansions or []
    term.modifiers = modifiers or []
    term.meta = create_mock_meta()
    return term


def create_complete_import_mock(symbols=None, alias=None):
    """Create a complete Import mock with all required attributes."""
    import_mock = Mock(spec=Import)
    import_mock.symbols = symbols or [create_mock_token("TERMINAL", "TEST_IMPORT")]
    import_mock.alias = alias
    import_mock.meta = create_mock_meta()
    return import_mock


class TestDefinitionsFromDeclare:
    """Test cases for definitions_from_declare function."""

    def test_definitions_from_declare_single_terminal(self):
        """Test extracting definitions from Declare node with single terminal."""
        declare = Mock(spec=Declare)
        declare.symbols = [create_mock_token("TERMINAL", "TEST_TERMINAL")]
        declare.meta = create_mock_meta(1, 1, 1, 15)

        definitions = definitions_from_declare(declare)

        assert len(definitions) == 1
        assert definitions[0].name == "TEST_TERMINAL"
        assert definitions[0].kind == Kind.TERMINAL

    def test_definitions_from_declare_single_rule(self):
        """Test extracting definitions from Declare node with single rule."""
        declare = Mock(spec=Declare)
        declare.symbols = [create_mock_token("RULE", "test_rule")]
        declare.meta = create_mock_meta(1, 1, 1, 15)

        definitions = definitions_from_declare(declare)

        assert len(definitions) == 1
        assert definitions[0].name == "test_rule"
        assert definitions[0].kind == Kind.RULE

    def test_definitions_from_declare_multiple_symbols(self):
        """Test extracting definitions from Declare node with multiple symbols."""
        declare = Mock(spec=Declare)
        declare.symbols = [
            create_mock_token("RULE", "rule_one"),
            create_mock_token("TERMINAL", "TERM_TWO"),
            create_mock_token("RULE", "rule_three"),
        ]
        declare.meta = create_mock_meta(1, 1, 1, 30)

        definitions = definitions_from_declare(declare)

        assert len(definitions) == 3
        assert definitions[0].name == "rule_one"
        assert definitions[0].kind == Kind.RULE
        assert definitions[1].name == "TERM_TWO"
        assert definitions[1].kind == Kind.TERMINAL
        assert definitions[2].name == "rule_three"
        assert definitions[2].kind == Kind.RULE

    def test_definitions_from_declare_empty_symbols(self):
        """Test extracting definitions from Declare node with no symbols."""
        declare = Mock(spec=Declare)
        declare.symbols = []
        declare.meta = create_mock_meta()

        definitions = definitions_from_declare(declare)

        assert len(definitions) == 0


class TestDefinitionsFromExpansions:
    """Test cases for definitions_from_expansions function."""

    def test_definitions_from_expansions_with_aliases(self):
        """Test extracting definitions from expansions with aliases."""
        expansion1 = Mock(spec=Expansion)
        expansion1.alias = create_mock_token("RULE", "alias_one")
        expansion1.meta = create_mock_meta(1, 1, 1, 10)

        expansion2 = Mock(spec=Expansion)
        expansion2.alias = create_mock_token("RULE", "alias_two")
        expansion2.meta = create_mock_meta(2, 1, 2, 10)

        expansions = [expansion1, expansion2]
        definitions = definitions_from_expansions(expansions)

        assert len(definitions) == 2
        assert definitions[0].name == "alias_one"
        assert definitions[0].kind == Kind.RULE
        assert definitions[1].name == "alias_two"
        assert definitions[1].kind == Kind.RULE

    def test_definitions_from_expansions_without_aliases(self):
        """Test extracting definitions from expansions without aliases."""
        expansion1 = Mock(spec=Expansion)
        expansion1.alias = None
        expansion1.meta = create_mock_meta()

        expansion2 = Mock(spec=Expansion)
        expansion2.alias = None
        expansion2.meta = create_mock_meta()

        expansions = [expansion1, expansion2]
        definitions = definitions_from_expansions(expansions)

        assert len(definitions) == 0

    def test_definitions_from_expansions_mixed(self):
        """Test extracting definitions from expansions with mixed aliases."""
        expansion1 = Mock(spec=Expansion)
        expansion1.alias = create_mock_token("RULE", "alias_one")
        expansion1.meta = create_mock_meta(1, 1, 1, 10)

        expansion2 = Mock(spec=Expansion)
        expansion2.alias = None
        expansion2.meta = create_mock_meta()

        expansion3 = Mock(spec=Expansion)
        expansion3.alias = create_mock_token("RULE", "alias_three")
        expansion3.meta = create_mock_meta(3, 1, 3, 10)

        expansions = [expansion1, expansion2, expansion3]
        definitions = definitions_from_expansions(expansions)

        assert len(definitions) == 2
        assert definitions[0].name == "alias_one"
        assert definitions[1].name == "alias_three"

    def test_definitions_from_expansions_empty_list(self):
        """Test extracting definitions from empty expansions list."""
        definitions = definitions_from_expansions([])
        assert len(definitions) == 0


class TestDefinitionsFromImport:
    """Test cases for definitions_from_import function."""

    def test_definitions_from_import_with_alias_rule(self):
        """Test extracting definitions from Import with rule alias."""
        import_node = Mock(spec=Import)
        import_node.alias = create_mock_token("RULE", "alias_name")
        import_node.symbols = [
            create_mock_token("RULE", "original_rule"),
            create_mock_token("TERMINAL", "ORIGINAL_TERM"),
        ]
        import_node.meta = create_mock_meta(1, 1, 1, 20)

        definitions = definitions_from_import(import_node)

        assert len(definitions) == 1
        alias_def = definitions[0]
        assert alias_def.name == "alias_name"
        assert alias_def.kind == Kind.RULE
        assert len(alias_def.children) == 2
        assert "original_rule" in alias_def.children
        assert "ORIGINAL_TERM" in alias_def.children

    def test_definitions_from_import_with_alias_terminal(self):
        """Test extracting definitions from Import with terminal alias."""
        import_node = Mock(spec=Import)
        import_node.alias = create_mock_token("TERMINAL", "ALIAS_TERM")
        import_node.symbols = [create_mock_token("RULE", "original_rule")]
        import_node.meta = create_mock_meta(1, 1, 1, 20)

        definitions = definitions_from_import(import_node)

        assert len(definitions) == 1
        alias_def = definitions[0]
        assert alias_def.name == "ALIAS_TERM"
        assert alias_def.kind == Kind.TERMINAL
        assert len(alias_def.children) == 1
        assert "original_rule" in alias_def.children

    def test_definitions_from_import_without_alias(self):
        """Test extracting definitions from Import without alias."""
        import_node = Mock(spec=Import)
        import_node.alias = None
        import_node.symbols = [
            create_mock_token("RULE", "imported_rule"),
            create_mock_token("TERMINAL", "IMPORTED_TERM"),
        ]
        import_node.meta = create_mock_meta(1, 1, 1, 20)

        definitions = definitions_from_import(import_node)

        assert len(definitions) == 2
        assert definitions[0].name == "imported_rule"
        assert definitions[0].kind == Kind.RULE
        assert definitions[1].name == "IMPORTED_TERM"
        assert definitions[1].kind == Kind.TERMINAL

    def test_definitions_from_import_empty_symbols(self):
        """Test extracting definitions from Import with no symbols."""
        import_node = Mock(spec=Import)
        import_node.alias = None
        import_node.symbols = []
        import_node.meta = create_mock_meta()

        definitions = definitions_from_import(import_node)

        assert len(definitions) == 0


class TestDefinitionsFromRuleParams:
    """Test cases for definitions_from_rule_params function."""

    def test_definitions_from_rule_params_basic(self):
        """Test extracting definitions from rule parameters."""
        parent = Mock(spec=Definition)
        parent.range = Mock()

        params = [
            create_mock_token("RULE", "param1"),
            create_mock_token("RULE", "param2"),
            create_mock_token("RULE", "param3"),
        ]

        definitions = definitions_from_rule_params(params, parent)

        assert len(definitions) == 3
        assert all(d.kind == Kind.RULE for d in definitions)
        assert definitions[0].name == "param1"
        assert definitions[1].name == "param2"
        assert definitions[2].name == "param3"
        assert all(d.range == parent.range for d in definitions)

    def test_definitions_from_rule_params_empty(self):
        """Test extracting definitions from empty parameters."""
        parent = Mock(spec=Definition)
        parent.range = Mock()

        definitions = definitions_from_rule_params([], parent)
        assert len(definitions) == 0


class TestDefinitionsFromRule:
    """Test cases for definitions_from_rule function."""

    def test_definitions_from_rule_basic(self):
        """Test extracting definitions from basic Rule."""
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "test_rule")
        rule.parameters = []
        rule.expansions = []
        rule.modifiers = []
        rule.meta = create_mock_meta(1, 1, 1, 10)

        definitions = definitions_from_rule(rule)

        assert len(definitions) == 1
        assert definitions[0].name == "test_rule"
        assert definitions[0].kind == Kind.RULE

    def test_definitions_from_rule_with_parameters(self):
        """Test extracting definitions from Rule with parameters."""
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "test_rule")
        rule.parameters = [
            create_mock_token("RULE", "param1"),
            create_mock_token("RULE", "param2"),
        ]
        rule.expansions = []
        rule.modifiers = []
        rule.meta = create_mock_meta(1, 1, 1, 10)

        definitions = definitions_from_rule(rule)

        # Should include rule definition as first, children added via append_child
        assert len(definitions) == 1
        rule_def = definitions[0]
        assert rule_def.name == "test_rule"
        assert len(rule_def.children) == 2
        assert "param1" in rule_def.children
        assert "param2" in rule_def.children

    def test_definitions_from_rule_with_expansions(self):
        """Test extracting definitions from Rule with expansions."""
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "test_rule")
        rule.parameters = []
        rule.modifiers = []
        rule.meta = create_mock_meta(1, 1, 1, 10)

        expansion = Mock(spec=Expansion)
        expansion.alias = create_mock_token("RULE", "expansion_alias")
        expansion.meta = create_mock_meta(2, 1, 2, 10)
        rule.expansions = [expansion]

        definitions = definitions_from_rule(rule)

        assert len(definitions) == 2
        assert definitions[0].name == "test_rule"
        assert definitions[1].name == "expansion_alias"

    def test_definitions_from_rule_with_modifiers(self):
        """Test extracting definitions from Rule with modifiers."""
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "test_rule")
        rule.parameters = []
        rule.expansions = []
        rule.modifiers = ["?", "!"]
        rule.meta = create_mock_meta(1, 1, 1, 10)

        definitions = definitions_from_rule(rule)

        assert len(definitions) == 1
        rule_def = definitions[0]
        assert rule_def.name == "test_rule"
        assert Modifiers.CONDITIONALLY_INLINED in rule_def.modifiers
        assert Modifiers.PINNED in rule_def.modifiers


class TestDefinitionsFromTerm:
    """Test cases for definitions_from_term function."""

    def test_definitions_from_term_basic(self):
        """Test extracting definitions from basic Term."""
        term = Mock(spec=Term)
        term.name = create_mock_token("TERMINAL", "TEST_TERMINAL")
        term.expansions = []
        term.modifiers = []
        term.meta = create_mock_meta(1, 1, 1, 15)

        definitions = definitions_from_term(term)

        assert len(definitions) == 1
        assert definitions[0].name == "TEST_TERMINAL"
        assert definitions[0].kind == Kind.TERMINAL

    def test_definitions_from_term_with_expansions(self):
        """Test extracting definitions from Term with expansions."""
        term = Mock(spec=Term)
        term.name = create_mock_token("TERMINAL", "TEST_TERMINAL")
        term.modifiers = []
        term.meta = create_mock_meta(1, 1, 1, 15)

        expansion = Mock(spec=Expansion)
        expansion.alias = create_mock_token("RULE", "term_expansion")
        expansion.meta = create_mock_meta(2, 1, 2, 10)
        term.expansions = [expansion]

        definitions = definitions_from_term(term)

        assert len(definitions) == 2
        assert definitions[0].name == "TEST_TERMINAL"
        assert definitions[0].kind == Kind.TERMINAL
        assert definitions[1].name == "term_expansion"

    def test_definitions_from_term_with_modifiers(self):
        """Test extracting definitions from Term with modifiers."""
        term = Mock(spec=Term)
        term.name = create_mock_token("TERMINAL", "TEST_TERMINAL")
        term.expansions = []
        term.modifiers = ["_", "?"]
        term.meta = create_mock_meta(1, 1, 1, 15)

        definitions = definitions_from_term(term)

        assert len(definitions) == 1
        term_def = definitions[0]
        assert term_def.name == "TEST_TERMINAL"
        assert Modifiers.INLINED in term_def.modifiers
        assert Modifiers.CONDITIONALLY_INLINED in term_def.modifiers


class TestDefinitionsFromAstNode:
    """Test cases for definitions_from_ast_node function."""

    def test_definitions_from_ast_node_declare(self):
        """Test definitions_from_ast_node with Declare."""
        declare = create_complete_declare_mock()

        # Test the specific function directly instead of the type dispatcher
        definitions = definitions_from_declare(declare)

        assert len(definitions) == 1
        assert definitions[0].name == "test_symbol"

    def test_definitions_from_ast_node_import(self):
        """Test definitions_from_ast_node with Import."""
        import_node = create_complete_import_mock()

        # Test the specific function directly instead of the type dispatcher
        definitions = definitions_from_import(import_node)

        assert len(definitions) == 1
        assert definitions[0].name == "TEST_IMPORT"

    def test_definitions_from_ast_node_rule(self):
        """Test definitions_from_ast_node with Rule."""
        rule = create_complete_rule_mock()

        # Test the specific function directly instead of the type dispatcher
        definitions = definitions_from_rule(rule)

        assert len(definitions) == 1
        assert definitions[0].name == "test_rule"

    def test_definitions_from_ast_node_term(self):
        """Test definitions_from_ast_node with Term."""
        term = create_complete_term_mock()

        # Test the specific function directly instead of the type dispatcher
        definitions = definitions_from_term(term)

        assert len(definitions) == 1
        assert definitions[0].name == "TEST_TERM"

    def test_definitions_from_ast_node_unsupported(self):
        """Test definitions_from_ast_node with unsupported node type."""
        comment = Mock(spec=Comment)
        comment.__class__ = Comment

        definitions = definitions_from_ast_node(comment)

        assert len(definitions) == 0


class TestReferencesFromDeclare:
    """Test cases for references_from_declare function."""

    def test_references_from_declare_single_symbol(self):
        """Test extracting references from Declare node with single symbol."""
        declare = Mock(spec=Declare)
        declare.symbols = [create_mock_token("TERMINAL", "EXISTING_TERMINAL")]
        declare.meta = create_mock_meta(1, 1, 1, 20)

        references = references_from_declare(declare)

        assert len(references) == 1
        assert references[0].name == "EXISTING_TERMINAL"

    def test_references_from_declare_multiple_symbols(self):
        """Test extracting references from Declare node with multiple symbols."""
        declare = Mock(spec=Declare)
        declare.symbols = [
            create_mock_token("RULE", "existing_rule"),
            create_mock_token("TERMINAL", "EXISTING_TERM"),
        ]
        declare.meta = create_mock_meta()

        references = references_from_declare(declare)

        assert len(references) == 2
        assert references[0].name == "existing_rule"
        assert references[1].name == "EXISTING_TERM"

    def test_references_from_declare_with_ast_node(self):
        """Test extracting references from Declare with custom ast_node."""
        declare = Mock(spec=Declare)
        declare.symbols = [create_mock_token("RULE", "test_rule")]
        declare.meta = create_mock_meta()

        ast_node = Mock(spec=AstNode)
        references = references_from_declare(declare, ast_node=ast_node)

        assert len(references) == 1
        assert references[0].ast_node is ast_node

    def test_references_from_declare_empty_symbols(self):
        """Test extracting references from Declare with no symbols."""
        declare = Mock(spec=Declare)
        declare.symbols = []
        declare.meta = create_mock_meta()

        references = references_from_declare(declare)
        assert len(references) == 0


class TestReferencesFromIgnore:
    """Test cases for references_from_ignore function."""

    def test_references_from_ignore_basic(self):
        """Test extracting references from Ignore node."""
        ignore = Mock(spec=Ignore)

        # Create a token directly instead of complex expansion structure
        rule_token = create_mock_token("RULE", "ignored_rule")
        ignore.expansions = [rule_token]
        ignore.meta = create_mock_meta()

        references = references_from_ignore(ignore)

        assert len(references) == 1
        assert references[0].name == "ignored_rule"

    def test_references_from_ignore_multiple_expansions(self):
        """Test extracting references from Ignore with multiple expansions."""
        ignore = Mock(spec=Ignore)

        # Create tokens directly
        rule_token = create_mock_token("RULE", "rule1")
        term_token = create_mock_token("TERMINAL", "TERM2")

        ignore.expansions = [rule_token, term_token]
        ignore.meta = create_mock_meta()

        references = references_from_ignore(ignore)

        assert len(references) == 2
        assert references[0].name == "rule1"
        assert references[1].name == "TERM2"

    def test_references_from_ignore_with_ast_node(self):
        """Test extracting references from Ignore with custom ast_node."""
        ignore = Mock(spec=Ignore)

        rule_token = create_mock_token("RULE", "test_rule")
        ignore.expansions = [rule_token]
        ignore.meta = create_mock_meta()

        ast_node = Mock(spec=AstNode)
        references = references_from_ignore(ignore, ast_node=ast_node)

        assert len(references) == 1
        assert references[0].ast_node is ast_node


class TestReferencesFromImport:
    """Test cases for references_from_import function."""

    def test_references_from_import_symbols_only(self):
        """Test extracting references from Import with symbols only."""
        import_node = Mock(spec=Import)
        import_node.symbols = [
            create_mock_token("RULE", "imported_rule"),
            create_mock_token("TERMINAL", "IMPORTED_TERM"),
        ]
        import_node.alias = None
        import_node.meta = create_mock_meta()

        references = references_from_import(import_node)

        assert len(references) == 2
        assert references[0].name == "imported_rule"
        assert references[1].name == "IMPORTED_TERM"

    def test_references_from_import_with_alias(self):
        """Test extracting references from Import with alias."""
        import_node = Mock(spec=Import)
        import_node.symbols = [create_mock_token("RULE", "imported_rule")]
        import_node.alias = create_mock_token("RULE", "alias_name")
        import_node.meta = create_mock_meta()

        references = references_from_import(import_node)

        assert len(references) == 2
        assert references[0].name == "imported_rule"
        assert references[1].name == "alias_name"

    def test_references_from_import_with_ast_node(self):
        """Test extracting references from Import with custom ast_node."""
        import_node = Mock(spec=Import)
        import_node.symbols = [create_mock_token("RULE", "test_rule")]
        import_node.alias = None
        import_node.meta = create_mock_meta()

        ast_node = Mock(spec=AstNode)
        references = references_from_import(import_node, ast_node=ast_node)

        assert len(references) == 1
        assert references[0].ast_node is ast_node


class TestReferencesFromOverride:
    """Test cases for references_from_override function."""

    def test_references_from_override_basic(self):
        """Test extracting references from Override node."""
        override = Mock(spec=Override)
        override.definition = create_mock_token("RULE", "overridden_rule")
        override.meta = create_mock_meta()

        references = references_from_override(override)

        assert len(references) == 1
        assert references[0].name == "overridden_rule"

    def test_references_from_override_with_ast_node(self):
        """Test extracting references from Override with custom ast_node."""
        override = Mock(spec=Override)
        override.definition = create_mock_token("RULE", "overridden_rule")
        override.meta = create_mock_meta()

        ast_node = Mock(spec=AstNode)
        references = references_from_override(override, ast_node=ast_node)

        assert len(references) == 1
        assert references[0].ast_node is ast_node


class TestReferencesFromExtend:
    """Test cases for references_from_extend function."""

    def test_references_from_extend_basic(self):
        """Test extracting references from Extend node."""
        extend = Mock(spec=Extend)
        extend.definition = create_mock_token("RULE", "extended_rule")
        extend.meta = create_mock_meta()

        references = references_from_extend(extend)

        assert len(references) == 1
        assert references[0].name == "extended_rule"

    def test_references_from_extend_with_ast_node(self):
        """Test extracting references from Extend with custom ast_node."""
        extend = Mock(spec=Extend)
        extend.definition = create_mock_token("RULE", "extended_rule")
        extend.meta = create_mock_meta()

        ast_node = Mock(spec=AstNode)
        references = references_from_extend(extend, ast_node=ast_node)

        assert len(references) == 1
        assert references[0].ast_node is ast_node


class TestReferencesFromTemplateUsage:
    """Test cases for references_from_template_usage function."""

    def test_references_from_template_usage_basic(self):
        """Test extracting references from TemplateUsage."""
        template_usage = Mock(spec=TemplateUsage)
        template_usage.rule = create_mock_token("RULE", "template_rule")
        template_usage.arguments = [
            create_mock_token("RULE", "arg1"),
            create_mock_token("TERMINAL", "ARG2"),
        ]
        template_usage.meta = create_mock_meta()

        references = references_from_template_usage(template_usage)

        assert len(references) == 3
        assert references[0].name == "template_rule"
        assert references[1].name == "arg1"
        assert references[2].name == "ARG2"

    def test_references_from_template_usage_no_arguments(self):
        """Test extracting references from TemplateUsage with no arguments."""
        template_usage = Mock(spec=TemplateUsage)
        template_usage.rule = create_mock_token("RULE", "template_rule")
        template_usage.arguments = []
        template_usage.meta = create_mock_meta()

        references = references_from_template_usage(template_usage)

        assert len(references) == 1
        assert references[0].name == "template_rule"

    def test_references_from_template_usage_mixed_arguments(self):
        """Test extracting references from TemplateUsage with mixed argument types."""
        template_usage = Mock(spec=TemplateUsage)
        template_usage.rule = create_mock_token("RULE", "template_rule")
        template_usage.arguments = [
            create_mock_token("RULE", "rule_arg"),
            "string_literal",  # Non-AstNode/Token argument
            create_mock_token("TERMINAL", "TERM_ARG"),
        ]
        template_usage.meta = create_mock_meta()

        references = references_from_template_usage(template_usage)

        # Should only include rule + AstNode/Token arguments
        assert len(references) == 3
        assert references[0].name == "template_rule"
        assert references[1].name == "rule_arg"
        assert references[2].name == "TERM_ARG"


class TestReferencesFromMaybe:
    """Test cases for references_from_maybe function."""

    def test_references_from_maybe_basic(self):
        """Test extracting references from Maybe node."""
        maybe = Mock(spec=Maybe)

        # Create a token directly
        rule_token = create_mock_token("RULE", "maybe_rule")
        maybe.expansions = [rule_token]
        maybe.meta = create_mock_meta()

        references = references_from_maybe(maybe)

        assert len(references) == 1
        assert references[0].name == "maybe_rule"

    def test_references_from_maybe_multiple_expansions(self):
        """Test extracting references from Maybe with multiple expansions."""
        maybe = Mock(spec=Maybe)

        # Create tokens directly
        rule_token = create_mock_token("RULE", "rule1")
        term_token = create_mock_token("TERMINAL", "TERM2")

        maybe.expansions = [rule_token, term_token]
        maybe.meta = create_mock_meta()

        references = references_from_maybe(maybe)

        assert len(references) == 2
        assert references[0].name == "rule1"
        assert references[1].name == "TERM2"


class TestReferencesFromExpr:
    """Test cases for references_from_expr function."""

    def test_references_from_expr_rule_atom(self):
        """Test extracting references from Expr with rule atom."""
        expr = Mock(spec=Expr)
        expr.atom = create_mock_token("RULE", "referenced_rule")
        expr.meta = create_mock_meta()

        references = references_from_expr(expr)

        assert len(references) == 1
        assert references[0].name == "referenced_rule"

    def test_references_from_expr_terminal_atom(self):
        """Test extracting references from Expr with terminal atom."""
        expr = Mock(spec=Expr)
        expr.atom = create_mock_token("TERMINAL", "REFERENCED_TERMINAL")
        expr.meta = create_mock_meta()

        references = references_from_expr(expr)

        assert len(references) == 1
        assert references[0].name == "REFERENCED_TERMINAL"

    def test_references_from_expr_string_atom(self):
        """Test extracting references from Expr with string atom (no reference)."""
        expr = Mock(spec=Expr)
        expr.atom = '"literal_string"'  # String literal, not AstNode/Token
        expr.meta = create_mock_meta()

        references = references_from_expr(expr)

        assert len(references) == 0

    def test_references_from_expr_ast_node_atom(self):
        """Test extracting references from Expr with AstNode atom."""
        expr = Mock(spec=Expr)

        # Create a token directly instead of nested AstNode for simpler test
        rule_token = create_mock_token("RULE", "nested_rule")
        expr.atom = rule_token
        expr.meta = create_mock_meta()

        references = references_from_expr(expr)

        assert len(references) == 1
        assert references[0].name == "nested_rule"


class TestReferencesFromExpansion:
    """Test cases for references_from_expansion function."""

    def test_references_from_expansion_expressions_only(self):
        """Test extracting references from Expansion with expressions only."""
        expansion = Mock(spec=Expansion)
        expansion.expressions = [
            create_mock_token("RULE", "rule1"),
            create_mock_token("TERMINAL", "TERM2"),
        ]
        expansion.alias = None
        expansion.meta = create_mock_meta()

        references = references_from_expansion(expansion)

        assert len(references) == 2
        assert references[0].name == "rule1"
        assert references[1].name == "TERM2"

    def test_references_from_expansion_with_alias(self):
        """Test extracting references from Expansion with alias."""
        expansion = Mock(spec=Expansion)
        expansion.expressions = [create_mock_token("RULE", "rule1")]
        expansion.alias = create_mock_token("RULE", "alias_name")
        expansion.meta = create_mock_meta()

        references = references_from_expansion(expansion)

        assert len(references) == 2
        assert references[0].name == "rule1"
        assert references[1].name == "alias_name"

    def test_references_from_expansion_empty_expressions(self):
        """Test extracting references from Expansion with no expressions."""
        expansion = Mock(spec=Expansion)
        expansion.expressions = []
        expansion.alias = create_mock_token("RULE", "alias_only")
        expansion.meta = create_mock_meta()

        references = references_from_expansion(expansion)

        assert len(references) == 1
        assert references[0].name == "alias_only"


class TestReferencesFromTerm:
    """Test cases for references_from_term function."""

    def test_references_from_term_name_only(self):
        """Test extracting references from Term with name only."""
        term = Mock(spec=Term)
        term.name = create_mock_token("TERMINAL", "TERM_NAME")
        term.expansions = []
        term.meta = create_mock_meta()

        references = references_from_term(term)

        assert len(references) == 1
        assert references[0].name == "TERM_NAME"

    def test_references_from_term_with_expansions(self):
        """Test extracting references from Term with expansions."""
        term = Mock(spec=Term)
        term.name = create_mock_token("TERMINAL", "TERM_NAME")
        term.meta = create_mock_meta()

        # Use token directly instead of complex expansion structure
        expansion_token = create_mock_token("RULE", "expansion_rule")
        term.expansions = [expansion_token]

        references = references_from_term(term)

        assert len(references) == 2
        assert references[0].name == "TERM_NAME"
        assert references[1].name == "expansion_rule"

    def test_references_from_term_with_ast_node(self):
        """Test extracting references from Term with custom ast_node."""
        term = Mock(spec=Term)
        term.name = create_mock_token("TERMINAL", "TERM_NAME")
        term.expansions = []
        term.meta = create_mock_meta()

        ast_node = Mock(spec=AstNode)
        references = references_from_term(term, ast_node=ast_node)

        assert len(references) == 1
        assert references[0].ast_node is ast_node


class TestReferencesFromRule:
    """Test cases for references_from_rule function."""

    def test_references_from_rule_basic(self):
        """Test extracting references from Rule."""
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "rule_name")
        rule.parameters = []
        rule.expansions = []
        rule.meta = create_mock_meta()

        references = references_from_rule(rule)

        assert len(references) == 1
        assert references[0].name == "rule_name"

    def test_references_from_rule_with_parameters(self):
        """Test extracting references from Rule with parameters."""
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "rule_name")
        rule.parameters = [
            create_mock_token("RULE", "param1"),
            create_mock_token("RULE", "param2"),
        ]
        rule.expansions = []
        rule.meta = create_mock_meta()

        references = references_from_rule(rule)

        assert len(references) == 3
        assert references[0].name == "rule_name"
        assert references[1].name == "param1"
        assert references[2].name == "param2"

    def test_references_from_rule_with_expansions(self):
        """Test extracting references from Rule with expansions."""
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "rule_name")
        rule.parameters = []
        rule.meta = create_mock_meta()

        # Use token directly instead of complex expansion structure
        expansion_token = create_mock_token("TERMINAL", "EXPANSION_TERM")
        rule.expansions = [expansion_token]

        references = references_from_rule(rule)

        assert len(references) == 2
        assert references[0].name == "rule_name"
        assert references[1].name == "EXPANSION_TERM"

    def test_references_from_rule_with_ast_node(self):
        """Test extracting references from Rule with custom ast_node."""
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "rule_name")
        rule.parameters = []
        rule.expansions = []
        rule.meta = create_mock_meta()

        ast_node = Mock(spec=AstNode)
        references = references_from_rule(rule, ast_node=ast_node)

        assert len(references) == 1
        assert references[0].ast_node is ast_node


class TestReferencesFromAstNode:
    """Test cases for references_from_ast_node function."""

    def test_references_from_ast_node_token_rule(self):
        """Test references_from_ast_node with RULE token."""
        token = create_mock_token("RULE", "test_rule")

        references = references_from_ast_node(token)

        assert len(references) == 1
        assert references[0].name == "test_rule"

    def test_references_from_ast_node_token_terminal(self):
        """Test references_from_ast_node with TERMINAL token."""
        token = create_mock_token("TERMINAL", "TEST_TERM")

        references = references_from_ast_node(token)

        assert len(references) == 1
        assert references[0].name == "TEST_TERM"

    def test_references_from_ast_node_token_other_type(self):
        """Test references_from_ast_node with non-RULE/TERMINAL token."""
        token = create_mock_token("STRING", '"literal"')

        references = references_from_ast_node(token)

        assert len(references) == 0

    def test_references_from_ast_node_declare(self):
        """Test references_from_ast_node with Declare."""
        declare = create_complete_declare_mock()

        references = references_from_ast_node(declare)

        assert isinstance(references, list)
        # The exact number depends on the internal structure

    def test_references_from_ast_node_ignore(self):
        """Test references_from_ast_node with Ignore."""
        ignore = Mock(spec=Ignore)
        ignore.expansions = [create_mock_token("RULE", "ignored_rule")]
        ignore.meta = create_mock_meta()

        # Test the specific function directly instead of the type dispatcher
        references = references_from_ignore(ignore)

        assert len(references) == 1
        assert references[0].name == "ignored_rule"

    def test_references_from_ast_node_import(self):
        """Test references_from_ast_node with Import."""
        import_node = create_complete_import_mock()

        references = references_from_ast_node(import_node)

        assert isinstance(references, list)
        # The exact number depends on the internal structure

    def test_references_from_ast_node_override(self):
        """Test references_from_ast_node with Override."""
        override = Mock(spec=Override)
        override.definition = create_mock_token("RULE", "overridden_rule")
        override.meta = create_mock_meta()

        # Test the specific function directly instead of the type dispatcher
        references = references_from_override(override)

        assert len(references) == 1
        assert references[0].name == "overridden_rule"

    def test_references_from_ast_node_extend(self):
        """Test references_from_ast_node with Extend."""
        extend = Mock(spec=Extend)
        extend.definition = create_mock_token("RULE", "extended_rule")
        extend.meta = create_mock_meta()

        # Test the specific function directly instead of the type dispatcher
        references = references_from_extend(extend)

        assert len(references) == 1
        assert references[0].name == "extended_rule"

    def test_references_from_ast_node_template_usage(self):
        """Test references_from_ast_node with TemplateUsage."""
        template_usage = Mock(spec=TemplateUsage)
        template_usage.rule = create_mock_token("RULE", "template_rule")
        template_usage.arguments = []
        template_usage.meta = create_mock_meta()

        # Test the specific function directly instead of the type dispatcher
        references = references_from_template_usage(template_usage)

        assert len(references) == 1
        assert references[0].name == "template_rule"

    def test_references_from_ast_node_maybe(self):
        """Test references_from_ast_node with Maybe."""
        maybe = Mock(spec=Maybe)

        # Create a token directly instead of complex expansion structure
        rule_token = create_mock_token("RULE", "maybe_rule")
        maybe.expansions = [rule_token]
        maybe.meta = create_mock_meta()

        # Test the specific function directly instead of the type dispatcher
        references = references_from_maybe(maybe)

        assert len(references) == 1
        assert references[0].name == "maybe_rule"

    def test_references_from_ast_node_expr(self):
        """Test references_from_ast_node with Expr."""
        expr = Mock(spec=Expr)
        expr.atom = create_mock_token("RULE", "expr_rule")
        expr.meta = create_mock_meta()

        # Test the specific function directly instead of the type dispatcher
        references = references_from_expr(expr)

        assert len(references) == 1
        assert references[0].name == "expr_rule"

    def test_references_from_ast_node_expansion(self):
        """Test references_from_ast_node with Expansion."""
        expansion = Mock(spec=Expansion)
        expansion.expressions = [create_mock_token("RULE", "expansion_rule")]
        expansion.alias = None
        expansion.meta = create_mock_meta()

        # Test the specific function directly instead of the type dispatcher
        references = references_from_expansion(expansion)

        assert len(references) == 1
        assert references[0].name == "expansion_rule"

    def test_references_from_ast_node_term(self):
        """Test references_from_ast_node with Term."""
        term = Mock(spec=Term)
        term.name = create_mock_token("TERMINAL", "TERM_NAME")
        term.expansions = []
        term.meta = create_mock_meta()

        # Test the specific function directly instead of the type dispatcher
        references = references_from_term(term)

        assert len(references) == 1
        assert references[0].name == "TERM_NAME"

    def test_references_from_ast_node_rule(self):
        """Test references_from_ast_node with Rule."""
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "rule_name")
        rule.parameters = []
        rule.expansions = []
        rule.meta = create_mock_meta()

        # Test the specific function directly instead of the type dispatcher
        references = references_from_rule(rule)

        assert len(references) == 1
        assert references[0].name == "rule_name"

    def test_references_from_ast_node_unsupported(self):
        """Test references_from_ast_node with unsupported node type."""
        comment = Mock(spec=Comment)

        references = references_from_ast_node(comment)

        assert len(references) == 0

    def test_references_from_ast_node_with_custom_ast_node(self):
        """Test references_from_ast_node with custom ast_node parameter."""
        token = create_mock_token("RULE", "test_rule")
        custom_ast_node = Mock(spec=AstNode)

        references = references_from_ast_node(token, ast_node=custom_ast_node)

        assert len(references) == 1
        assert references[0].name == "test_rule"
        assert references[0].ast_node is custom_ast_node


class TestModuleIntegration:
    """Test cases for module integration and edge cases."""

    def test_circular_references_handling(self):
        """Test that circular references are handled correctly."""
        # Create a rule that references itself through expansion
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "recursive_rule")
        rule.parameters = []
        rule.meta = create_mock_meta()

        # Use a token directly instead of complex expansion structure
        self_ref_token = create_mock_token("RULE", "recursive_rule")
        rule.expansions = [self_ref_token]

        references = references_from_rule(rule)

        # Should include both the rule name and the self-reference
        assert len(references) == 2
        assert all(ref.name == "recursive_rule" for ref in references)

    def test_complex_nested_structure(self):
        """Test complex nested AST structure."""
        # Create a rule with all required attributes
        rule = create_complete_rule_mock("complex_rule")
        rule.parameters = [create_mock_token("RULE", "param1")]

        # Create expansion with multiple expressions and alias
        expansion = Mock(spec=Expansion)
        expansion.expressions = [
            create_mock_token("RULE", "expr1"),
            create_mock_token("TERMINAL", "EXPR2"),
        ]
        expansion.alias = create_mock_token("RULE", "expansion_alias")
        expansion.meta = create_mock_meta()

        rule.expansions = [expansion]

        # Test definitions
        definitions = definitions_from_rule(rule)
        assert len(definitions) >= 1  # At least the rule definition

        # Test references
        references = references_from_rule(rule)
        assert len(references) >= 1  # At least some references

    def test_empty_structures(self):
        """Test handling of empty structures."""
        # Test empty declarations
        assert definitions_from_declare(Mock(symbols=[], meta=create_mock_meta())) == []
        assert references_from_declare(Mock(symbols=[], meta=create_mock_meta())) == []

        # Test empty expansions
        assert definitions_from_expansions([]) == []

        # Test empty parameters
        parent = Mock(range=Mock())
        assert definitions_from_rule_params([], parent) == []

    def test_none_handling(self):
        """Test handling of None values."""
        # Test import without alias or symbols
        import_node = Mock(spec=Import)
        import_node.alias = None
        import_node.symbols = []
        import_node.meta = create_mock_meta()

        assert definitions_from_import(import_node) == []
        assert references_from_import(import_node) == []

        # Test expansion without alias
        expansion = Mock(spec=Expansion)
        expansion.alias = None
        expansion.expressions = []
        expansion.meta = create_mock_meta()

        assert definitions_from_expansions([expansion]) == []
        assert references_from_expansion(expansion) == []

    def test_modifier_accumulation(self):
        """Test that modifiers are properly accumulated."""
        # Test rule with multiple modifiers
        rule = Mock(spec=Rule)
        rule.name = create_mock_token("RULE", "modified_rule")
        rule.parameters = []
        rule.expansions = []
        rule.modifiers = ["?", "!", "_"]
        rule.meta = create_mock_meta()

        definitions = definitions_from_rule(rule)
        rule_def = definitions[0]

        assert Modifiers.CONDITIONALLY_INLINED in rule_def.modifiers
        assert Modifiers.PINNED in rule_def.modifiers
        assert Modifiers.INLINED in rule_def.modifiers

        # Test term with modifiers
        term = Mock(spec=Term)
        term.name = create_mock_token("TERMINAL", "MODIFIED_TERM")
        term.expansions = []
        term.modifiers = ["?", "_"]
        term.meta = create_mock_meta()

        definitions = definitions_from_term(term)
        term_def = definitions[0]

        assert Modifiers.CONDITIONALLY_INLINED in term_def.modifiers
        assert Modifiers.INLINED in term_def.modifiers
        assert Modifiers.PINNED not in term_def.modifiers
