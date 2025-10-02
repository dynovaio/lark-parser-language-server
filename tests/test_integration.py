"""Integration tests for LarkLanguageServer."""

from lark_parser_language_server.document import LarkDocument
from lark_parser_language_server.server import LarkLanguageServer

from .fixtures import INVALID_GRAMMAR, SIMPLE_GRAMMAR, VALID_GRAMMAR


class TestLarkLanguageServerIntegration:
    """Integration tests for LarkLanguageServer."""

    server: LarkLanguageServer
    test_uri: str

    def setup_method(self):
        """Set up test fixtures."""
        self.server = LarkLanguageServer()
        self.test_uri = "file:///test.lark"

    def test_full_document_lifecycle(self, mocker):
        """Test complete document lifecycle: create -> use -> delete."""
        # Mock publish_diagnostics
        mock_publish = mocker.patch.object(self.server, "publish_diagnostics")

        # 1. Create document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, SIMPLE_GRAMMAR
        )
        self.server._publish_diagnostics(self.test_uri)

        assert self.test_uri in self.server.documents
        assert mock_publish.call_count >= 1

        # 2. Change document content
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, VALID_GRAMMAR
        )
        self.server._publish_diagnostics(self.test_uri)

        assert self.server.documents[self.test_uri].source == VALID_GRAMMAR

        # 3. Use document features
        doc = self.server.documents[self.test_uri]
        completions = doc.get_completions(0, 0)
        assert len(completions) > 0

        # 4. Remove document
        del self.server.documents[self.test_uri]
        assert self.test_uri not in self.server.documents

    def test_multiple_documents(self, mocker):
        """Test handling multiple documents simultaneously."""
        _ = mocker.patch.object(self.server, "publish_diagnostics")

        # Create multiple documents
        uri1 = "file:///test1.lark"
        uri2 = "file:///test2.lark"

        self.server.documents[uri1] = LarkDocument(uri1, SIMPLE_GRAMMAR)
        self.server.documents[uri2] = LarkDocument(uri2, VALID_GRAMMAR)

        # Both documents should be tracked
        assert uri1 in self.server.documents
        assert uri2 in self.server.documents

        # Features should work for both
        doc1 = self.server.documents[uri1]
        doc2 = self.server.documents[uri2]

        completions1 = doc1.get_completions(0, 0)
        completions2 = doc2.get_completions(0, 0)

        assert len(completions1) > 0
        assert len(completions2) > 0

    def test_error_recovery(self, mocker):
        """Test server recovers from document with errors."""
        _ = mocker.patch.object(self.server, "publish_diagnostics")

        # Create document with errors
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, INVALID_GRAMMAR
        )

        # Document should still be tracked
        assert self.test_uri in self.server.documents

        # Should have diagnostics
        doc = self.server.documents[self.test_uri]
        diagnostics = doc.get_diagnostics()
        assert len(diagnostics) > 0

        # Features should still work
        completions = doc.get_completions(0, 0)
        assert len(completions) > 0  # Should still provide keyword completions

    def test_concurrent_access_simulation(self):
        """Test simulated concurrent access to documents."""
        # Simulate multiple operations on the same document
        doc_content = VALID_GRAMMAR

        # Add document (simulating one operation)
        self.server.documents[self.test_uri] = LarkDocument(self.test_uri, doc_content)

        # Perform multiple operations (simulating concurrent access)
        doc = self.server.documents[self.test_uri]

        # All operations should work without interference
        completions = doc.get_completions(1, 0)
        _ = doc.get_hover_info(1, 0)
        _ = doc.get_definition_location("start")
        symbols = doc.get_document_symbols()

        assert isinstance(completions, list)
        assert isinstance(symbols, list)
        # hover_result and definition_result can be None

    def test_large_document_handling(self, mocker):
        """Test handling of large documents."""
        _ = mocker.patch.object(self.server, "publish_diagnostics")

        # Create a large grammar
        large_grammar_parts = [VALID_GRAMMAR]
        for i in range(50):  # Add many rules
            large_grammar_parts.append(f'rule_{i}: "test_{i}"')
            large_grammar_parts.append(f"TERMINAL_{i}: /term_{i}/")

        large_grammar = "\n".join(large_grammar_parts)

        # Create large document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, large_grammar
        )

        # Should handle large document
        assert self.test_uri in self.server.documents

        # Operations should still work
        doc = self.server.documents[self.test_uri]
        completions = doc.get_completions(0, 0)
        symbols = doc.get_document_symbols()

        assert len(completions) > 50  # Should have many completions
        assert len(symbols) > 50  # Should have many symbols

    def test_unicode_content_handling(self, mocker):
        """Test handling of documents with unicode content."""
        _ = mocker.patch.object(self.server, "publish_diagnostics")

        # Grammar with unicode content
        unicode_grammar = """
        // Grammar with unicode comments: 测试 🚀
        start: grüßung

        grüßung: "hëllö" NÄM€

        NÄM€: /[α-ωΑ-Ω]+/
        """

        # Create unicode document
        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, unicode_grammar
        )

        # Should handle unicode content
        assert self.test_uri in self.server.documents

        # Operations should work
        doc = self.server.documents[self.test_uri]
        completions = doc.get_completions(0, 0)
        assert len(completions) > 0

    def test_empty_and_whitespace_documents(self, mocker):
        """Test handling of empty and whitespace-only documents."""
        _ = mocker.patch.object(self.server, "publish_diagnostics")

        test_cases = [
            "",  # Empty
            "   ",  # Whitespace only
            "\n\n\n",  # Newlines only
            "   \n   \n   ",  # Mixed whitespace
        ]

        for i, content in enumerate(test_cases):
            uri = f"file:///test_{i}.lark"

            # Create document
            self.server.documents[uri] = LarkDocument(uri, content)

            # Should handle empty/whitespace content
            assert uri in self.server.documents

            # Features should still provide basic functionality
            doc = self.server.documents[uri]
            completions = doc.get_completions(0, 0)
            symbols = doc.get_document_symbols()

            # Should at least have keyword completions
            keyword_completions = [c for c in completions if c.detail == "Keyword"]
            assert len(keyword_completions) > 0
            assert isinstance(symbols, list)

    def test_server_diagnostics_integration(self, mocker):
        """Test integration of diagnostics publishing."""
        mock_base_publish = mocker.patch(
            "pygls.server.LanguageServer.publish_diagnostics"
        )

        # Create document with various types of issues
        problematic_grammar = """
        start: undefined_rule

        rule_with_undefined_terminal: UNDEFINED_TERMINAL

        valid_rule: "hello"
        """

        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, problematic_grammar
        )

        # Publish diagnostics
        self.server._publish_diagnostics(self.test_uri)

        # Should have called the base publish method
        mock_base_publish.assert_called_once()

        # Check that diagnostics were published
        args = mock_base_publish.call_args[0]
        assert args[0] == self.test_uri
        diagnostics = args[1]
        assert isinstance(diagnostics, list)
        assert len(diagnostics) > 0  # Should have undefined reference diagnostics

    def test_features_with_real_grammar(self):
        """Test all features with a realistic grammar."""
        realistic_grammar = """
        // Calculator grammar
        start: sum

        ?sum: product
            | sum "+" product   -> add
            | sum "-" product   -> sub

        ?product: atom
                | product "*" atom  -> mul
                | product "/" atom  -> div

        ?atom: NUMBER
             | "-" atom         -> neg
             | "(" sum ")"

        %import common.NUMBER
        %import common.WS_INLINE
        %ignore WS_INLINE
        """

        self.server.documents[self.test_uri] = LarkDocument(
            self.test_uri, realistic_grammar
        )
        doc = self.server.documents[self.test_uri]

        # Test all features
        completions = doc.get_completions(5, 0)
        symbols = doc.get_document_symbols()

        # Test hover on different symbols
        _ = doc.get_hover_info(2, 0)  # "start" rule

        # Test definition lookup
        _ = doc.get_definition_location("sum")

        # Test references
        refs_number = doc.get_references("NUMBER")

        # Verify results
        assert len(completions) > 0
        assert len(symbols) > 0
        assert isinstance(refs_number, list)

        # Should have rules and terminals in symbols
        rule_symbols = [s for s in symbols if s.kind.name == "Function"]
        _ = [s for s in symbols if s.kind.name == "Constant"]
        assert len(rule_symbols) > 0
