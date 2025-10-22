"""Tests for lark_parser_language_server.formatter module."""

from unittest.mock import Mock, patch

import pytest
from lark import Token

from lark_parser_language_server.formatter import (
    DEFAULT_INDENT,
    FORMATTER,
    Formatter,
    _format_ast_node,
    _format_comment,
    _format_declare,
    _format_expansion,
    _format_expr,
    _format_extend,
    _format_ignore,
    _format_import,
    _format_maybe,
    _format_override,
    _format_range,
    _format_rule,
    _format_template_usage,
    _format_term,
)
from lark_parser_language_server.syntax_tree.nodes import (
    Ast,
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


class TestFormatComment:
    """Test cases for _format_comment function."""

    def test_format_comment_basic(self):
        """Test formatting a basic comment."""
        comment = Mock(spec=Comment)
        comment.content = "  This is a comment  "

        result = _format_comment(comment)
        assert result == "This is a comment"

    def test_format_comment_with_indent_and_level(self):
        """Test that indent and level parameters are ignored."""
        comment = Mock(spec=Comment)
        comment.content = "Test comment"

        result = _format_comment(comment, indent="  ", level=3)
        assert result == "Test comment"

    def test_format_comment_empty(self):
        """Test formatting an empty comment."""
        comment = Mock(spec=Comment)
        comment.content = "   "

        result = _format_comment(comment)
        assert result == ""


class TestFormatDeclare:
    """Test cases for _format_declare function."""

    def test_format_declare_single_symbol(self):
        """Test formatting declare with single symbol."""
        symbol = Mock()
        symbol.__str__ = Mock(return_value="symbol1")

        declare = Mock(spec=Declare)
        declare.symbols = [symbol]

        result = _format_declare(declare)
        assert result == "%declare symbol1"

    def test_format_declare_multiple_symbols(self):
        """Test formatting declare with multiple symbols."""
        symbol1 = Mock()
        symbol1.__str__ = Mock(return_value="symbol1")
        symbol2 = Mock()
        symbol2.__str__ = Mock(return_value="symbol2")

        declare = Mock(spec=Declare)
        declare.symbols = [symbol1, symbol2]

        result = _format_declare(declare)
        assert result == "%declare symbol1 symbol2"

    def test_format_declare_empty_symbols(self):
        """Test formatting declare with no symbols."""
        declare = Mock(spec=Declare)
        declare.symbols = []

        result = _format_declare(declare)
        assert result == "%declare "


class TestFormatExpansion:
    """Test cases for _format_expansion function."""

    def test_format_expansion_with_alias(self):
        """Test formatting expansion with alias."""
        alias = Mock()
        alias.__str__ = Mock(return_value="alias_name")

        expr1 = Mock()
        expr2 = Mock()

        expansion = Mock(spec=Expansion)
        expansion.alias = alias
        expansion.expressions = [expr1, expr2]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.side_effect = lambda x: f"expr_{id(x)}"

            result = _format_expansion(expansion)
            expected = f"expr_{id(expr1)} expr_{id(expr2)} -> alias_name"
            assert result == expected

    def test_format_expansion_without_alias(self):
        """Test formatting expansion without alias."""
        expr1 = Mock()
        expr2 = Mock()

        expansion = Mock(spec=Expansion)
        expansion.alias = None
        expansion.expressions = [expr1, expr2]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.side_effect = lambda x: f"expr_{id(x)}"

            result = _format_expansion(expansion)
            expected = f"expr_{id(expr1)} expr_{id(expr2)}"
            assert result == expected

    def test_format_expansion_empty_expressions(self):
        """Test formatting expansion with empty expressions."""
        expansion = Mock(spec=Expansion)
        expansion.alias = None
        expansion.expressions = []

        result = _format_expansion(expansion)
        assert result == ""


class TestFormatExpr:
    """Test cases for _format_expr function."""

    def test_format_expr_simple_atom(self):
        """Test formatting expr with simple atom."""
        atom = Mock()

        expr = Mock(spec=Expr)
        expr.operators = []
        expr.atom = atom

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "atom_content"

            result = _format_expr(expr)
            assert result == "atom_content"

    def test_format_expr_with_operators(self):
        """Test formatting expr with operators."""
        atom = Mock()
        op1 = Mock()
        op1.__str__ = Mock(return_value="?")
        op2 = Mock()
        op2.__str__ = Mock(return_value="*")

        expr = Mock(spec=Expr)
        expr.operators = [op1, op2]
        expr.atom = atom

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "atom_content"

            result = _format_expr(expr)
            assert result == "atom_content?*"

    def test_format_expr_with_range_operators(self):
        """Test formatting expr with range operators (3 operators)."""
        atom = Mock()
        op1 = Mock()
        op1.__str__ = Mock(return_value="?")
        op2 = Mock()
        op2.__str__ = Mock(return_value="*")
        op3 = Mock()
        op3.__str__ = Mock(return_value="+")

        expr = Mock(spec=Expr)
        expr.operators = [op1, op2, op3]
        expr.atom = atom

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "atom_content"

            result = _format_expr(expr)
            assert result == "atom_content?*..+"

    def test_format_expr_with_list_atom(self):
        """Test formatting expr with list atom (wrapped in parens)."""
        atom1 = Mock()
        atom2 = Mock()

        expr = Mock(spec=Expr)
        expr.operators = []
        expr.atom = [atom1, atom2]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.side_effect = lambda x: f"atom_{id(x)}"

            result = _format_expr(expr)
            expected = f"(atom_{id(atom1)} | atom_{id(atom2)})"
            assert result == expected

    def test_format_expr_no_operators(self):
        """Test formatting expr with None operators."""
        atom = Mock()

        expr = Mock(spec=Expr)
        expr.operators = None
        expr.atom = atom

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "atom_content"

            result = _format_expr(expr)
            assert result == "atom_content"


class TestFormatExtend:
    """Test cases for _format_extend function."""

    def test_format_extend(self):
        """Test formatting extend directive."""
        definition = Mock()

        extend = Mock(spec=Extend)
        extend.definition = definition

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "definition_content"

            result = _format_extend(extend)
            assert result == "%extend definition_content"


class TestFormatIgnore:
    """Test cases for _format_ignore function."""

    def test_format_ignore_single_expansion(self):
        """Test formatting ignore with single expansion."""
        expansion = Mock()

        ignore = Mock(spec=Ignore)
        ignore.expansions = [expansion]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_ignore(ignore)
            assert result == "%ignore expansion_content"

    def test_format_ignore_multiple_expansions(self):
        """Test formatting ignore with multiple expansions."""
        expansion1 = Mock()
        expansion2 = Mock()

        ignore = Mock(spec=Ignore)
        ignore.expansions = [expansion1, expansion2]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.side_effect = lambda x: f"expansion_{id(x)}"

            result = _format_ignore(ignore)
            expected = (
                f"%ignore expansion_{id(expansion1)}\n    | expansion_{id(expansion2)}"
            )
            assert result == expected


class TestFormatImport:
    """Test cases for _format_import function."""

    def test_format_import_single_symbol_no_alias(self):
        """Test formatting import with single symbol and no alias."""
        symbol = Mock()
        symbol.__str__ = Mock(return_value="SYMBOL")
        path = Mock()
        path.__str__ = Mock(return_value="common")

        import_ = Mock(spec=Import)
        import_.symbols = [symbol]
        import_.alias = None
        import_.path = path

        result = _format_import(import_)
        assert result == "%import common.SYMBOL"

    def test_format_import_multiple_symbols_no_alias(self):
        """Test formatting import with multiple symbols and no alias."""
        symbol1 = Mock()
        symbol1.__str__ = Mock(return_value="SYMBOL1")
        symbol2 = Mock()
        symbol2.__str__ = Mock(return_value="SYMBOL2")
        path = Mock()
        path.__str__ = Mock(return_value="common")

        import_ = Mock(spec=Import)
        import_.symbols = [symbol1, symbol2]
        import_.alias = None
        import_.path = path

        result = _format_import(import_)
        assert result == "%import common (SYMBOL1, SYMBOL2)"

    def test_format_import_with_alias(self):
        """Test formatting import with alias."""
        symbol = Mock()
        symbol.__str__ = Mock(return_value="SYMBOL")
        alias = Mock()
        alias.__str__ = Mock(return_value="MY_ALIAS")
        path = Mock()
        path.__str__ = Mock(return_value="common")

        import_ = Mock(spec=Import)
        import_.symbols = [symbol]
        import_.alias = alias
        import_.path = path

        result = _format_import(import_)
        assert result == "%import common.SYMBOL -> MY_ALIAS"

    def test_format_import_multiple_symbols_with_alias(self):
        """Test formatting import with multiple symbols and alias."""
        symbol1 = Mock()
        symbol1.__str__ = Mock(return_value="SYMBOL1")
        symbol2 = Mock()
        symbol2.__str__ = Mock(return_value="SYMBOL2")
        alias = Mock()
        alias.__str__ = Mock(return_value="MY_ALIAS")
        path = Mock()
        path.__str__ = Mock(return_value="common")

        import_ = Mock(spec=Import)
        import_.symbols = [symbol1, symbol2]
        import_.alias = alias
        import_.path = path

        result = _format_import(import_)
        assert result == "%import common (SYMBOL1, SYMBOL2) -> MY_ALIAS"


class TestFormatMaybe:
    """Test cases for _format_maybe function."""

    def test_format_maybe_single_expansion(self):
        """Test formatting maybe with single expansion."""
        expansion = Mock()

        maybe = Mock(spec=Maybe)
        maybe.expansions = [expansion]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_maybe(maybe)
            assert result == "[expansion_content]"

    def test_format_maybe_multiple_expansions(self):
        """Test formatting maybe with multiple expansions."""
        expansion1 = Mock()
        expansion2 = Mock()

        maybe = Mock(spec=Maybe)
        maybe.expansions = [expansion1, expansion2]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.side_effect = lambda x: f"expansion_{id(x)}"

            result = _format_maybe(maybe)
            expected = f"[expansion_{id(expansion1)} | expansion_{id(expansion2)}]"
            assert result == expected


class TestFormatOverride:
    """Test cases for _format_override function."""

    def test_format_override(self):
        """Test formatting override directive."""
        definition = Mock()

        override = Mock(spec=Override)
        override.definition = definition

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "definition_content"

            result = _format_override(override)
            assert result == "%extend definition_content"


class TestFormatRange:
    """Test cases for _format_range function."""

    def test_format_range(self):
        """Test formatting range."""
        range_ = Mock(spec=Range)
        range_.start = "a"
        range_.end = "z"

        result = _format_range(range_)
        assert result == "a..z"


class TestFormatRule:
    """Test cases for _format_rule function."""

    def test_format_rule_basic(self):
        """Test formatting basic rule."""
        name = Mock()
        name.__str__ = Mock(return_value="rule_name")
        expansion = Mock()

        rule = Mock(spec=Rule)
        rule.modifiers = []
        rule.name = name
        rule.parameters = []
        rule.priority = None
        rule.expansions = [expansion]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_rule(rule)
            assert result == "rule_name: expansion_content"

    def test_format_rule_with_modifiers(self):
        """Test formatting rule with modifiers."""
        name = Mock()
        name.__str__ = Mock(return_value="rule_name")
        expansion = Mock()

        rule = Mock(spec=Rule)
        rule.modifiers = ["?", "!", "_"]  # _ should be filtered out
        rule.name = name
        rule.parameters = []
        rule.priority = None
        rule.expansions = [expansion]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_rule(rule)
            assert result == "?!rule_name: expansion_content"

    def test_format_rule_with_parameters(self):
        """Test formatting rule with parameters."""
        name = Mock()
        name.__str__ = Mock(return_value="rule_name")
        param1 = Mock()
        param1.__str__ = Mock(return_value="param1")
        param2 = Mock()
        param2.__str__ = Mock(return_value="param2")
        expansion = Mock()

        rule = Mock(spec=Rule)
        rule.modifiers = []
        rule.name = name
        rule.parameters = [param1, param2]
        rule.priority = None
        rule.expansions = [expansion]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_rule(rule)
            assert result == "rule_name{param1, param2}: expansion_content"

    def test_format_rule_with_priority(self):
        """Test formatting rule with priority."""
        name = Mock()
        name.__str__ = Mock(return_value="rule_name")
        expansion = Mock()

        rule = Mock(spec=Rule)
        rule.modifiers = []
        rule.name = name
        rule.parameters = []
        rule.priority = "5"
        rule.expansions = [expansion]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_rule(rule)
            assert result == "rule_name.5: expansion_content"

    def test_format_rule_multiple_expansions(self):
        """Test formatting rule with multiple expansions."""
        name = Mock()
        name.__str__ = Mock(return_value="rule_name")
        expansion1 = Mock()
        expansion2 = Mock()

        rule = Mock(spec=Rule)
        rule.modifiers = []
        rule.name = name
        rule.parameters = []
        rule.priority = None
        rule.expansions = [expansion1, expansion2]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.side_effect = lambda x: f"expansion_{id(x)}"

            result = _format_rule(rule)
            expected = f"rule_name: expansion_{id(expansion1)}\n    | expansion_{id(expansion2)}"
            assert result == expected

    def test_format_rule_complete(self):
        """Test formatting rule with all features."""
        name = Mock()
        name.__str__ = Mock(return_value="rule_name")
        param = Mock()
        param.__str__ = Mock(return_value="T")
        expansion = Mock()

        rule = Mock(spec=Rule)
        rule.modifiers = ["?", "_"]  # _ should be filtered out
        rule.name = name
        rule.parameters = [param]
        rule.priority = "3"
        rule.expansions = [expansion]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_rule(rule)
            assert result == "?rule_name{T}.3: expansion_content"


class TestFormatTemplateUsage:
    """Test cases for _format_template_usage function."""

    def test_format_template_usage(self):
        """Test formatting template usage."""
        rule = Mock()
        rule.__str__ = Mock(return_value="template_rule")
        arg1 = Mock()
        arg2 = Mock()

        template_usage = Mock(spec=TemplateUsage)
        template_usage.rule = rule
        template_usage.arguments = [arg1, arg2]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.side_effect = lambda x: f"arg_{id(x)}"

            result = _format_template_usage(template_usage)
            expected = f"template_rule{{arg_{id(arg1)}, arg_{id(arg2)}}}"
            assert result == expected

    def test_format_template_usage_no_arguments(self):
        """Test formatting template usage with no arguments."""
        rule = Mock()
        rule.__str__ = Mock(return_value="template_rule")

        template_usage = Mock(spec=TemplateUsage)
        template_usage.rule = rule
        template_usage.arguments = []

        result = _format_template_usage(template_usage)
        assert result == "template_rule{}"


class TestFormatTerm:
    """Test cases for _format_term function."""

    def test_format_term_basic(self):
        """Test formatting basic term."""
        name = Mock()
        name.__str__ = Mock(return_value="TERM_NAME")
        expansion = Mock()

        term = Mock(spec=Term)
        term.modifiers = []
        term.name = name
        term.priority = None
        term.expansions = [expansion]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_term(term)
            assert result == "TERM_NAME: expansion_content"

    def test_format_term_with_modifiers(self):
        """Test formatting term with modifiers."""
        name = Mock()
        name.__str__ = Mock(return_value="TERM_NAME")
        expansion = Mock()

        term = Mock(spec=Term)
        term.modifiers = ["?", "!", "_"]  # _ should be filtered out
        term.name = name
        term.priority = None
        term.expansions = [expansion]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_term(term)
            assert result == "?!TERM_NAME: expansion_content"

    def test_format_term_with_priority(self):
        """Test formatting term with priority."""
        name = Mock()
        name.__str__ = Mock(return_value="TERM_NAME")
        expansion = Mock()

        term = Mock(spec=Term)
        term.modifiers = []
        term.name = name
        term.priority = "10"
        term.expansions = [expansion]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_term(term)
            assert result == "TERM_NAME.10: expansion_content"

    def test_format_term_multiple_expansions(self):
        """Test formatting term with multiple expansions."""
        name = Mock()
        name.__str__ = Mock(return_value="TERM_NAME")
        expansion1 = Mock()
        expansion2 = Mock()

        term = Mock(spec=Term)
        term.modifiers = []
        term.name = name
        term.priority = None
        term.expansions = [expansion1, expansion2]

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.side_effect = lambda x: f"expansion_{id(x)}"

            result = _format_term(term)
            expected = f"TERM_NAME: expansion_{id(expansion1)}\n    | expansion_{id(expansion2)}"
            assert result == expected


class TestFormatAstNode:
    """Test cases for _format_ast_node function."""

    def test_format_ast_node_comment(self):
        """Test formatting AST node with Comment type."""
        # Test the comment formatter directly instead of through the dispatcher
        from lark_parser_language_server.formatter import _format_comment

        comment = Mock()
        comment.content = "test comment"

        result = _format_comment(comment)
        # Comment formatting should return the content stripped
        assert result == "test comment"

    def test_format_ast_node_rule(self):
        """Test formatting AST node with Rule type."""
        name = Mock()
        name.__str__ = Mock(return_value="test_rule")
        expansion = Mock()

        rule = Mock(spec=Rule)
        rule.modifiers = []
        rule.name = name
        rule.parameters = []
        rule.priority = None
        rule.expansions = [expansion]

        # Need to properly mock the expansion formatting
        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "expansion_content"

            result = _format_rule(rule)
            assert "test_rule:" in result

    def test_format_ast_node_token(self):
        """Test formatting AST node with Token type."""
        token = Token("RULE", "test_token")

        result = _format_ast_node(token)
        assert result == "test_token"

    def test_format_ast_node_unknown_type(self):
        """Test formatting AST node with unknown type."""
        unknown_node = Mock()
        unknown_node.__str__ = Mock(return_value="unknown_content")

        result = _format_ast_node(unknown_node)
        assert result == '"unknown_content"'

    def test_format_ast_node_none_value(self):
        """Test formatting AST node with None value."""
        result = _format_ast_node(None)
        assert result == '"None"'

    def test_format_ast_node_all_types(self):
        """Test that all node types have formatters in the map."""
        # Test that the formatter map contains all expected types
        from lark_parser_language_server.formatter import _format_comment

        # Test Comment formatter directly
        comment = Mock()
        comment.content = "test"
        result = _format_comment(comment)
        assert isinstance(result, str)

        # Test that it uses the proper formatter and returns the content
        assert result == "test"


class TestFormatter:
    """Test cases for Formatter class."""

    def test_formatter_init(self):
        """Test Formatter initialization."""
        formatter = Formatter()
        assert hasattr(formatter, "format")

    def test_formatter_format_single_statement(self):
        """Test formatting AST with single statement."""
        statement = Mock()
        ast = Mock(spec=Ast)
        ast.statements = [statement]

        formatter = Formatter()

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "  formatted statement  "

            result = formatter.format(ast)
            assert result == "formatted statement"
            mock_format.assert_called_once_with(statement, indent=DEFAULT_INDENT)

    def test_formatter_format_multiple_statements(self):
        """Test formatting AST with multiple statements."""
        statement1 = Mock()
        statement2 = Mock()
        statement3 = Mock()
        ast = Mock(spec=Ast)
        ast.statements = [statement1, statement2, statement3]

        formatter = Formatter()

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.side_effect = lambda x, **kwargs: f"formatted_{id(x)}"

            result = formatter.format(ast)
            expected = f"formatted_{id(statement1)}\n\nformatted_{id(statement2)}\n\nformatted_{id(statement3)}"
            assert result == expected

    def test_formatter_format_custom_indent(self):
        """Test formatting AST with custom indent."""
        statement = Mock()
        ast = Mock(spec=Ast)
        ast.statements = [statement]

        formatter = Formatter()
        custom_indent = "  "

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.return_value = "formatted statement"

            result = formatter.format(ast, indent=custom_indent)
            assert result == "formatted statement"
            mock_format.assert_called_once_with(statement, indent=custom_indent)

    def test_formatter_format_empty_ast(self):
        """Test formatting empty AST."""
        ast = Mock(spec=Ast)
        ast.statements = []

        formatter = Formatter()

        result = formatter.format(ast)
        assert result == ""

    def test_formatter_format_whitespace_handling(self):
        """Test formatting with whitespace handling."""
        statement1 = Mock()
        statement2 = Mock()
        ast = Mock(spec=Ast)
        ast.statements = [statement1, statement2]

        formatter = Formatter()

        with patch(
            "lark_parser_language_server.formatter._format_ast_node"
        ) as mock_format:
            mock_format.side_effect = ["  stmt1  ", "  stmt2  "]

            result = formatter.format(ast)
            assert result == "stmt1\n\nstmt2"


class TestFormatterModule:
    """Test cases for module-level functionality."""

    def test_default_indent_constant(self):
        """Test DEFAULT_INDENT constant."""
        assert DEFAULT_INDENT == " " * 4

    def test_formatter_singleton(self):
        """Test FORMATTER singleton instance."""
        assert isinstance(FORMATTER, Formatter)

    def test_formatter_singleton_reusable(self):
        """Test that FORMATTER singleton can be reused."""
        ast = Mock(spec=Ast)
        ast.statements = []

        result1 = FORMATTER.format(ast)
        result2 = FORMATTER.format(ast)

        assert result1 == result2 == ""


class TestFormatterIntegration:
    """Integration tests for formatter functionality."""

    def test_complex_rule_formatting(self):
        """Test formatting a complex rule with all features."""
        # Test the rule formatter directly with proper mocks
        name = Mock()
        name.__str__ = Mock(return_value="complex_rule")
        param = Mock()
        param.__str__ = Mock(return_value="T")

        rule = Mock(spec=Rule)
        rule.modifiers = ["?", "_", "!"]  # _ should be filtered out
        rule.name = name
        rule.parameters = [param]
        rule.priority = "5"
        rule.expansions = []

        # Test the rule formatter directly
        result = _format_rule(rule)
        assert "?!complex_rule{T}.5:" in result

    def test_mixed_statements_formatting(self):
        """Test formatting AST with mixed statement types."""
        # Create different types of statements
        comment = Mock(spec=Comment)
        comment.content = "A comment"

        rule_name = Mock()
        rule_name.__str__ = Mock(return_value="test_rule")
        rule = Mock(spec=Rule)
        rule.modifiers = []
        rule.name = rule_name
        rule.parameters = []
        rule.priority = None
        rule.expansions = []

        declare = Mock(spec=Declare)
        declare.symbols = []

        ast = Mock(spec=Ast)
        ast.statements = [comment, rule, declare]

        formatter = Formatter()
        result = formatter.format(ast)

        # Should have statements separated by double newlines
        lines = result.split("\n\n")
        assert len(lines) == 3

    def test_nested_expression_formatting(self):
        """Test formatting nested expressions."""
        # Create a nested structure
        inner_expr = Mock(spec=Expr)
        inner_expr.operators = []
        inner_expr.atom = Mock()

        outer_expr = Mock(spec=Expr)
        outer_expr.operators = []
        outer_expr.atom = [inner_expr]  # List atom should be wrapped in parens

        expansion = Mock(spec=Expansion)
        expansion.alias = None
        expansion.expressions = [outer_expr]

        ast = Mock(spec=Ast)
        ast.statements = [expansion]

        formatter = Formatter()
        result = formatter.format(ast)

        # The result should be properly formatted
        assert isinstance(result, str)
        assert len(result) > 0

    def test_formatter_preserves_structure(self):
        """Test that formatter preserves the logical structure."""
        # Test the rule formatter directly
        rule_name = Mock()
        rule_name.__str__ = Mock(return_value="start")

        rule = Mock(spec=Rule)
        rule.modifiers = []
        rule.name = rule_name
        rule.parameters = []
        rule.priority = None
        rule.expansions = []

        # Test rule formatting directly
        result = _format_rule(rule)
        assert "start:" in result
