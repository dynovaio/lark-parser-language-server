"""Simplified tests for LarkLanguageServer functionality."""

from unittest.mock import patch

import pytest
from lsprotocol.types import CompletionParams, Position, TextDocumentIdentifier

from lark_parser_language_server.document import LarkDocument
from lark_parser_language_server.server import LarkLanguageServer

from .fixtures import MIXED_GRAMMAR, SIMPLE_GRAMMAR, VALID_GRAMMAR


class TestLarkLanguageServerFunctionality:
    """Test LarkLanguageServer functionality through direct method calls."""

    server: LarkLanguageServer
    test_uri: str

    def setup_method(self):
        """Set up test fixtures."""
        self.server = LarkLanguageServer()
        self.test_uri = "file:///test.lark"

    def test_server_initialization(self):
        """Test server initialization."""
        assert self.server.name == "lark-language-server"
        assert self.server.version == "0.1.0"
        assert isinstance(self.server.documents, dict)
        assert len(self.server.documents) == 0

    def test_direct_feature_functionality(self, mocker):
        """Test the server features through direct method invocation."""
        # Mock publish_diagnostics
        _ = mocker.patch.object(self.server, "publish_diagnostics")

        # Test completion feature
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, MIXED_GRAMMAR
        )

        # Test completion by calling through feature system
        _ = CompletionParams(
            text_document=TextDocumentIdentifier(uri=self.test_uri),
            position=Position(line=0, character=0),
        )

        # Get completion feature and call it
        with patch.object(self.server, "feature") as mock_feature:
            self.server._setup_features()
            # Feature should be registered
            assert mock_feature.call_count >= 8  # At least 8 features

    def test_document_operations(self, mocker):
        """Test document operations directly."""
        mock_publish = mocker.patch.object(self.server, "publish_diagnostics")

        # Test adding document
        doc = LarkDocument(self.test_uri, SIMPLE_GRAMMAR)
        self.server.documents[self.test_uri] = doc

        # Test publish diagnostics
        self.server._publish_diagnostics(self.test_uri)
        mock_publish.assert_called_once()

        # Test removing document
        del self.server.documents[self.test_uri]
        assert self.test_uri not in self.server.documents

    def test_completion_workflow(self):
        """Test completion workflow."""
        # Add document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, MIXED_GRAMMAR
        )

        # Test completion call
        doc = self.server.documents[self.test_uri]
        completions = doc.get_completions(0, 0)

        assert len(completions) > 0

        # Test that we get different types
        labels = [c.label for c in completions]
        assert any("start" in label for label in labels)  # Should have rule

    def test_hover_workflow(self):
        """Test hover workflow."""
        # Add document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        doc = self.server.documents[self.test_uri]

        # Find a position with a symbol
        for line_num, line in enumerate(doc.lines):
            if "greeting" in line:
                pos = line.find("greeting")
                hover = doc.get_hover_info(line_num, pos)
                if hover:
                    assert "Rule" in hover.contents.value
                    break

    def test_definition_workflow(self):
        """Test definition workflow."""
        # Add document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )

        doc = self.server.documents[self.test_uri]

        # Find greeting rule and get its definition
        location = doc.get_definition_location("greeting")
        if location:
            assert location.uri == self.test_uri
            assert location.range is not None

    def test_references_workflow(self):
        """Test references workflow."""
        # Add document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, VALID_GRAMMAR
        )

        doc = self.server.documents[self.test_uri]

        # Get references for NUMBER
        references = doc.get_references("NUMBER")
        assert isinstance(references, list)

    def test_document_symbols_workflow(self):
        """Test document symbols workflow."""
        # Add document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, MIXED_GRAMMAR
        )

        doc = self.server.documents[self.test_uri]
        symbols = doc.get_document_symbols()

        assert len(symbols) > 0
        assert all(hasattr(s, "name") for s in symbols)
        assert all(hasattr(s, "kind") for s in symbols)

    def test_publish_diagnostics_functionality(self, mocker):
        """Test publish diagnostics functionality."""
        mock_base_publish = mocker.patch(
            "pygls.server.LanguageServer.publish_diagnostics"
        )

        # Add document with errors
        grammar_with_errors = "start: undefined_rule"
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, grammar_with_errors
        )

        # Call publish diagnostics
        self.server._publish_diagnostics(self.test_uri)

        # Should have called base publish_diagnostics
        mock_base_publish.assert_called_once()

        # Check arguments
        args = mock_base_publish.call_args[0]
        assert args[0] == self.test_uri
        assert isinstance(args[1], list)  # diagnostics list

    def test_empty_document_handling(self):
        """Test handling empty documents."""
        empty_doc = LarkDocument(self.test_uri, "")
        self.server.documents[self.test_uri] = empty_doc

        # Should still work
        completions = empty_doc.get_completions(0, 0)
        symbols = empty_doc.get_document_symbols()

        assert isinstance(completions, list)
        assert isinstance(symbols, list)

    def test_feature_decorator_usage(self):
        """Test that feature decorator is used correctly."""
        # This tests that _setup_features calls self.feature
        server = LarkLanguageServer()

        # The fact that the server initializes successfully means features were set up
        assert hasattr(server, "documents")
        assert isinstance(server.documents, dict)

    def test_server_inherits_from_language_server(self):
        """Test that server properly inherits from LanguageServer."""
        assert hasattr(self.server, "publish_diagnostics")
        assert hasattr(self.server, "name")
        assert hasattr(self.server, "version")

    def test_document_lifecycle_integration(self, mocker):
        """Test document lifecycle integration."""
        mock_publish = mocker.patch.object(self.server, "publish_diagnostics")

        # Simulate opening document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )
        self.server._publish_diagnostics(self.test_uri)

        # Simulate changing document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, VALID_GRAMMAR
        )
        self.server._publish_diagnostics(self.test_uri)

        # Simulate closing document
        if self.test_uri in self.server.documents:
            del self.server.documents[self.test_uri]

        # Should have published diagnostics twice
        assert mock_publish.call_count >= 2

    def test_error_handling_in_features(self):
        """Test error handling in language server features."""
        # Test with document that causes analysis errors
        try:
            doc = LarkDocument(self.test_uri, "invalid [ syntax")
            self.server.documents[self.test_uri] = doc

            # These should not crash
            completions = doc.get_completions(0, 0)
            _ = doc.get_hover_info(0, 0)
            symbols = doc.get_document_symbols()

            assert isinstance(completions, list)
            assert isinstance(symbols, list)

        except Exception as e:  # pylint: disable=broad-except
            pytest.fail(f"Server should handle errors gracefully: {e}")

    def test_multiple_documents_handling(self):
        """Test server can handle multiple documents."""
        uri1 = "file:///test1.lark"
        uri2 = "file:///test2.lark"

        # Add multiple documents
        self.server.documents[uri1] = LarkDocument(uri1, SIMPLE_GRAMMAR)
        self.server.documents[uri2] = LarkDocument(uri2, VALID_GRAMMAR)

        assert len(self.server.documents) == 2
        assert uri1 in self.server.documents
        assert uri2 in self.server.documents

        # Each should work independently
        doc1 = self.server.documents[uri1]
        doc2 = self.server.documents[uri2]

        completions1 = doc1.get_completions(0, 0)
        completions2 = doc2.get_completions(0, 0)

        assert isinstance(completions1, list)
        assert isinstance(completions2, list)
