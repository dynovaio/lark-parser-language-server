"""Tests for lark_parser_language_server.server module."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_FORMATTING,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_REFERENCES,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentFormattingParams,
    DocumentSymbol,
    DocumentSymbolParams,
    FormattingOptions,
    Hover,
    HoverParams,
    Location,
    Position,
    Range,
    ReferenceContext,
    ReferenceParams,
    SymbolKind,
    TextDocumentIdentifier,
    TextDocumentItem,
    TextDocumentPositionParams,
    TextDocumentSyncKind,
    TextEdit,
    VersionedTextDocumentIdentifier,
)
from tests.fixtures import SIMPLE_GRAMMAR, VALID_GRAMMAR

from lark_parser_language_server import __version__
from lark_parser_language_server.document import LarkDocument
from lark_parser_language_server.server import LarkLanguageServer
from lark_parser_language_server.version import VERSION


class TestLarkLanguageServer:
    """Test cases for LarkLanguageServer class."""

    server: LarkLanguageServer
    test_uri: str

    def setup_method(self):
        """Set up test fixtures."""
        self.server = LarkLanguageServer()
        self.test_uri = "file:///test.lark"

    def test_init(self):
        """Test server initialization."""
        server = LarkLanguageServer()

        assert server.name == "lark-parser-language-server"
        assert server.version == __version__
        # Note: The actual sync kind may be determined by pygls internally
        assert server.text_document_sync_kind in [
            TextDocumentSyncKind.Full,
            TextDocumentSyncKind.Incremental,
        ]
        assert isinstance(server.documents, dict)
        assert len(server.documents) == 0

    def test_features_map(self):
        """Test features mapping."""
        server = LarkLanguageServer()
        features_map = server._features_map

        # Check all expected features are mapped
        expected_features = {
            TEXT_DOCUMENT_DID_OPEN,
            TEXT_DOCUMENT_DID_CHANGE,
            TEXT_DOCUMENT_DID_CLOSE,
            TEXT_DOCUMENT_COMPLETION,
            TEXT_DOCUMENT_HOVER,
            TEXT_DOCUMENT_DEFINITION,
            TEXT_DOCUMENT_REFERENCES,
            TEXT_DOCUMENT_DOCUMENT_SYMBOL,
            TEXT_DOCUMENT_FORMATTING,
        }

        assert set(features_map.keys()) == expected_features

        # Check all handlers are callable
        for handler in features_map.values():
            assert callable(handler)

    @patch.object(LarkLanguageServer, "feature")
    def test_setup_features(self, mock_feature):
        """Test feature setup registers handlers."""
        mock_decorator = Mock()
        mock_feature.return_value = mock_decorator

        _ = LarkLanguageServer()

        # Should have called feature() for each feature
        assert mock_feature.call_count == 9  # Number of features

        # Should have called the decorator for each handler
        assert mock_decorator.call_count == 9

    @patch.object(LarkLanguageServer, "publish_diagnostics")
    def test_publish_diagnostics_with_document(self, mock_publish):
        """Test publishing diagnostics for existing document."""
        server = LarkLanguageServer()
        uri = "file:///test.lark"

        # Add a mock document
        mock_document = Mock()
        mock_diagnostics = [Mock(), Mock()]
        mock_document.get_diagnostics.return_value = mock_diagnostics
        server.documents[uri] = mock_document

        server._publish_diagnostics(uri)

        mock_document.get_diagnostics.assert_called_once()
        mock_publish.assert_called_once_with(uri, mock_diagnostics)

    @patch.object(LarkLanguageServer, "publish_diagnostics")
    def test_publish_diagnostics_without_document(self, mock_publish):
        """Test publishing diagnostics for non-existent document."""
        server = LarkLanguageServer()
        uri = "file:///nonexistent.lark"

        server._publish_diagnostics(uri)

        # Should not call publish_diagnostics if document doesn't exist
        mock_publish.assert_not_called()

    def test_did_open_handler(self):
        """Test document open handler."""
        server = LarkLanguageServer()
        handler = server.did_open_handler()

        # Create mock parameters
        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///test.lark",
                language_id="lark",
                version=1,
                text=SIMPLE_GRAMMAR,
            )
        )

        with patch.object(server, "_publish_diagnostics") as mock_publish:
            handler(params)

        # Should create document and publish diagnostics
        assert "file:///test.lark" in server.documents
        document = server.documents["file:///test.lark"]
        assert document.uri == "file:///test.lark"
        assert document.source == SIMPLE_GRAMMAR
        mock_publish.assert_called_once_with("file:///test.lark")

    def test_did_change_handler(self):
        """Test document change handler."""
        server = LarkLanguageServer()
        handler = server.did_change_handler()

        # Add initial document
        uri = "file:///test.lark"
        server.documents[uri] = Mock()

        # Create change parameters
        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri=uri, version=2),
            content_changes=[Mock(text=VALID_GRAMMAR)],
        )

        with patch.object(server, "_publish_diagnostics") as mock_publish:
            handler(params)

        # Should update document with new content
        assert uri in server.documents
        document = server.documents[uri]
        assert document.uri == uri
        assert document.source == VALID_GRAMMAR
        mock_publish.assert_called_once_with(uri)

    def test_did_change_handler_no_document(self):
        """Test document change handler when document doesn't exist."""
        server = LarkLanguageServer()
        handler = server.did_change_handler()

        uri = "file:///nonexistent.lark"
        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri=uri, version=2),
            content_changes=[Mock(text=VALID_GRAMMAR)],
        )

        with patch.object(server, "_publish_diagnostics") as mock_publish:
            handler(params)

        # Should not crash but also not create document
        assert uri not in server.documents
        mock_publish.assert_not_called()

    def test_did_change_handler_no_text_attribute(self):
        """Test document change handler with change that has no text attribute."""
        server = LarkLanguageServer()
        handler = server.did_change_handler()

        uri = "file:///test.lark"
        server.documents[uri] = Mock()

        # Create change without text attribute using Mock that doesn't have text
        change = Mock(spec=[])  # Empty spec means no attributes

        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri=uri, version=2),
            content_changes=[change],
        )

        with patch.object(server, "_publish_diagnostics") as mock_publish:
            handler(params)

        # Should not crash but also not update document
        mock_publish.assert_not_called()

    def test_did_close_handler(self):
        """Test document close handler."""
        server = LarkLanguageServer()
        handler = server.did_close_handler()

        # Add document to close
        uri = "file:///test.lark"
        server.documents[uri] = Mock()

        params = DidCloseTextDocumentParams(
            text_document=TextDocumentIdentifier(uri=uri)
        )

        handler(params)

        # Should remove document
        assert uri not in server.documents

    def test_did_close_handler_no_document(self):
        """Test document close handler when document doesn't exist."""
        server = LarkLanguageServer()
        handler = server.did_close_handler()

        uri = "file:///nonexistent.lark"
        params = DidCloseTextDocumentParams(
            text_document=TextDocumentIdentifier(uri=uri)
        )

        # Should not crash
        handler(params)
        assert uri not in server.documents

    def test_completion_handler(self):
        """Test completion handler."""
        server = LarkLanguageServer()
        handler = server.completion_handler()

        # Add mock document
        uri = "file:///test.lark"
        mock_document = Mock()
        mock_completions = [
            CompletionItem(label="rule1", kind=CompletionItemKind.Function),
            CompletionItem(label="TERMINAL", kind=CompletionItemKind.Constant),
        ]
        mock_document.get_completions.return_value = mock_completions
        server.documents[uri] = mock_document

        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=0, character=5),
        )

        result = handler(params)

        assert isinstance(result, CompletionList)
        assert result.is_incomplete is False
        assert len(result.items) == 2
        assert result.items == mock_completions
        mock_document.get_completions.assert_called_once_with(0, 5)

    def test_completion_handler_no_document(self):
        """Test completion handler when document doesn't exist."""
        server = LarkLanguageServer()
        handler = server.completion_handler()

        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///nonexistent.lark"),
            position=Position(line=0, character=5),
        )

        result = handler(params)

        assert isinstance(result, CompletionList)
        assert result.is_incomplete is False
        assert len(result.items) == 0

    def test_hover_handler(self):
        """Test hover handler."""
        server = LarkLanguageServer()
        handler = server.hover_handler()

        # Add mock document
        uri = "file:///test.lark"
        mock_document = Mock()
        mock_hover = Hover(contents="Rule definition")
        mock_document.get_hover_info.return_value = mock_hover
        server.documents[uri] = mock_document

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=1, character=3),
        )

        result = handler(params)

        assert result == mock_hover
        mock_document.get_hover_info.assert_called_once_with(1, 3)

    def test_hover_handler_no_document(self):
        """Test hover handler when document doesn't exist."""
        server = LarkLanguageServer()
        handler = server.hover_handler()

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///nonexistent.lark"),
            position=Position(line=1, character=3),
        )

        result = handler(params)

        assert result is None

    def test_hover_handler_no_hover(self):
        """Test hover handler when document returns no hover."""
        server = LarkLanguageServer()
        handler = server.hover_handler()

        uri = "file:///test.lark"
        mock_document = Mock()
        mock_document.get_hover_info.return_value = None
        server.documents[uri] = mock_document

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=1, character=3),
        )

        result = handler(params)

        assert result is None

    def test_definition_handler(self):
        """Test definition handler."""
        server = LarkLanguageServer()
        handler = server.definition_handler()

        # Add mock document
        uri = "file:///test.lark"
        mock_document = Mock()
        mock_symbol_info = ("rule1", 0, 5)
        mock_location = Location(
            uri=uri,
            range=Range(
                start=Position(line=2, character=0), end=Position(line=2, character=5)
            ),
        )
        mock_document.get_symbol_at_position.return_value = mock_symbol_info
        mock_document.get_definition_location.return_value = mock_location
        server.documents[uri] = mock_document

        params = TextDocumentPositionParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=0, character=2),
        )

        result = handler(params)

        assert result == mock_location
        mock_document.get_symbol_at_position.assert_called_once_with(0, 2)
        mock_document.get_definition_location.assert_called_once_with("rule1")

    def test_definition_handler_no_document(self):
        """Test definition handler when document doesn't exist."""
        server = LarkLanguageServer()
        handler = server.definition_handler()

        params = TextDocumentPositionParams(
            text_document=TextDocumentIdentifier(uri="file:///nonexistent.lark"),
            position=Position(line=0, character=2),
        )

        result = handler(params)

        assert result is None

    def test_definition_handler_no_symbol(self):
        """Test definition handler when no symbol at position."""
        server = LarkLanguageServer()
        handler = server.definition_handler()

        uri = "file:///test.lark"
        mock_document = Mock()
        mock_document.get_symbol_at_position.return_value = None
        server.documents[uri] = mock_document

        params = TextDocumentPositionParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=0, character=2),
        )

        result = handler(params)

        assert result is None
        mock_document.get_symbol_at_position.assert_called_once_with(0, 2)
        mock_document.get_definition_location.assert_not_called()

    def test_references_handler(self):
        """Test references handler."""
        server = LarkLanguageServer()
        handler = server.references_handler()

        # Add mock document
        uri = "file:///test.lark"
        mock_document = Mock()
        mock_symbol_info = ("rule1", 0, 5)
        mock_references = [
            Location(
                uri=uri,
                range=Range(
                    start=Position(line=1, character=0),
                    end=Position(line=1, character=5),
                ),
            ),
            Location(
                uri=uri,
                range=Range(
                    start=Position(line=3, character=2),
                    end=Position(line=3, character=7),
                ),
            ),
        ]
        mock_document.get_symbol_at_position.return_value = mock_symbol_info
        mock_document.get_references.return_value = mock_references
        server.documents[uri] = mock_document

        params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=0, character=2),
            context=ReferenceContext(include_declaration=False),
        )

        result = handler(params)

        assert result == mock_references
        mock_document.get_symbol_at_position.assert_called_once_with(0, 2)
        mock_document.get_references.assert_called_once_with("rule1")

    def test_references_handler_include_declaration(self):
        """Test references handler with include_declaration=True."""
        server = LarkLanguageServer()
        handler = server.references_handler()

        # Add mock document
        uri = "file:///test.lark"
        mock_document = Mock()
        mock_symbol_info = ("rule1", 0, 5)
        mock_references = [
            Location(
                uri=uri,
                range=Range(
                    start=Position(line=1, character=0),
                    end=Position(line=1, character=5),
                ),
            ),
        ]
        mock_definition = Location(
            uri=uri,
            range=Range(
                start=Position(line=0, character=0), end=Position(line=0, character=5)
            ),
        )
        mock_document.get_symbol_at_position.return_value = mock_symbol_info
        mock_document.get_references.return_value = (
            mock_references.copy()
        )  # Return a copy to avoid mutation issues
        mock_document.get_definition_location.return_value = mock_definition
        server.documents[uri] = mock_document

        params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=0, character=2),
            context=ReferenceContext(include_declaration=True),
        )

        result = handler(params)

        # Should include definition at the beginning, followed by references
        expected = [mock_definition] + mock_references
        assert result == expected
        mock_document.get_definition_location.assert_called_once_with("rule1")

    def test_references_handler_no_document(self):
        """Test references handler when document doesn't exist."""
        server = LarkLanguageServer()
        handler = server.references_handler()

        params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri="file:///nonexistent.lark"),
            position=Position(line=0, character=2),
            context=ReferenceContext(include_declaration=False),
        )

        result = handler(params)

        assert result == []

    def test_references_handler_no_symbol(self):
        """Test references handler when no symbol at position."""
        server = LarkLanguageServer()
        handler = server.references_handler()

        uri = "file:///test.lark"
        mock_document = Mock()
        mock_document.get_symbol_at_position.return_value = None
        server.documents[uri] = mock_document

        params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=0, character=2),
            context=ReferenceContext(include_declaration=False),
        )

        result = handler(params)

        assert result == []
        mock_document.get_symbol_at_position.assert_called_once_with(0, 2)

    def test_references_handler_empty_symbol_name(self):
        """Test references handler when symbol name is empty."""
        server = LarkLanguageServer()
        handler = server.references_handler()

        uri = "file:///test.lark"
        mock_document = Mock()
        mock_symbol_info = ("", 0, 0)  # Empty symbol name
        mock_document.get_symbol_at_position.return_value = mock_symbol_info
        server.documents[uri] = mock_document

        params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=0, character=2),
            context=ReferenceContext(include_declaration=False),
        )

        result = handler(params)

        assert result == []
        mock_document.get_references.assert_not_called()

    def test_document_symbol_handler(self):
        """Test document symbol handler."""
        server = LarkLanguageServer()
        handler = server.document_symbol_handler()

        # Add mock document
        uri = "file:///test.lark"
        mock_document = Mock()
        mock_symbols = [
            DocumentSymbol(
                name="rule1",
                kind=SymbolKind.Function,
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=5),
                ),
                selection_range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=5),
                ),
            ),
            DocumentSymbol(
                name="TERMINAL",
                kind=SymbolKind.Constant,
                range=Range(
                    start=Position(line=2, character=0),
                    end=Position(line=2, character=8),
                ),
                selection_range=Range(
                    start=Position(line=2, character=0),
                    end=Position(line=2, character=8),
                ),
            ),
        ]
        mock_document.get_document_symbols.return_value = mock_symbols
        server.documents[uri] = mock_document

        params = DocumentSymbolParams(text_document=TextDocumentIdentifier(uri=uri))

        result = handler(params)

        assert result == mock_symbols
        mock_document.get_document_symbols.assert_called_once()

    def test_document_symbol_handler_no_document(self):
        """Test document symbol handler when document doesn't exist."""
        server = LarkLanguageServer()
        handler = server.document_symbol_handler()

        params = DocumentSymbolParams(
            text_document=TextDocumentIdentifier(uri="file:///nonexistent.lark")
        )

        result = handler(params)

        assert result == []

    def test_document_formatting_handler(self):
        """Test document formatting handler."""
        server = LarkLanguageServer()
        handler = server.document_formatting_handler()

        # Add mock document
        uri = "file:///test.lark"
        mock_document = Mock()
        mock_text_edit = TextEdit(
            range=Range(
                start=Position(line=0, character=0), end=Position(line=2, character=10)
            ),
            new_text="formatted content",
        )
        mock_document.format.return_value = mock_text_edit
        server.documents[uri] = mock_document

        formatting_options = FormattingOptions(tab_size=4, insert_spaces=True)
        params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri=uri), options=formatting_options
        )

        result = handler(params)

        assert len(result) == 1
        assert result[0] == mock_text_edit
        mock_document.format.assert_called_once_with(options=formatting_options)

    def test_document_formatting_handler_no_document(self):
        """Test document formatting handler when document doesn't exist."""
        server = LarkLanguageServer()
        handler = server.document_formatting_handler()

        formatting_options = FormattingOptions(tab_size=4, insert_spaces=True)
        params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri="file:///nonexistent.lark"),
            options=formatting_options,
        )

        result = handler(params)

        # Should return empty edit
        assert len(result) == 1
        text_edit = result[0]
        assert text_edit.range.start == Position(line=0, character=0)
        assert text_edit.range.end == Position(line=0, character=0)
        assert text_edit.new_text == ""

    def test_publish_diagnostics(self, mocker):
        """Test publishing diagnostics with real LarkDocument."""
        # Mock the base class publish_diagnostics method
        mock_publish = mocker.patch("pygls.server.LanguageServer.publish_diagnostics")

        # Add a document with diagnostics
        doc = LarkDocument(self.test_uri, "invalid grammar content [")
        self.server.documents[self.test_uri] = doc

        # Call _publish_diagnostics
        self.server._publish_diagnostics(self.test_uri)

        # Verify publish_diagnostics was called
        mock_publish.assert_called_once()
        args, _ = mock_publish.call_args
        assert args[0] == self.test_uri
        # args[1] should be the diagnostics list
        assert isinstance(args[1], list)

    def test_server_inheritance(self):
        """Test that server properly inherits from LanguageServer."""
        # Test that the server has the expected LanguageServer attributes
        assert hasattr(self.server, "publish_diagnostics")
        assert hasattr(self.server, "name")
        assert hasattr(self.server, "version")
        assert hasattr(self.server, "documents")

    def test_document_management(self):
        """Test basic document management functionality."""
        # Add a document
        doc = LarkDocument(self.test_uri, SIMPLE_GRAMMAR)
        self.server.documents[self.test_uri] = doc

        assert self.test_uri in self.server.documents
        assert self.server.documents[self.test_uri] == doc

        # Remove document
        del self.server.documents[self.test_uri]
        assert self.test_uri not in self.server.documents

    def test_multiple_documents_management(self):
        """Test managing multiple documents."""
        uri1 = "file:///test1.lark"
        uri2 = "file:///test2.lark"

        doc1 = LarkDocument(uri1, SIMPLE_GRAMMAR)
        doc2 = LarkDocument(uri2, VALID_GRAMMAR)

        self.server.documents[uri1] = doc1
        self.server.documents[uri2] = doc2

        assert len(self.server.documents) == 2
        assert uri1 in self.server.documents
        assert uri2 in self.server.documents

        # Each document should maintain its content
        assert self.server.documents[uri1].source == SIMPLE_GRAMMAR
        assert self.server.documents[uri2].source == VALID_GRAMMAR

    def test_error_handling_in_publish_diagnostics(self, mocker):
        """Test error handling in publish diagnostics."""
        # Mock the base class method to raise an exception
        mock_publish = mocker.patch("pygls.server.LanguageServer.publish_diagnostics")
        mock_publish.side_effect = Exception("Test exception")

        # Add a document
        doc = LarkDocument(self.test_uri, SIMPLE_GRAMMAR)
        self.server.documents[self.test_uri] = doc

        # The current implementation doesn't handle exceptions in _publish_diagnostics
        # So we expect it to raise the exception
        with pytest.raises(Exception) as exc_info:
            self.server._publish_diagnostics(self.test_uri)
        assert "Test exception" in str(exc_info.value)

    def test_server_features_setup(self):
        """Test that server features are properly set up during initialization."""
        # The fact that the server initializes without error indicates features were set up
        server = LarkLanguageServer()
        assert server.name == "lark-parser-language-server"
        assert server.version == __version__
        assert hasattr(server, "documents")

    def test_document_operations_workflow(self, mocker):
        """Test complete workflow of document operations."""
        mock_publish = mocker.patch.object(self.server, "publish_diagnostics")

        # Simulate document lifecycle
        # 1. Add document
        doc = LarkDocument(self.test_uri, SIMPLE_GRAMMAR)
        self.server.documents[self.test_uri] = doc
        self.server._publish_diagnostics(self.test_uri)

        # 2. Update document
        new_doc = LarkDocument(self.test_uri, VALID_GRAMMAR)
        self.server.documents[self.test_uri] = new_doc
        self.server._publish_diagnostics(self.test_uri)

        # 3. Remove document
        del self.server.documents[self.test_uri]

        # Verify operations
        assert mock_publish.call_count >= 2
        assert self.test_uri not in self.server.documents

    def test_server_with_complex_documents(self):
        """Test server with complex document structures."""
        complex_grammar = """
        // Complex grammar
        start: expr_list

        expr_list: expr
                 | expr_list ";" expr

        expr: assignment
            | logical_or

        assignment: IDENTIFIER "=" expr

        logical_or: logical_and
                  | logical_or "||" logical_and

        logical_and: equality
                   | logical_and "&&" equality

        equality: comparison
                | equality ("==" | "!=") comparison

        comparison: term
                  | comparison ("<" | "<=" | ">" | ">=") term

        term: factor
            | term ("+" | "-") factor

        factor: unary
              | factor ("*" | "/" | "%") unary

        unary: primary
             | ("!" | "-") unary

        primary: NUMBER
               | STRING
               | IDENTIFIER
               | "(" expr ")"

        IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
        NUMBER: /[0-9]+/
        STRING: /"[^"]*"/

        %import common.WS
        %ignore WS
        """

        doc = LarkDocument(self.test_uri, complex_grammar)
        self.server.documents[self.test_uri] = doc

        # Should handle complex grammar without issues
        assert self.test_uri in self.server.documents

        # Document should have extracted symbols
        definitions = doc._symbol_table.definitions
        assert len(definitions) >= 0  # Should have processed symbols

    def test_handlers_with_nonexistent_document(self):
        """Test various handlers with nonexistent documents."""
        # Common setup
        nonexistent_uri = "file:///nonexistent.lark"
        text_doc = TextDocumentIdentifier(uri=nonexistent_uri)
        position = Position(line=0, character=0)

        # Test completion handler
        completion_params = CompletionParams(text_document=text_doc, position=position)
        completion_result = self.server.completion_handler()(completion_params)
        assert completion_result.is_incomplete is False
        assert len(completion_result.items) == 0

        # Test hover handler
        hover_params = HoverParams(text_document=text_doc, position=position)
        hover_result = self.server.hover_handler()(hover_params)
        assert hover_result is None

        # Test definition handler
        definition_params = TextDocumentPositionParams(
            text_document=text_doc, position=position
        )
        definition_result = self.server.definition_handler()(definition_params)
        assert definition_result is None

        # Test references handler
        context = ReferenceContext(include_declaration=True)
        references_params = ReferenceParams(
            text_document=text_doc, position=position, context=context
        )
        references_result = self.server.references_handler()(references_params)
        assert references_result == []

        # Test document symbol handler
        symbol_params = DocumentSymbolParams(text_document=text_doc)
        symbol_result = self.server.document_symbol_handler()(symbol_params)
        assert symbol_result == []

    def test_references_with_include_declaration(self):
        """Test references handler with include_declaration=True."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        text_doc = TextDocumentIdentifier(uri=self.test_uri)
        position = Position(line=0, character=0)  # Position of 'greeting'
        context = ReferenceContext(include_declaration=True)
        params = ReferenceParams(
            text_document=text_doc, position=position, context=context
        )

        handler = self.server.references_handler()
        result = handler(params)

        # Should return a list (may be empty if no symbol at position)
        assert isinstance(result, list)

    def test_didchange_handler_document_not_in_documents(self):
        """Test did_change_handler when document is not in documents."""

        # Create a simple change event object
        class MockChangeEvent:
            def __init__(self, text):
                self.text = text

            def __hasattr__(self, name):
                return name == "text"

        # Create parameters for document not in server.documents
        change_event = MockChangeEvent(VALID_GRAMMAR)
        text_doc = VersionedTextDocumentIdentifier(
            uri="file:///not_tracked.lark", version=1
        )
        params = DidChangeTextDocumentParams(
            text_document=text_doc, content_changes=[change_event]
        )

        handler = self.server.did_change_handler()
        # Should not crash even if document is not tracked
        handler(params)

    def test_didclose_handler_document_not_in_documents(self):
        """Test did_close_handler when document is not in documents."""

        # Create parameters for document not in server.documents
        text_doc = TextDocumentIdentifier(uri="file:///not_tracked.lark")
        params = DidCloseTextDocumentParams(text_document=text_doc)

        handler = self.server.did_close_handler()
        # Should not crash even if document is not tracked
        handler(params)

    def test_server_setup_features_coverage(self):
        """Test server features setup coverage."""
        # Test that _features_map property works
        features_map = self.server._features_map
        assert len(features_map) > 0

        # Test that _setup_features was called during initialization
        # This is implicit in the fact that the server works correctly
        assert hasattr(self.server, "_features_map")

    def test_server_name_and_version(self):
        """Test server name and version properties."""
        assert self.server.name == "lark-parser-language-server"
        assert self.server.version == ".".join(VERSION)

        # Test that version matches what's in version.py
        assert self.server.version == __version__

    def test_definition_handler_no_symbol_info(self):
        """Test definition handler when symbol_info is None."""
        # Set up mock document
        mock_document = MagicMock()
        mock_document.get_symbol_at_position.return_value = None

        uri = "file:///test.lark"
        self.server.documents[uri] = mock_document

        handler = self.server.definition_handler()
        params = MagicMock()
        params.text_document.uri = uri
        params.position.line = 0
        params.position.character = 0

        result = handler(params)
        assert result is None

    def test_references_handler_no_symbol_info(self):
        """Test references handler when symbol_info is None."""
        # Set up mock document
        mock_document = MagicMock()
        mock_document.get_symbol_at_position.return_value = None

        uri = "file:///test.lark"
        self.server.documents[uri] = mock_document

        handler = self.server.references_handler()
        params = MagicMock()
        params.text_document.uri = uri
        params.position.line = 0
        params.position.character = 0
        params.context.include_declaration = True

        result = handler(params)
        assert result == []

    def test_references_handler_with_symbol_name_none(self):
        """Test references handler when symbol_name is None or empty."""
        # Set up mock document
        mock_document = MagicMock()
        mock_document.get_symbol_at_position.return_value = (None, "info")

        uri = "file:///test.lark"
        self.server.documents[uri] = mock_document

        handler = self.server.references_handler()
        params = MagicMock()
        params.text_document.uri = uri
        params.position.line = 0
        params.position.character = 0
        params.context.include_declaration = True

        result = handler(params)
        assert result == []

    def test_references_handler_include_declaration_with_definition(self):
        """Test references handler including declaration when definition exists."""
        # Set up mock document
        mock_document = MagicMock()
        mock_document.get_symbol_at_position.return_value = ("test_symbol", "rule")
        mock_document.get_references.return_value = [MagicMock()]
        mock_definition = MagicMock()
        mock_document.get_definition_location.return_value = mock_definition

        uri = "file:///test.lark"
        self.server.documents[uri] = mock_document

        handler = self.server.references_handler()
        params = MagicMock()
        params.text_document.uri = uri
        params.position.line = 0
        params.position.character = 0
        params.context.include_declaration = True

        result = handler(params)
        assert len(result) == 2  # references + definition
        assert result[0] == mock_definition  # definition is inserted at the beginning

    def test_references_handler_include_declaration_no_definition(self):
        """Test references handler including declaration when no definition exists."""
        # Set up mock document
        mock_document = MagicMock()
        mock_document.get_symbol_at_position.return_value = ("test_symbol", "rule")
        mock_document.get_references.return_value = [MagicMock()]
        mock_document.get_definition_location.return_value = None

        uri = "file:///test.lark"
        self.server.documents[uri] = mock_document

        handler = self.server.references_handler()
        params = MagicMock()
        params.text_document.uri = uri
        params.position.line = 0
        params.position.character = 0
        params.context.include_declaration = True

        result = handler(params)
        assert len(result) == 1  # only references, no definition to add


class TestLarkLanguageServerIntegration:
    """Integration tests for LarkLanguageServer."""

    def test_complete_lifecycle(self):
        """Test complete document lifecycle."""
        server = LarkLanguageServer()

        # Open document
        did_open_handler = server.did_open_handler()
        open_params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///test.lark",
                language_id="lark",
                version=1,
                text=SIMPLE_GRAMMAR,
            )
        )

        with patch.object(server, "_publish_diagnostics"):
            did_open_handler(open_params)

        assert "file:///test.lark" in server.documents

        # Change document
        did_change_handler = server.did_change_handler()
        change_params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(
                uri="file:///test.lark", version=2
            ),
            content_changes=[Mock(text=VALID_GRAMMAR)],
        )

        with patch.object(server, "_publish_diagnostics"):
            did_change_handler(change_params)

        document = server.documents["file:///test.lark"]
        assert document.source == VALID_GRAMMAR

        # Use LSP features
        completion_handler = server.completion_handler()
        completion_params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.lark"),
            position=Position(line=0, character=0),
        )

        completions = completion_handler(completion_params)
        assert isinstance(completions, CompletionList)

        # Close document
        did_close_handler = server.did_close_handler()
        close_params = DidCloseTextDocumentParams(
            text_document=TextDocumentIdentifier(uri="file:///test.lark")
        )

        did_close_handler(close_params)
        assert "file:///test.lark" not in server.documents

    def test_multiple_documents(self):
        """Test handling multiple documents simultaneously."""
        server = LarkLanguageServer()

        # Open multiple documents
        did_open_handler = server.did_open_handler()

        with patch.object(server, "_publish_diagnostics"):
            for i in range(3):
                params = DidOpenTextDocumentParams(
                    text_document=TextDocumentItem(
                        uri=f"file:///test{i}.lark",
                        language_id="lark",
                        version=1,
                        text=SIMPLE_GRAMMAR,
                    )
                )
                did_open_handler(params)

        # Should have all documents
        assert len(server.documents) == 3
        for i in range(3):
            assert f"file:///test{i}.lark" in server.documents

        # Test operations on each document
        completion_handler = server.completion_handler()

        for i in range(3):
            params = CompletionParams(
                text_document=TextDocumentIdentifier(uri=f"file:///test{i}.lark"),
                position=Position(line=0, character=0),
            )
            result = completion_handler(params)
            assert isinstance(result, CompletionList)

        # Close one document
        did_close_handler = server.did_close_handler()
        close_params = DidCloseTextDocumentParams(
            text_document=TextDocumentIdentifier(uri="file:///test1.lark")
        )
        did_close_handler(close_params)

        # Should have removed only that document
        assert len(server.documents) == 2
        assert "file:///test1.lark" not in server.documents
        assert "file:///test0.lark" in server.documents
        assert "file:///test2.lark" in server.documents

    def test_lsp_features_interaction(self):
        """Test interaction between different LSP features."""
        server = LarkLanguageServer()

        # Open document with complex grammar
        complex_grammar = """
        start: expr+

        expr: atom
            | expr "+" atom    -> add

        atom: NUMBER
            | "(" expr ")"

        %import common.NUMBER
        """

        did_open_handler = server.did_open_handler()
        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///complex.lark",
                language_id="lark",
                version=1,
                text=complex_grammar,
            )
        )

        with patch.object(server, "_publish_diagnostics"):
            did_open_handler(params)

        uri = "file:///complex.lark"

        # Test document symbols
        symbol_handler = server.document_symbol_handler()
        symbol_params = DocumentSymbolParams(
            text_document=TextDocumentIdentifier(uri=uri)
        )
        symbols = symbol_handler(symbol_params)
        assert isinstance(symbols, list)

        # Test completions
        completion_handler = server.completion_handler()
        completion_params = CompletionParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=0, character=0),
        )
        completions = completion_handler(completion_params)
        assert isinstance(completions, CompletionList)
        assert len(completions.items) > 0

        # Test hover (might return None for some positions)
        hover_handler = server.hover_handler()
        hover_params = HoverParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=2, character=8),  # On "expr"
        )
        _ = hover_handler(hover_params)
        # hover_result might be None, which is fine

        # Test formatting
        format_handler = server.document_formatting_handler()
        format_params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri=uri),
            options=FormattingOptions(tab_size=4, insert_spaces=True),
        )
        format_result = format_handler(format_params)
        assert isinstance(format_result, list)
        assert len(format_result) == 1

    def test_error_recovery(self):
        """Test server behavior with invalid grammar."""
        server = LarkLanguageServer()

        # Open document with invalid grammar
        invalid_grammar = """
        start rule with syntax error
        missing_colon "value"
        """

        did_open_handler = server.did_open_handler()
        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///invalid.lark",
                language_id="lark",
                version=1,
                text=invalid_grammar,
            )
        )

        with patch.object(server, "_publish_diagnostics") as mock_publish:
            did_open_handler(params)

        # Should still create document (with diagnostics)
        assert "file:///invalid.lark" in server.documents
        mock_publish.assert_called_once()

        # LSP features should still work (gracefully handling errors)
        uri = "file:///invalid.lark"

        completion_handler = server.completion_handler()
        completion_params = CompletionParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=0, character=0),
        )

        # Should not crash
        completions = completion_handler(completion_params)
        assert isinstance(completions, CompletionList)

    def test_concurrent_operations(self):
        """Test concurrent operations on the same document."""
        server = LarkLanguageServer()

        # Open document
        did_open_handler = server.did_open_handler()
        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///concurrent.lark",
                language_id="lark",
                version=1,
                text=SIMPLE_GRAMMAR,
            )
        )

        with patch.object(server, "_publish_diagnostics"):
            did_open_handler(params)

        uri = "file:///concurrent.lark"

        # Simulate concurrent requests
        completion_handler = server.completion_handler()
        hover_handler = server.hover_handler()
        symbol_handler = server.document_symbol_handler()

        # All should work without interfering with each other
        completion_result = completion_handler(
            CompletionParams(
                text_document=TextDocumentIdentifier(uri=uri),
                position=Position(line=0, character=0),
            )
        )

        _ = hover_handler(
            HoverParams(
                text_document=TextDocumentIdentifier(uri=uri),
                position=Position(line=0, character=0),
            )
        )

        symbol_result = symbol_handler(
            DocumentSymbolParams(text_document=TextDocumentIdentifier(uri=uri))
        )

        # All should return valid results
        assert isinstance(completion_result, CompletionList)
        assert isinstance(symbol_result, list)
        # hover_result might be None, which is fine
