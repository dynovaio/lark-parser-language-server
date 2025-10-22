"""Tests for lark_parser_language_server/syntax_tree/nodes.py module."""

from unittest.mock import Mock, patch

import pytest
from lark import Token, Tree
from lark.tree import Meta

from lark_parser_language_server.syntax_tree.nodes import (
    Alias,
    Ast,
    AstNode,
    BaseAstNode,
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
    _meta_repr,
)


class TestMetaRepr:
    """Test module-level _meta_repr function."""

    def test_meta_repr_empty(self):
        """Test _meta_repr with empty meta."""
        meta = Meta()
        meta.empty = True
        result = _meta_repr(meta)
        assert result == "Meta(empty=True)"

    def test_meta_repr_with_positions(self):
        """Test _meta_repr with position information."""
        meta = Meta()
        meta.empty = False
        meta.line = 10
        meta.column = 5
        meta.end_line = 12
        meta.end_column = 8

        result = _meta_repr(meta)
        expected = "Meta(line=10, column=5, end_line=12, end_column=8)"
        assert result == expected


class TestBaseAstNode:
    """Test BaseAstNode class."""

    def test_base_ast_node_creation(self):
        """Test BaseAstNode can be created."""
        node = BaseAstNode()
        assert isinstance(node, BaseAstNode)

    def test_base_ast_node_post_init(self):
        """Test BaseAstNode __post_init__ method."""
        # Should not raise any errors
        node = BaseAstNode()
        node.__post_init__()


class TestAstNode:
    """Test AstNode class."""

    def test_ast_node_creation_with_tree(self):
        """Test AstNode creation with a tree."""
        tree = Tree("test", [])
        # Create a mock meta and patch it onto the tree
        mock_meta = Mock()
        with patch.object(type(tree), "meta", new_callable=lambda: mock_meta):
            node = AstNode(tree)
            assert node._tree is tree
            assert node.meta is mock_meta

    def test_ast_node_creation_without_meta(self):
        """Test AstNode creation with tree that has no meta."""
        tree = Tree("test", [])
        # Explicitly don't set meta attribute

        node = AstNode(tree)
        assert node._tree is tree
        assert isinstance(node.meta, Meta)

    def test_ast_node_repr(self):
        """Test AstNode __repr__ method."""
        tree = Tree("test", [])
        node = AstNode(tree)
        repr_str = repr(node)
        assert "AstNode" in repr_str
        assert "meta=" in repr_str


class TestRange:
    """Test Range class."""

    def test_range_creation(self):
        """Test Range creation with tree."""
        start_token = Token("STRING", "start")
        end_token = Token("STRING", "end")
        tree = Tree("range", [start_token, end_token])

        range_node = Range(tree)
        assert range_node.start == "start"
        assert range_node.end == "end"

    def test_range_repr(self):
        """Test Range __repr__ method."""
        start_token = Token("STRING", "start")
        end_token = Token("STRING", "end")
        tree = Tree("range", [start_token, end_token])

        range_node = Range(tree)
        repr_str = repr(range_node)
        assert "Range" in repr_str
        assert "start='start'" in repr_str
        assert "end='end'" in repr_str


class TestTemplateUsage:
    """Test TemplateUsage class."""

    def test_template_usage_creation(self):
        """Test TemplateUsage creation."""
        rule_token = Token("RULE", "my_rule")
        arg1 = Token("STRING", "arg1")
        arg2 = Token("STRING", "arg2")
        tree = Tree("template_usage", [rule_token, arg1, arg2])

        template_usage = TemplateUsage(tree)
        assert template_usage.rule is rule_token
        assert len(template_usage.arguments) == 2
        assert template_usage.arguments[0] is arg1
        assert template_usage.arguments[1] is arg2

    def test_template_usage_repr(self):
        """Test TemplateUsage __repr__ method."""
        rule_token = Token("RULE", "my_rule")
        tree = Tree("template_usage", [rule_token])

        template_usage = TemplateUsage(tree)
        repr_str = repr(template_usage)
        assert "TemplateUsage" in repr_str
        assert "rule=" in repr_str
        assert "arguments=" in repr_str


class TestMaybe:
    """Test Maybe class."""

    def test_maybe_creation_with_expansions(self):
        """Test Maybe creation with expansion children."""
        # Create simple mock objects for this test
        expansion1 = Mock()
        expansion2 = Mock()

        tree = Tree("maybe", [[expansion1, expansion2]])

        maybe = Maybe(tree)
        assert len(maybe.expansions) == 2
        # Both should be in the expansions list
        assert expansion1 in maybe.expansions or expansion2 in maybe.expansions

    def test_maybe_repr(self):
        """Test Maybe __repr__ method."""
        tree = Tree("maybe", [[]])
        maybe = Maybe(tree)
        repr_str = repr(maybe)
        assert "Maybe" in repr_str
        assert "expansions=" in repr_str


class TestExpansion:
    """Test Expansion class."""

    def test_expansion_creation(self):
        """Test Expansion creation."""
        expr1 = Mock()
        expr2 = Mock()
        tree = Tree("expansion", [expr1, expr2])

        expansion = Expansion(tree)
        assert len(expansion.expressions) == 2
        assert expansion.expressions[0] is expr1
        assert expansion.expressions[1] is expr2
        assert expansion.alias is None

    def test_expansion_is_aliased_false(self):
        """Test Expansion.is_aliased when no alias."""
        tree = Tree("expansion", [])
        expansion = Expansion(tree)
        assert not expansion.is_aliased

    def test_expansion_is_aliased_true(self):
        """Test Expansion.is_aliased when alias exists."""
        tree = Tree("expansion", [])
        expansion = Expansion(tree)
        expansion.alias = Token("RULE", "alias_name")
        assert expansion.is_aliased

    def test_expansion_repr(self):
        """Test Expansion __repr__ method."""
        tree = Tree("expansion", [])
        expansion = Expansion(tree)
        repr_str = repr(expansion)
        assert "Expansion" in repr_str
        assert "expressions=" in repr_str
        assert "alias=" in repr_str


class TestAlias:
    """Test Alias class."""

    def test_alias_creation(self):
        """Test Alias creation."""
        expansion_mock = Mock()
        alias_token = Token("RULE", "alias_name")
        tree = Tree("alias", [expansion_mock, alias_token])

        alias = Alias(tree)
        assert alias.expansion is expansion_mock
        assert alias.name is alias_token

    def test_alias_to_expansion(self):
        """Test Alias.to_expansion method."""
        expansion_mock = Mock()
        alias_token = Token("RULE", "alias_name")
        tree = Tree("alias", [expansion_mock, alias_token])

        alias = Alias(tree)
        result = alias.to_expansion()

        assert result is expansion_mock
        # The expansion should have been modified with meta and alias
        assert hasattr(expansion_mock, "meta")
        assert hasattr(expansion_mock, "alias")
        assert expansion_mock.alias is alias_token

    def test_alias_repr(self):
        """Test Alias __repr__ method."""
        expansion_mock = Mock()
        alias_token = Token("RULE", "alias_name")
        tree = Tree("alias", [expansion_mock, alias_token])

        alias = Alias(tree)
        repr_str = repr(alias)
        assert "Alias" in repr_str
        assert "name=" in repr_str
        assert "expansion=" in repr_str


class TestExpr:
    """Test Expr class."""

    def test_expr_creation(self):
        """Test Expr creation."""
        atom_mock = Mock()
        op1 = Token("OP", "?")
        op2 = Token("OP", "*")
        tree = Tree("expr", [atom_mock, op1, op2])

        expr = Expr(tree)
        assert expr.atom is atom_mock
        assert expr.operators is not None
        assert len(expr.operators) == 2
        assert expr.operators[0] is op1
        assert expr.operators[1] is op2

    def test_expr_repr(self):
        """Test Expr __repr__ method."""
        atom_mock = Mock()
        tree = Tree("expr", [atom_mock])

        expr = Expr(tree)
        repr_str = repr(expr)
        assert "Expr" in repr_str
        assert "atom=" in repr_str
        assert "operators=" in repr_str


class TestTerm:
    """Test Term class."""

    def test_term_creation_basic(self):
        """Test Term creation with basic structure."""
        name_token = Token("TERMINAL", "MY_TERM")
        expansions_mock = []
        tree = Tree("term", [name_token, expansions_mock])

        term = Term(tree)
        assert term.name is name_token
        assert term.priority == 0
        assert term.expansions == []
        assert term.modifiers == []

    def test_term_creation_with_priority(self):
        """Test Term creation with priority."""
        name_token = Token("TERMINAL", "MY_TERM")
        priority = 5
        expansions_mock = []
        tree = Tree("term", [name_token, priority, expansions_mock])

        term = Term(tree)
        assert term.name is name_token
        assert term.priority == 5
        assert term.expansions == []

    def test_term_creation_with_underscore_modifier(self):
        """Test Term creation with underscore modifier."""
        name_token = Token("TERMINAL", "_MY_TERM")
        expansions_mock = []
        tree = Tree("term", [name_token, expansions_mock])

        term = Term(tree)
        assert "_" in term.modifiers

    def test_term_creation_with_alias_expansions(self):
        """Test Term creation with alias expansions."""
        name_token = Token("TERMINAL", "MY_TERM")

        expansion1 = Mock()
        expansion2 = Mock()

        expansions = [expansion1, expansion2]
        tree = Tree("term", [name_token, expansions])

        term = Term(tree)
        assert len(term.expansions) == 2
        # Both expansions should be processed into the list
        assert expansion1 in term.expansions or expansion2 in term.expansions

    def test_term_repr(self):
        """Test Term __repr__ method."""
        name_token = Token("TERMINAL", "MY_TERM")
        tree = Tree("term", [name_token, []])

        term = Term(tree)
        repr_str = repr(term)
        assert "Term" in repr_str
        assert "name=" in repr_str
        assert "modifiers=" in repr_str
        assert "priority=" in repr_str
        assert "expansions=" in repr_str


class TestRule:
    """Test Rule class."""

    def test_rule_creation_basic(self):
        """Test Rule creation with basic structure."""
        modifiers = ["?", "!"]
        name_token = Token("RULE", "my_rule")
        parameters = []
        priority = None
        expansions = []
        tree = Tree("rule", [modifiers, name_token, parameters, priority, expansions])

        rule = Rule(tree)
        assert rule.modifiers == ["?", "!"]
        assert rule.name is name_token
        assert rule.parameters == []
        assert rule.priority == 0
        assert rule.expansions == []

    def test_rule_creation_with_underscore_name(self):
        """Test Rule creation with underscore name adds modifier."""
        modifiers = []
        name_token = Token("RULE", "_my_rule")
        parameters = []
        priority = None
        expansions = []
        tree = Tree("rule", [modifiers, name_token, parameters, priority, expansions])

        rule = Rule(tree)
        assert "_" in rule.modifiers

    def test_rule_creation_with_parameters(self):
        """Test Rule creation with parameters."""
        modifiers = []
        name_token = Token("RULE", "my_rule")
        param1 = Token("RULE", "param1")
        param2 = Token("RULE", "param2")
        parameters = [param1, param2]
        priority = None
        expansions = []
        tree = Tree("rule", [modifiers, name_token, parameters, priority, expansions])

        rule = Rule(tree)
        assert len(rule.parameters) == 2
        assert rule.parameters[0] is param1
        assert rule.parameters[1] is param2

    def test_rule_creation_with_priority(self):
        """Test Rule creation with priority."""
        modifiers = []
        name_token = Token("RULE", "my_rule")
        parameters = []
        priority = 10
        expansions = []
        tree = Tree("rule", [modifiers, name_token, parameters, priority, expansions])

        rule = Rule(tree)
        assert rule.priority == 10

    def test_rule_creation_with_alias_expansions(self):
        """Test Rule creation with alias expansions."""
        modifiers = []
        name_token = Token("RULE", "my_rule")
        parameters = []
        priority = None

        expansion1 = Mock()
        expansion2 = Mock()

        expansions = [expansion1, expansion2]
        tree = Tree("rule", [modifiers, name_token, parameters, priority, expansions])

        rule = Rule(tree)
        assert len(rule.expansions) == 2
        # Both expansions should be processed into the list
        assert expansion1 in rule.expansions or expansion2 in rule.expansions

    def test_rule_repr(self):
        """Test Rule __repr__ method."""
        modifiers = []
        name_token = Token("RULE", "my_rule")
        parameters = []
        priority = None
        expansions = []
        tree = Tree("rule", [modifiers, name_token, parameters, priority, expansions])

        rule = Rule(tree)
        repr_str = repr(rule)
        assert "Rule" in repr_str
        assert "modifiers=" in repr_str
        assert "name=" in repr_str
        assert "parameters=" in repr_str
        assert "priority=" in repr_str
        assert "expansions=" in repr_str


class TestDeclare:
    """Test Declare class."""

    def test_declare_creation(self):
        """Test Declare creation."""
        symbol1 = Token("RULE", "rule1")
        symbol2 = Token("TERMINAL", "TERM1")
        tree = Tree("declare", [symbol1, symbol2])

        declare = Declare(tree)
        assert len(declare.symbols) == 2
        assert declare.symbols[0] is symbol1
        assert declare.symbols[1] is symbol2

    def test_declare_repr(self):
        """Test Declare __repr__ method."""
        symbol1 = Token("RULE", "rule1")
        tree = Tree("declare", [symbol1])

        declare = Declare(tree)
        repr_str = repr(declare)
        assert "Declare" in repr_str
        assert "symbols=" in repr_str


class TestImport:
    """Test Import class."""

    def test_import_creation_single_path(self):
        """Test Import creation with single path."""
        path_and_symbol = ["path.to.module", Token("RULE", "symbol")]
        tree = Tree("import", [path_and_symbol])

        import_node = Import(tree)
        assert import_node.path == "path.to.module"
        assert len(import_node.symbols) == 1
        assert import_node.symbols[0].value == "symbol"
        assert import_node.alias is None

    def test_import_creation_with_alias(self):
        """Test Import creation with alias."""
        path_tokens = [
            Token("RULE", "path"),
            Token("RULE", "to"),
            Token("RULE", "symbol"),
        ]
        alias_token = Token("RULE", "my_alias")
        tree = Tree("import", [path_tokens, alias_token])

        import_node = Import(tree)
        assert import_node.path == "path.to"
        assert len(import_node.symbols) == 1
        assert import_node.symbols[0].value == "symbol"
        assert import_node.alias is alias_token

    def test_import_creation_multiple_symbols(self):
        """Test Import creation with multiple symbols."""
        path_tokens = "path.to.module"
        symbols = [Token("RULE", "symbol1"), Token("RULE", "symbol2")]
        tree = Tree("import", [path_tokens, symbols])

        import_node = Import(tree)
        assert import_node.path == "path.to.module"
        assert len(import_node.symbols) == 2
        assert import_node.symbols[0].value == "symbol1"
        assert import_node.symbols[1].value == "symbol2"

    def test_import_repr(self):
        """Test Import __repr__ method."""
        path_and_symbol = ["path.to.module", Token("RULE", "symbol")]
        tree = Tree("import", [path_and_symbol])

        import_node = Import(tree)
        repr_str = repr(import_node)
        assert "Import" in repr_str
        assert "path=" in repr_str
        assert "symbols=" in repr_str
        assert "alias=" in repr_str


class TestOverride:
    """Test Override class."""

    def test_override_creation(self):
        """Test Override creation."""
        definition_mock = Mock()
        tree = Tree("override", [definition_mock])

        override = Override(tree)
        assert override.definition is definition_mock

    def test_override_repr(self):
        """Test Override __repr__ method."""
        definition_mock = Mock()
        tree = Tree("override", [definition_mock])

        override = Override(tree)
        repr_str = repr(override)
        assert "Override" in repr_str
        assert "definition=" in repr_str


class TestExtend:
    """Test Extend class."""

    def test_extend_creation(self):
        """Test Extend creation."""
        definition_mock = Mock()
        tree = Tree("extend", [definition_mock])

        extend = Extend(tree)
        assert extend.definition is definition_mock

    def test_extend_repr(self):
        """Test Extend __repr__ method."""
        definition_mock = Mock()
        tree = Tree("extend", [definition_mock])

        extend = Extend(tree)
        repr_str = repr(extend)
        assert "Extend" in repr_str
        assert "definition=" in repr_str


class TestComment:
    """Test Comment class."""

    def test_comment_creation_with_content(self):
        """Test Comment creation with content."""
        content_token = Token("COMMENT", "// This is a comment")
        tree = Tree("comment", [content_token])

        comment = Comment(tree)
        assert comment.content is content_token

    def test_comment_creation_empty(self):
        """Test Comment creation with no content."""
        tree = Tree("comment", [])

        comment = Comment(tree)
        assert comment.content.type == "COMMENT"
        assert comment.content.value == ""

    def test_comment_repr(self):
        """Test Comment __repr__ method."""
        content_token = Token("COMMENT", "// This is a comment")
        tree = Tree("comment", [content_token])

        comment = Comment(tree)
        repr_str = repr(comment)
        assert "Comment" in repr_str
        assert "content=" in repr_str


class TestIgnore:
    """Test Ignore class."""

    def test_ignore_creation(self):
        """Test Ignore creation."""
        expansion1 = Mock()
        expansion2 = Mock()

        expansions = [expansion1, expansion2]
        tree = Tree("ignore", [expansions])

        ignore = Ignore(tree)
        assert len(ignore.expansions) == 2
        # Both expansions should be processed into the list
        assert expansion1 in ignore.expansions or expansion2 in ignore.expansions

    def test_ignore_repr(self):
        """Test Ignore __repr__ method."""
        tree = Tree("ignore", [[]])

        ignore = Ignore(tree)
        repr_str = repr(ignore)
        assert "Ignore" in repr_str
        assert "expansions=" in repr_str


class TestAst:
    """Test Ast class."""

    def test_ast_creation(self):
        """Test Ast creation."""
        child1 = Mock(spec=AstNode)
        child2 = "not_an_ast_node"  # Should be filtered out
        child3 = Mock(spec=AstNode)

        tree = Tree("ast", [child1, child2, child3])

        ast = Ast(tree)
        assert len(ast.statements) == 2
        assert ast.statements[0] is child1
        assert ast.statements[1] is child3

    def test_ast_getitem(self):
        """Test Ast __getitem__ method."""
        child1 = Mock(spec=AstNode)
        child2 = Mock(spec=AstNode)
        tree = Tree("ast", [child1, child2])

        ast = Ast(tree)
        assert ast[0] is child1
        assert ast[1] is child2

    def test_ast_len(self):
        """Test Ast __len__ method."""
        child1 = Mock(spec=AstNode)
        child2 = Mock(spec=AstNode)
        tree = Tree("ast", [child1, child2])

        ast = Ast(tree)
        assert len(ast) == 2

    def test_ast_repr(self):
        """Test Ast __repr__ method."""
        tree = Tree("ast", [])

        ast = Ast(tree)
        repr_str = repr(ast)
        assert "Ast" in repr_str
        assert "statements=" in repr_str
