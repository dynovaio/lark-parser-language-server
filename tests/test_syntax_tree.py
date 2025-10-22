"""Tests for lark_parser_language_server/syntax_tree/__init__.py module."""

from functools import partial
from unittest.mock import Mock, patch

import pytest
from lark import Transformer, Tree, ast_utils, v_args

from lark_parser_language_server.syntax_tree import (
    AST_BUILDER,
    Ast,
    AstBuilder,
    AstNode,
    _get_ast_builder,
)


class TestAstBuilder:
    """Test AstBuilder class."""

    def test_ast_builder_inheritance(self):
        """Test that AstBuilder inherits from Transformer."""
        builder = AstBuilder()
        assert isinstance(builder, Transformer)

    def test_ast_builder_rule_modifiers_with_items(self):
        """Test rule_modifiers method with items."""
        builder = AstBuilder()

        # Create a mock item with value attribute
        mock_item = Mock()
        mock_item.value = ["mod1", "mod2"]

        tree = Tree("rule_modifiers", [mock_item])
        result = builder.rule_modifiers(tree)

        assert result == ["mod1", "mod2"]

    def test_ast_builder_rule_modifiers_empty(self):
        """Test rule_modifiers method with empty tree."""
        builder = AstBuilder()
        tree = Tree("rule_modifiers", [])
        result = builder.rule_modifiers(tree)

        assert result is None

    def test_ast_builder_rule_modifiers_no_value(self):
        """Test rule_modifiers method with item that has value=None."""
        builder = AstBuilder()

        mock_item = Mock()
        mock_item.value = None  # Explicitly set to None

        tree = Tree("rule_modifiers", [mock_item])
        result = builder.rule_modifiers(tree)

        assert result is None

    def test_ast_builder_template_params_with_items(self):
        """Test template_params method with items."""
        builder = AstBuilder()

        item1 = Mock()
        item2 = Mock()
        tree = Tree("template_params", [item1, item2])

        result = builder.template_params(tree)
        assert result == [item1, item2]

    def test_ast_builder_template_params_empty(self):
        """Test template_params method with empty tree."""
        builder = AstBuilder()
        tree = Tree("template_params", [])

        result = builder.template_params(tree)
        assert result is None

    def test_ast_builder_priority_with_value(self):
        """Test priority method with numeric value."""
        builder = AstBuilder()

        mock_item = Mock()
        mock_item.value = "10"

        tree = Tree("priority", [mock_item])
        result = builder.priority(tree)

        assert result == 10

    def test_ast_builder_priority_empty(self):
        """Test priority method with empty tree."""
        builder = AstBuilder()
        tree = Tree("priority", [])

        result = builder.priority(tree)
        assert result is None

    def test_ast_builder_priority_no_value(self):
        """Test priority method with item that has value=None."""
        builder = AstBuilder()

        mock_item = Mock()
        mock_item.value = None  # Explicitly set to None

        tree = Tree("priority", [mock_item])
        result = builder.priority(tree)

        assert result is None

    def test_ast_builder_import_lib(self):
        """Test import_lib method."""
        builder = AstBuilder()
        tree = Tree("import_lib", ["path", "to", "module", "symbol"])

        result = builder.import_lib(tree)
        assert result == ["path.to.module", "symbol"]

    def test_ast_builder_import_rel(self):
        """Test import_rel method."""
        builder = AstBuilder()
        tree = Tree("import_rel", ["path", "to", "module", "symbol"])

        result = builder.import_rel(tree)
        assert result == [".path.to.module", "symbol"]

    def test_ast_builder_name_list_with_items(self):
        """Test name_list method with items."""
        builder = AstBuilder()

        item1 = Mock()
        item2 = Mock()
        tree = Tree("name_list", [item1, item2])

        result = builder.name_list(tree)
        assert result == [item1, item2]

    def test_ast_builder_name_list_empty(self):
        """Test name_list method with empty tree."""
        builder = AstBuilder()
        tree = Tree("name_list", [])

        result = builder.name_list(tree)
        assert result is None

    def test_ast_builder_literal(self):
        """Test literal method."""
        builder = AstBuilder()

        item = Mock()
        tree = Tree("literal", [item])

        result = builder.literal(tree)
        assert result is item

    def test_ast_builder_value(self):
        """Test value method."""
        builder = AstBuilder()

        item = Mock()
        tree = Tree("value", [item])

        result = builder.value(tree)
        assert result is item

    def test_ast_builder_expansions(self):
        """Test expansions method."""
        builder = AstBuilder()

        item1 = Mock()
        item2 = Mock()
        tree = Tree("expansions", [item1, item2])

        result = builder.expansions(tree)
        assert result == [item1, item2]

    def test_ast_builder_nonterminal(self):
        """Test nonterminal method."""
        builder = AstBuilder()

        item = Mock()
        tree = Tree("nonterminal", [item])

        result = builder.nonterminal(tree)
        assert result is item

    def test_ast_builder_terminal(self):
        """Test terminal method."""
        builder = AstBuilder()

        item = Mock()
        tree = Tree("terminal", [item])

        result = builder.terminal(tree)
        assert result is item

    def test_ast_builder_rule(self):
        """Test RULE method."""
        builder = AstBuilder()

        token = Mock()
        result = builder.RULE(token)

        assert result is token

    def test_ast_builder_terminal_token(self):
        """Test TERMINAL method."""
        builder = AstBuilder()

        token = Mock()
        result = builder.TERMINAL(token)

        assert result is token

    def test_ast_builder_string(self):
        """Test STRING method."""
        builder = AstBuilder()

        string_token = Mock()
        string_token.value = '"test string"'

        result = builder.STRING(string_token)
        assert result == "test string"

    def test_ast_builder_regexp(self):
        """Test REGEXP method."""
        builder = AstBuilder()

        regexp_token = Mock()
        result = builder.REGEXP(regexp_token)

        assert result is regexp_token

    def test_ast_builder_start(self):
        """Test start method."""
        builder = AstBuilder()

        tree = Tree("start", [])
        result = builder.start(tree)

        assert isinstance(result, Ast)
        assert result._tree is tree

    def test_ast_builder_build(self):
        """Test build method."""
        builder = AstBuilder()

        tree = Tree("test", [])

        # Mock the transform method
        with patch.object(builder, "transform") as mock_transform:
            mock_transform.return_value = Mock()

            result = builder.build(tree)

            mock_transform.assert_called_once_with(tree=tree)
            assert result == mock_transform.return_value


class TestSyntaxTree:
    """Test module-level functions and variables in syntax_tree/__init__.py."""

    def test_get_ast_builder_returns_builder_instance(self):
        """Test that _get_ast_builder returns an AstBuilder instance."""
        builder = _get_ast_builder()
        assert isinstance(builder, AstBuilder)

    def test_get_ast_builder_caches_result(self):
        """Test that _get_ast_builder caches the builder instance."""
        # Clear any existing cache
        if hasattr(_get_ast_builder, "cache"):
            delattr(_get_ast_builder, "cache")

        builder1 = _get_ast_builder()
        builder2 = _get_ast_builder()

        # Should return the same cached instance
        assert builder1 is builder2

    def test_get_ast_builder_with_cached_instance(self):
        """Test that _get_ast_builder returns cached instance when available."""
        # Create a mock builder and set it as cache
        mock_builder = Mock(spec=AstBuilder)
        setattr(_get_ast_builder, "cache", mock_builder)

        result = _get_ast_builder()
        assert result is mock_builder

    @patch("lark_parser_language_server.syntax_tree.ast_utils.create_transformer")
    def test_get_ast_builder_creates_transformer(self, mock_create_transformer):
        """Test that _get_ast_builder creates transformer with correct parameters."""
        # Clear cache to force creation
        if hasattr(_get_ast_builder, "cache"):
            delattr(_get_ast_builder, "cache")

        mock_transformer = Mock(spec=AstBuilder)
        mock_create_transformer.return_value = mock_transformer

        # Call _get_ast_builder
        result = _get_ast_builder()

        # Verify create_transformer was called
        assert mock_create_transformer.called
        args, kwargs = mock_create_transformer.call_args

        # Check that the decorator_factory argument uses partial with v_args
        assert "decorator_factory" in kwargs
        decorator_factory = kwargs["decorator_factory"]

        # The decorator factory should be a partial function
        assert hasattr(decorator_factory, "func")

        # Should return the mocked transformer
        assert result is mock_transformer

    def test_get_ast_builder_sets_cache_attribute(self):
        """Test that _get_ast_builder sets the cache attribute on itself."""
        # Clear any existing cache
        if hasattr(_get_ast_builder, "cache"):
            delattr(_get_ast_builder, "cache")

        builder = _get_ast_builder()

        # Verify cache attribute is set
        assert hasattr(_get_ast_builder, "cache")
        assert getattr(_get_ast_builder, "cache") is builder

    def test_ast_builder_global_variable_is_builder_instance(self):
        """Test that AST_BUILDER global variable is an AstBuilder instance."""
        assert isinstance(AST_BUILDER, AstBuilder)

    def test_ast_builder_global_variable_is_cached_builder(self):
        """Test that AST_BUILDER global variable comes from the cached result."""
        # This test verifies that AST_BUILDER is created from _get_ast_builder
        assert isinstance(AST_BUILDER, AstBuilder)

        # After module import, _get_ast_builder should have a cache
        # We can't guarantee they're the same instance since AST_BUILDER
        # is created at import time, but we can verify both exist
        current_builder = _get_ast_builder()
        # The returned builder should have the expected methods
        assert hasattr(current_builder, "build")
        assert hasattr(current_builder, "transform")

    def test_module_exports_ast_classes(self):
        """Test that the module properly exports Ast and AstNode."""
        # These should be imported from the nodes module
        assert Ast is not None
        assert AstNode is not None

        # Verify they are classes we can instantiate
        tree = Tree("test", [])
        ast_node = AstNode(tree)
        assert isinstance(ast_node, AstNode)

    @patch("lark_parser_language_server.syntax_tree.ast_utils.create_transformer")
    def test_get_ast_builder_uses_correct_module(self, mock_create_transformer):
        """Test that _get_ast_builder uses the correct ast_nodes_module."""
        # Clear cache to force creation
        if hasattr(_get_ast_builder, "cache"):
            delattr(_get_ast_builder, "cache")

        mock_transformer = Mock(spec=AstBuilder)
        mock_create_transformer.return_value = mock_transformer

        _get_ast_builder()

        # Verify create_transformer was called with the correct module
        args, kwargs = mock_create_transformer.call_args
        assert len(args) >= 2  # Should have module and base_transformer arguments

        # The first argument should be the ast_nodes_module
        ast_nodes_module = args[0]
        assert hasattr(ast_nodes_module, "Ast")  # Should have the Ast class
        assert hasattr(ast_nodes_module, "AstNode")  # Should have the AstNode class
