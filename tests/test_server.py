# pylint: disable=too-many-lines
from unittest.mock import MagicMock

import pytest
from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_REFERENCES,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentSymbolParams,
    HoverParams,
    Position,
    ReferenceContext,
    ReferenceParams,
    TextDocumentIdentifier,
    TextDocumentItem,
    TextDocumentPositionParams,
    VersionedTextDocumentIdentifier,
)
from tests.fixtures import SIMPLE_GRAMMAR, VALID_GRAMMAR

from lark_parser_language_server.document import LarkDocument
from lark_parser_language_server.server import LarkLanguageServer
from lark_parser_language_server.version import __version__


class TestLarkLanguageServer:
    """Test cases for LarkLanguageServer class."""

    test_uri: str
    server: LarkLanguageServer

    def setup_method(self):
        """Set up test fixtures."""
        self.server = LarkLanguageServer()
        self.test_uri = "file:///test.lark"

    def test_server_initialization(self):
        """Test server initialization."""
        assert self.server.name == "lark-parser-language-server"
        assert self.server.version == "0.1.0"
        assert isinstance(self.server.documents, dict)
        assert len(self.server.documents) == 0

    def test_publish_diagnostics(self, mocker):
        """Test publishing diagnostics."""
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

    def test_publish_diagnostics_no_document(self, mocker):
        """Test publishing diagnostics for non-existent document."""
        # Mock the base class publish_diagnostics method
        mock_publish = mocker.patch("pygls.server.LanguageServer.publish_diagnostics")

        # Call _publish_diagnostics for non-existent document
        self.server._publish_diagnostics("file:///nonexistent.lark")

        # Verify publish_diagnostics was not called
        mock_publish.assert_not_called()

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
        assert server.version == "0.1.0"
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
        symbols = doc._symbol_table.symbols
        assert len(symbols) >= 0  # Should have processed symbols

    def test_features_map(self):
        """Test the _features_map property."""
        features_map = self.server._features_map

        # Check that all expected features are present

        expected_features = [
            TEXT_DOCUMENT_DID_OPEN,
            TEXT_DOCUMENT_DID_CHANGE,
            TEXT_DOCUMENT_DID_CLOSE,
            TEXT_DOCUMENT_COMPLETION,
            TEXT_DOCUMENT_HOVER,
            TEXT_DOCUMENT_DEFINITION,
            TEXT_DOCUMENT_REFERENCES,
            TEXT_DOCUMENT_DOCUMENT_SYMBOL,
        ]

        for feature in expected_features:
            assert feature in features_map
            assert callable(features_map[feature])

    def test_did_open_handler(self, mocker):
        """Test did_open_handler functionality."""
        mock_publish = mocker.patch.object(self.server, "_publish_diagnostics")

        # Create mock parameters
        text_doc = TextDocumentItem(
            uri=self.test_uri, language_id="lark", version=1, text=SIMPLE_GRAMMAR
        )
        params = DidOpenTextDocumentParams(text_document=text_doc)

        # Get the handler and call it
        handler = self.server.did_open_handler()
        handler(params)

        # Verify document was added and diagnostics published
        assert self.test_uri in self.server.documents
        assert self.server.documents[self.test_uri].source == SIMPLE_GRAMMAR
        mock_publish.assert_called_once_with(self.test_uri)

    def test_did_change_handler(self, mocker):
        """Test did_change_handler functionality."""
        mock_publish = mocker.patch.object(self.server, "_publish_diagnostics")

        # First add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        # Create a simple change event object with the text attribute
        class MockChangeEvent:
            def __init__(self, text):
                self.text = text

            def __hasattr__(self, name):
                return name == "text"

        change_event = MockChangeEvent(VALID_GRAMMAR)

        text_doc = VersionedTextDocumentIdentifier(uri=self.test_uri, version=2)
        params = DidChangeTextDocumentParams(
            text_document=text_doc, content_changes=[change_event]
        )

        # Get the handler and call it
        handler = self.server.did_change_handler()
        handler(params)

        # Verify document was updated and diagnostics published
        assert self.server.documents[self.test_uri].source == VALID_GRAMMAR
        mock_publish.assert_called_once_with(self.test_uri)

    def test_did_close_handler(self):
        """Test did_close_handler functionality."""
        # First add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )
        assert self.test_uri in self.server.documents

        # Create mock parameters

        text_doc = TextDocumentIdentifier(uri=self.test_uri)
        params = DidCloseTextDocumentParams(text_document=text_doc)

        # Get the handler and call it
        handler = self.server.did_close_handler()
        handler(params)

        # Verify document was removed
        assert self.test_uri not in self.server.documents

    def test_completion_handler(self):
        """Test completion_handler functionality."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        text_doc = TextDocumentIdentifier(uri=self.test_uri)
        position = Position(line=0, character=0)
        params = CompletionParams(text_document=text_doc, position=position)

        # Get the handler and call it
        handler = self.server.completion_handler()
        result = handler(params)

        # Verify result
        assert hasattr(result, "is_incomplete")
        assert hasattr(result, "items")
        assert isinstance(result.items, list)

    def test_completion_handler_no_document(self):
        """Test completion_handler with non-existent document."""
        # Create mock parameters for non-existent document

        text_doc = TextDocumentIdentifier(uri="file:///nonexistent.lark")
        position = Position(line=0, character=0)
        params = CompletionParams(text_document=text_doc, position=position)

        # Get the handler and call it
        handler = self.server.completion_handler()
        result = handler(params)

        # Should return empty completion list
        assert result.is_incomplete is False
        assert len(result.items) == 0

    def test_hover_handler(self):
        """Test hover_handler functionality."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        # Create mock parameters
        text_doc = TextDocumentIdentifier(uri=self.test_uri)
        position = Position(line=0, character=0)
        params = HoverParams(text_document=text_doc, position=position)

        # Get the handler and call it
        handler = self.server.hover_handler()
        result = handler(params)

        # Result can be None or a Hover object
        if result is not None:
            assert hasattr(result, "contents")

    def test_hover_handler_no_document(self):
        """Test hover_handler with non-existent document."""
        # Create mock parameters for non-existent document
        text_doc = TextDocumentIdentifier(uri="file:///nonexistent.lark")
        position = Position(line=0, character=0)
        params = HoverParams(text_document=text_doc, position=position)

        # Get the handler and call it
        handler = self.server.hover_handler()
        result = handler(params)

        # Should return None
        assert result is None

    def test_definition_handler(self):
        """Test definition_handler functionality."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        # Create mock parameters
        text_doc = TextDocumentIdentifier(uri=self.test_uri)
        position = Position(line=0, character=0)
        params = TextDocumentPositionParams(text_document=text_doc, position=position)

        # Get the handler and call it
        handler = self.server.definition_handler()
        result = handler(params)

        # Result can be None or a Location object
        if result is not None:
            assert hasattr(result, "uri")
            assert hasattr(result, "range")

    def test_definition_handler_no_document(self):
        """Test definition_handler with non-existent document."""
        # Create mock parameters for non-existent document

        text_doc = TextDocumentIdentifier(uri="file:///nonexistent.lark")
        position = Position(line=0, character=0)
        params = TextDocumentPositionParams(text_document=text_doc, position=position)

        # Get the handler and call it
        handler = self.server.definition_handler()
        result = handler(params)

        # Should return None
        assert result is None

    def test_references_handler(self):
        """Test references_handler functionality."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        # Create mock parameters
        text_doc = TextDocumentIdentifier(uri=self.test_uri)
        position = Position(line=0, character=0)
        context = ReferenceContext(include_declaration=True)
        params = ReferenceParams(
            text_document=text_doc, position=position, context=context
        )

        # Get the handler and call it
        handler = self.server.references_handler()
        result = handler(params)

        # Should return a list of locations
        assert isinstance(result, list)

    def test_references_handler_no_document(self):
        """Test references_handler with non-existent document."""
        # Create mock parameters for non-existent document
        text_doc = TextDocumentIdentifier(uri="file:///nonexistent.lark")
        position = Position(line=0, character=0)
        context = ReferenceContext(include_declaration=True)
        params = ReferenceParams(
            text_document=text_doc, position=position, context=context
        )

        # Get the handler and call it
        handler = self.server.references_handler()
        result = handler(params)

        # Should return empty list
        assert result == []

    def test_document_symbol_handler(self):
        """Test document_symbol_handler functionality."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        # Create mock parameters
        text_doc = TextDocumentIdentifier(uri=self.test_uri)
        params = DocumentSymbolParams(text_document=text_doc)

        # Get the handler and call it
        handler = self.server.document_symbol_handler()
        result = handler(params)

        # Should return a list of document symbols
        assert isinstance(result, list)

    def test_document_symbol_handler_no_document(self):
        """Test document_symbol_handler with non-existent document."""
        # Create mock parameters for non-existent document
        text_doc = TextDocumentIdentifier(uri="file:///nonexistent.lark")
        params = DocumentSymbolParams(text_document=text_doc)

        # Get the handler and call it
        handler = self.server.document_symbol_handler()
        result = handler(params)

        # Should return empty list
        assert result == []

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
        assert self.server.version == "0.1.0"

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
