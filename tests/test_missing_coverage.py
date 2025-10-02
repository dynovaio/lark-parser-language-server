"""Tests to cover the remaining missing lines in server.py to achieve >95% coverage."""

from unittest.mock import Mock, patch

from lsprotocol.types import (
    Position,
    ReferenceContext,
    ReferenceParams,
    TextDocumentIdentifier,
    TextDocumentPositionParams,
)

from lark_parser_language_server.document import LarkDocument
from lark_parser_language_server.server import LarkLanguageServer

from .fixtures import VALID_GRAMMAR


class TestMissingCoverage:
    """Tests designed to cover the remaining missing lines in server.py."""

    server: LarkLanguageServer
    test_uri: str

    def setup_method(self):
        """Set up test fixtures."""
        self.server = LarkLanguageServer()
        self.test_uri = "file:///test.lark"

    def test_hover_info_unknown_symbol(self):
        """Test hover info when symbol is not a rule or terminal (line 358)."""
        # Create a document with known symbols
        document = LarkDocument(self.test_uri, VALID_GRAMMAR)

        # Mock get_symbol_at_position to return an unknown symbol
        with patch.object(
            document, "get_symbol_at_position", return_value="unknown_symbol"
        ):
            hover_result = document.get_hover_info(0, 0)

        # Should return None for unknown symbols (line 358: else: return None)
        assert hover_result is None

    def test_definition_handler_no_symbol_found(self):
        """Test definition handler when no symbol is found at position (line 442)."""
        # Add document to server
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, VALID_GRAMMAR
        )

        # Mock get_symbol_at_position to return None (no symbol found)
        with patch.object(
            self.server.documents[self.test_uri],
            "get_symbol_at_position",
            return_value=None,
        ):
            # Get the definition handler directly
            feature_handlers = {}

            def mock_feature(feature_name):
                def decorator(func):
                    feature_handlers[feature_name] = func
                    return func

                return decorator

            # Patch the feature decorator and re-setup features
            with patch.object(self.server, "feature", side_effect=mock_feature):
                self.server._setup_features()

            # Test the definition handler
            definition_handler = feature_handlers["textDocument/definition"]
            params = TextDocumentPositionParams(
                text_document=TextDocumentIdentifier(uri=self.test_uri),
                position=Position(line=0, character=0),
            )

            result = definition_handler(params)

        # Should return None when no symbol is found (line 442)
        assert result is None

    def test_references_handler_with_include_declaration_and_definition(self):
        """Test references handler with include_declaration=True and definition found (lines 459-463)."""
        # Add document to server
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, VALID_GRAMMAR
        )

        # Mock methods to control the test flow
        mock_locations = [Mock(), Mock()]  # Some reference locations
        mock_definition = Mock()  # A definition location

        with (
            patch.object(
                self.server.documents[self.test_uri],
                "get_symbol_at_position",
                return_value="start",
            ),
            patch.object(
                self.server.documents[self.test_uri],
                "get_references",
                return_value=mock_locations,
            ),
            patch.object(
                self.server.documents[self.test_uri],
                "get_definition_location",
                return_value=mock_definition,
            ),
        ):

            # Get the references handler directly
            feature_handlers = {}

            def mock_feature(feature_name):
                def decorator(func):
                    feature_handlers[feature_name] = func
                    return func

                return decorator

            # Patch the feature decorator and re-setup features
            with patch.object(self.server, "feature", side_effect=mock_feature):
                self.server._setup_features()

            # Test the references handler with include_declaration=True
            references_handler = feature_handlers["textDocument/references"]
            params = ReferenceParams(
                text_document=TextDocumentIdentifier(uri=self.test_uri),
                position=Position(line=0, character=0),
                context=ReferenceContext(include_declaration=True),
            )

            result = references_handler(params)

        # Should return locations with definition at the beginning (lines 459-463)
        assert result is not None
        assert len(result) == 3  # 2 references + 1 definition
        assert result[0] == mock_definition  # Definition should be first

    def test_references_handler_with_include_declaration_no_definition(self):
        """Test references handler with include_declaration=True but no definition found."""
        # Add document to server
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, VALID_GRAMMAR
        )

        # Mock methods to control the test flow
        mock_locations = [Mock(), Mock()]  # Some reference locations

        with (
            patch.object(
                self.server.documents[self.test_uri],
                "get_symbol_at_position",
                return_value="start",
            ),
            patch.object(
                self.server.documents[self.test_uri],
                "get_references",
                return_value=mock_locations,
            ),
            patch.object(
                self.server.documents[self.test_uri],
                "get_definition_location",
                return_value=None,
            ),
        ):

            # Get the references handler directly
            feature_handlers = {}

            def mock_feature(feature_name):
                def decorator(func):
                    feature_handlers[feature_name] = func
                    return func

                return decorator

            # Patch the feature decorator and re-setup features
            with patch.object(self.server, "feature", side_effect=mock_feature):
                self.server._setup_features()

            # Test the references handler with include_declaration=True
            references_handler = feature_handlers["textDocument/references"]
            params = ReferenceParams(
                text_document=TextDocumentIdentifier(uri=self.test_uri),
                position=Position(line=0, character=0),
                context=ReferenceContext(include_declaration=True),
            )

            result = references_handler(params)

        # Should return only the references without adding definition (since definition is None)
        assert result is not None
        assert len(result) == 2  # Only the 2 references
        assert result == mock_locations

    def test_references_handler_no_symbol_found(self):
        """Test references handler when no symbol is found at position (line 465)."""
        # Add document to server
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, VALID_GRAMMAR
        )

        # Mock get_symbol_at_position to return None (no symbol found)
        with patch.object(
            self.server.documents[self.test_uri],
            "get_symbol_at_position",
            return_value=None,
        ):
            # Get the references handler directly
            feature_handlers = {}

            def mock_feature(feature_name):
                def decorator(func):
                    feature_handlers[feature_name] = func
                    return func

                return decorator

            # Patch the feature decorator and re-setup features
            with patch.object(self.server, "feature", side_effect=mock_feature):
                self.server._setup_features()

            # Test the references handler
            references_handler = feature_handlers["textDocument/references"]
            params = ReferenceParams(
                text_document=TextDocumentIdentifier(uri=self.test_uri),
                position=Position(line=0, character=0),
                context=ReferenceContext(include_declaration=False),
            )

            result = references_handler(params)

        # Should return empty list when no symbol is found (line 465)
        assert result == []

    def test_didchange_handler_without_content_changes(self):
        """Test didChange handler when content_changes is empty or has no text attribute."""
        # Add document to server
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, VALID_GRAMMAR
        )

        # Mock a change without text attribute
        class MockChangeWithoutText:
            def __init__(self):
                pass  # No text attribute

        # Get the handlers directly
        feature_handlers = {}

        def mock_feature(feature_name):
            def decorator(func):
                feature_handlers[feature_name] = func
                return func

            return decorator

        # Patch the feature decorator and re-setup features
        with patch.object(self.server, "feature", side_effect=mock_feature):
            self.server._setup_features()

        # Create mock params with changes that don't have text
        from lsprotocol.types import (  # pylint: disable=import-outside-toplevel
            DidChangeTextDocumentParams,
            VersionedTextDocumentIdentifier,
        )

        mock_change = MockChangeWithoutText()
        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri=self.test_uri, version=1),
            content_changes=[mock_change],
        )

        # Test the didChange handler - should not crash
        did_change_handler = feature_handlers["textDocument/didChange"]

        # Store original document for comparison
        original_doc = self.server.documents[self.test_uri]

        # Execute the handler
        did_change_handler(params)

        # Document should remain unchanged since the change has no text
        assert self.server.documents[self.test_uri] == original_doc
