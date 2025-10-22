"""Tests for lark_parser_language_server.symbol_table.validators module."""

from unittest.mock import Mock

import pytest

from lark_parser_language_server.symbol_table.errors import (
    DefinitionNotFoundError,
    DefinitionNotFoundForReferenceError,
    MultipleDefinitionsError,
    ShadowedDefinitionError,
)
from lark_parser_language_server.symbol_table.flags import Kind
from lark_parser_language_server.symbol_table.symbol import (
    Definition,
    Position,
    Range,
    Reference,
)
from lark_parser_language_server.symbol_table.validators import (
    _reference_is_in_local_scope,
    validate_shadowed_definition,
    validate_single_definition,
    validate_undefined_reference,
)
from lark_parser_language_server.syntax_tree.nodes import Import, Rule


def create_mock_definition(name="test_def", line=1, column=1):
    """Helper to create a mock Definition."""
    position = Position(line=line, column=column)
    range_obj = Range(
        start=position, end=Position(line=line, column=column + len(name))
    )

    definition = Mock(spec=Definition)
    definition.name = name
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


class TestValidateSingleDefinition:
    """Test cases for validate_single_definition function."""

    def test_validate_single_definition_valid(self):
        """Test validation passes with exactly one definition."""
        definition = create_mock_definition("valid_def")
        definitions = [definition]

        # Should not raise any exception
        validate_single_definition("valid_def", definitions)

    def test_validate_single_definition_no_definitions_raises(self):
        """Test validation raises error with no definitions."""
        with pytest.raises(DefinitionNotFoundError) as exc_info:
            validate_single_definition("missing_def", [])

        assert "No definitions found with name 'missing_def'" in str(exc_info.value)

    def test_validate_single_definition_no_definitions_with_handler(self):
        """Test validation calls error handler with no definitions."""
        error_handler = Mock()

        validate_single_definition("missing_def", [], error_handler=error_handler)

        error_handler.assert_called_once()
        args = error_handler.call_args[0]
        assert isinstance(args[0], DefinitionNotFoundError)
        assert args[1] is None

    def test_validate_single_definition_multiple_definitions_raises(self):
        """Test validation raises error with multiple definitions."""
        def1 = create_mock_definition("dup_def", line=1, column=1)
        def2 = create_mock_definition("dup_def", line=2, column=1)
        definitions = [def1, def2]

        with pytest.raises(MultipleDefinitionsError):
            validate_single_definition("dup_def", definitions)

    def test_validate_single_definition_multiple_definitions_with_handler(self):
        """Test validation calls error handler with multiple definitions."""
        def1 = create_mock_definition("dup_def", line=1, column=1)
        def2 = create_mock_definition("dup_def", line=2, column=1)
        def3 = create_mock_definition("dup_def", line=3, column=1)
        definitions = [def1, def2, def3]

        error_handler = Mock()
        validate_single_definition("dup_def", definitions, error_handler=error_handler)

        # Should be called twice (for def2 and def3)
        assert error_handler.call_count == 2

        # Check first call
        first_call_args = error_handler.call_args_list[0][0]
        assert isinstance(first_call_args[0], MultipleDefinitionsError)
        assert first_call_args[1] is def2

        # Check second call
        second_call_args = error_handler.call_args_list[1][0]
        assert isinstance(second_call_args[0], MultipleDefinitionsError)
        assert second_call_args[1] is def3


class TestValidateShadowedDefinition:
    """Test cases for validate_shadowed_definition function."""

    def test_validate_shadowed_definition_no_shadow(self):
        """Test validation passes when no shadowing occurs."""
        definition = create_mock_definition("unique_def")
        definitions = {"other_def": [create_mock_definition("other_def")]}

        # Should not raise any exception
        validate_shadowed_definition(definition, definitions)

    def test_validate_shadowed_definition_with_shadow_raises(self):
        """Test validation raises error when shadowing occurs."""
        definition = create_mock_definition("shadowed_def")
        existing_def = create_mock_definition("shadowed_def")
        definitions = {"shadowed_def": [existing_def]}

        with pytest.raises(ShadowedDefinitionError):
            validate_shadowed_definition(definition, definitions)

    def test_validate_shadowed_definition_with_shadow_and_handler(self):
        """Test validation calls error handler when shadowing occurs."""
        definition = create_mock_definition("shadowed_def")
        existing_def = create_mock_definition("shadowed_def")
        definitions = {"shadowed_def": [existing_def]}

        error_handler = Mock()
        validate_shadowed_definition(
            definition, definitions, error_handler=error_handler
        )

        error_handler.assert_called_once()
        args = error_handler.call_args[0]
        assert isinstance(args[0], ShadowedDefinitionError)
        assert args[1] is definition


class TestReferenceIsInLocalScope:
    """Test cases for _reference_is_in_local_scope function."""

    def test_reference_is_in_local_scope_rule_in_range(self):
        """Test reference in local scope when it's in a rule's range."""
        rule_ast = Mock(spec=Rule)
        rule_ast.name = Mock()
        rule_ast.name.__str__ = Mock(return_value="test_rule")

        reference = create_mock_reference("param", ast_node=rule_ast)

        # Create definition with range that contains the reference
        definition = create_mock_definition("test_rule")
        definition.range = Mock()
        definition.range.__contains__ = Mock(return_value=True)

        definitions = {"test_rule": [definition]}

        result = _reference_is_in_local_scope("param", reference, definitions)
        assert result is True

    def test_reference_is_in_local_scope_rule_in_children(self):
        """Test reference in local scope when it's in a rule's children."""
        rule_ast = Mock(spec=Rule)
        rule_ast.name = Mock()
        rule_ast.name.__str__ = Mock(return_value="test_rule")

        reference = create_mock_reference("param", ast_node=rule_ast)

        # Create definition with children that contains the reference
        definition = create_mock_definition("test_rule")
        definition.range = Mock()
        definition.range.__contains__ = Mock(return_value=False)
        definition.children = {"param": []}

        definitions = {"test_rule": [definition]}

        result = _reference_is_in_local_scope("param", reference, definitions)
        assert result is True

    def test_reference_is_in_local_scope_import_in_range(self):
        """Test reference in local scope when it's in an import's range."""
        import_ast = Mock(spec=Import)
        import_ast.alias = Mock()
        import_ast.alias.__str__ = Mock(return_value="import_alias")

        reference = create_mock_reference("imported_symbol", ast_node=import_ast)

        # Create definition with range that contains the reference
        definition = create_mock_definition("import_alias")
        definition.range = Mock()
        definition.range.__contains__ = Mock(return_value=True)

        definitions = {"import_alias": [definition]}

        result = _reference_is_in_local_scope("imported_symbol", reference, definitions)
        assert result is True

    def test_reference_is_in_local_scope_import_in_children(self):
        """Test reference in local scope when it's in an import's children."""
        import_ast = Mock(spec=Import)
        import_ast.alias = Mock()
        import_ast.alias.__str__ = Mock(return_value="import_alias")

        reference = create_mock_reference("imported_symbol", ast_node=import_ast)

        # Create definition with children that contains the reference
        definition = create_mock_definition("import_alias")
        definition.range = Mock()
        definition.range.__contains__ = Mock(return_value=False)
        definition.children = {"imported_symbol": []}

        definitions = {"import_alias": [definition]}

        result = _reference_is_in_local_scope("imported_symbol", reference, definitions)
        assert result is True

    def test_reference_is_in_local_scope_import_no_alias(self):
        """Test reference in local scope when import has no alias."""
        import_ast = Mock(spec=Import)
        import_ast.alias = None

        reference = create_mock_reference("imported_symbol", ast_node=import_ast)
        definitions = {}

        result = _reference_is_in_local_scope("imported_symbol", reference, definitions)
        assert result is False

    def test_reference_is_in_local_scope_not_rule_or_import(self):
        """Test reference not in local scope when ast_node is not Rule or Import."""
        other_ast = Mock()  # Not Rule or Import
        reference = create_mock_reference("symbol", ast_node=other_ast)
        definitions = {}

        result = _reference_is_in_local_scope("symbol", reference, definitions)
        assert result is False

    def test_reference_is_in_local_scope_no_ast_node(self):
        """Test reference not in local scope when no ast_node."""
        reference = create_mock_reference("symbol")
        definitions = {}

        result = _reference_is_in_local_scope("symbol", reference, definitions)
        assert result is False

    def test_reference_is_in_local_scope_rule_not_found(self):
        """Test reference not in local scope when rule definition not found."""
        rule_ast = Mock(spec=Rule)
        rule_ast.name = Mock()
        rule_ast.name.__str__ = Mock(return_value="missing_rule")

        reference = create_mock_reference("param", ast_node=rule_ast)
        definitions = {}  # No definition for the rule

        result = _reference_is_in_local_scope("param", reference, definitions)
        assert result is False

    def test_reference_is_in_local_scope_import_alias_not_found(self):
        """Test reference not in local scope when import alias definition not found."""
        import_ast = Mock(spec=Import)
        import_ast.alias = Mock()
        import_ast.alias.__str__ = Mock(return_value="missing_alias")

        reference = create_mock_reference("symbol", ast_node=import_ast)
        definitions = {}  # No definition for the alias

        result = _reference_is_in_local_scope("symbol", reference, definitions)
        assert result is False


class TestValidateUndefinedReference:
    """Test cases for validate_undefined_reference function."""

    def test_validate_undefined_reference_defined(self):
        """Test validation passes when reference is defined."""
        reference = create_mock_reference("defined_symbol")
        references = [reference]
        definitions = {"defined_symbol": [create_mock_definition("defined_symbol")]}

        # Should not raise any exception
        validate_undefined_reference("defined_symbol", references, definitions)

    def test_validate_undefined_reference_undefined_raises(self):
        """Test validation raises error when reference is undefined."""
        reference = create_mock_reference("undefined_symbol")
        references = [reference]
        definitions = {}  # No definitions

        with pytest.raises(DefinitionNotFoundForReferenceError):
            validate_undefined_reference("undefined_symbol", references, definitions)

    def test_validate_undefined_reference_undefined_with_handler(self):
        """Test validation calls error handler when reference is undefined."""
        reference = create_mock_reference("undefined_symbol")
        references = [reference]
        definitions = {}

        error_handler = Mock()
        validate_undefined_reference(
            "undefined_symbol", references, definitions, error_handler=error_handler
        )

        error_handler.assert_called_once()
        args = error_handler.call_args[0]
        assert isinstance(args[0], DefinitionNotFoundForReferenceError)
        assert args[1] is reference
        assert args[2] is None

    def test_validate_undefined_reference_in_local_scope(self):
        """Test validation passes when reference is in local scope."""
        # Create a rule ast node
        rule_ast = Mock(spec=Rule)
        rule_ast.name = Mock()
        rule_ast.name.__str__ = Mock(return_value="test_rule")

        reference = create_mock_reference("local_param", ast_node=rule_ast)
        references = [reference]

        # Create rule definition with children containing the reference
        rule_def = create_mock_definition("test_rule")
        rule_def.range = Mock()
        rule_def.range.__contains__ = Mock(return_value=False)
        rule_def.children = {"local_param": []}

        definitions = {"test_rule": [rule_def]}  # No global definition for local_param

        # Should not raise any exception because reference is in local scope
        validate_undefined_reference("local_param", references, definitions)

    def test_validate_undefined_reference_multiple_references(self):
        """Test validation with multiple references, some undefined."""
        ref1 = create_mock_reference("undefined_symbol", line=1, column=1)
        ref2 = create_mock_reference("undefined_symbol", line=2, column=1)
        references = [ref1, ref2]
        definitions = {}

        error_handler = Mock()
        validate_undefined_reference(
            "undefined_symbol", references, definitions, error_handler=error_handler
        )

        # Should be called twice (once for each reference)
        assert error_handler.call_count == 2

        # Check both calls
        for i, call_args in enumerate(error_handler.call_args_list):
            args = call_args[0]
            assert isinstance(args[0], DefinitionNotFoundForReferenceError)
            assert args[1] is references[i]
            assert args[2] is None

    def test_validate_undefined_reference_mixed_scope(self):
        """Test validation with mix of local and global scope references."""
        # Create rule ast node for local reference
        rule_ast = Mock(spec=Rule)
        rule_ast.name = Mock()
        rule_ast.name.__str__ = Mock(return_value="test_rule")

        local_ref = create_mock_reference(
            "undefined_symbol", ast_node=rule_ast, line=1, column=1
        )
        global_ref = create_mock_reference(
            "undefined_symbol", line=2, column=1
        )  # No ast_node
        references = [local_ref, global_ref]

        # Create rule definition with children containing the local reference
        rule_def = create_mock_definition("test_rule")
        rule_def.range = Mock()
        rule_def.range.__contains__ = Mock(return_value=False)
        rule_def.children = {"undefined_symbol": []}

        definitions = {"test_rule": [rule_def]}  # No global definition

        error_handler = Mock()
        validate_undefined_reference(
            "undefined_symbol", references, definitions, error_handler=error_handler
        )

        # Should be called once (only for the global reference)
        error_handler.assert_called_once()
        args = error_handler.call_args[0]
        assert isinstance(args[0], DefinitionNotFoundForReferenceError)
        assert args[1] is global_ref
        assert args[2] is None


class TestModuleIntegration:
    """Integration tests for the validators module."""

    def test_complete_validation_workflow(self):
        """Test a complete validation workflow."""
        # Create some definitions and references
        def1 = create_mock_definition("rule1", line=1, column=1)
        def2 = create_mock_definition("rule2", line=2, column=1)
        dup_def = create_mock_definition("rule1", line=3, column=1)  # Duplicate

        ref1 = create_mock_reference("rule1", line=5, column=1)
        ref2 = create_mock_reference("rule2", line=6, column=1)
        ref_undefined = create_mock_reference("undefined_rule", line=7, column=1)

        definitions = {
            "rule1": [def1, dup_def],  # Multiple definitions
            "rule2": [def2],
        }

        references = {
            "rule1": [ref1],
            "rule2": [ref2],
            "undefined_rule": [ref_undefined],
        }

        errors = []

        def error_handler(error, *args):
            errors.append((error, args))

        # Test single definition validation
        for name, defs in definitions.items():
            validate_single_definition(name, defs, error_handler=error_handler)

        # Test shadowing validation
        existing_definitions = {"rule2": [def2]}  # Existing scope
        validate_shadowed_definition(
            def1, existing_definitions, error_handler=error_handler
        )

        # Test undefined reference validation
        for name, refs in references.items():
            validate_undefined_reference(
                name, refs, definitions, error_handler=error_handler
            )

        # Check that we collected the expected errors
        assert (
            len(errors) >= 2
        )  # At least multiple definitions error and undefined reference error

        # Verify we have a MultipleDefinitionsError
        multiple_def_errors = [
            e for e, _ in errors if isinstance(e, MultipleDefinitionsError)
        ]
        assert len(multiple_def_errors) == 1

        # Verify we have an undefined reference error
        undefined_ref_errors = [
            e for e, _ in errors if isinstance(e, DefinitionNotFoundForReferenceError)
        ]
        assert len(undefined_ref_errors) == 1

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with empty inputs
        validate_single_definition("test", [create_mock_definition("test")])
        validate_shadowed_definition(create_mock_definition("test"), {})
        validate_undefined_reference(
            "test", [], {"test": [create_mock_definition("test")]}
        )

        # Test with None values where appropriate
        ref_no_ast = create_mock_reference("test")
        ref_no_ast.ast_node = None
        result = _reference_is_in_local_scope("test", ref_no_ast, {})
        assert result is False

        # Test with missing attributes - remove range and children attributes
        definition = create_mock_definition("test")
        if hasattr(definition, "range"):
            delattr(definition, "range")
        if hasattr(definition, "children"):
            delattr(definition, "children")

        rule_ast = Mock(spec=Rule)
        rule_ast.name = Mock()
        rule_ast.name.__str__ = Mock(return_value="test")

        reference = create_mock_reference("param", ast_node=rule_ast)
        definitions = {"test": [definition]}

        result = _reference_is_in_local_scope("param", reference, definitions)
        assert result is False
