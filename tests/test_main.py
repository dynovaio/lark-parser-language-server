import argparse
import logging
import sys
from unittest.mock import Mock, patch

import lark_parser_language_server.__main__ as main_module
from lark_parser_language_server.__main__ import add_arguments, main


class TestAddArguments:
    """Test the add_arguments function."""

    def test_add_arguments_basic(self):
        """Test that add_arguments adds expected arguments to parser."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        # Test that description is set
        assert parser.description == "Lark Language Server"

        # Parse empty args to get defaults
        args = parser.parse_args([])

        # Test default values
        assert args.stdio is False
        assert args.tcp is False
        assert args.ws is False
        assert args.host == "127.0.0.1"
        assert args.port == 2087
        assert args.log_level == "INFO"

    def test_add_arguments_stdio_flag(self):
        """Test --stdio argument."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        args = parser.parse_args(["--stdio"])
        assert args.stdio is True

    def test_add_arguments_tcp_flag(self):
        """Test --tcp argument."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        args = parser.parse_args(["--tcp"])
        assert args.tcp is True

    def test_add_arguments_ws_flag(self):
        """Test --ws argument."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        args = parser.parse_args(["--ws"])
        assert args.ws is True

    def test_add_arguments_host_custom(self):
        """Test custom --host argument."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        args = parser.parse_args(["--host", "0.0.0.0"])  # nosec
        assert args.host == "0.0.0.0"  # nosec

    def test_add_arguments_port_custom(self):
        """Test custom --port argument."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        args = parser.parse_args(["--port", "8080"])
        assert args.port == 8080

    def test_add_arguments_log_level_debug(self):
        """Test --log-level DEBUG."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        args = parser.parse_args(["--log-level", "DEBUG"])
        assert args.log_level == "DEBUG"

    def test_add_arguments_log_level_error(self):
        """Test --log-level ERROR."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        args = parser.parse_args(["--log-level", "ERROR"])
        assert args.log_level == "ERROR"

    def test_add_arguments_log_level_critical(self):
        """Test --log-level CRITICAL."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        args = parser.parse_args(["--log-level", "CRITICAL"])
        assert args.log_level == "CRITICAL"

    def test_add_arguments_log_level_warning(self):
        """Test --log-level WARNING."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        args = parser.parse_args(["--log-level", "WARNING"])
        assert args.log_level == "WARNING"

    def test_add_arguments_combined_flags(self):
        """Test multiple arguments combined."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        args = parser.parse_args(
            ["--tcp", "--host", "192.168.1.1", "--port", "9999", "--log-level", "DEBUG"]
        )
        assert args.tcp is True
        assert args.host == "192.168.1.1"
        assert args.port == 9999
        assert args.log_level == "DEBUG"


class TestMainFunction:
    """Test the main function."""

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("logging.basicConfig")
    def test_main_default_stdio(self, mock_logging, mock_parse_args, mock_server_class):
        """Test main function with default (stdio) configuration."""
        # Setup mocks
        mock_args = Mock()
        mock_args.log_level = "INFO"
        mock_args.tcp = False
        mock_args.ws = False
        mock_args.host = "127.0.0.1"
        mock_args.port = 2087
        mock_parse_args.return_value = mock_args

        mock_server = Mock()
        mock_server_class.return_value = mock_server

        # Call main
        main()

        # Verify logging was configured
        mock_logging.assert_called_once_with(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr,
        )

        # Verify server was created and started with stdio
        mock_server_class.assert_called_once()
        mock_server.start_io.assert_called_once()
        mock_server.start_tcp.assert_not_called()
        mock_server.start_ws.assert_not_called()

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("logging.basicConfig")
    def test_main_tcp_mode(self, mock_logging, mock_parse_args, mock_server_class):
        """Test main function with TCP mode."""
        # Setup mocks
        mock_args = Mock()
        mock_args.log_level = "DEBUG"
        mock_args.tcp = True
        mock_args.ws = False
        mock_args.host = "0.0.0.0"  # nosec
        mock_args.port = 8080
        mock_parse_args.return_value = mock_args

        mock_server = Mock()
        mock_server_class.return_value = mock_server

        # Call main
        main()

        # Verify logging was configured with DEBUG level
        mock_logging.assert_called_once_with(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr,
        )

        # Verify server was started with TCP
        mock_server_class.assert_called_once()
        mock_server.start_tcp.assert_called_once_with("0.0.0.0", 8080)  # nosec
        mock_server.start_io.assert_not_called()
        mock_server.start_ws.assert_not_called()

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("logging.basicConfig")
    def test_main_websocket_mode(
        self, mock_logging, mock_parse_args, mock_server_class
    ):
        """Test main function with WebSocket mode."""
        # Setup mocks
        mock_args = Mock()
        mock_args.log_level = "ERROR"
        mock_args.tcp = False
        mock_args.ws = True
        mock_args.host = "localhost"
        mock_args.port = 3000
        mock_parse_args.return_value = mock_args

        mock_server = Mock()
        mock_server_class.return_value = mock_server

        # Call main
        main()

        # Verify logging was configured with ERROR level
        mock_logging.assert_called_once_with(
            level=logging.ERROR,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr,
        )

        # Verify server was started with WebSocket
        mock_server_class.assert_called_once()
        mock_server.start_ws.assert_called_once_with("localhost", 3000)
        mock_server.start_io.assert_not_called()
        mock_server.start_tcp.assert_not_called()

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("logging.basicConfig")
    def test_main_stdio_explicit(
        self, mock_logging, mock_parse_args, mock_server_class
    ):
        """Test main function with explicit stdio flag."""
        # Setup mocks
        mock_args = Mock()
        mock_args.log_level = "WARNING"
        mock_args.tcp = False
        mock_args.ws = False
        mock_args.stdio = True  # Explicitly set stdio
        mock_args.host = "127.0.0.1"
        mock_args.port = 2087
        mock_parse_args.return_value = mock_args

        mock_server = Mock()
        mock_server_class.return_value = mock_server

        # Call main
        main()

        # Verify logging was configured with WARNING level
        mock_logging.assert_called_once_with(
            level=logging.WARNING,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr,
        )

        # Verify server was started with stdio (default case)
        mock_server_class.assert_called_once()
        mock_server.start_io.assert_called_once()
        mock_server.start_tcp.assert_not_called()
        mock_server.start_ws.assert_not_called()

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("logging.basicConfig")
    def test_main_critical_log_level(
        self, mock_logging, mock_parse_args, mock_server_class
    ):
        """Test main function with CRITICAL log level."""
        # Setup mocks
        mock_args = Mock()
        mock_args.log_level = "CRITICAL"
        mock_args.tcp = False
        mock_args.ws = False
        mock_args.host = "127.0.0.1"
        mock_args.port = 2087
        mock_parse_args.return_value = mock_args

        mock_server = Mock()
        mock_server_class.return_value = mock_server

        # Call main
        main()

        # Verify logging was configured with CRITICAL level
        mock_logging.assert_called_once_with(
            level=logging.CRITICAL,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            stream=sys.stderr,
        )

        # Verify server was started
        mock_server_class.assert_called_once()
        mock_server.start_io.assert_called_once()

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("logging.basicConfig")
    def test_main_tcp_and_ws_both_false_defaults_to_stdio(
        self, _, mock_parse_args, mock_server_class
    ):
        """Test that when both TCP and WS are False, it defaults to stdio."""
        # Setup mocks
        mock_args = Mock()
        mock_args.log_level = "INFO"
        mock_args.tcp = False
        mock_args.ws = False
        mock_args.host = "127.0.0.1"
        mock_args.port = 2087
        mock_parse_args.return_value = mock_args

        mock_server = Mock()
        mock_server_class.return_value = mock_server

        # Call main
        main()

        # Verify server defaults to stdio
        mock_server.start_io.assert_called_once()
        mock_server.start_tcp.assert_not_called()
        mock_server.start_ws.assert_not_called()


class TestMain:
    """Tests for the main module additional functionality."""

    def test_import_main_module(self):
        """Test that the main module can be imported."""
        # Should have the expected functions
        assert hasattr(main_module, "add_arguments")
        assert hasattr(main_module, "main")

    def test_add_arguments_with_parser(self):
        """Test add_arguments function with a real parser."""
        # Create a real argument parser
        parser = argparse.ArgumentParser()

        # Call add_arguments
        add_arguments(parser)

        # Should have added multiple arguments - test by parsing some sample args
        args = parser.parse_args(["--stdio"])
        assert args.stdio is True
        assert args.tcp is False

        args = parser.parse_args(
            ["--tcp", "--host", "0.0.0.0", "--port", "9999"]  # nosec
        )
        assert args.tcp is True
        assert args.host == "0.0.0.0"  # nosec
        assert args.port == 9999

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_function_stdio(self, mock_parse_args, mock_server_class):
        """Test main function with stdio mode."""
        # Mock the parsed arguments
        mock_parse_args.return_value = argparse.Namespace(
            stdio=True,
            tcp=False,
            ws=False,
            host="localhost",
            port=8888,
            log_level="INFO",
        )

        # Mock the server instance
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.start_io = Mock()

        main()

        # Verify server was created and started
        mock_server_class.assert_called_once()
        mock_server.start_io.assert_called_once()

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_function_tcp(self, mock_parse_args, mock_server_class):
        """Test main function with TCP mode."""
        # Mock the parsed arguments
        mock_parse_args.return_value = argparse.Namespace(
            stdio=False,
            tcp=True,
            ws=False,
            host="localhost",
            port=8888,
            log_level="INFO",
        )

        # Mock the server instance
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.start_tcp = Mock()

        main()

        # Verify server was started with TCP
        mock_server.start_tcp.assert_called_once_with("localhost", 8888)

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_function_websocket(self, mock_parse_args, mock_server_class):
        """Test main function with WebSocket mode."""
        # Mock the parsed arguments
        mock_parse_args.return_value = argparse.Namespace(
            stdio=False,
            tcp=False,
            ws=True,
            host="localhost",
            port=8888,
            log_level="INFO",
        )

        # Mock the server instance
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.start_ws = Mock()

        main()

        # Verify server was started with WebSockets
        mock_server.start_ws.assert_called_once_with("localhost", 8888)

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_function_default_stdio(self, mock_parse_args, mock_server_class):
        """Test main function defaults to stdio when no mode specified."""
        # Mock the parsed arguments - when all modes are False, should default to stdio
        mock_parse_args.return_value = argparse.Namespace(
            stdio=False,
            tcp=False,
            ws=False,
            host="localhost",
            port=8888,
            log_level="INFO",
        )

        # Mock the server instance
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.start_io = Mock()

        main()

        # Should default to stdio
        mock_server.start_io.assert_called_once()

    @patch("lark_parser_language_server.__main__.LarkLanguageServer")
    @patch("lark_parser_language_server.__main__.logging")
    @patch("argparse.ArgumentParser.parse_args")
    def test_logging_configuration(
        self, mock_parse_args, mock_logging, mock_server_class
    ):
        """Test that logging is configured."""

        # Mock the parsed arguments
        mock_parse_args.return_value = argparse.Namespace(
            stdio=True,
            tcp=False,
            ws=False,
            host="localhost",
            port=8888,
            log_level="DEBUG",
        )

        # Mock the server
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.start_io = Mock()

        main()

        # Should have configured logging
        mock_logging.basicConfig.assert_called_once()
        # Verify DEBUG level was set correctly
        call_args = mock_logging.basicConfig.call_args
        assert "level" in call_args[1]

    def test_argument_parser_choices(self):
        """Test that argument parser has correct choices for log level."""
        parser = argparse.ArgumentParser()
        add_arguments(parser)

        # Test valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            args = parser.parse_args(["--log-level", level])
            assert args.log_level == level

        # Test default values
        args = parser.parse_args([])
        assert args.stdio is False  # Not explicitly set
        assert args.tcp is False
        assert args.ws is False
        assert args.host == "127.0.0.1"
        assert args.port == 2087
        assert args.log_level == "INFO"
