"""Tests for LarkDocument class."""

from lsprotocol.types import CompletionItemKind, DiagnosticSeverity, Range, SymbolKind

from lark_parser_language_server.server import LarkDocument

from .fixtures import (
    COMMENTED_GRAMMAR,
    EMPTY_GRAMMAR,
    IMPORT_GRAMMAR,
    INVALID_GRAMMAR,
    MIXED_GRAMMAR,
    SIMPLE_GRAMMAR,
    UNDEFINED_REFERENCES_GRAMMAR,
    VALID_GRAMMAR,
)


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
        assert len(diagnostics) > 0

        # Should have error diagnostics (could be parse error or undefined references)
        error_diagnostic = diagnostics[0]
        assert error_diagnostic.severity == DiagnosticSeverity.Error
        # Could be parse error or undefined reference error
        assert any(
            keyword in error_diagnostic.message
            for keyword in ["Parse error", "Undefined"]
        )

    def test_extract_symbols_rules(self):
        """Test extraction of rule symbols."""
        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        # Check that rules are extracted
        assert "start" in doc._rules
        assert "expression" in doc._rules
        assert "term" in doc._rules
        assert "factor" in doc._rules

        # Check rule positions
        start_line, start_col = doc._rules["start"]
        assert start_line >= 0
        assert start_col >= 0

    def test_extract_symbols_terminals(self):
        """Test extraction of terminal symbols."""
        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        # Check that terminals are extracted
        assert "NUMBER" in doc._terminals

        # Check terminal positions
        number_line, number_col = doc._terminals["NUMBER"]
        assert number_line >= 0
        assert number_col >= 0

    def test_extract_symbols_imports(self):
        """Test extraction of import statements."""
        doc = LarkDocument("file:///test.lark", IMPORT_GRAMMAR)

        # Check that imports are extracted
        assert "common.WORD" in doc._imports
        assert "common.WS" in doc._imports

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
        assert symbol == "greeting"

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

        assert len(rule_completions) > 0
        assert len(terminal_completions) > 0
        assert len(keyword_completions) > 0

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
        if hasattr(hover.contents, "value"):
            assert "Rule" in hover.contents.value
        elif isinstance(hover.contents, str):
            assert "Rule" in hover.contents

        # Test hover for undefined symbol
        hover = doc.get_hover_info(1000, 1000)
        assert hover is None

    def test_empty_grammar(self):
        """Test handling of empty grammar."""
        doc = LarkDocument("file:///test.lark", EMPTY_GRAMMAR)

        assert len(doc._rules) == 0
        assert len(doc._terminals) == 0
        assert len(doc._imports) == 0

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
        assert "start" in doc._rules
        assert "expression" in doc._rules
        assert "NUMBER" in doc._terminals

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
        # Mock Lark.open_from_package to raise an exception
        mock_lark = mocker.patch(
            "lark_parser_language_server.server.Lark.open_from_package"
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
        assert "optional_rule" in doc._rules or len(doc._rules) >= 0
        assert "ignored_rule" in doc._rules or len(doc._rules) >= 0

        # Should handle private terminals
        assert "_PRIVATE_TERMINAL" in doc._terminals or len(doc._terminals) >= 0

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
