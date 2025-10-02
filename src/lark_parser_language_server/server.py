import logging
from typing import Dict, List, Optional

from lsprotocol.types import (
    CompletionList,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentSymbol,
    DocumentSymbolParams,
    Hover,
    HoverParams,
    Location,
    ReferenceParams,
    TextDocumentPositionParams,
)
from pygls.server import LanguageServer

from .document import LarkDocument
from .version import __version__

logger = logging.getLogger(__name__)


class LarkLanguageServer(LanguageServer):
    """Language Server for Lark grammar files."""

    def __init__(self) -> None:
        super().__init__(
            "lark-parser-language-server",
            __version__,
        )
        self.documents: Dict[str, LarkDocument] = {}
        self._setup_features()

    def _setup_features(self) -> None:  # pylint: disable=too-complex

        @self.feature("textDocument/didOpen")
        def did_open(params: DidOpenTextDocumentParams) -> None:
            """Handle document open."""
            document = params.text_document
            self.documents[document.uri] = LarkDocument(document.uri, document.text)
            self._publish_diagnostics(document.uri)

        @self.feature("textDocument/didChange")
        def did_change(params: DidChangeTextDocumentParams) -> None:
            """Handle document changes."""
            uri = params.text_document.uri
            if uri in self.documents:
                # For now, we handle full document changes
                for change in params.content_changes:
                    if hasattr(change, "text"):  # Full document change
                        self.documents[uri] = LarkDocument(uri, change.text)
                        self._publish_diagnostics(uri)

        @self.feature("textDocument/didClose")
        def did_close(params: DidCloseTextDocumentParams) -> None:
            """Handle document close."""
            uri = params.text_document.uri
            if uri in self.documents:
                del self.documents[uri]

        @self.feature("textDocument/completion")
        def completion(params: CompletionParams) -> CompletionList:
            """Provide completion suggestions."""
            uri = params.text_document.uri
            if uri not in self.documents:
                return CompletionList(is_incomplete=False, items=[])

            document = self.documents[uri]
            position = params.position
            items = document.get_completions(position.line, position.character)

            return CompletionList(is_incomplete=False, items=items)

        @self.feature("textDocument/hover")
        def hover(params: HoverParams) -> Optional[Hover]:
            """Provide hover information."""
            uri = params.text_document.uri
            if uri not in self.documents:
                return None

            document = self.documents[uri]
            position = params.position
            return document.get_hover_info(position.line, position.character)

        @self.feature("textDocument/definition")
        def definition(params: TextDocumentPositionParams) -> Optional[Location]:
            """Go to definition."""
            uri = params.text_document.uri
            if uri not in self.documents:
                return None

            document = self.documents[uri]
            position = params.position
            symbol = document.get_symbol_at_position(position.line, position.character)

            if symbol:
                return document.get_definition_location(symbol)
            return None

        @self.feature("textDocument/references")
        def references(params: ReferenceParams) -> List[Location]:
            """Find references."""
            uri = params.text_document.uri
            if uri not in self.documents:
                return []

            document = self.documents[uri]
            position = params.position
            symbol = document.get_symbol_at_position(position.line, position.character)

            if symbol:
                locations = document.get_references(symbol)
                # Include definition if requested
                if params.context.include_declaration:
                    definition_loc = document.get_definition_location(symbol)
                    if definition_loc:
                        locations.insert(0, definition_loc)
                return locations
            return []

        @self.feature("textDocument/documentSymbol")
        def document_symbol(params: DocumentSymbolParams) -> List[DocumentSymbol]:
            """Provide document symbols for outline view."""
            uri = params.text_document.uri
            if uri not in self.documents:
                return []

            document = self.documents[uri]
            return document.get_document_symbols()

    def _publish_diagnostics(self, uri: str) -> None:
        """Publish diagnostics for a document."""
        if uri in self.documents:
            diagnostics = self.documents[uri].get_diagnostics()
            self.publish_diagnostics(uri, diagnostics)
