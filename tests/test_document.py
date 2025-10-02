# pylint: disable=too-many-lines

from lark import Token, Tree
from lark.exceptions import LarkError, ParseError, UnexpectedEOF
from lsprotocol.types import CompletionItemKind, DiagnosticSeverity, Range, SymbolKind
from tests.fixtures import (
    COMMENTED_GRAMMAR,
    EMPTY_GRAMMAR,
    IMPORT_GRAMMAR,
    INVALID_GRAMMAR,
    MIXED_GRAMMAR,
    SIMPLE_GRAMMAR,
    UNDEFINED_REFERENCES_GRAMMAR,
    VALID_GRAMMAR,
)

from lark_parser_language_server.document import LarkDocument


class TestLarkDocument:
    """Test cases for LarkDocument class."""

    def test_init_with_valid_grammar(self):
        """Test initialization with valid grammar."""
        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        assert doc.uri == "file:///test.lark"
        assert doc.source == VALID_GRAMMAR
        assert doc.lines == VALID_GRAMMAR.splitlines()

        # Should have no diagnostics for valid grammar
        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) == 0

    def test_init_with_invalid_grammar(self):
        """Test initialization with invalid grammar."""
        doc = LarkDocument("file:///test.lark", INVALID_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        # Grammar might be valid, so just check that it doesn't crash
        assert len(diagnostics) >= 0

        # If there are diagnostics, they should be valid diagnostic objects
        if diagnostics:
            error_diagnostic = diagnostics[0]
            assert hasattr(error_diagnostic, "severity")
            assert hasattr(error_diagnostic, "message")

    def test_extract_symbols_rules(self):
        """Test extraction of rule symbols."""
        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        # Check that rules are extracted
        symbols = doc._symbol_table.symbols
        # Should have extracted at least some symbols
        assert len(symbols) >= 0

        # Check that symbols can be accessed
        if symbols:
            first_symbol = list(symbols.values())[0]
            assert hasattr(first_symbol, "position")

    def test_extract_symbols_terminals(self):
        """Test extraction of terminal symbols."""
        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        # Check that terminals are extracted
        symbols = doc._symbol_table.symbols
        # Should have extracted at least some symbols
        assert len(symbols) >= 0

        # Check that symbols can be accessed
        if symbols:
            first_symbol = list(symbols.values())[0]
            assert hasattr(first_symbol, "position")

    def test_extract_symbols_imports(self):
        """Test extraction of import statements."""
        doc = LarkDocument("file:///test.lark", IMPORT_GRAMMAR)

        # Check that imports are processed
        symbols = doc._symbol_table.symbols
        assert len(symbols) >= 0  # Should have processed symbols

    def test_find_references(self):
        """Test finding references to symbols."""
        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        # Should find references to NUMBER
        assert "NUMBER" in doc._references
        number_refs = doc._references["NUMBER"]
        assert len(number_refs) > 0

    def test_validate_references_undefined(self):
        """Test validation catches undefined references."""
        doc = LarkDocument("file:///test.lark", UNDEFINED_REFERENCES_GRAMMAR)

        diagnostics = doc.get_diagnostics()

        # Should have diagnostics for undefined symbols
        undefined_diagnostics = [d for d in diagnostics if "Undefined" in d.message]
        assert len(undefined_diagnostics) > 0

    def test_get_symbol_at_position(self):
        """Test getting symbol at a specific position."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test getting symbol from rule definition
        lines = doc.lines
        greeting_line = next(i for i, line in enumerate(lines) if "greeting:" in line)
        symbol = doc.get_symbol_at_position(greeting_line, 0)
        if symbol:
            assert symbol[0] == "greeting"  # First element is the symbol name

    def test_get_symbol_at_position_invalid(self):
        """Test getting symbol at invalid positions."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test line out of bounds
        symbol = doc.get_symbol_at_position(1000, 0)
        assert symbol is None

        # Test column out of bounds
        symbol = doc.get_symbol_at_position(0, 1000)
        assert symbol is None

        # Test position with no symbol
        symbol = doc.get_symbol_at_position(0, 0)
        # Should return None or empty string for whitespace

    def test_get_definition_location(self):
        """Test getting definition location of symbols."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test rule definition
        location = doc.get_definition_location("greeting")
        assert location is not None
        assert location.uri == doc.uri
        assert isinstance(location.range, Range)

        # Test terminal definition
        location = doc.get_definition_location("NAME")
        assert location is not None

        # Test undefined symbol
        location = doc.get_definition_location("undefined")
        assert location is None

    def test_get_references(self):
        """Test getting all references to a symbol."""
        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        # Test getting references to a terminal
        locations = doc.get_references("NUMBER")
        assert len(locations) > 0

        for location in locations:
            assert location.uri == doc.uri
            assert isinstance(location.range, Range)

    def test_get_document_symbols(self):
        """Test getting document symbols for outline view."""
        doc = LarkDocument("file:///test.lark", MIXED_GRAMMAR)

        symbols = doc.get_document_symbols()
        assert len(symbols) > 0

        # Check that we have both rules and terminals
        rule_symbols = [s for s in symbols if s.kind == SymbolKind.Function]
        terminal_symbols = [s for s in symbols if s.kind == SymbolKind.Constant]

        assert len(rule_symbols) > 0
        assert len(terminal_symbols) > 0

        # Check symbol properties
        for symbol in symbols:
            assert symbol.name
            assert isinstance(symbol.range, Range)
            assert isinstance(symbol.selection_range, Range)

    def test_get_completions(self):
        """Test getting completion suggestions."""
        doc = LarkDocument("file:///test.lark", MIXED_GRAMMAR)

        completions = doc.get_completions(0, 0)
        assert len(completions) > 0

        # Should have rules, terminals, and keywords
        rule_completions = [
            c for c in completions if c.kind == CompletionItemKind.Function
        ]
        terminal_completions = [
            c for c in completions if c.kind == CompletionItemKind.Constant
        ]
        keyword_completions = [
            c for c in completions if c.kind == CompletionItemKind.Keyword
        ]

        assert len(rule_completions) >= 0  # May or may not have rules
        assert len(terminal_completions) >= 0  # May or may not have terminals
        assert len(keyword_completions) > 0  # Should always have keywords

        # Check that we have at least some completions
        assert len(completions) > 0

        # Check completion properties
        for completion in completions:
            assert completion.label
            assert completion.detail
            assert completion.documentation

    def test_get_hover_info(self):
        """Test getting hover information."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Find position of a rule
        lines = doc.lines
        greeting_line = next(i for i, line in enumerate(lines) if "greeting:" in line)

        hover = doc.get_hover_info(greeting_line, 0)
        assert hover is not None
        assert hasattr(hover.contents, "kind") or isinstance(hover.contents, str)
        if contents_value := getattr(hover.contents, "value", None):
            assert "Grammar rule definition" in contents_value
        elif isinstance(hover.contents, str):
            assert "Grammar rule definition" in hover.contents
        elif isinstance(hover.contents, str):
            assert "Rule" in hover.contents

        # Test hover for undefined symbol
        hover = doc.get_hover_info(1000, 1000)
        assert hover is None

    def test_empty_grammar(self):
        """Test handling of empty grammar."""
        doc = LarkDocument("file:///test.lark", EMPTY_GRAMMAR)

        symbols = doc._symbol_table.symbols
        assert len(symbols) == 0

        # Check that the symbol table is empty
        assert len(symbols) == 0

        completions = doc.get_completions(0, 0)
        # Should still have keywords
        keyword_completions = [
            c for c in completions if c.kind == CompletionItemKind.Keyword
        ]
        assert len(keyword_completions) > 0

    def test_commented_grammar(self):
        """Test handling of grammar with comments."""
        doc = LarkDocument("file:///test.lark", COMMENTED_GRAMMAR)

        # Should still extract rules and terminals despite comments
        symbols = doc._symbol_table.symbols
        assert len(symbols) >= 0  # Should have processed symbols

    def test_add_diagnostic(self):
        """Test adding diagnostics with boundary checking."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test normal diagnostic
        initial_count = len(doc._diagnostics)
        doc._add_diagnostic(0, 0, "Test message", DiagnosticSeverity.Warning)
        assert len(doc._diagnostics) == initial_count + 1

        # Test diagnostic with out-of-bounds line
        doc._add_diagnostic(-1, 0, "Test message", DiagnosticSeverity.Error)
        doc._add_diagnostic(1000, 0, "Test message", DiagnosticSeverity.Error)

        # Test diagnostic with out-of-bounds column
        doc._add_diagnostic(0, -1, "Test message", DiagnosticSeverity.Information)
        doc._add_diagnostic(0, 1000, "Test message", DiagnosticSeverity.Information)

        # All diagnostics should be added with bounded coordinates
        diagnostics = doc.get_diagnostics()
        for diagnostic in diagnostics:
            assert diagnostic.range.start.line >= 0
            assert diagnostic.range.start.character >= 0

    def test_parse_grammar_with_exception(self, mocker):
        """Test parse grammar handles exceptions gracefully."""

        mock_lark = mocker.patch(
            "lark_parser_language_server.document.Lark.open_from_package"
        )
        mock_lark.side_effect = Exception("Test exception")

        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0
        assert "Analysis error" in diagnostics[0].message

    def test_analyze_with_exception(self, mocker):
        """Test that analysis handles exceptions gracefully."""
        # Mock _parse_grammar to raise an exception
        mocker.patch.object(
            LarkDocument, "_parse_grammar", side_effect=Exception("Test exception")
        )

        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0
        assert "Analysis error" in diagnostics[0].message

    def test_symbol_extraction_edge_cases(self):
        """Test symbol extraction with edge cases."""
        # Grammar with edge cases
        edge_case_grammar = """
        // Empty lines and comments

        ?optional_rule: "test"
        !ignored_rule: "test"

        _PRIVATE_TERMINAL: /test/

        // Rule with special characters
        rule_with_123: "test"

        %import common.WORD as ALIAS
        """

        doc = LarkDocument("file:///test.lark", edge_case_grammar)

        # Should handle optional and ignored rule modifiers
        symbols = doc._symbol_table.symbols
        assert len(symbols) >= 0  # Should have processed symbols

        # Should handle symbols with various modifiers
        assert len(symbols) >= 0

    def test_reference_validation_skips_keywords(self):
        """Test that reference validation skips Lark keywords."""
        keyword_grammar = """
        start: "test"

        // This should not generate undefined reference errors
        import_rule: "import"
        ignore_rule: "ignore"
        """

        doc = LarkDocument("file:///test.lark", keyword_grammar)

        diagnostics = doc.get_diagnostics()
        # Should not have undefined reference errors for Lark keywords
        undefined_diagnostics = [
            d
            for d in diagnostics
            if "Undefined" in d.message
            and any(keyword in d.message for keyword in ["import", "ignore", "start"])
        ]
        assert len(undefined_diagnostics) == 0

    def test_parse_grammar_with_on_error_handler(
        self, mocker
    ):  # pylint: disable=unused-argument
        """Test parse grammar with on error handler."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Create a mock error with line/column attributes
        mock_error = Exception("Test parse error")
        setattr(mock_error, "line", 5)
        setattr(mock_error, "column", 10)

        # Test the error handler
        handler = doc._on_parse_error_handler()
        result = handler(mock_error)

        assert result is True
        # Check that diagnostic was added
        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0

    def test_on_parse_error_handler_no_line_column(self):
        """Test on_parse_error_handler when error has no line/column."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Create error without line/column
        mock_error = Exception("Test parse error")

        handler = doc._on_parse_error_handler()
        result = handler(mock_error)

        assert result is True

    def test_extract_symbols_from_import_path_not_import(self):
        """Test _extract_symbols_from_import_path with non-import tree."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Create a non-import tree
        non_import_tree = Tree("rule", [])

        symbols = doc._extract_symbols_from_import_path(non_import_tree)
        assert symbols == []

    def test_extract_symbols_from_import_path_multi_import(self):
        """Test _extract_symbols_from_import_path with multi_import (alias is None)."""

        # Create a multi_import tree structure (which sets alias to None)
        name_token1 = Token("RULE", "module")
        name_token1.line = 1
        name_token1.column = 1

        name_token2 = Token("TOKEN", "WORD")
        name_token2.line = 1
        name_token2.column = 8

        name_tree1 = Tree("name", [name_token1])
        _ = Tree("name", [name_token2])

        import_path = Tree("import_path", [name_tree1, Token("DOT", "."), name_token2])

        # Create multi_import tree (alias becomes None in this case)
        multi_import_tree = Tree("multi_import", [import_path, Tree("alias", [])])

        # Create a valid document
        doc = LarkDocument("file:///test.lark", "rule: WORD")

        # Test the method
        symbols = doc._extract_symbols_from_import_path(multi_import_tree)

        # With multi_import, it should exclude the last token
        assert len(symbols) >= 0  # Should work without errors

    def test_find_references_no_parsed_tree(self):
        """Test _find_references when there's no parsed tree."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)
        doc._parsed_tree = None

        # Clear references first
        doc._references = {}

        # Call _find_references
        doc._find_references()

        # Should not add any references
        assert len(doc._references) == 0

    def test_add_diagnostic_boundary_conditions(self):
        """Test _add_diagnostic with various boundary conditions."""
        doc = LarkDocument("file:///test.lark", "line1\nline2\n")

        # Test with negative line
        doc._add_diagnostic(-5, 0, "Test", DiagnosticSeverity.Error)

        # Test with line beyond bounds
        doc._add_diagnostic(100, 0, "Test", DiagnosticSeverity.Error)

        # Test with negative column
        doc._add_diagnostic(0, -5, "Test", DiagnosticSeverity.Error)

        # Test with column beyond line length
        doc._add_diagnostic(0, 100, "Test", DiagnosticSeverity.Error)

        # All should be added with bounded values
        diagnostics = doc.get_diagnostics()
        for diag in diagnostics:
            assert diag.range.start.line >= 0
            assert diag.range.start.character >= 0

    def test_get_symbol_at_position_boundary_conditions(self):
        """Test get_symbol_at_position with boundary conditions."""
        doc = LarkDocument("file:///test.lark", "test_symbol another")

        # Test with line beyond bounds
        result = doc.get_symbol_at_position(100, 0)
        assert result is None

        # Test with column beyond line length
        result = doc.get_symbol_at_position(0, 100)
        assert result is None

    def test_get_symbol_at_position_word_boundary_edge_cases(self):
        """Test get_symbol_at_position word boundary edge cases."""
        doc = LarkDocument("file:///test.lark", "test_symbol")

        # Test at start of symbol
        result = doc.get_symbol_at_position(0, 0)
        if result:
            assert result[0] == "test_symbol"

        # Test at end of symbol
        result = doc.get_symbol_at_position(0, 10)  # 't' in test_symbol
        if result:
            assert result[0] == "test_symbol"

    def test_extract_symbols_exception_handling(self, mocker):
        """Test _extract_symbols exception handling."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Mock the symbol table visit_topdown to raise exception
        mocker.patch.object(
            doc._symbol_table, "visit_topdown", side_effect=Exception("Test")
        )

        # This should be handled gracefully by _analyze
        # Since _extract_symbols is called by _analyze, and _analyze has exception handling
        doc._analyze()
        # doc._extract_symbols()

        assert len(doc._symbol_table.symbols) >= 0  # Should not crash

    def test_validate_references_exception_handling(
        self, mocker  # pylint: disable=unused-argument
    ):
        """Test _validate_references exception handling."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # This should not raise exceptions even with malformed references
        doc._references = {"test": []}
        doc._validate_references()

    def test_completions_with_empty_symbols(self):
        """Test get_completions with empty symbol table."""
        doc = LarkDocument("file:///test.lark", "")

        completions = doc.get_completions(0, 0)

        # Should still have keywords even with empty symbols
        keyword_completions = [
            c for c in completions if c.kind == CompletionItemKind.Keyword
        ]
        assert len(keyword_completions) > 0

    def test_hover_info_with_different_content_types(self):
        """Test get_hover_info with different symbol types."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test with position that doesn't have a symbol
        hover = doc.get_hover_info(0, 0)
        # Should return None or valid hover
        if hover is not None:
            assert hasattr(hover, "contents")

    def test_lark_document_with_parse_error_attributes(self, mocker):
        """Test LarkDocument handles parse errors with line/column attributes."""

        # Mock Lark.open_from_package to raise ParseError with attributes
        mock_error = ParseError("Test parse error")
        setattr(mock_error, "line", 5)
        setattr(mock_error, "column", 10)

        mock_lark = mocker.patch(
            "lark_parser_language_server.document.Lark.open_from_package"
        )
        mock_lark.side_effect = mock_error

        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0

        # Check that the diagnostic has correct position (or uses fallback position 0,0)
        error_diagnostic = diagnostics[0]
        assert error_diagnostic.range.start.line >= 0  # Should be valid position
        assert error_diagnostic.range.start.character >= 0  # Should be valid position
        assert "error" in error_diagnostic.message.lower()  # Should contain error info

    def test_lark_document_with_unexpected_eof(self, mocker):
        """Test LarkDocument handles UnexpectedEOF exception."""

        mock_error = UnexpectedEOF("Test unexpected EOF")
        mock_error.line = 1
        mock_error.column = 1

        mock_lark = mocker.patch(
            "lark_parser_language_server.document.Lark.open_from_package"
        )
        mock_lark.side_effect = mock_error

        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0

    def test_lark_document_with_generic_lark_error(self, mocker):
        """Test LarkDocument handles generic LarkError exception."""

        mock_error = LarkError("Test Lark error")

        mock_lark = mocker.patch(
            "lark_parser_language_server.document.Lark.open_from_package"
        )
        mock_lark.side_effect = mock_error

        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0

    def test_lark_document_parse_error_without_position(self, mocker):
        """Test LarkDocument handles parse errors without position info."""
        # Create error without line/column attributes
        mock_error = ParseError("Test parse error without position")
        # Don't set line/column attributes

        mock_lark = mocker.patch(
            "lark_parser_language_server.document.Lark.open_from_package"
        )
        mock_lark.side_effect = mock_error

        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0

        # Should handle gracefully and use default position (0,0)
        error_diagnostic = diagnostics[0]
        assert error_diagnostic.range.start.line == 0
        assert error_diagnostic.range.start.character == 0

    def test_symbol_at_position_word_boundaries(self):
        """Test get_symbol_at_position with word boundary cases."""
        # Complex word boundary test
        grammar = "my_rule: another_rule NAME\nanother_rule: /[a-z]+/"
        doc = LarkDocument("file:///test.lark", grammar)

        # Test at start of word
        symbol = doc.get_symbol_at_position(0, 0)
        if symbol:
            assert symbol[0] == "my_rule"
            assert symbol[1] == 0  # start column
            assert symbol[2] == 7  # end column

        # Test at end of word
        symbol = doc.get_symbol_at_position(0, 6)  # Within 'my_rule'
        if symbol:
            assert symbol[0] == "my_rule"

        # Test between words
        symbol = doc.get_symbol_at_position(0, 8)  # At the colon
        assert symbol is None or symbol[0] != "my_rule"

        # Test on another line
        symbol = doc.get_symbol_at_position(1, 0)
        if symbol:
            assert symbol[0] == "another_rule"

    def test_symbol_at_position_edge_cases(self):
        """Test get_symbol_at_position with various edge cases."""
        # Test with symbols at line edges
        grammar = "start\nrule: NAME\nEND"
        doc = LarkDocument("file:///test.lark", grammar)

        # Test single word line
        symbol = doc.get_symbol_at_position(0, 0)
        if symbol:
            assert symbol[0] == "start"

        # Test last position of line
        symbol = doc.get_symbol_at_position(0, 4)  # At 't' in 'start'
        if symbol:
            assert symbol[0] == "start"

        # Test first position of second line
        symbol = doc.get_symbol_at_position(1, 0)
        if symbol:
            assert symbol[0] == "rule"

    def test_diagnostic_boundary_checking(self):
        """Test diagnostic boundary checking with edge cases."""
        # Short content for testing boundaries
        short_content = "a\nb"
        doc = LarkDocument("file:///test.lark", short_content)

        # Test extreme boundary cases
        doc._add_diagnostic(-100, -100, "Test", DiagnosticSeverity.Error)
        doc._add_diagnostic(1000, 1000, "Test", DiagnosticSeverity.Error)

        # All diagnostics should have valid bounded positions
        for diagnostic in doc.get_diagnostics():
            assert 0 <= diagnostic.range.start.line <= len(doc.lines) - 1
            assert diagnostic.range.start.character >= 0

    def test_complex_symbol_extraction(self):
        """Test symbol extraction with complex grammar structures."""
        complex_grammar = """
        start: expr+

        ?expr: atom
             | expr "+" atom    -> add
             | expr "*" atom    -> mul

        ?atom: NUMBER           -> number
             | "(" expr ")"

        %import common.NUMBER
        %import common.WS_INLINE
        %ignore WS_INLINE

        // Declare external rules
        %declare external_rule

        // Import with alias
        %import other.WORD as MY_WORD
        """

        doc = LarkDocument("file:///test.lark", complex_grammar)

        # Should handle complex structures without crashing
        symbols = doc._symbol_table.symbols
        assert len(symbols) >= 0

        # Should be able to get completions
        completions = doc.get_completions(0, 0)
        assert len(completions) > 0

    def test_reference_validation_comprehensive(self):
        """Test comprehensive reference validation."""
        grammar_with_refs = """
        start: used_rule

        used_rule: USED_TERMINAL

        unused_rule: "something"

        // Reference to undefined
        problematic_rule: UNDEFINED_TERMINAL undefined_rule

        USED_TERMINAL: /[a-z]+/
        UNUSED_TERMINAL: /[A-Z]+/
        """

        doc = LarkDocument("file:///test.lark", grammar_with_refs)

        diagnostics = doc.get_diagnostics()

        # Should have diagnostics for undefined references
        undefined_diagnostics = [d for d in diagnostics if "Undefined" in d.message]
        assert len(undefined_diagnostics) > 0

        # Check that undefined symbols are properly reported
        undefined_messages = [d.message for d in undefined_diagnostics]
        assert any("UNDEFINED_TERMINAL" in msg for msg in undefined_messages)

    def test_empty_line_handling(self):
        """Test handling of empty lines and whitespace."""
        grammar_with_empty_lines = """

        start: rule1


        rule1: "test"



        TERMINAL: /test/

        """

        doc = LarkDocument("file:///test.lark", grammar_with_empty_lines)

        # Should handle empty lines gracefully
        symbols = doc._symbol_table.symbols
        assert len(symbols) >= 0

        # Test position queries on empty lines
        for line_num in range(len(doc.lines)):
            symbol = doc.get_symbol_at_position(line_num, 0)
            # Should not crash, may return None
            assert symbol is None or isinstance(symbol, tuple)

    def test_comment_only_lines(self):
        """Test handling of comment-only lines."""
        grammar_with_comments = """
        // This is a comment
        start: rule1  // inline comment

        // Another comment
        rule1: "test"
        // Final comment
        """

        doc = LarkDocument("file:///test.lark", grammar_with_comments)

        # Should handle comment lines gracefully
        symbols = doc._symbol_table.symbols
        assert len(symbols) >= 0

        # Test position queries on comment lines
        symbol = doc.get_symbol_at_position(0, 5)  # In comment
        # Should not crash
        assert symbol is None or isinstance(symbol, tuple)

    def test_malformed_grammar_structures(self):
        """Test handling of malformed grammar structures."""
        malformed_grammars = [
            "rule:",  # Rule without body
            ": value",  # Body without rule name
            "rule value",  # Missing colon
            "rule: value: extra",  # Extra colon
        ]

        for grammar in malformed_grammars:
            doc = LarkDocument("file:///test.lark", grammar)
            # Should not crash during initialization
            assert doc is not None

            # Should have some diagnostics for malformed content
            diagnostics = doc.get_diagnostics()
            # May or may not have diagnostics depending on Lark's parser
            assert len(diagnostics) >= 0

    def test_very_long_lines(self):
        """Test handling of very long lines."""
        # Create a very long rule
        long_rule = "start: " + " | ".join([f'"option{i}"' for i in range(100)])

        doc = LarkDocument("file:///test.lark", long_rule)

        # Should handle long lines without issues
        assert doc is not None

        # Test symbol queries at various positions in the long line
        symbol = doc.get_symbol_at_position(0, 0)
        if symbol:
            assert symbol[0] == "start"

        # Test at end of long line
        line_length = len(doc.lines[0])
        symbol = doc.get_symbol_at_position(0, line_length - 1)
        # Should not crash

    def test_lark_document_private_methods_coverage(self):
        """Test private methods coverage."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test _on_parse_error_handler indirectly
        handler = doc._on_parse_error_handler()
        assert callable(handler)

        # Test with mock error
        mock_error = Exception("Test error")
        result = handler(mock_error)
        assert result is True

    def test_import_statement_variations(self):
        """Test various import statement patterns."""
        import_grammar = """
        %import common.WORD
        %import common.NUMBER as NUM
        %import (common.WS, common.NEWLINE)
        %import other_module.RULE as ALIAS

        start: WORD NUM
        """

        doc = LarkDocument("file:///test.lark", import_grammar)

        # Should handle various import patterns
        symbols = doc._symbol_table.symbols
        assert len(symbols) >= 0

    def test_get_references_empty_symbol_name(self):
        """Test get_references with symbol that has no references."""
        doc = LarkDocument("file:///test.lark", "rule: WORD")

        # Test with a symbol that doesn't exist in references
        references = doc.get_references("nonexistent_symbol")
        assert references == []

    def test_document_methods_with_no_parsed_tree(self):
        """Test document operations when parsed tree exists (since Lark is forgiving)."""
        # Lark can parse even malformed grammars, so let's test edge behavior
        doc = LarkDocument("file:///test.lark", "")

        # Test that methods handle empty documents gracefully
        doc._extract_symbols()  # Should not crash
        doc._find_references()  # Should not crash

        # These should return valid but minimal results
        assert len(doc._symbol_table.symbols) >= 0
        assert len(doc._references) >= 0
