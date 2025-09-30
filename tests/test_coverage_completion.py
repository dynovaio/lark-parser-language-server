"""Tests to achieve >90% coverage for server.py by testing LSP features directly."""

from unittest.mock import Mock, patch

from lsprotocol.types import (
    CompletionParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentSymbolParams,
    HoverParams,
    Position,
    ReferenceContext,
    ReferenceParams,
    TextDocumentItem,
    TextDocumentPositionParams,
)

from lark_parser_language_server.server import LarkDocument, LarkLanguageServer

from .fixtures import MIXED_GRAMMAR, SIMPLE_GRAMMAR, VALID_GRAMMAR


class MockContentChange:
    """Mock content change for testing."""

    def __init__(self, text=None):
        if text is not None:
            self.text = text


class TestLarkLanguageServerCoverage:
    """Tests designed to achieve high coverage of server.py."""

    server: LarkLanguageServer
    test_uri: str

    def setup_method(self):
        """Set up test fixtures."""
        self.server = LarkLanguageServer()
        self.test_uri = "file:///test.lark"

    def test_feature_handlers_directly(self, mocker):
        """Test feature handlers by invoking them directly."""
        # Mock publish_diagnostics
        mock_publish = mocker.patch.object(self.server, "publish_diagnostics")

        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            # Re-run setup_features to capture handlers
            self.server._setup_features()

        # Test didOpen handler
        did_open = feature_handlers["textDocument/didOpen"]
        text_document = TextDocumentItem(
            uri=self.test_uri, language_id="lark", version=1, text=SIMPLE_GRAMMAR
        )
        params = DidOpenTextDocumentParams(text_document=text_document)
        did_open(params)

        assert self.test_uri in self.server.documents
        # SIMPLE_GRAMMAR actually has undefined references, so it has diagnostics
        mock_publish.assert_called_once()
        args, _ = mock_publish.call_args
        assert args[0] == self.test_uri
        assert isinstance(args[1], list)  # diagnostics list

    def test_didchange_handler_with_text(self, mocker):
        """Test didChange handler with text changes."""
        _ = mocker.patch.object(self.server, "publish_diagnostics")

        # First add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test didChange handler with text
        did_change = feature_handlers["textDocument/didChange"]

        # Create change with text attribute
        change_with_text = MockContentChange(text=VALID_GRAMMAR)

        params = DidChangeTextDocumentParams(
            text_document=Mock(uri=self.test_uri),
            content_changes=[change_with_text],
        )

        did_change(params)

        # Document should be updated
        assert self.server.documents[self.test_uri].source == VALID_GRAMMAR

    def test_didchange_handler_without_text(self, mocker):
        """Test didChange handler with changes without text attribute."""
        _ = mocker.patch.object(self.server, "publish_diagnostics")

        # First add a document
        original_source = SIMPLE_GRAMMAR
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, original_source
        )

        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test didChange handler without text
        did_change = feature_handlers["textDocument/didChange"]

        # Create change without text attribute
        change_without_text = MockContentChange()  # No text attribute

        params = DidChangeTextDocumentParams(
            text_document=Mock(uri=self.test_uri),
            content_changes=[change_without_text],
        )

        did_change(params)

        # Document should remain unchanged
        assert self.server.documents[self.test_uri].source == original_source

    def test_didclose_handler(self):
        """Test didClose handler."""
        # First add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test didClose handler
        did_close = feature_handlers["textDocument/didClose"]

        params = DidCloseTextDocumentParams(text_document=Mock(uri=self.test_uri))

        did_close(params)

        # Document should be removed
        assert self.test_uri not in self.server.documents

    def test_completion_handler(self):
        """Test completion handler."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, MIXED_GRAMMAR
        )

        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test completion handler
        completion = feature_handlers["textDocument/completion"]

        params = CompletionParams(
            text_document=Mock(uri=self.test_uri),
            position=Position(line=0, character=0),
        )

        result = completion(params)

        assert result.is_incomplete is False
        assert len(result.items) > 0

    def test_completion_handler_no_document(self):
        """Test completion handler with non-existent document."""
        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test completion handler
        completion = feature_handlers["textDocument/completion"]

        params = CompletionParams(
            text_document=Mock(uri="file:///nonexistent.lark"),
            position=Position(line=0, character=0),
        )

        result = completion(params)

        assert result.is_incomplete is False
        assert len(result.items) == 0

    def test_hover_handler(self):
        """Test hover handler."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test hover handler
        hover = feature_handlers["textDocument/hover"]

        params = HoverParams(
            text_document=Mock(uri=self.test_uri),
            position=Position(
                line=2, character=0
            ),  # Position where "greeting" might be
        )

        result = hover(params)
        # Result might be None if no symbol at position
        assert result is not None

    def test_hover_handler_no_document(self):
        """Test hover handler with non-existent document."""
        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test hover handler
        hover = feature_handlers["textDocument/hover"]

        params = HoverParams(
            text_document=Mock(uri="file:///nonexistent.lark"),
            position=Position(line=0, character=0),
        )

        result = hover(params)

        assert result is None

    def test_definition_handler(self):
        """Test definition handler."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test definition handler
        definition = feature_handlers["textDocument/definition"]

        params = TextDocumentPositionParams(
            text_document=Mock(uri=self.test_uri),
            position=Position(line=2, character=0),
        )

        result = definition(params)
        # Result might be None if no symbol at position
        assert result is not None

    def test_definition_handler_no_document(self):
        """Test definition handler with non-existent document."""
        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test definition handler
        definition = feature_handlers["textDocument/definition"]

        params = TextDocumentPositionParams(
            text_document=Mock(uri="file:///nonexistent.lark"),
            position=Position(line=0, character=0),
        )

        result = definition(params)

        assert result is None

    def test_references_handler(self):
        """Test references handler."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, VALID_GRAMMAR
        )

        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test references handler
        references = feature_handlers["textDocument/references"]

        params = ReferenceParams(
            text_document=Mock(uri=self.test_uri),
            position=Position(line=10, character=0),
            context=ReferenceContext(include_declaration=True),
        )

        result = references(params)

        assert isinstance(result, list)

    def test_references_handler_no_document(self):
        """Test references handler with non-existent document."""
        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test references handler
        references = feature_handlers["textDocument/references"]

        params = ReferenceParams(
            text_document=Mock(uri="file:///nonexistent.lark"),
            position=Position(line=0, character=0),
            context=ReferenceContext(include_declaration=True),
        )

        result = references(params)

        assert result == []

    def test_document_symbol_handler(self):
        """Test document symbol handler."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, MIXED_GRAMMAR
        )

        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test document symbol handler
        doc_symbol = feature_handlers["textDocument/documentSymbol"]

        params = DocumentSymbolParams(text_document=Mock(uri=self.test_uri))

        result = doc_symbol(params)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_document_symbol_handler_no_document(self):
        """Test document symbol handler with non-existent document."""
        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test document symbol handler
        doc_symbol = feature_handlers["textDocument/documentSymbol"]

        params = DocumentSymbolParams(
            text_document=Mock(uri="file:///nonexistent.lark")
        )

        result = doc_symbol(params)

        assert result == []

    def test_references_with_include_declaration(self):
        """Test references handler with include_declaration=True."""
        # Add a document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test references handler
        references = feature_handlers["textDocument/references"]

        params = ReferenceParams(
            text_document=Mock(uri=self.test_uri),
            position=Position(line=2, character=0),  # Position of greeting
            context=ReferenceContext(include_declaration=True),
        )

        result = references(params)

        assert isinstance(result, list)

    def test_didchange_handler_document_not_in_documents(self):
        """Test didChange handler when document not in documents."""
        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test didChange handler without document in documents
        did_change = feature_handlers["textDocument/didChange"]

        change_with_text = MockContentChange(text=VALID_GRAMMAR)

        params = DidChangeTextDocumentParams(
            text_document=Mock(uri="file:///nonexistent.lark"),
            content_changes=[change_with_text],
        )

        # Should not crash
        did_change(params)

        # Document should not be added
        assert "file:///nonexistent.lark" not in self.server.documents

    def test_didclose_handler_document_not_in_documents(self):
        """Test didClose handler when document not in documents."""
        # Create a mock feature decorator to capture handlers
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator temporarily
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Test didClose handler without document in documents
        did_close = feature_handlers["textDocument/didClose"]

        params = DidCloseTextDocumentParams(
            text_document=Mock(uri="file:///nonexistent.lark")
        )

        # Should not crash
        did_close(params)

        # No effect expected
        assert len(self.server.documents) == 0
