"""Tests for LarkLanguageServer class."""

import pytest

from lark_parser_language_server.server import LarkDocument, LarkLanguageServer

from .fixtures import SIMPLE_GRAMMAR, VALID_GRAMMAR


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
        assert self.server.name == "lark-language-server"
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
        assert server.name == "lark-language-server"
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
        assert len(doc._rules) > 10
        assert len(doc._terminals) > 0
