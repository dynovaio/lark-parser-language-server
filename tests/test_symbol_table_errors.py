"""Tests for lark_parser_language_server/symbol_table/errors.py module."""

import pytest

from lark_parser_language_server.symbol_table.errors import (
    DefinitionNotFoundError,
    DefinitionNotFoundForReferenceError,
    MultipleDefinitionsError,
    ShadowedDefinitionError,
    SymbolTableError,
)
from lark_parser_language_server.symbol_table.symbol import Position


class TestSymbolTableError:
    """Test SymbolTableError base class."""

    def test_symbol_table_error_creation_without_position(self):
        """Test SymbolTableError creation without position."""
        error = SymbolTableError("Test error message")

        assert str(error) == "Test error message"
        assert error.line == 0
        assert error.column == 0
        assert error.width == 1

    def test_symbol_table_error_creation_with_position(self):
        """Test SymbolTableError creation with position."""
        position = Position(line=10, column=5)
        error = SymbolTableError("Test error message", position)

        assert str(error) == "Test error message"
        assert error.line == 10
        assert error.column == 5
        assert error.width == 1

    def test_symbol_table_error_creation_with_none_position(self):
        """Test SymbolTableError creation with None position."""
        error = SymbolTableError("Test error message", None)

        assert str(error) == "Test error message"
        assert error.line == 0
        assert error.column == 0
        assert error.width == 1

    def test_symbol_table_error_inheritance(self):
        """Test that SymbolTableError inherits from Exception."""
        error = SymbolTableError("Test error")
        assert isinstance(error, Exception)

    def test_symbol_table_error_default_attributes(self):
        """Test SymbolTableError default class attributes."""
        assert SymbolTableError.line == 0
        assert SymbolTableError.column == 0
        assert SymbolTableError.width == 1


class TestDefinitionNotFoundError:
    """Test DefinitionNotFoundError class."""

    def test_definition_not_found_error_creation_without_position(self):
        """Test DefinitionNotFoundError creation without position."""
        error = DefinitionNotFoundError("test_symbol")

        assert str(error) == "Definition for symbol 'test_symbol' not found."
        assert error.name == "test_symbol"
        assert error.width == len("test_symbol")
        assert error.line == 0
        assert error.column == 0

    def test_definition_not_found_error_creation_with_position(self):
        """Test DefinitionNotFoundError creation with position."""
        position = Position(line=15, column=8)
        error = DefinitionNotFoundError("another_symbol", position)

        assert str(error) == "Definition for symbol 'another_symbol' not found."
        assert error.name == "another_symbol"
        assert error.width == len("another_symbol")
        assert error.line == 15
        assert error.column == 8

    def test_definition_not_found_error_inheritance(self):
        """Test that DefinitionNotFoundError inherits from SymbolTableError."""
        error = DefinitionNotFoundError("test")
        assert isinstance(error, SymbolTableError)
        assert isinstance(error, Exception)

    def test_definition_not_found_error_with_empty_name(self):
        """Test DefinitionNotFoundError with empty name."""
        error = DefinitionNotFoundError("")

        assert str(error) == "Definition for symbol '' not found."
        assert error.name == ""
        assert error.width == 0

    def test_definition_not_found_error_with_long_name(self):
        """Test DefinitionNotFoundError with long symbol name."""
        long_name = "very_long_symbol_name_for_testing"
        error = DefinitionNotFoundError(long_name)

        assert error.name == long_name
        assert error.width == len(long_name)


class TestShadowedDefinitionError:
    """Test ShadowedDefinitionError class."""

    def test_shadowed_definition_error_rule_name(self):
        """Test ShadowedDefinitionError with rule name (lowercase)."""
        error = ShadowedDefinitionError("my_rule")

        expected_message = (
            "Template parameter 'my_rule' conflicts with existing rule 'my_rule'."
        )
        assert str(error) == expected_message
        assert error.name == "my_rule"
        assert error.width == len("my_rule")

    def test_shadowed_definition_error_terminal_name(self):
        """Test ShadowedDefinitionError with terminal name (uppercase)."""
        error = ShadowedDefinitionError("MY_TERMINAL")

        expected_message = "Template parameter 'MY_TERMINAL' conflicts with existing terminal 'MY_TERMINAL'."
        assert str(error) == expected_message
        assert error.name == "MY_TERMINAL"
        assert error.width == len("MY_TERMINAL")

    def test_shadowed_definition_error_with_position(self):
        """Test ShadowedDefinitionError with position."""
        position = Position(line=20, column=12)
        error = ShadowedDefinitionError("conflict_name", position)

        assert error.line == 20
        assert error.column == 12
        assert error.name == "conflict_name"

    def test_shadowed_definition_error_inheritance(self):
        """Test that ShadowedDefinitionError inherits from SymbolTableError."""
        error = ShadowedDefinitionError("test")
        assert isinstance(error, SymbolTableError)
        assert isinstance(error, Exception)

    def test_shadowed_definition_error_mixed_case(self):
        """Test ShadowedDefinitionError with mixed case name."""
        error = ShadowedDefinitionError("Mixed_Case_Name")

        # Mixed case should be treated as rule (not all uppercase)
        expected_message = "Template parameter 'Mixed_Case_Name' conflicts with existing rule 'Mixed_Case_Name'."
        assert str(error) == expected_message

    def test_shadowed_definition_error_single_char_rule(self):
        """Test ShadowedDefinitionError with single character rule name."""
        error = ShadowedDefinitionError("a")

        expected_message = "Template parameter 'a' conflicts with existing rule 'a'."
        assert str(error) == expected_message
        assert error.width == 1

    def test_shadowed_definition_error_single_char_terminal(self):
        """Test ShadowedDefinitionError with single character terminal name."""
        error = ShadowedDefinitionError("A")

        expected_message = (
            "Template parameter 'A' conflicts with existing terminal 'A'."
        )
        assert str(error) == expected_message
        assert error.width == 1


class TestMultipleDefinitionsError:
    """Test MultipleDefinitionsError class."""

    def test_multiple_definitions_error_rule_name(self):
        """Test MultipleDefinitionsError with rule name (lowercase)."""
        error = MultipleDefinitionsError("duplicate_rule")

        expected_message = "Multiple definitions found for rule 'duplicate_rule'."
        assert str(error) == expected_message
        assert error.name == "duplicate_rule"
        assert error.width == len("duplicate_rule")

    def test_multiple_definitions_error_terminal_name(self):
        """Test MultipleDefinitionsError with terminal name (uppercase)."""
        error = MultipleDefinitionsError("DUPLICATE_TERMINAL")

        expected_message = (
            "Multiple definitions found for terminal 'DUPLICATE_TERMINAL'."
        )
        assert str(error) == expected_message
        assert error.name == "DUPLICATE_TERMINAL"
        assert error.width == len("DUPLICATE_TERMINAL")

    def test_multiple_definitions_error_with_position(self):
        """Test MultipleDefinitionsError with position."""
        position = Position(line=25, column=3)
        error = MultipleDefinitionsError("dup_symbol", position)

        assert error.line == 25
        assert error.column == 3
        assert error.name == "dup_symbol"

    def test_multiple_definitions_error_inheritance(self):
        """Test that MultipleDefinitionsError inherits from SymbolTableError."""
        error = MultipleDefinitionsError("test")
        assert isinstance(error, SymbolTableError)
        assert isinstance(error, Exception)

    def test_multiple_definitions_error_mixed_case(self):
        """Test MultipleDefinitionsError with mixed case name."""
        error = MultipleDefinitionsError("Another_Mixed_Case")

        # Mixed case should be treated as rule (not all uppercase)
        expected_message = "Multiple definitions found for rule 'Another_Mixed_Case'."
        assert str(error) == expected_message

    def test_multiple_definitions_error_empty_name(self):
        """Test MultipleDefinitionsError with empty name."""
        error = MultipleDefinitionsError("")

        expected_message = "Multiple definitions found for rule ''."
        assert str(error) == expected_message
        assert error.width == 0


class TestDefinitionNotFoundForReferenceError:
    """Test DefinitionNotFoundForReferenceError class."""

    def test_definition_not_found_for_reference_error_rule_name(self):
        """Test DefinitionNotFoundForReferenceError with rule name (lowercase)."""
        error = DefinitionNotFoundForReferenceError("missing_rule")

        expected_message = "No definition found for rule 'missing_rule'."
        assert str(error) == expected_message
        assert error.name == "missing_rule"
        assert error.width == len("missing_rule")

    def test_definition_not_found_for_reference_error_terminal_name(self):
        """Test DefinitionNotFoundForReferenceError with terminal name (uppercase)."""
        error = DefinitionNotFoundForReferenceError("MISSING_TERMINAL")

        expected_message = "No definition found for terminal 'MISSING_TERMINAL'."
        assert str(error) == expected_message
        assert error.name == "MISSING_TERMINAL"
        assert error.width == len("MISSING_TERMINAL")

    def test_definition_not_found_for_reference_error_with_position(self):
        """Test DefinitionNotFoundForReferenceError with position."""
        position = Position(line=30, column=7)
        error = DefinitionNotFoundForReferenceError("undefined_ref", position)

        assert error.line == 30
        assert error.column == 7
        assert error.name == "undefined_ref"

    def test_definition_not_found_for_reference_error_inheritance(self):
        """Test that DefinitionNotFoundForReferenceError inherits from SymbolTableError."""
        error = DefinitionNotFoundForReferenceError("test")
        assert isinstance(error, SymbolTableError)
        assert isinstance(error, Exception)

    def test_definition_not_found_for_reference_error_mixed_case(self):
        """Test DefinitionNotFoundForReferenceError with mixed case name."""
        error = DefinitionNotFoundForReferenceError("Mixed_Reference")

        # Mixed case should be treated as rule (not all uppercase)
        expected_message = "No definition found for rule 'Mixed_Reference'."
        assert str(error) == expected_message

    def test_definition_not_found_for_reference_error_numeric_name(self):
        """Test DefinitionNotFoundForReferenceError with numeric characters."""
        error = DefinitionNotFoundForReferenceError("rule123")

        expected_message = "No definition found for rule 'rule123'."
        assert str(error) == expected_message
        assert error.name == "rule123"

    def test_definition_not_found_for_reference_error_special_chars(self):
        """Test DefinitionNotFoundForReferenceError with special characters."""
        error = DefinitionNotFoundForReferenceError("rule_with_underscores")

        expected_message = "No definition found for rule 'rule_with_underscores'."
        assert str(error) == expected_message


class TestErrorsCommonBehavior:
    """Test common behavior across all error classes."""

    def test_all_errors_set_width_correctly(self):
        """Test that all error classes set width to name length."""
        errors = [
            DefinitionNotFoundError("test_name"),
            ShadowedDefinitionError("test_name"),
            MultipleDefinitionsError("test_name"),
            DefinitionNotFoundForReferenceError("test_name"),
        ]

        for error in errors:
            assert error.width == len("test_name")
            assert hasattr(error, "name")
            assert error.name == "test_name"

    def test_all_errors_handle_position_correctly(self):
        """Test that all error classes handle position parameter correctly."""
        position = Position(line=42, column=24)

        errors = [
            DefinitionNotFoundError("test", position),
            ShadowedDefinitionError("test", position),
            MultipleDefinitionsError("test", position),
            DefinitionNotFoundForReferenceError("test", position),
        ]

        for error in errors:
            assert error.line == 42
            assert error.column == 24

    def test_all_errors_distinguish_rule_vs_terminal(self):
        """Test that errors distinguish between rules and terminals correctly."""
        rule_name = "lowercase_rule"
        terminal_name = "UPPERCASE_TERMINAL"

        # Test that rule names (lowercase) are identified correctly
        shadowed_rule = ShadowedDefinitionError(rule_name)
        multiple_rule = MultipleDefinitionsError(rule_name)
        reference_rule = DefinitionNotFoundForReferenceError(rule_name)

        assert "rule" in str(shadowed_rule)
        assert "rule" in str(multiple_rule)
        assert "rule" in str(reference_rule)

        # Test that terminal names (uppercase) are identified correctly
        shadowed_terminal = ShadowedDefinitionError(terminal_name)
        multiple_terminal = MultipleDefinitionsError(terminal_name)
        reference_terminal = DefinitionNotFoundForReferenceError(terminal_name)

        assert "terminal" in str(shadowed_terminal)
        assert "terminal" in str(multiple_terminal)
        assert "terminal" in str(reference_terminal)

    def test_all_errors_are_exceptions(self):
        """Test that all error classes are proper exceptions."""
        errors = [
            SymbolTableError("test"),
            DefinitionNotFoundError("test"),
            ShadowedDefinitionError("test"),
            MultipleDefinitionsError("test"),
            DefinitionNotFoundForReferenceError("test"),
        ]

        for error in errors:
            assert isinstance(error, Exception)
            assert isinstance(error, SymbolTableError)

    def test_error_message_content(self):
        """Test that error messages contain expected content."""
        name = "test_symbol"

        def_not_found = DefinitionNotFoundError(name)
        assert "Definition for symbol" in str(def_not_found)
        assert name in str(def_not_found)

        shadowed = ShadowedDefinitionError(name)
        assert "Template parameter" in str(shadowed)
        assert "conflicts with existing" in str(shadowed)
        assert name in str(shadowed)

        multiple = MultipleDefinitionsError(name)
        assert "Multiple definitions found" in str(multiple)
        assert name in str(multiple)

        ref_not_found = DefinitionNotFoundForReferenceError(name)
        assert "No definition found" in str(ref_not_found)
        assert name in str(ref_not_found)
