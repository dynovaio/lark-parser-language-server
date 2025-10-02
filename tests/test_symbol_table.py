"""Tests for symbol table functionality."""

from lark import Token, Tree
from lsprotocol.types import SymbolKind

from lark_parser_language_server.symbol_table import (
    Symbol,
    SymbolModifier,
    SymbolPosition,
    SymbolRange,
    SymbolTable,
)


class TestSymbolModifier:
    """Test SymbolModifier functionality."""

    def test_symbol_modifier_mapping(self):
        """Test symbol modifier character mapping."""
        assert SymbolModifier.map("_") == SymbolModifier.INLINED
        assert SymbolModifier.map("?") == SymbolModifier.CONDITIONALLY_INLINED
        assert SymbolModifier.map("!") == SymbolModifier.PINNED
        assert SymbolModifier.map("x") == SymbolModifier(0)  # Unknown character


class TestSymbolPosition:
    """Test SymbolPosition functionality."""

    def test_symbol_position_from_token(self):
        """Test creating SymbolPosition from token."""
        token = Token("RULE", "test_rule")
        token.line = 5
        token.column = 10

        pos = SymbolPosition.from_token(token)
        assert pos.line == 4  # 0-based
        assert pos.column == 9  # 0-based

    def test_symbol_position_from_token_with_modifiers(self):
        """Test creating SymbolPosition from token with modifiers."""
        token = Token("RULE", "?!test_rule")
        token.line = 5
        token.column = 10

        pos = SymbolPosition.from_token(token, use_clean_name=True)
        assert pos.line == 4  # 0-based
        assert pos.column == 11  # 0-based + offset for modifiers

    def test_symbol_position_no_line_column(self):
        """Test creating SymbolPosition when token has no line/column."""
        token = Token("RULE", "test_rule")
        # Don't set line/column

        pos = SymbolPosition.from_token(token)
        assert pos.line == 0
        assert pos.column == 0

    def test_to_lsp_position(self):
        """Test converting to LSP Position."""
        pos = SymbolPosition(line=5, column=10)
        lsp_pos = pos.to_lsp_position()
        assert lsp_pos.line == 5
        assert lsp_pos.character == 10


class TestSymbolRange:
    """Test SymbolRange functionality."""

    def test_symbol_range_from_token(self):
        """Test creating SymbolRange from token."""
        token = Token("RULE", "test_rule")
        token.line = 5
        token.column = 10

        range_obj = SymbolRange.from_token(token)
        assert range_obj.start.line == 4
        assert range_obj.start.column == 9
        assert range_obj.end.line == 4
        assert range_obj.end.column == 18  # start + length

    def test_symbol_range_from_tree_no_tokens(self):
        """Test creating SymbolRange from tree with no tokens."""
        tree = Tree("start", [])

        try:
            SymbolRange.from_tree(tree)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "does not contain any tokens" in str(e)

    def test_symbol_range_from_tree_with_tokens(self):
        """Test creating SymbolRange from tree with tokens."""
        token1 = Token("RULE", "start")
        token1.line = 1
        token1.column = 1

        token2 = Token("TOKEN", "END")
        token2.line = 1
        token2.column = 10

        tree = Tree("start", [token1, token2])

        range_obj = SymbolRange.from_tree(tree)
        assert range_obj.start.line == 0  # 0-based
        assert range_obj.start.column == 0  # 0-based
        assert range_obj.end.line == 0
        assert range_obj.end.column == 12  # position + length of "END" minus 1


class TestSymbol:
    """Test Symbol functionality."""

    def test_symbol_creation(self):
        """Test creating a symbol."""
        token = Token("RULE", "test_rule")
        token.line = 1
        token.column = 1

        symbol = Symbol(token)
        assert symbol.name == "test_rule"
        assert symbol.kind == "rule"
        assert symbol.is_rule is True
        assert symbol.is_terminal is False

    def test_symbol_with_modifiers(self):
        """Test symbol with modifiers."""
        token = Token("RULE", "?!_test_rule")
        token.line = 1
        token.column = 1

        symbol = Symbol(token)
        assert symbol.name == "_test_rule"  # Only strips ? and ! not _
        assert symbol.is_conditionally_inlined is True
        assert symbol.is_pinned is True
        assert symbol.is_inlined is True

    def test_symbol_terminal(self):
        """Test terminal symbol."""
        token = Token("TOKEN", "TEST_TOKEN")
        token.line = 1
        token.column = 1

        symbol = Symbol(token)
        assert symbol.name == "TEST_TOKEN"
        assert symbol.kind == "terminal"
        assert symbol.is_rule is False
        assert symbol.is_terminal is True

    def test_symbol_invalid_name(self):
        """Test symbol with invalid name."""
        token = Token("TOKEN", "Mixed_Case_Invalid")
        token.line = 1
        token.column = 1

        symbol = Symbol(token)
        try:
            _ = symbol.kind
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "Invalid symbol name" in str(e)

    def test_symbol_alias(self):
        """Test symbol with alias flag."""
        token = Token("RULE", "test_rule")
        token.line = 1
        token.column = 1

        symbol = Symbol(token, alias=True)
        assert symbol.is_alias is True

    def test_symbol_directive(self):
        """Test symbol with directive."""
        token = Token("RULE", "test_rule")
        token.line = 1
        token.column = 1

        symbol = Symbol(token, directive="import")
        assert symbol._directive == "import"
        assert "Import" in symbol.description

    def test_symbol_equality(self):
        """Test symbol equality."""
        token1 = Token("RULE", "test_rule")
        token1.line = 1
        token1.column = 1

        token2 = Token("RULE", "test_rule")
        token2.line = 1
        token2.column = 1

        symbol1 = Symbol(token1)
        symbol2 = Symbol(token2)

        assert symbol1 == symbol2

    def test_symbol_inequality_with_non_symbol(self):
        """Test symbol inequality with non-symbol object."""
        token = Token("RULE", "test_rule")
        token.line = 1
        token.column = 1

        symbol = Symbol(token)

        assert symbol != "not_a_symbol"

    def test_symbol_repr(self):
        """Test symbol string representation."""
        token = Token("RULE", "test_rule")
        token.line = 1
        token.column = 1

        symbol = Symbol(token)
        repr_str = repr(symbol)
        assert "Symbol" in repr_str
        assert "test_rule" in repr_str

    def test_symbol_documentation(self):
        """Test symbol documentation."""
        token = Token("RULE", "test_rule")
        token.line = 1
        token.column = 1

        symbol = Symbol(token)
        doc = symbol.documentation
        assert "Grammar rule definition" in doc
        assert "test_rule" in doc

    def test_symbol_get_lsp_kind(self):
        """Test getting LSP symbol kind."""
        # Rule symbol
        token = Token("RULE", "test_rule")
        token.line = 1
        token.column = 1
        symbol = Symbol(token)
        assert symbol.get_lsp_kind() == SymbolKind.Function

        # Terminal symbol
        token = Token("TOKEN", "TEST_TOKEN")
        token.line = 1
        token.column = 1
        symbol = Symbol(token)
        assert symbol.get_lsp_kind() == SymbolKind.Constant

    def test_symbol_to_lsp_symbol(self):
        """Test converting to LSP DocumentSymbol."""
        token = Token("RULE", "test_rule")
        token.line = 1
        token.column = 1

        symbol = Symbol(token)
        lsp_symbol = symbol.to_lsp_symbol()

        assert lsp_symbol.name == "test_rule"
        assert lsp_symbol.detail is not None


class TestSymbolTable:
    """Test SymbolTable functionality."""

    def test_symbol_table_rule(self):
        """Test symbol table with rule."""
        token = Token("RULE", "test_rule")
        token.line = 1
        token.column = 1

        tree = Tree("rule", [token])

        symbol_table = SymbolTable()
        symbol_table.rule(tree)

        assert "test_rule" in symbol_table.symbols

    def test_symbol_table_token(self):
        """Test symbol table with token."""
        token = Token("TOKEN", "TEST_TOKEN")
        token.line = 1
        token.column = 1

        tree = Tree("token", [token])

        symbol_table = SymbolTable()
        symbol_table.token(tree)

        assert "TEST_TOKEN" in symbol_table.symbols

    def test_symbol_table_alias(self):
        """Test symbol table with alias."""
        token = Token("RULE", "alias_name")
        token.line = 1
        token.column = 1

        tree = Tree("alias", [None, token])  # Alias tree has target first, then alias

        symbol_table = SymbolTable()
        symbol_table.alias(tree)

        assert "alias_name" in symbol_table.symbols

    def test_symbol_table_alias_no_alias(self):
        """Test symbol table with alias tree but no alias token."""
        tree = Tree("alias", [None])  # No alias token

        symbol_table = SymbolTable()
        symbol_table.alias(tree)

        # Should not crash, just do nothing
        assert len(symbol_table.symbols) == 0

    def test_symbol_table_getitem(self):
        """Test symbol table getitem."""
        token = Token("RULE", "test_rule")
        token.line = 1
        token.column = 1

        tree = Tree("rule", [token])

        symbol_table = SymbolTable()
        symbol_table.rule(tree)

        # Test successful lookup
        symbol = symbol_table["test_rule"]
        assert symbol.name == "test_rule"

        # Test with modifiers
        symbol = symbol_table["?!test_rule"]
        assert symbol.name == "test_rule"

        # Test missing symbol
        try:
            _ = symbol_table["missing_rule"]
            assert False, "Should raise KeyError"
        except KeyError:
            pass

    def test_symbol_table_import(self):
        """Test symbol table with import statement."""
        # Create import path tokens
        name_token1 = Token("RULE", "common")
        name_token1.line = 1
        name_token1.column = 1

        name_token2 = Token("TOKEN", "WORD")
        name_token2.line = 1
        name_token2.column = 8

        # Create import path tree
        name_tree1 = Tree("name", [name_token1])
        name_tree2 = Tree("name", [name_token2])
        import_path = Tree("import_path", [name_tree1, Token("DOT", "."), name_tree2])

        # Test import without alias
        import_tree = Tree("import", [import_path, None])

        symbol_table = SymbolTable()
        symbol_table._handle_import(import_tree)

        assert "WORD" in symbol_table.symbols

    def test_symbol_table_import_with_alias(self):
        """Test symbol table with import statement with alias."""
        # Create import path tokens
        name_token1 = Token("RULE", "common")
        name_token1.line = 1
        name_token1.column = 1

        name_token2 = Token("TOKEN", "WORD")
        name_token2.line = 1
        name_token2.column = 8

        alias_token = Token("TOKEN", "MY_WORD")
        alias_token.line = 1
        alias_token.column = 15

        # Create trees
        name_tree1 = Tree("name", [name_token1])
        name_tree2 = Tree("name", [name_token2])
        import_path = Tree("import_path", [name_tree1, Token("DOT", "."), name_tree2])
        alias_tree = Tree("alias", [alias_token])

        # Test import with alias
        import_tree = Tree("import", [import_path, alias_tree])

        symbol_table = SymbolTable()
        symbol_table._handle_import(import_tree)

        assert "MY_WORD" in symbol_table.symbols

    def test_symbol_table_multi_import(self):
        """Test symbol table with multi import statement."""
        # Create import path
        name_token1 = Token("RULE", "common")
        name_token1.line = 1
        name_token1.column = 1

        import_path = Tree("import_path", [Tree("name", [name_token1])])

        # Create name list
        name_token2 = Token("TOKEN", "WORD")
        name_token2.line = 1
        name_token2.column = 8

        name_token3 = Token("TOKEN", "NUMBER")
        name_token3.line = 1
        name_token3.column = 15

        name_list = Tree(
            "name_list", [Tree("name", [name_token2]), Tree("name", [name_token3])]
        )

        multi_import_tree = Tree("multi_import", [import_path, name_list])

        symbol_table = SymbolTable()
        symbol_table._handle_multi_import(multi_import_tree)

        assert "WORD" in symbol_table.symbols
        assert "NUMBER" in symbol_table.symbols

    def test_symbol_table_declare(self):
        """Test symbol table with declare statement."""
        name_token1 = Token("RULE", "declared_rule")
        name_token1.line = 1
        name_token1.column = 1

        name_token2 = Token("TOKEN", "DECLARED_TOKEN")
        name_token2.line = 1
        name_token2.column = 15

        declare_tree = Tree(
            "declare", [Tree("name", [name_token1]), Tree("name", [name_token2])]
        )

        symbol_table = SymbolTable()
        symbol_table._handle_declare(declare_tree)

        assert "declared_rule" in symbol_table.symbols
        assert "DECLARED_TOKEN" in symbol_table.symbols

    def test_symbol_table_consume_symbol_non_token(self):
        """Test _consume_symbol with non-token branch."""
        tree = Tree("test", [])
        branch = Tree("not_a_token", [])  # Tree instead of Token

        symbol_table = SymbolTable()
        symbol_table._consume_symbol(tree, branch)

        # Should not add anything since branch is not a Token
        assert len(symbol_table.symbols) == 0

    def test_symbol_no_modifiers_extraction(self):
        """Test symbol with no modifiers to cover _extract_modifiers branch."""
        token = Token("RULE", "simple_rule")
        token.line = 1
        token.column = 1

        symbol = Symbol(token)

        # Should have no modifiers (SymbolModifier with value 0)
        assert symbol.modifiers == SymbolModifier(0)

    def test_symbol_description_with_directive(self):
        """Test symbol description with directive."""
        token = Token("RULE", "rule_with_directive")
        token.line = 1
        token.column = 1

        symbol = Symbol(token, directive="test directive")
        desc = symbol.description

        assert "Test directive" in desc

    def test_symbol_description_with_inlined_flag(self):
        """Test symbol description with inlined flag."""
        token = Token("RULE", "_inline_rule")  # Underscore prefix makes it inlined
        token.line = 1
        token.column = 1

        symbol = Symbol(token)
        desc = symbol.description

        assert "Inlined" in desc

    def test_symbol_description_with_conditional_inline_flag(self):
        """Test symbol description with conditional inline flag."""
        token = Token(
            "RULE", "?cond_inline_rule"
        )  # Question mark prefix makes it conditionally inlined
        token.line = 1
        token.column = 1

        symbol = Symbol(token)
        desc = symbol.description

        assert "Conditionally Inlined" in desc

    def test_symbol_description_multiple_flags(self):
        """Test symbol description with multiple flags and directive."""
        token = Token("RULE", "_?multi_flag_rule")  # Both underscore and question mark
        token.line = 1
        token.column = 1

        symbol = Symbol(token, directive="complex directive")
        desc = symbol.description

        assert "Complex directive" in desc
        assert "Inlined" in desc
        assert "Conditionally Inlined" in desc
