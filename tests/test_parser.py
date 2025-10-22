"""Tests for lark_parser_language_server/parser.py module."""

from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

import pytest
from lark import Lark

from lark_parser_language_server.parser import PARSER, _get_parser


class TestParser:
    """Test module-level functions and variables in parser.py."""

    original_cache: Optional[Lark]

    def setup_method(self):
        """Reset the parser cache before each test."""
        # Store original cache value if it exists
        self.original_cache = getattr(_get_parser, "cache", None)

    def teardown_method(self):
        """Restore the original cache after each test."""
        if hasattr(self, "original_cache") and self.original_cache is not None:
            setattr(_get_parser, "cache", self.original_cache)
        elif hasattr(_get_parser, "cache"):
            delattr(_get_parser, "cache")

    def test_get_parser_returns_lark_instance(self):
        """Test that _get_parser returns a Lark parser instance."""
        # Clear cache to force fresh creation
        if hasattr(_get_parser, "cache"):
            delattr(_get_parser, "cache")
        parser = _get_parser()
        assert isinstance(parser, Lark)

    def test_get_parser_caches_result(self):
        """Test that _get_parser caches the parser instance."""
        # Clear any existing cache first
        if hasattr(_get_parser, "cache"):
            delattr(_get_parser, "cache")

        parser1 = _get_parser()
        parser2 = _get_parser()

        # Should return the same cached instance
        assert parser1 is parser2

    def test_get_parser_with_cached_instance(self):
        """Test that _get_parser returns cached instance when available."""
        # Clear existing cache first
        if hasattr(_get_parser, "cache"):
            delattr(_get_parser, "cache")

        # Create a mock parser and set it as cache
        mock_parser = Mock(spec=Lark)
        setattr(_get_parser, "cache", mock_parser)

        result = _get_parser()
        assert result is mock_parser

    @patch("lark_parser_language_server.parser.Lark")
    @patch("lark_parser_language_server.parser.Path")
    def test_get_parser_creates_lark_with_correct_params(self, mock_path, mock_lark):
        """Test that _get_parser creates Lark with correct parameters."""
        # Clear cache to force creation
        if hasattr(_get_parser, "cache"):
            delattr(_get_parser, "cache")

        # Mock the grammar file path and content
        mock_grammar_file = Mock()
        mock_grammar_file.read_text.return_value = "test_grammar_content"

        mock_path_instance = Mock()
        mock_path_instance.parent = Mock()
        mock_path_instance.parent.__truediv__ = Mock(return_value=Mock())
        mock_path_instance.parent.__truediv__.return_value.__truediv__ = Mock(
            return_value=mock_grammar_file
        )

        mock_path.return_value = mock_path_instance

        mock_lark_instance = Mock(spec=Lark)
        mock_lark.return_value = mock_lark_instance

        # Call _get_parser
        _get_parser()

        # Verify Lark was called with correct parameters
        mock_lark.assert_called_once_with(
            "test_grammar_content",
            parser="lalr",
            lexer="basic",
            propagate_positions=True,
            maybe_placeholders=False,
            start="start",
            source_path=str(mock_grammar_file),
        )

    def test_parser_global_variable_is_lark_instance(self):
        """Test that PARSER global variable is a Lark parser instance."""
        assert isinstance(PARSER, Lark)

    def test_parser_global_variable_is_cached_parser(self):
        """Test that PARSER global variable comes from the cached result."""
        # This test verifies that PARSER is created from _get_parser
        # but we can't test identity since PARSER is set at module import time
        assert isinstance(PARSER, Lark)
        # Verify that _get_parser() now returns the same cached instance as PARSER
        current_parser = _get_parser()
        assert current_parser is PARSER

    @patch("lark_parser_language_server.parser.Path")
    def test_get_parser_reads_correct_grammar_file(self, mock_path):
        """Test that _get_parser reads the correct grammar file."""
        # Clear cache to force file reading
        if hasattr(_get_parser, "cache"):
            delattr(_get_parser, "cache")

        # Mock the Path behavior
        mock_file = Mock()
        mock_file.read_text.return_value = "test_grammar"

        mock_grammars_dir = Mock()
        mock_grammars_dir.__truediv__ = Mock(return_value=mock_file)

        mock_parent = Mock()
        mock_parent.__truediv__ = Mock(return_value=mock_grammars_dir)

        mock_path_instance = Mock()
        mock_path_instance.parent = mock_parent

        mock_path.return_value = mock_path_instance

        # Call _get_parser to trigger file reading
        with patch("lark_parser_language_server.parser.Lark") as mock_lark:
            _get_parser()

        # Verify the correct file path was constructed
        mock_parent.__truediv__.assert_called_once_with("grammars")
        mock_grammars_dir.__truediv__.assert_called_once_with("lark4ls.lark")
        mock_file.read_text.assert_called_once_with(encoding="utf-8")

    def test_get_parser_sets_cache_attribute(self):
        """Test that _get_parser sets the cache attribute on itself."""
        # Clear any existing cache
        if hasattr(_get_parser, "cache"):
            delattr(_get_parser, "cache")

        parser = _get_parser()

        # Verify cache attribute is set
        assert hasattr(_get_parser, "cache")
        assert getattr(_get_parser, "cache") is parser

    @patch("lark_parser_language_server.parser.Path")
    def test_get_parser_handles_file_path_correctly(self, mock_path):
        """Test that _get_parser handles file path construction correctly."""
        # Clear cache
        if hasattr(_get_parser, "cache"):
            delattr(_get_parser, "cache")

        # Mock the file structure
        mock_grammar_file = Mock()
        mock_grammar_file.read_text.return_value = "grammar content"

        # Mock __file__ path behavior
        mock_path.return_value.parent = (
            Path(__file__).parent.parent / "src" / "lark_parser_language_server"
        )

        with patch("lark_parser_language_server.parser.Lark") as mock_lark:
            with patch.object(Path, "read_text", return_value="grammar content"):
                _get_parser()

        # Verify Lark was called with the grammar content
        assert mock_lark.called
        args, _ = mock_lark.call_args
        assert args[0] == "grammar content"
