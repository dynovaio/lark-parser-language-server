"""Tests for lark_parser_language_server.symbol_table.symbol module."""

from unittest.mock import Mock

import pytest
from lark import Token, Tree
from lark.tree import Meta
from lsprotocol.types import CompletionItemKind, DocumentSymbol, Location
from lsprotocol.types import Position as LspPosition
from lsprotocol.types import Range as LspRange
from lsprotocol.types import SymbolKind

from lark_parser_language_server.formatter import FORMATTER
from lark_parser_language_server.symbol_table.flags import Directives, Kind, Modifiers
from lark_parser_language_server.symbol_table.symbol import (
    KEYWORDS,
    Definition,
    Keyword,
    Position,
    Range,
    Reference,
)
from lark_parser_language_server.syntax_tree.nodes import AstNode


class TestPosition:
    """Test cases for Position dataclass."""

    def test_position_creation(self):
        """Test Position creation with basic values."""
        pos = Position(line=5, column=10)
        assert pos.line == 5
        assert pos.column == 10

    def test_position_from_token_basic(self):
        """Test Position.from_token with basic token."""
        token = Mock(spec=Token)
        token.value = "test_rule"
        token.line = 3
        token.column = 7

        pos = Position.from_token(token)
        assert pos.line == 2  # 0-based
        assert pos.column == 6  # 0-based

    def test_position_from_token_with_modifiers(self):
        """Test Position.from_token with modifier prefixes."""
        token = Mock(spec=Token)
        token.value = "?test_rule"
        token.line = 3
        token.column = 7

        pos = Position.from_token(token, use_clean_name=True)
        assert pos.line == 2  # 0-based
        assert pos.column == 7  # 0-based + 1 offset for '?'

    def test_position_from_token_multiple_modifiers(self):
        """Test Position.from_token with multiple modifier prefixes."""
        token = Mock(spec=Token)
        token.value = "!?test_rule"
        token.line = 3
        token.column = 7

        pos = Position.from_token(token, use_clean_name=True)
        assert pos.line == 2  # 0-based
        assert pos.column == 8  # 0-based + 2 offset for '!?'

    def test_position_from_token_no_clean_name(self):
        """Test Position.from_token without cleaning name."""
        token = Mock(spec=Token)
        token.value = "?test_rule"
        token.line = 3
        token.column = 7

        pos = Position.from_token(token, use_clean_name=False)
        assert pos.line == 2  # 0-based
        assert pos.column == 6  # 0-based, no offset

    def test_position_from_token_none_values(self):
        """Test Position.from_token with None line/column."""
        token = Mock(spec=Token)
        token.value = "test_rule"
        token.line = None
        token.column = None

        pos = Position.from_token(token)
        assert pos.line == 0
        assert pos.column == 0

    def test_position_to_lsp_position(self):
        """Test Position.to_lsp_position conversion."""
        pos = Position(line=5, column=10)
        lsp_pos = pos.to_lsp_position()

        assert isinstance(lsp_pos, LspPosition)
        assert lsp_pos.line == 5
        assert lsp_pos.character == 10

    def test_position_equality(self):
        """Test Position equality comparison."""
        pos1 = Position(line=5, column=10)
        pos2 = Position(line=5, column=10)
        pos3 = Position(line=5, column=11)

        assert pos1 == pos2
        assert pos1 != pos3


class TestRange:
    """Test cases for Range dataclass."""

    def test_range_creation(self):
        """Test Range creation with Position objects."""
        start = Position(line=1, column=2)
        end = Position(line=1, column=8)

        range_obj = Range(start=start, end=end)
        assert range_obj.start == start
        assert range_obj.end == end

    def test_range_from_token_basic(self):
        """Test Range.from_token with basic token."""
        token = Mock(spec=Token)
        token.value = "test_rule"
        token.line = 3
        token.column = 7

        range_obj = Range.from_token(token)
        assert range_obj.start.line == 2  # 0-based
        assert range_obj.start.column == 6  # 0-based
        assert range_obj.end.line == 2
        assert range_obj.end.column == 15  # start + len("test_rule")

    def test_range_from_token_with_modifiers(self):
        """Test Range.from_token with modifier prefixes."""
        token = Mock(spec=Token)
        token.value = "?test_rule"
        token.line = 3
        token.column = 7

        range_obj = Range.from_token(token, use_clean_name=True)
        assert range_obj.start.line == 2  # 0-based
        assert range_obj.start.column == 7  # 0-based + 1 offset
        assert range_obj.end.line == 2
        assert range_obj.end.column == 16  # start + len("test_rule")

    def test_range_from_token_no_clean_name(self):
        """Test Range.from_token without cleaning name."""
        token = Mock(spec=Token)
        token.value = "?test_rule"
        token.line = 3
        token.column = 7

        range_obj = Range.from_token(token, use_clean_name=False)
        assert range_obj.start.line == 2  # 0-based
        assert range_obj.start.column == 6  # 0-based, no offset
        assert range_obj.end.line == 2
        assert range_obj.end.column == 16  # start + len("?test_rule")

    def test_range_from_tree_basic(self):
        """Test Range.from_tree with tree containing tokens."""
        token1 = Mock(spec=Token)
        token1.line = 1
        token1.column = 1
        token1.value = "start"

        token2 = Mock(spec=Token)
        token2.line = 1
        token2.column = 10
        token2.value = "end"

        tree = Mock(spec=Tree)
        tree.scan_values.return_value = [token1, token2]

        range_obj = Range.from_tree(tree)
        assert range_obj.start.line == 0  # 0-based
        assert range_obj.start.column == 0  # 0-based
        assert range_obj.end.line == 0
        assert range_obj.end.column == 12  # token2.column - 1 + len("end")

    def test_range_from_tree_no_tokens(self):
        """Test Range.from_tree with tree containing no tokens."""
        tree = Mock(spec=Tree)
        tree.scan_values.return_value = []

        with pytest.raises(ValueError, match="Tree does not contain any tokens"):
            Range.from_tree(tree)

    def test_range_from_meta_basic(self):
        """Test Range.from_meta with Meta object."""
        meta = Mock(spec=Meta)
        meta.line = 5
        meta.column = 10
        meta.end_line = 5
        meta.end_column = 20

        range_obj = Range.from_meta(meta)
        assert range_obj.start.line == 4  # 0-based
        assert range_obj.start.column == 9  # 0-based
        assert range_obj.end.line == 4
        assert range_obj.end.column == 19

    def test_range_from_meta_missing_attributes(self):
        """Test Range.from_meta with missing attributes (uses defaults)."""
        meta = Mock(spec=Meta)
        # Remove attributes to test getattr defaults
        if hasattr(meta, "line"):
            delattr(meta, "line")
        if hasattr(meta, "column"):
            delattr(meta, "column")
        if hasattr(meta, "end_line"):
            delattr(meta, "end_line")
        if hasattr(meta, "end_column"):
            delattr(meta, "end_column")

        range_obj = Range.from_meta(meta)
        assert range_obj.start.line == 0  # getattr default 1 - 1
        assert range_obj.start.column == 0
        assert range_obj.end.line == 0
        assert range_obj.end.column == 0

    def test_range_contains_position_inside(self):
        """Test Range.__contains__ with position inside range."""
        start = Position(line=1, column=5)
        end = Position(line=3, column=10)
        range_obj = Range(start=start, end=end)

        pos_inside = Position(line=2, column=7)
        assert pos_inside in range_obj

    def test_range_contains_position_outside(self):
        """Test Range.__contains__ with position outside range."""
        start = Position(line=1, column=5)
        end = Position(line=3, column=10)
        range_obj = Range(start=start, end=end)

        pos_outside = Position(line=0, column=7)
        assert pos_outside not in range_obj

    def test_range_contains_position_edge_cases(self):
        """Test Range.__contains__ with edge case positions."""
        start = Position(line=1, column=5)
        end = Position(line=3, column=10)
        range_obj = Range(start=start, end=end)

        # Start position - should be included
        assert start in range_obj

        # End position - should be included
        assert end in range_obj

        # Just before start column on same line
        pos_before = Position(line=1, column=4)
        assert pos_before not in range_obj

        # Just after end column on same line
        pos_after = Position(line=3, column=11)
        assert pos_after not in range_obj

    def test_range_contains_range_inside(self):
        """Test Range.__contains__ with range inside."""
        outer_start = Position(line=1, column=5)
        outer_end = Position(line=5, column=15)
        outer_range = Range(start=outer_start, end=outer_end)

        inner_start = Position(line=2, column=8)
        inner_end = Position(line=3, column=12)
        inner_range = Range(start=inner_start, end=inner_end)

        assert inner_range in outer_range

    def test_range_contains_range_outside(self):
        """Test Range.__contains__ with range partially outside."""
        start = Position(line=1, column=5)
        end = Position(line=3, column=10)
        range_obj = Range(start=start, end=end)

        outside_start = Position(line=0, column=5)
        outside_end = Position(line=2, column=8)
        outside_range = Range(start=outside_start, end=outside_end)

        assert outside_range not in range_obj

    def test_range_contains_invalid_type(self):
        """Test Range.__contains__ with invalid type."""
        start = Position(line=1, column=5)
        end = Position(line=3, column=10)
        range_obj = Range(start=start, end=end)

        with pytest.raises(TypeError, match="Unsupported type for containment check"):
            _ = "invalid" in range_obj

    def test_range_to_lsp_range(self):
        """Test Range.to_lsp_range conversion."""
        start = Position(line=1, column=5)
        end = Position(line=3, column=10)
        range_obj = Range(start=start, end=end)

        lsp_range = range_obj.to_lsp_range()
        assert isinstance(lsp_range, LspRange)
        assert lsp_range.start.line == 1
        assert lsp_range.start.character == 5
        assert lsp_range.end.line == 3
        assert lsp_range.end.character == 10


class TestDefinition:
    """Test cases for Definition dataclass."""

    def test_definition_creation_basic(self):
        """Test Definition creation with basic parameters."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        assert definition.name == "test_rule"
        assert definition.kind == Kind.RULE
        assert definition.range == range_obj
        assert definition.selection_range == range_obj
        assert definition.parent is None
        assert definition.children == {}

    def test_definition_post_init_children_none(self):
        """Test Definition.__post_init__ initializes children if None."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
            children=None,
        )

        assert definition.children == {}

    def test_definition_post_init_children_provided(self):
        """Test Definition.__post_init__ preserves provided children."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        children = {"existing": []}
        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
            children=children,
        )

        assert definition.children is children

    def test_definition_lsp_kind_rule_no_parent(self):
        """Test Definition._lsp_kind for rule without parent."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        assert definition._lsp_kind() == SymbolKind.Method

    def test_definition_lsp_kind_terminal_no_parent(self):
        """Test Definition._lsp_kind for terminal without parent."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="TEST_TERMINAL",
            kind=Kind.TERMINAL,
            range=range_obj,
            selection_range=range_obj,
        )

        assert definition._lsp_kind() == SymbolKind.Constant

    def test_definition_lsp_kind_unknown_kind(self):
        """Test Definition._lsp_kind for unknown kind."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        # Create a definition with invalid kind by monkey-patching
        definition = Definition(
            name="test_unknown",
            kind=Kind.RULE,  # Start with valid kind
            range=range_obj,
            selection_range=range_obj,
        )

        # Replace the kind with an invalid value
        definition.kind = "invalid_kind"  # type: ignore

        assert definition._lsp_kind() == SymbolKind.Null

    def test_definition_lsp_completion_item_kind_unknown_kind(self):
        """Test Definition._lsp_completion_item_kind for unknown kind."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        # Create a definition with invalid kind
        definition = Definition(
            name="test_unknown",
            kind=Kind.RULE,  # Start with valid kind
            range=range_obj,
            selection_range=range_obj,
        )

        # Replace the kind with an invalid value
        definition.kind = "invalid_kind"  # type: ignore

        assert definition._lsp_completion_item_kind() == CompletionItemKind.Text

    def test_definition_lsp_kind_with_parent(self):
        """Test Definition._lsp_kind with parent (always Variable)."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        parent = Definition(
            name="parent_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        definition = Definition(
            name="child_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
            parent=parent,
        )

        assert definition._lsp_kind() == SymbolKind.Variable

    def test_definition_lsp_completion_item_kind_rule(self):
        """Test Definition._lsp_completion_item_kind for rule."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        assert definition._lsp_completion_item_kind() == CompletionItemKind.Function

    def test_definition_lsp_completion_item_kind_terminal(self):
        """Test Definition._lsp_completion_item_kind for terminal."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="TEST_TERMINAL",
            kind=Kind.TERMINAL,
            range=range_obj,
            selection_range=range_obj,
        )

        assert definition._lsp_completion_item_kind() == CompletionItemKind.Variable

    def test_definition_documentation_rule(self):
        """Test Definition.documentation property for rule."""
        FORMATTER.format_ast_node = Mock(return_value="test_rule")

        mock_range = Mock(spec=Range)
        mock_range.to_lsp_range.return_value = LspRange(
            start=LspPosition(line=1, character=2),
            end=LspPosition(line=3, character=4),
        )

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=mock_range,
            selection_range=Mock(),
            ast_node=Mock(),
        )

        hover = definition.to_lsp_hover_info()

        expected_documentation = """```lark
test_rule
```

---

Grammar rule: test_rule

---

"""
        assert hover.contents.value == expected_documentation
        assert hover.range.start.line == 1
        assert hover.range.start.character == 2
        assert hover.range.end.line == 3
        assert hover.range.end.character == 4

    def test_definition_documentation_terminal(self):
        """Test Definition.documentation property for terminal."""
        FORMATTER.format_ast_node = Mock(return_value="TEST_TERMINAL")
        definition = Definition(
            name="TEST_TERMINAL",
            kind=Kind.TERMINAL,
            range=Mock(),
            selection_range=Mock(),
            ast_node=Mock(),
        )

        expected_documentation = """```lark
TEST_TERMINAL
```

---

Grammar terminal: TEST_TERMINAL

---

"""
        assert definition.documentation == expected_documentation

    def test_definition_append_child_new_name(self):
        """Test Definition.append_child with new child name."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        parent = Definition(
            name="parent_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        child = Definition(
            name="child_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        parent.append_child(child)

        assert child.parent is parent
        assert "child_rule" in parent.children
        assert child in parent.children["child_rule"]

    def test_definition_append_child_existing_name(self):
        """Test Definition.append_child with existing child name."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        parent = Definition(
            name="parent_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        child1 = Definition(
            name="child_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        child2 = Definition(
            name="child_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        parent.append_child(child1)
        parent.append_child(child2)

        assert len(parent.children["child_rule"]) == 2
        assert child1 in parent.children["child_rule"]
        assert child2 in parent.children["child_rule"]

    def test_definition_append_child_none_children(self):
        """Test Definition.append_child when children is None."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        parent = Definition(
            name="parent_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
            children=None,
        )

        child = Definition(
            name="child_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        parent.append_child(child)

        assert parent.children is not None
        assert "child_rule" in parent.children

    def test_definition_append_child_parent_assignment(self):
        """Test that append_child properly assigns parent reference."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        parent = Definition(
            name="parent_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        child = Definition(
            name="child_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        # Explicitly verify parent is None before
        assert child.parent is None

        parent.append_child(child)

        # Verify parent assignment (this should cover line 181)
        assert child.parent is parent
        assert child.parent == parent

    def test_definition_to_lsp_document_symbol_no_children(self):
        """Test Definition.to_lsp_document_symbol without children."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        symbol = definition.to_lsp_document_symbol()

        assert isinstance(symbol, DocumentSymbol)
        assert symbol.name == "test_rule"
        assert symbol.kind == SymbolKind.Method
        assert symbol.children is None

    def test_definition_to_lsp_document_symbol_with_children(self):
        """Test Definition.to_lsp_document_symbol with children."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        parent = Definition(
            name="parent_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        child = Definition(
            name="child_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        parent.append_child(child)
        symbol = parent.to_lsp_document_symbol()

        assert symbol.children is not None
        assert len(symbol.children) == 1
        assert symbol.children[0].name == "child_rule"

    def test_definition_to_lsp_completion_item(self):
        """Test Definition.to_lsp_completion_item."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        item = definition.to_lsp_completion_item()

        assert item.label == "test_rule"
        assert item.kind == CompletionItemKind.Function
        assert item.detail == "Rule"
        assert item.documentation == "Grammar rule: test_rule"

    def test_definition_to_lsp_hover_info_default_range(self):
        """Test Definition.to_lsp_hover_info with default range."""
        FORMATTER.format_ast_node = Mock(return_value="test_rule")

        mock_range = Mock(spec=Range)
        mock_range.to_lsp_range.return_value = LspRange(
            start=LspPosition(line=1, character=2),
            end=LspPosition(line=3, character=4),
        )

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=mock_range,
            selection_range=Mock(),
            ast_node=Mock(),
        )

        hover = definition.to_lsp_hover_info()

        expected_documentation = """```lark
test_rule
```

---

Grammar rule: test_rule

---

"""

        assert hover.contents.value == expected_documentation
        assert hover.range.start.line == 1
        assert hover.range.start.character == 2

    def test_definition_to_lsp_hover_info_custom_range(self):
        """Test Definition.to_lsp_hover_info with custom Range."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        custom_start = Position(line=2, column=10)
        custom_end = Position(line=2, column=20)
        custom_range = Range(start=custom_start, end=custom_end)

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        hover = definition.to_lsp_hover_info(custom_range)

        assert hover.range.start.line == 2
        assert hover.range.start.character == 10

    def test_definition_to_lsp_hover_info_lsp_range(self):
        """Test Definition.to_lsp_hover_info with LspRange."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        lsp_range = LspRange(
            start=LspPosition(line=3, character=15),
            end=LspPosition(line=3, character=25),
        )

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        hover = definition.to_lsp_hover_info(lsp_range)

        assert hover.range.start.line == 3
        assert hover.range.start.character == 15

    def test_definition_to_lsp_location(self):
        """Test Definition.to_lsp_location."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        uri = "file:///test.lark"
        location = definition.to_lsp_location(uri)

        assert isinstance(location, Location)
        assert location.uri == uri
        assert location.range.start.line == 1
        assert location.range.start.character == 5


class TestReference:
    """Test cases for Reference dataclass."""

    def test_reference_creation_basic(self):
        """Test Reference creation with basic parameters."""
        pos = Position(line=1, column=5)
        range_obj = Range(start=pos, end=Position(line=1, column=15))

        reference = Reference(
            name="test_rule",
            position=pos,
            range=range_obj,
        )

        assert reference.name == "test_rule"
        assert reference.position == pos
        assert reference.range == range_obj
        assert reference.kind is None
        assert reference.ast_node is None

    def test_reference_from_token_rule(self):
        """Test Reference.from_token with RULE token."""
        token = Mock(spec=Token)
        token.value = "test_rule"
        token.type = "RULE"
        token.line = 3
        token.column = 7
        # Configure str() to return the value
        token.__str__ = Mock(return_value="test_rule")

        reference = Reference.from_token(token)

        assert reference.name == "test_rule"
        assert reference.kind == Kind.RULE
        assert reference.position.line == 2  # 0-based
        assert reference.position.column == 6  # 0-based

    def test_reference_from_token_terminal(self):
        """Test Reference.from_token with terminal token."""
        token = Mock(spec=Token)
        token.value = "TEST_TERMINAL"
        token.type = "TERMINAL"
        token.line = 3
        token.column = 7
        # Configure str() to return the value
        token.__str__ = Mock(return_value="TEST_TERMINAL")

        reference = Reference.from_token(token)

        assert reference.name == "TEST_TERMINAL"
        assert reference.kind == Kind.TERMINAL
        assert reference.position.line == 2  # 0-based
        assert reference.position.column == 6  # 0-based

    def test_reference_from_token_with_ast_node(self):
        """Test Reference.from_token with AST node."""
        token = Mock(spec=Token)
        token.value = "test_rule"
        token.type = "RULE"
        token.line = 3
        token.column = 7
        token.__str__ = Mock(return_value="test_rule")

        ast_node = Mock(spec=AstNode)
        reference = Reference.from_token(token, ast_node=ast_node)

        assert reference.ast_node is ast_node

    def test_reference_to_lsp_location(self):
        """Test Reference.to_lsp_location."""
        pos = Position(line=1, column=5)
        range_obj = Range(start=pos, end=Position(line=1, column=15))

        reference = Reference(
            name="test_rule",
            position=pos,
            range=range_obj,
        )

        uri = "file:///test.lark"
        location = reference.to_lsp_location(uri)

        assert isinstance(location, Location)
        assert location.uri == uri
        assert location.range.start.line == 1
        assert location.range.start.character == 5


class TestKeyword:
    """Test cases for Keyword dataclass."""

    def test_keyword_creation(self):
        """Test Keyword creation."""
        keyword = Keyword(name="import")
        assert keyword.name == "import"

    def test_keyword_to_lsp_completion_item(self):
        """Test Keyword.to_lsp_completion_item."""
        keyword = Keyword(name="import")
        item = keyword.to_lsp_completion_item()

        assert item.label == "import"
        assert item.kind == CompletionItemKind.Keyword
        assert item.detail == "Keyword"
        assert item.documentation == "Lark keyword: import"


class TestModuleConstants:
    """Test cases for module-level constants."""

    def test_keywords_constant_exists(self):
        """Test that KEYWORDS constant exists and is a list."""
        assert isinstance(KEYWORDS, list)
        assert len(KEYWORDS) > 0

    def test_keywords_constant_content(self):
        """Test that KEYWORDS contains expected keywords."""
        keyword_names = [kw.name for kw in KEYWORDS]

        expected_keywords = ["import", "ignore", "override", "extend", "declare"]
        for expected in expected_keywords:
            assert expected in keyword_names

    def test_keywords_are_keyword_objects(self):
        """Test that all KEYWORDS items are Keyword objects."""
        for keyword in KEYWORDS:
            assert isinstance(keyword, Keyword)

    def test_keywords_unique_names(self):
        """Test that all keywords have unique names."""
        names = [kw.name for kw in KEYWORDS]
        assert len(names) == len(set(names))

    def test_keywords_completion_items(self):
        """Test that all keywords can generate completion items."""
        for keyword in KEYWORDS:
            item = keyword.to_lsp_completion_item()
            assert item.label == keyword.name
            assert item.kind == CompletionItemKind.Keyword


class TestModuleIntegration:
    """Test cases for module integration and complex scenarios."""

    def test_definition_with_all_flags(self):
        """Test Definition with directives and modifiers."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
            directives=Directives.OVERRIDED | Directives.EXTENDED,
            modifiers=Modifiers.INLINED | Modifiers.PINNED,
        )

        assert Directives.OVERRIDED in definition.directives
        assert Directives.EXTENDED in definition.directives
        assert Modifiers.INLINED in definition.modifiers
        assert Modifiers.PINNED in definition.modifiers

    def test_nested_definitions(self):
        """Test nested definition structure."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        root = Definition(
            name="root",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        child1 = Definition(
            name="child1",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        child2 = Definition(
            name="child2",
            kind=Kind.TERMINAL,
            range=range_obj,
            selection_range=range_obj,
        )

        grandchild = Definition(
            name="grandchild",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        root.append_child(child1)
        root.append_child(child2)
        child1.append_child(grandchild)

        # Test structure
        assert len(root.children) == 2
        assert child1.parent is root
        assert child2.parent is root
        assert grandchild.parent is child1
        assert len(child1.children["grandchild"]) == 1

    def test_position_range_integration(self):
        """Test Position and Range working together."""
        # Test overlapping ranges
        pos1 = Position(line=1, column=5)
        pos2 = Position(line=1, column=10)
        pos3 = Position(line=1, column=15)

        range1 = Range(start=pos1, end=pos2)
        range2 = Range(start=pos2, end=pos3)

        # pos2 should be in both ranges (inclusive)
        assert pos2 in range1
        assert pos2 in range2

        # range1 should not contain range2
        assert range2 not in range1

    def test_lsp_conversion_consistency(self):
        """Test that LSP conversions are consistent."""
        start = Position(line=1, column=5)
        end = Position(line=1, column=15)
        range_obj = Range(start=start, end=end)

        definition = Definition(
            name="test_rule",
            kind=Kind.RULE,
            range=range_obj,
            selection_range=range_obj,
        )

        reference = Reference(
            name="test_rule",
            position=start,
            range=range_obj,
        )

        uri = "file:///test.lark"

        def_location = definition.to_lsp_location(uri)
        ref_location = reference.to_lsp_location(uri)

        # Both should have same URI and range
        assert def_location.uri == ref_location.uri
        assert def_location.range.start.line == ref_location.range.start.line
        assert def_location.range.start.character == ref_location.range.start.character
