"""Tests for lark_parser_language_server.symbol_table.flags module."""

from enum import Flag, StrEnum

import pytest

from lark_parser_language_server.symbol_table.flags import Directives, Kind, Modifiers


class TestDirectives:
    """Test cases for Directives flag enum."""

    def test_directives_enum_values(self):
        """Test that Directives enum has correct values."""
        assert hasattr(Directives, "OVERRIDED")
        assert hasattr(Directives, "EXTENDED")
        assert hasattr(Directives, "IGNORED")
        assert hasattr(Directives, "DECLARED")
        assert hasattr(Directives, "IMPORTED")

    def test_directives_flag_inheritance(self):
        """Test that Directives inherits from Flag."""
        assert issubclass(Directives, Flag)

    def test_directives_auto_values(self):
        """Test that Directives uses auto() for values."""
        # Flag enums using auto() should have power-of-2 values
        assert Directives.OVERRIDED.value == 1
        assert Directives.EXTENDED.value == 2
        assert Directives.IGNORED.value == 4
        assert Directives.DECLARED.value == 8
        assert Directives.IMPORTED.value == 16

    def test_directives_flag_combinations(self):
        """Test that Directives flags can be combined."""
        combined = Directives.OVERRIDED | Directives.EXTENDED
        assert Directives.OVERRIDED in combined
        assert Directives.EXTENDED in combined
        assert Directives.IGNORED not in combined

    def test_directives_flag_operations(self):
        """Test various flag operations."""
        # Test OR operation
        combined = Directives.DECLARED | Directives.IMPORTED
        assert combined.value == 24  # 8 + 16

        # Test AND operation
        result = combined & Directives.DECLARED
        assert result == Directives.DECLARED

        # Test XOR operation
        xor_result = Directives.OVERRIDED ^ Directives.EXTENDED
        assert Directives.OVERRIDED in xor_result
        assert Directives.EXTENDED in xor_result

    def test_directives_membership(self):
        """Test membership operations with Directives."""
        flags = Directives.OVERRIDED | Directives.IGNORED
        assert Directives.OVERRIDED in flags
        assert Directives.IGNORED in flags
        assert Directives.EXTENDED not in flags

    def test_directives_repr(self):
        """Test string representation of Directives."""
        assert "OVERRIDED" in repr(Directives.OVERRIDED)
        assert "EXTENDED" in repr(Directives.EXTENDED)

    def test_directives_all_flags_unique(self):
        """Test that all directive flags have unique values."""
        values = {
            Directives.OVERRIDED.value,
            Directives.EXTENDED.value,
            Directives.IGNORED.value,
            Directives.DECLARED.value,
            Directives.IMPORTED.value,
        }
        assert len(values) == 5  # All values should be unique


class TestKind:
    """Test cases for Kind string enum."""

    def test_kind_enum_values(self):
        """Test that Kind enum has correct string values."""
        assert Kind.RULE == "rule"
        assert Kind.TERMINAL == "terminal"

    def test_kind_str_enum_inheritance(self):
        """Test that Kind inherits from StrEnum."""
        assert issubclass(Kind, StrEnum)

    def test_kind_string_behavior(self):
        """Test that Kind behaves like strings."""
        assert str(Kind.RULE) == "rule"
        assert str(Kind.TERMINAL) == "terminal"

    def test_kind_equality_with_string(self):
        """Test that Kind values are equal to their string equivalents."""
        assert Kind.RULE == "rule"
        assert Kind.TERMINAL == "terminal"
        assert Kind.RULE != "terminal"
        assert Kind.TERMINAL != "rule"

    def test_kind_repr_method(self):
        """Test the custom __repr__ method."""
        assert repr(Kind.RULE) == "Kind.RULE"
        assert repr(Kind.TERMINAL) == "Kind.TERMINAL"

    def test_kind_repr_format(self):
        """Test that repr follows expected format."""
        rule_repr = repr(Kind.RULE)
        terminal_repr = repr(Kind.TERMINAL)

        assert rule_repr.startswith("Kind.")
        assert terminal_repr.startswith("Kind.")
        assert "RULE" in rule_repr
        assert "TERMINAL" in terminal_repr

    def test_kind_iteration(self):
        """Test iterating over Kind enum."""
        kinds = list(Kind)
        assert len(kinds) == 2
        assert Kind.RULE in kinds
        assert Kind.TERMINAL in kinds

    def test_kind_membership(self):
        """Test membership testing with Kind."""
        assert "rule" in [kind.value for kind in Kind]
        assert "terminal" in [kind.value for kind in Kind]
        assert "unknown" not in [kind.value for kind in Kind]

    def test_kind_comparison(self):
        """Test comparison operations with Kind."""
        assert Kind.RULE != Kind.TERMINAL
        assert Kind.RULE == Kind.RULE
        assert Kind.TERMINAL == Kind.TERMINAL


class TestModifiers:
    """Test cases for Modifiers flag enum."""

    def test_modifiers_enum_values(self):
        """Test that Modifiers enum has correct values."""
        assert hasattr(Modifiers, "INLINED")
        assert hasattr(Modifiers, "CONDITIONALLY_INLINED")
        assert hasattr(Modifiers, "PINNED")

    def test_modifiers_flag_inheritance(self):
        """Test that Modifiers inherits from Flag."""
        assert issubclass(Modifiers, Flag)

    def test_modifiers_auto_values(self):
        """Test that Modifiers uses auto() for values."""
        # Flag enums using auto() should have power-of-2 values
        assert Modifiers.INLINED.value == 1
        assert Modifiers.CONDITIONALLY_INLINED.value == 2
        assert Modifiers.PINNED.value == 4

    def test_modifiers_flag_combinations(self):
        """Test that Modifiers flags can be combined."""
        combined = Modifiers.INLINED | Modifiers.PINNED
        assert Modifiers.INLINED in combined
        assert Modifiers.PINNED in combined
        assert Modifiers.CONDITIONALLY_INLINED not in combined

    def test_modifiers_from_char_valid_chars(self):
        """Test from_char method with valid characters."""
        assert Modifiers.from_char("_") == Modifiers.INLINED
        assert Modifiers.from_char("?") == Modifiers.CONDITIONALLY_INLINED
        assert Modifiers.from_char("!") == Modifiers.PINNED

    def test_modifiers_from_char_invalid_char(self):
        """Test from_char method with invalid character."""
        result = Modifiers.from_char("x")
        assert result == Modifiers(0)  # Should return empty flag

    def test_modifiers_from_char_empty_string(self):
        """Test from_char method with empty string."""
        result = Modifiers.from_char("")
        assert result == Modifiers(0)

    def test_modifiers_from_char_none(self):
        """Test from_char method with None."""
        result = Modifiers.from_char(None)  # type: ignore
        assert result == Modifiers(0)  # Should return empty flag

    def test_modifiers_to_char_valid_modifiers(self):
        """Test to_char method with valid modifiers."""
        assert Modifiers.to_char(Modifiers.INLINED) == "_"
        assert Modifiers.to_char(Modifiers.CONDITIONALLY_INLINED) == "?"
        assert Modifiers.to_char(Modifiers.PINNED) == "!"

    def test_modifiers_to_char_invalid_modifier(self):
        """Test to_char method with invalid modifier."""
        # Create a combined modifier not in the mapping
        combined = Modifiers.INLINED | Modifiers.PINNED
        result = Modifiers.to_char(combined)
        assert result == ""

    def test_modifiers_to_char_empty_modifier(self):
        """Test to_char method with empty modifier."""
        result = Modifiers.to_char(Modifiers(0))
        assert result == ""

    def test_modifiers_roundtrip_conversion(self):
        """Test roundtrip conversion from char to modifier and back."""
        chars = ["_", "?", "!"]
        for char in chars:
            modifier = Modifiers.from_char(char)
            converted_char = Modifiers.to_char(modifier)
            assert converted_char == char

    def test_modifiers_char_mapping_completeness(self):
        """Test that all single modifiers have character mappings."""
        single_modifiers = [
            Modifiers.INLINED,
            Modifiers.CONDITIONALLY_INLINED,
            Modifiers.PINNED,
        ]

        for modifier in single_modifiers:
            char = Modifiers.to_char(modifier)
            assert char != ""  # Should have a character mapping

            # Verify reverse mapping works
            reverse_modifier = Modifiers.from_char(char)
            assert reverse_modifier == modifier

    def test_modifiers_classmethod_annotations(self):
        """Test that from_char and to_char are classmethods."""
        assert hasattr(Modifiers.from_char, "__self__")
        assert hasattr(Modifiers.to_char, "__self__")
        assert Modifiers.from_char.__self__ is Modifiers
        assert Modifiers.to_char.__self__ is Modifiers

    def test_modifiers_type_hints(self):
        """Test that methods have proper type annotations."""
        # Test from_char return type annotation
        from_char_annotations = getattr(Modifiers.from_char, "__annotations__", {})
        assert "return" in from_char_annotations

        # Test to_char return type annotation
        to_char_annotations = getattr(Modifiers.to_char, "__annotations__", {})
        assert "return" in to_char_annotations


class TestFlagsModuleIntegration:
    """Test cases for flags module integration and edge cases."""

    def test_all_enums_are_importable(self):
        """Test that all enums can be imported from the module."""
        from lark_parser_language_server.symbol_table.flags import (
            Directives,
            Kind,
            Modifiers,
        )

        assert Directives is not None
        assert Kind is not None
        assert Modifiers is not None

    def test_enum_types_distinct(self):
        """Test that different enum types are distinct."""
        assert Directives != Kind
        assert Directives != Modifiers
        assert Kind != Modifiers

    def test_flag_enums_vs_string_enum(self):
        """Test distinction between Flag and StrEnum."""
        assert issubclass(Directives, Flag)
        assert issubclass(Modifiers, Flag)
        assert issubclass(Kind, StrEnum)
        assert not issubclass(Kind, Flag)

    def test_modifiers_edge_cases(self):
        """Test edge cases for Modifiers methods."""
        # Test with numeric input (returns empty flag, doesn't raise)
        result = Modifiers.from_char(1)  # type: ignore
        assert result == Modifiers(0)

        # Test with multi-character string
        result = Modifiers.from_char("??")
        assert result == Modifiers(0)

    def test_module_constants_immutable(self):
        """Test that enum values are immutable."""
        original_rule = Kind.RULE
        original_inlined = Modifiers.INLINED

        # These should be the same objects
        assert Kind.RULE is original_rule
        assert Modifiers.INLINED is original_inlined

    def test_directives_comprehensive_combinations(self):
        """Test comprehensive combinations of Directives."""
        all_directives = (
            Directives.OVERRIDED
            | Directives.EXTENDED
            | Directives.IGNORED
            | Directives.DECLARED
            | Directives.IMPORTED
        )

        # All should be present in the combination
        for directive in [
            Directives.OVERRIDED,
            Directives.EXTENDED,
            Directives.IGNORED,
            Directives.DECLARED,
            Directives.IMPORTED,
        ]:
            assert directive in all_directives

    def test_modifiers_comprehensive_combinations(self):
        """Test comprehensive combinations of Modifiers."""
        all_modifiers = (
            Modifiers.INLINED | Modifiers.CONDITIONALLY_INLINED | Modifiers.PINNED
        )

        # All should be present in the combination
        for modifier in [
            Modifiers.INLINED,
            Modifiers.CONDITIONALLY_INLINED,
            Modifiers.PINNED,
        ]:
            assert modifier in all_modifiers
