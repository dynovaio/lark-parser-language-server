import argparse
import logging
import sys

from lark_parser_language_server.server import LarkLanguageServer


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Add command-line arguments."""
    parser.description = "Lark Language Server"

    parser.add_argument(
        "--stdio", action="store_true", help="Use stdio for communication (default)"
    )
    parser.add_argument(
        "--tcp", action="store_true", help="Use TCP server instead of stdio"
    )
    parser.add_argument(
        "--ws", action="store_true", help="Use WebSocket server instead of stdio"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind to this address")
    parser.add_argument("--port", type=int, default=2087, help="Bind to this port")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    server = LarkLanguageServer()

    if args.tcp:
        server.start_tcp(args.host, args.port)
    elif args.ws:
        server.start_ws(args.host, args.port)
    else:
        # Default to stdio (whether --stdio is specified or not)
        server.start_io()


if __name__ == "__main__":  # pragma: no cover
    main()
