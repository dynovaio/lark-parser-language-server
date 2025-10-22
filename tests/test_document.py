"""Tests for lark_parser_language_server.document module."""

from unittest.mock import Mock, patch

import pytest
from lark.exceptions import LarkError, ParseError, UnexpectedEOF
from lsprotocol.types import (
    CompletionItemKind,
    DiagnosticSeverity,
    FormattingOptions,
    Position,
    Range,
    SymbolKind,
)
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
        assert isinstance(doc._symbol_table, object)
        assert doc._parsed_tree is not None
        assert doc._diagnostics == []
        assert doc._ast is not None

    def test_init_with_empty_grammar(self):
        """Test initialization with empty grammar."""
        doc = LarkDocument("file:///test.lark", EMPTY_GRAMMAR)

        assert doc.uri == "file:///test.lark"
        assert doc.source == EMPTY_GRAMMAR
        assert doc.lines == []
        # Empty grammar should have parse errors
        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0  # Should have diagnostics for empty grammar

    def test_init_with_simple_grammar(self):
        """Test initialization with simple grammar."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Should have parsed successfully
        assert doc._parsed_tree is not None
        assert doc._ast is not None

        # Should have extracted symbols
        assert hasattr(doc._symbol_table, "definitions")
        assert hasattr(doc._symbol_table, "references")

    def test_analyze_method_flow(self):
        """Test the analysis method flow."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # All analysis steps should have completed
        assert doc._parsed_tree is not None
        assert doc._ast is not None
        assert hasattr(doc._symbol_table, "definitions")

    @patch("lark_parser_language_server.document.PARSER.parse")
    def test_parse_grammar_error_handling(self, mock_parse):
        """Test parse grammar error handling."""
        mock_parse.side_effect = ParseError("Test parse error")

        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0
        assert "Error analyzing document" in diagnostics[0].message

    @patch("lark_parser_language_server.document.AST_BUILDER.build")
    def test_build_ast_error_handling(self, mock_build):
        """Test AST building error handling."""
        mock_build.side_effect = Exception("AST build error")

        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0

    @patch("lark_parser_language_server.document.Lark")
    def test_load_document_grammar_error(self, mock_lark):
        """Test load document grammar error handling."""
        mock_lark.side_effect = LarkError("Grammar error")

        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0

    def test_on_parse_error_handler(self):
        """Test parse error handler."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        handler = doc._on_parse_error_handler()

        # Test with error that has line/column
        error = ParseError("Test error")
        error.line = 5
        error.column = 10

        result = handler(error)
        assert result is True

        # Should have added a diagnostic
        diagnostics = doc.get_diagnostics()
        parse_errors = [d for d in diagnostics if "Parse error" in d.message]
        assert len(parse_errors) > 0

    def test_add_diagnostic(self):
        """Test adding diagnostics."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        initial_count = len(doc._diagnostics)

        # Add diagnostic with error object
        error = Exception("Test error")
        error.line = 1
        error.column = 5
        error.width = 3

        doc._add_diagnostic(error, DiagnosticSeverity.Warning, "Custom message")

        assert len(doc._diagnostics) == initial_count + 1
        diagnostic = doc._diagnostics[-1]
        assert diagnostic.message == "Custom message"
        assert diagnostic.severity == DiagnosticSeverity.Warning
        assert diagnostic.source == "lark-parser-language-server"

    def test_add_diagnostic_boundary_checking(self):
        """Test diagnostic boundary checking."""
        doc = LarkDocument("file:///test.lark", "line1\nline2")

        # Test with out-of-bounds line
        error = Exception("Test error")
        error.line = -1
        error.column = 0
        error.width = 1

        doc._add_diagnostic(error)

        diagnostic = doc._diagnostics[-1]
        assert diagnostic.range.start.line >= 0
        assert diagnostic.range.start.character >= 0

    def test_add_diagnostic_no_attributes(self):
        """Test diagnostic with error that has no line/column attributes."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        error = Exception("Simple error")
        # No line/column/width attributes

        doc._add_diagnostic(error)

        diagnostic = doc._diagnostics[-1]
        assert diagnostic.range.start.line == 0
        assert diagnostic.range.start.character == 0

    def test_get_diagnostics(self):
        """Test getting diagnostics."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        diagnostics = doc.get_diagnostics()
        assert isinstance(diagnostics, list)

        # Add a diagnostic and verify it's returned
        doc._add_diagnostic(Exception("Test"), message="Test diagnostic")
        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0

    def test_get_symbol_at_position(self):
        """Test getting symbol at position."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test valid position
        symbol = doc.get_symbol_at_position(0, 0)
        # May or may not return a symbol depending on content
        if symbol:
            assert isinstance(symbol, tuple)
            assert len(symbol) == 3  # (name, start, end)
            assert isinstance(symbol[0], str)
            assert isinstance(symbol[1], int)
            assert isinstance(symbol[2], int)

    def test_get_symbol_at_position_out_of_bounds(self):
        """Test getting symbol at out-of-bounds positions."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Line out of bounds
        result = doc.get_symbol_at_position(1000, 0)
        assert result is None

        # Column out of bounds
        result = doc.get_symbol_at_position(0, 1000)
        assert result is None

    def test_get_symbol_at_position_word_boundaries(self):
        """Test symbol detection at word boundaries."""
        doc = LarkDocument("file:///test.lark", "test_symbol another")

        # Test at different positions
        for col in range(len(doc.lines[0])):
            symbol = doc.get_symbol_at_position(0, col)
            # Should either return None or a valid symbol tuple
            if symbol:
                assert isinstance(symbol, tuple)
                assert len(symbol) == 3

    def test_get_definition_location(self):
        """Test getting definition location."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test with existing symbols (may or may not exist in simple grammar)
        location = doc.get_definition_location("start")
        if location:
            assert location.uri == doc.uri
            assert isinstance(location.range, Range)

        # Test with non-existent symbol
        location = doc.get_definition_location("nonexistent_symbol")
        assert location is None

    def test_get_references(self):
        """Test getting references."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test with some symbol (may or may not have references)
        references = doc.get_references("start")
        assert isinstance(references, list)

        # Test with non-existent symbol
        references = doc.get_references("nonexistent_symbol")
        assert references == []

    def test_get_document_symbols(self):
        """Test getting document symbols."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        symbols = doc.get_document_symbols()
        assert isinstance(symbols, list)

        # If symbols exist, they should have proper structure
        for symbol in symbols:
            assert hasattr(symbol, "name")
            assert hasattr(symbol, "kind")
            assert hasattr(symbol, "range")

    def test_get_completions(self):
        """Test getting completions."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        completions = doc.get_completions(0, 0)
        assert isinstance(completions, list)

        # Should at least have keyword completions
        assert len(completions) > 0

        # Check completion structure
        for completion in completions:
            assert hasattr(completion, "label")
            assert hasattr(completion, "kind")

    def test_get_hover_info(self):
        """Test getting hover information."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test at various positions
        hover = doc.get_hover_info(0, 0)
        # May or may not return hover info
        if hover:
            assert hasattr(hover, "contents")

        # Test at invalid position
        hover = doc.get_hover_info(1000, 1000)
        assert hover is None

    def test_format_with_ast(self):
        """Test formatting with valid AST."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        options = FormattingOptions(
            tab_size=4, insert_spaces=True, insert_final_newline=True
        )
        result = doc.format(options)

        assert hasattr(result, "new_text")
        assert hasattr(result, "range")
        assert isinstance(result.new_text, str)

    def test_format_without_ast(self):
        """Test formatting without AST."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)
        doc._ast = None  # Force no AST

        options = FormattingOptions(
            tab_size=2, insert_spaces=False, insert_final_newline=False
        )
        result = doc.format(options)

        # Should return original source
        assert result.new_text == doc.source
        assert hasattr(result, "range")

    def test_format_options_variations(self):
        """Test formatting with different options."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test with tabs
        options = FormattingOptions(
            tab_size=4, insert_spaces=False, insert_final_newline=True
        )
        result = doc.format(options)
        assert isinstance(result.new_text, str)

        # Test without final newline
        options = FormattingOptions(
            tab_size=2, insert_spaces=True, insert_final_newline=False
        )
        result = doc.format(options)
        assert isinstance(result.new_text, str)


class TestLarkDocumentErrorHandling:
    """Test error handling in LarkDocument."""

    def test_analyze_exception_handling(self):
        """Test analyze handles exceptions gracefully."""
        with patch.object(
            LarkDocument, "_parse_grammar", side_effect=Exception("Test error")
        ):
            doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

            diagnostics = doc.get_diagnostics()
            assert len(diagnostics) > 0
            assert "Error analyzing document" in diagnostics[0].message

    def test_collect_definitions_exception_handling(self):
        """Test collect definitions error handling."""
        with patch(
            "lark_parser_language_server.symbol_table.SymbolTable.collect_definitions",
            side_effect=Exception("Definition error"),
        ):
            doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

            diagnostics = doc.get_diagnostics()
            assert len(diagnostics) > 0

    def test_validate_definitions_with_errors(self):
        """Test validate definitions with symbol table errors."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Manually add an error to symbol table
        from lark_parser_language_server.symbol_table.errors import (
            MultipleDefinitionsError,
        )

        error = MultipleDefinitionsError("test_rule")
        doc._symbol_table.definition_errors.append((error, None))

        # Re-run validation
        doc._validate_definitions()

        # Should have added diagnostic for the error
        diagnostics = doc.get_diagnostics()
        assert any(str(error) in d.message for d in diagnostics)

    def test_validate_references_with_errors(self):
        """Test validate references with symbol table errors."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Manually add a reference error to symbol table
        from lark_parser_language_server.symbol_table.errors import (
            DefinitionNotFoundForReferenceError,
        )

        error = DefinitionNotFoundForReferenceError("undefined_rule")
        doc._symbol_table.reference_errors.append((error, None, None))

        # Re-run validation
        doc._validate_references()

        # Should have added diagnostic for the error
        diagnostics = doc.get_diagnostics()
        assert any(str(error) in d.message for d in diagnostics)


class TestLarkDocumentIntegration:
    """Integration tests for LarkDocument."""

    def test_complete_workflow_valid_grammar(self):
        """Test complete workflow with valid grammar."""
        doc = LarkDocument("file:///test.lark", VALID_GRAMMAR)

        # Should have completed all analysis steps
        assert doc._parsed_tree is not None
        assert doc._ast is not None

        # Should be able to provide all services
        diagnostics = doc.get_diagnostics()
        symbols = doc.get_document_symbols()
        completions = doc.get_completions(0, 0)

        assert isinstance(diagnostics, list)
        assert isinstance(symbols, list)
        assert isinstance(completions, list)

    def test_complete_workflow_complex_grammar(self):
        """Test complete workflow with complex grammar."""
        complex_grammar = """
        start: expr+

        ?expr: atom
             | expr "+" atom    -> add
             | expr "*" atom    -> mul

        atom: NUMBER           -> number
            | "(" expr ")"

        %import common.NUMBER
        %import common.WS_INLINE
        %ignore WS_INLINE
        """

        doc = LarkDocument("file:///test.lark", complex_grammar)

        # Should handle complex grammar
        assert doc._parsed_tree is not None
        diagnostics = doc.get_diagnostics()
        # Complex grammar might have some issues but shouldn't crash
        assert isinstance(diagnostics, list)

    def test_workflow_with_imports(self):
        """Test workflow with import statements."""
        doc = LarkDocument("file:///test.lark", IMPORT_GRAMMAR)

        # Should handle imports
        assert doc._parsed_tree is not None
        symbols = doc.get_document_symbols()
        assert isinstance(symbols, list)

    def test_workflow_with_comments(self):
        """Test workflow with commented grammar."""
        doc = LarkDocument("file:///test.lark", COMMENTED_GRAMMAR)

        # Should handle comments gracefully
        assert doc._parsed_tree is not None
        diagnostics = doc.get_diagnostics()
        symbols = doc.get_document_symbols()

        assert isinstance(diagnostics, list)
        assert isinstance(symbols, list)

    def test_edge_case_empty_lines(self):
        """Test handling of empty lines and whitespace."""
        grammar_with_empty_lines = """

        start: rule1


        rule1: "test"



        TERMINAL: /test/

        """

        doc = LarkDocument("file:///test.lark", grammar_with_empty_lines)

        # Should handle empty lines gracefully
        assert doc._parsed_tree is not None

        # Test position queries on empty lines
        for line_num in range(len(doc.lines)):
            symbol = doc.get_symbol_at_position(line_num, 0)
            # Should not crash
            assert symbol is None or isinstance(symbol, tuple)

    def test_edge_case_very_long_lines(self):
        """Test handling of very long lines."""
        long_rule = "start: " + " | ".join([f'"option{i}"' for i in range(50)])

        doc = LarkDocument("file:///test.lark", long_rule)

        # Should handle long lines
        assert doc._parsed_tree is not None

        # Test symbol queries at various positions
        symbol = doc.get_symbol_at_position(0, 0)
        if symbol:
            assert isinstance(symbol, tuple)

    def test_symbol_queries_consistency(self):
        """Test consistency of symbol-related queries."""
        doc = LarkDocument("file:///test.lark", MIXED_GRAMMAR)

        # Get all document symbols
        document_symbols = doc.get_document_symbols()

        # Test definition locations for each symbol
        for symbol in document_symbols:
            location = doc.get_definition_location(symbol.name)
            # Should either return a location or None
            if location:
                assert location.uri == doc.uri
                assert isinstance(location.range, Range)

    def test_completion_consistency(self):
        """Test completion consistency across different positions."""
        doc = LarkDocument("file:///test.lark", MIXED_GRAMMAR)

        # Test completions at different positions
        for line in range(min(3, len(doc.lines))):
            for col in range(
                min(10, len(doc.lines[line]) if line < len(doc.lines) else 0)
            ):
                completions = doc.get_completions(line, col)
                assert isinstance(completions, list)
                # Should always have at least keyword completions
                assert len(completions) > 0

    def test_hover_consistency(self):
        """Test hover consistency."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Test hover at various positions
        for line in range(min(3, len(doc.lines))):
            if line < len(doc.lines):
                for col in range(min(10, len(doc.lines[line]))):
                    hover = doc.get_hover_info(line, col)
                    # Should return None or valid hover
                    if hover:
                        assert hasattr(hover, "contents")

    def test_format_preserves_functionality(self):
        """Test that formatting preserves document functionality."""
        doc = LarkDocument("file:///test.lark", SIMPLE_GRAMMAR)

        # Format the document
        options = FormattingOptions(
            tab_size=4, insert_spaces=True, insert_final_newline=True
        )
        formatted = doc.format(options)

        # Create new document with formatted content
        new_doc = LarkDocument("file:///test_formatted.lark", formatted.new_text)

        # Should still be functional
        assert new_doc._parsed_tree is not None
        new_diagnostics = new_doc.get_diagnostics()
        new_symbols = new_doc.get_document_symbols()

        assert isinstance(new_diagnostics, list)
        assert isinstance(new_symbols, list)
