"""Tests for lark_parser_language_server.symbol_table module."""

from unittest.mock import Mock, patch

import pytest

from lark_parser_language_server.symbol_table import SymbolTable
from lark_parser_language_server.symbol_table.errors import (
    DefinitionNotFoundError,
    DefinitionNotFoundForReferenceError,
    MultipleDefinitionsError,
    ShadowedDefinitionError,
)
from lark_parser_language_server.symbol_table.flags import Kind, Modifiers
from lark_parser_language_server.symbol_table.symbol import (
    Definition,
    Position,
    Range,
    Reference,
)
from lark_parser_language_server.syntax_tree.nodes import Ast, Import, Rule, Term


def create_mock_definition(name="test_def", kind=Kind.RULE, line=1, column=1):
    """Helper to create a mock Definition."""
    position = Position(line=line, column=column)
    range_obj = Range(
        start=position, end=Position(line=line, column=column + len(name))
    )

    definition = Mock(spec=Definition)
    definition.name = name
    definition.kind = kind
    definition.selection_range = range_obj
    definition.range = range_obj
    definition.children = {}
    return definition


def create_mock_reference(name="test_ref", line=1, column=1, ast_node=None):
    """Helper to create a mock Reference."""
    position = Position(line=line, column=column)
    range_obj = Range(
        start=position, end=Position(line=line, column=column + len(name))
    )

    reference = Mock(spec=Reference)
    reference.name = name
    reference.position = position
    reference.range = range_obj
    reference.ast_node = ast_node
    return reference


def create_mock_ast(statements=None):
    """Helper to create a mock Ast."""
    ast = Mock(spec=Ast)
    ast.statements = statements or []
    return ast


class TestSymbolTable:
    """Test cases for SymbolTable class."""

    def test_init(self):
        """Test SymbolTable initialization."""
        symbol_table = SymbolTable()

        assert (
            isinstance(symbol_table.definitions, dict) and not symbol_table.definitions
        )
        assert isinstance(symbol_table.references, dict) and not symbol_table.references
        assert (
            isinstance(symbol_table.definition_errors, list)
            and not symbol_table.definition_errors
        )
        assert (
            isinstance(symbol_table.reference_errors, list)
            and not symbol_table.reference_errors
        )
        assert (
            isinstance(symbol_table._all_references, list)
            and not symbol_table._all_references
        )
        assert (
            isinstance(symbol_table._all_definitions, list)
            and not symbol_table._all_definitions
        )

    def test_getitem(self):
        """Test __getitem__ method."""
        symbol_table = SymbolTable()
        definition = create_mock_definition("test_rule")
        symbol_table.definitions["test_rule"] = [definition]

        # Test existing definition
        result = symbol_table["test_rule"]
        assert result == [definition]

        # Test non-existing definition
        result = symbol_table["non_existent"]
        assert result is None

    def test_contains(self):
        """Test __contains__ method."""
        symbol_table = SymbolTable()
        definition = create_mock_definition("test_rule")
        symbol_table.definitions["test_rule"] = [definition]

        # Test existing definition
        assert "test_rule" in symbol_table

        # Test non-existing definition
        assert "non_existent" not in symbol_table

    def test_register_definition(self):
        """Test _register_definition method."""
        symbol_table = SymbolTable()
        definition1 = create_mock_definition("test_rule")
        definition2 = create_mock_definition("test_rule")

        # Register first definition
        symbol_table._register_definition(definition1)
        assert "test_rule" in symbol_table.definitions
        assert len(symbol_table.definitions["test_rule"]) == 1
        assert symbol_table.definitions["test_rule"][0] is definition1

        # Register second definition with same name
        symbol_table._register_definition(definition2)
        assert len(symbol_table.definitions["test_rule"]) == 2
        assert symbol_table.definitions["test_rule"][1] is definition2

    def test_register_definition_error(self):
        """Test _register_definition_error method."""
        symbol_table = SymbolTable()
        error = MultipleDefinitionsError("test_rule")
        definition = create_mock_definition("test_rule")

        symbol_table._register_definition_error(error, definition)

        assert len(symbol_table.definition_errors) == 1
        assert symbol_table.definition_errors[0] == (error, definition)

    def test_register_definition_error_no_definition(self):
        """Test _register_definition_error method without definition."""
        symbol_table = SymbolTable()
        error = DefinitionNotFoundError("missing_rule")

        symbol_table._register_definition_error(error)

        assert len(symbol_table.definition_errors) == 1
        assert symbol_table.definition_errors[0] == (error, None)

    def test_register_reference(self):
        """Test _register_reference method."""
        symbol_table = SymbolTable()
        reference1 = create_mock_reference("test_rule")
        reference2 = create_mock_reference("test_rule")

        # Register first reference
        symbol_table._register_reference(reference1)
        assert "test_rule" in symbol_table.references
        assert len(symbol_table.references["test_rule"]) == 1
        assert symbol_table.references["test_rule"][0] is reference1

        # Register second reference with same name
        symbol_table._register_reference(reference2)
        assert len(symbol_table.references["test_rule"]) == 2
        assert symbol_table.references["test_rule"][1] is reference2

    def test_register_reference_error(self):
        """Test _register_reference_error method."""
        symbol_table = SymbolTable()
        error = DefinitionNotFoundForReferenceError("undefined_rule")
        reference = create_mock_reference("undefined_rule")
        definition = create_mock_definition("undefined_rule")

        symbol_table._register_reference_error(error, reference, definition)

        assert len(symbol_table.reference_errors) == 1
        assert symbol_table.reference_errors[0] == (error, reference, definition)

    def test_register_reference_error_minimal(self):
        """Test _register_reference_error method with minimal parameters."""
        symbol_table = SymbolTable()
        error = DefinitionNotFoundForReferenceError("undefined_rule")

        symbol_table._register_reference_error(error)

        assert len(symbol_table.reference_errors) == 1
        assert symbol_table.reference_errors[0] == (error, None, None)

    def test_get_rule_definitions(self):
        """Test get_rule_definitions method."""
        symbol_table = SymbolTable()
        rule_def1 = create_mock_definition("rule1", kind=Kind.RULE)
        rule_def2 = create_mock_definition("rule2", kind=Kind.RULE)
        terminal_def = create_mock_definition("TERMINAL", kind=Kind.TERMINAL)

        symbol_table.definitions["rule1"] = [rule_def1]
        symbol_table.definitions["rule2"] = [rule_def2]
        symbol_table.definitions["TERMINAL"] = [terminal_def]

        rule_definitions = symbol_table.get_rule_definitions()

        assert len(rule_definitions) == 2
        assert rule_def1 in rule_definitions
        assert rule_def2 in rule_definitions
        assert terminal_def not in rule_definitions

    def test_get_terminal_definitions(self):
        """Test get_terminal_definitions method."""
        symbol_table = SymbolTable()
        rule_def = create_mock_definition("rule", kind=Kind.RULE)
        terminal_def1 = create_mock_definition("TERMINAL1", kind=Kind.TERMINAL)
        terminal_def2 = create_mock_definition("TERMINAL2", kind=Kind.TERMINAL)

        symbol_table.definitions["rule"] = [rule_def]
        symbol_table.definitions["TERMINAL1"] = [terminal_def1]
        symbol_table.definitions["TERMINAL2"] = [terminal_def2]

        terminal_definitions = symbol_table.get_terminal_definitions()

        assert len(terminal_definitions) == 2
        assert terminal_def1 in terminal_definitions
        assert terminal_def2 in terminal_definitions
        assert rule_def not in terminal_definitions

    def test_get_all_definitions_basic(self):
        """Test get_all_definitions method with basic definitions."""
        symbol_table = SymbolTable()
        rule_def = create_mock_definition("rule", kind=Kind.RULE)
        terminal_def = create_mock_definition("TERMINAL", kind=Kind.TERMINAL)

        symbol_table.definitions["rule"] = [rule_def]
        symbol_table.definitions["TERMINAL"] = [terminal_def]

        all_definitions = symbol_table.get_all_definitions()

        assert len(all_definitions) == 2
        assert rule_def in all_definitions
        assert terminal_def in all_definitions

    def test_get_all_definitions_with_template_parameters(self):
        """Test get_all_definitions method with template parameters."""
        symbol_table = SymbolTable()

        # Create a rule definition with children (template parameters)
        rule_def = create_mock_definition("template_rule", kind=Kind.RULE)
        param_def = create_mock_definition("param1", kind=Kind.RULE)
        rule_def.children = {"param1": [param_def]}

        symbol_table.definitions["template_rule"] = [rule_def]

        all_definitions = symbol_table.get_all_definitions()

        # Should include both the rule and its parameter
        assert len(all_definitions) >= 1
        assert rule_def in all_definitions

    def test_get_all_definitions_cached(self):
        """Test get_all_definitions method caching behavior."""
        symbol_table = SymbolTable()
        rule_def = create_mock_definition("rule", kind=Kind.RULE)
        symbol_table.definitions["rule"] = [rule_def]

        # First call
        all_definitions1 = symbol_table.get_all_definitions()

        # Second call should return the same cached result
        all_definitions2 = symbol_table.get_all_definitions()

        assert all_definitions1 is all_definitions2

    def test_get_definition_direct_match(self):
        """Test get_definition method with direct definition match."""
        symbol_table = SymbolTable()
        definition = create_mock_definition("test_rule")
        symbol_table.definitions["test_rule"] = [definition]

        result = symbol_table.get_definition("test_rule")
        assert result is definition

    def test_get_definition_no_match(self):
        """Test get_definition method with no match."""
        symbol_table = SymbolTable()

        result = symbol_table.get_definition("non_existent")
        assert result is None

    def test_get_definition_from_rule_reference(self):
        """Test get_definition method finding definition through rule reference."""
        symbol_table = SymbolTable()

        # Create a rule and its definition
        rule_def = create_mock_definition("parent_rule")
        symbol_table.definitions["parent_rule"] = [rule_def]

        # Create a rule AST node and reference
        rule_ast = Mock(spec=Rule)
        rule_ast.name = Mock()
        rule_ast.name.__str__ = Mock(return_value="parent_rule")

        reference = create_mock_reference("param", ast_node=rule_ast)
        symbol_table.references["param"] = [reference]

        result = symbol_table.get_definition("param")
        assert result is rule_def

    def test_get_definition_from_import_reference(self):
        """Test get_definition method finding definition through import reference."""
        symbol_table = SymbolTable()

        # Create an import alias and its definition
        import_def = create_mock_definition("import_alias")
        symbol_table.definitions["import_alias"] = [import_def]

        # Create an import AST node and reference
        import_ast = Mock(spec=Import)
        import_ast.alias = Mock()
        import_ast.alias.__str__ = Mock(return_value="import_alias")

        reference = create_mock_reference("imported_symbol", ast_node=import_ast)
        symbol_table.references["imported_symbol"] = [reference]

        result = symbol_table.get_definition("imported_symbol")
        assert result is import_def

    def test_get_definition_import_no_alias(self):
        """Test get_definition method with import reference but no alias."""
        symbol_table = SymbolTable()

        # Create an import AST node without alias
        import_ast = Mock(spec=Import)
        import_ast.alias = None

        reference = create_mock_reference("imported_symbol", ast_node=import_ast)
        symbol_table.references["imported_symbol"] = [reference]

        result = symbol_table.get_definition("imported_symbol")
        assert result is None

    def test_get_all_references_basic(self):
        """Test get_all_references method."""
        symbol_table = SymbolTable()
        reference1 = create_mock_reference("rule1")
        reference2 = create_mock_reference("rule2")
        reference3 = create_mock_reference("rule1")  # Another reference to rule1

        symbol_table.references["rule1"] = [reference1, reference3]
        symbol_table.references["rule2"] = [reference2]

        all_references = symbol_table.get_all_references()

        assert len(all_references) == 3
        assert reference1 in all_references
        assert reference2 in all_references
        assert reference3 in all_references

    def test_get_all_references_cached(self):
        """Test get_all_references method caching behavior."""
        symbol_table = SymbolTable()
        reference = create_mock_reference("rule1")
        symbol_table.references["rule1"] = [reference]

        # First call
        all_references1 = symbol_table.get_all_references()

        # Second call should return the same cached result
        all_references2 = symbol_table.get_all_references()

        assert all_references1 is all_references2

    @patch("lark_parser_language_server.symbol_table.definitions_from_ast_node")
    def test_collect_definitions(self, mock_definitions_from_ast_node):
        """Test collect_definitions method."""
        symbol_table = SymbolTable()

        # Create mock statements and definitions
        statement1 = Mock()
        statement2 = Mock()
        ast = create_mock_ast([statement1, statement2])

        definition1 = create_mock_definition("rule1")
        definition2 = create_mock_definition("rule2")

        # Mock the definitions_from_ast_node to return different definitions for each statement
        mock_definitions_from_ast_node.side_effect = [[definition1], [definition2]]

        symbol_table.collect_definitions(ast)

        # Verify that definitions_from_ast_node was called for each statement
        assert mock_definitions_from_ast_node.call_count == 2
        mock_definitions_from_ast_node.assert_any_call(statement1)
        mock_definitions_from_ast_node.assert_any_call(statement2)

        # Verify that definitions were registered
        assert "rule1" in symbol_table.definitions
        assert "rule2" in symbol_table.definitions
        assert symbol_table.definitions["rule1"][0] is definition1
        assert symbol_table.definitions["rule2"][0] is definition2

    @patch("lark_parser_language_server.symbol_table.validate_single_definition")
    @patch("lark_parser_language_server.symbol_table.validate_shadowed_definition")
    def test_validate_definitions(self, mock_validate_shadowed, mock_validate_single):
        """Test validate_definitions method."""
        symbol_table = SymbolTable()

        # Add some regular definitions
        rule_def = create_mock_definition("rule1", kind=Kind.RULE)
        terminal_def = create_mock_definition("TERMINAL1", kind=Kind.TERMINAL)

        symbol_table.definitions["rule1"] = [rule_def]
        symbol_table.definitions["TERMINAL1"] = [terminal_def]

        # Add a rule with children (template parameters)
        template_rule = create_mock_definition("template_rule", kind=Kind.RULE)
        param_def = create_mock_definition("param1")
        template_rule.children = {"param1": [param_def]}
        symbol_table.definitions["template_rule"] = [template_rule]

        symbol_table.validate_definitions()

        # Should validate single definition for each name (including child definitions)
        expected_calls = len(symbol_table.definitions) + 1  # +1 for child definition
        assert mock_validate_single.call_count == expected_calls

        # Should validate shadowed definitions for child definitions
        mock_validate_shadowed.assert_called()

    @patch("lark_parser_language_server.symbol_table.references_from_ast_node")
    def test_collect_references(self, mock_references_from_ast_node):
        """Test collect_references method."""
        symbol_table = SymbolTable()

        # Create mock statements and references
        statement1 = Mock()
        statement2 = Mock()
        ast = create_mock_ast([statement1, statement2])

        reference1 = create_mock_reference("rule1")
        reference2 = create_mock_reference("rule2")

        # Mock the references_from_ast_node to return different references for each statement
        mock_references_from_ast_node.side_effect = [[reference1], [reference2]]

        symbol_table.collect_references(ast)

        # Verify that references_from_ast_node was called for each statement
        assert mock_references_from_ast_node.call_count == 2
        mock_references_from_ast_node.assert_any_call(statement1)
        mock_references_from_ast_node.assert_any_call(statement2)

        # Verify that references were registered
        assert "rule1" in symbol_table.references
        assert "rule2" in symbol_table.references
        assert symbol_table.references["rule1"][0] is reference1
        assert symbol_table.references["rule2"][0] is reference2

    @patch("lark_parser_language_server.symbol_table.validate_undefined_reference")
    def test_validate_references(self, mock_validate_undefined):
        """Test validate_references method."""
        symbol_table = SymbolTable()

        # Add some references
        reference1 = create_mock_reference("rule1")
        reference2 = create_mock_reference("rule2")

        symbol_table.references["rule1"] = [reference1]
        symbol_table.references["rule2"] = [reference2]

        symbol_table.validate_references()

        # Should validate undefined reference for each reference name
        assert mock_validate_undefined.call_count == len(symbol_table.references)


class TestSymbolTableIntegration:
    """Integration tests for SymbolTable class."""

    def test_complete_workflow(self):
        """Test complete symbol table workflow."""
        symbol_table = SymbolTable()

        # Create some definitions and references
        rule_def = create_mock_definition("main_rule", kind=Kind.RULE)
        terminal_def = create_mock_definition("TOKEN", kind=Kind.TERMINAL)

        # Register definitions
        symbol_table._register_definition(rule_def)
        symbol_table._register_definition(terminal_def)

        # Create and register references
        reference1 = create_mock_reference("main_rule")
        reference2 = create_mock_reference("TOKEN")
        reference3 = create_mock_reference("undefined_rule")

        symbol_table._register_reference(reference1)
        symbol_table._register_reference(reference2)
        symbol_table._register_reference(reference3)

        # Test various getter methods
        assert len(symbol_table.get_rule_definitions()) == 1
        assert len(symbol_table.get_terminal_definitions()) == 1
        assert len(symbol_table.get_all_definitions()) == 2
        assert len(symbol_table.get_all_references()) == 3

        # Test definition lookup
        assert symbol_table.get_definition("main_rule") is rule_def
        assert symbol_table.get_definition("TOKEN") is terminal_def
        assert symbol_table.get_definition("undefined_rule") is None

    def test_error_collection(self):
        """Test error collection functionality."""
        symbol_table = SymbolTable()

        # Test definition error registration
        def_error = MultipleDefinitionsError("duplicate_rule")
        definition = create_mock_definition("duplicate_rule")
        symbol_table._register_definition_error(def_error, definition)

        # Test reference error registration
        ref_error = DefinitionNotFoundForReferenceError("undefined_rule")
        reference = create_mock_reference("undefined_rule")
        symbol_table._register_reference_error(ref_error, reference)

        assert len(symbol_table.definition_errors) == 1
        assert len(symbol_table.reference_errors) == 1
        assert symbol_table.definition_errors[0] == (def_error, definition)
        assert symbol_table.reference_errors[0] == (ref_error, reference, None)

    def test_complex_definition_lookup(self):
        """Test complex definition lookup scenarios."""
        symbol_table = SymbolTable()

        # Create a rule with template parameters
        template_rule = create_mock_definition("template_rule", kind=Kind.RULE)
        param_def = create_mock_definition("T")
        template_rule.children = {"T": [param_def]}

        symbol_table.definitions["template_rule"] = [template_rule]

        # Create a reference within the template rule scope
        rule_ast = Mock(spec=Rule)
        rule_ast.name = Mock()
        rule_ast.name.__str__ = Mock(return_value="template_rule")

        param_reference = create_mock_reference("T", ast_node=rule_ast)
        symbol_table.references["T"] = [param_reference]

        # The definition lookup should find the template rule
        result = symbol_table.get_definition("T")
        assert result is template_rule

    def test_empty_symbol_table(self):
        """Test behavior with empty symbol table."""
        symbol_table = SymbolTable()

        assert symbol_table.get_rule_definitions() == []
        assert symbol_table.get_terminal_definitions() == []
        assert symbol_table.get_all_definitions() == []
        assert symbol_table.get_all_references() == []
        assert symbol_table.get_definition("any_name") is None
        assert "any_name" not in symbol_table
        assert symbol_table["any_name"] is None

    def test_multiple_definitions_same_name(self):
        """Test handling multiple definitions with the same name."""
        symbol_table = SymbolTable()

        # Add multiple definitions with the same name
        def1 = create_mock_definition("duplicate_rule", line=1)
        def2 = create_mock_definition("duplicate_rule", line=2)

        symbol_table._register_definition(def1)
        symbol_table._register_definition(def2)

        # Should have both definitions
        assert len(symbol_table.definitions["duplicate_rule"]) == 2
        assert symbol_table.definitions["duplicate_rule"][0] is def1
        assert symbol_table.definitions["duplicate_rule"][1] is def2

        # get_definition should return the first one
        assert symbol_table.get_definition("duplicate_rule") is def1

    def test_cache_invalidation_scenarios(self):
        """Test scenarios where caches should be properly managed."""
        symbol_table = SymbolTable()

        # First, populate and access caches
        rule_def = create_mock_definition("rule", kind=Kind.RULE)
        symbol_table._register_definition(rule_def)
        reference = create_mock_reference("rule")
        symbol_table._register_reference(reference)

        # Access to populate caches
        all_defs1 = symbol_table.get_all_definitions()
        all_refs1 = symbol_table.get_all_references()

        # Verify cache is used
        all_defs2 = symbol_table.get_all_definitions()
        all_refs2 = symbol_table.get_all_references()

        assert all_defs1 is all_defs2
        assert all_refs1 is all_refs2
