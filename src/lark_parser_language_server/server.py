import logging
from typing import Callable, Dict, List, Optional

from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_REFERENCES,
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

from lark_parser_language_server import __version__
from lark_parser_language_server.document import LarkDocument

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

    @property
    def _features_map(self) -> Dict[str, Callable]:
        """Return a mapping of LSP features to their handlers."""
        return {
            TEXT_DOCUMENT_DID_OPEN: self.did_open_handler(),
            TEXT_DOCUMENT_DID_CHANGE: self.did_change_handler(),
            TEXT_DOCUMENT_DID_CLOSE: self.did_close_handler(),
            TEXT_DOCUMENT_COMPLETION: self.completion_handler(),
            TEXT_DOCUMENT_HOVER: self.hover_handler(),
            TEXT_DOCUMENT_DEFINITION: self.definition_handler(),
            TEXT_DOCUMENT_REFERENCES: self.references_handler(),
            TEXT_DOCUMENT_DOCUMENT_SYMBOL: self.document_symbol_handler(),
        }

    def _setup_features(self) -> None:
        """Set up LSP features by registering their handlers."""
        for feature, handler in self._features_map.items():
            self.feature(feature)(handler)

    def _publish_diagnostics(self, uri: str) -> None:
        """Publish diagnostics for a document."""
        if uri in self.documents:
            diagnostics = self.documents[uri].get_diagnostics()
            self.publish_diagnostics(uri, diagnostics)

    def did_open_handler(self) -> Callable[[DidOpenTextDocumentParams], None]:
        def _did_open(params: DidOpenTextDocumentParams) -> None:
            """Handle document open."""
            document = params.text_document
            self.documents[document.uri] = LarkDocument(document.uri, document.text)
            self._publish_diagnostics(document.uri)

        return _did_open

    def did_change_handler(self) -> Callable[[DidChangeTextDocumentParams], None]:
        def _did_change(params: DidChangeTextDocumentParams) -> None:
            """Handle document changes."""
            uri = params.text_document.uri
            if uri in self.documents:
                # For now, we handle full document changes
                for change in params.content_changes:
                    print(f"Document changed: {uri}")
                    print(f"New content: {change.text}")

                    if hasattr(change, "text"):  # Full document change
                        self.documents[uri] = LarkDocument(uri, change.text)
                        self._publish_diagnostics(uri)

        return _did_change

    def did_close_handler(self) -> Callable[[DidCloseTextDocumentParams], None]:
        def _did_close(params: DidCloseTextDocumentParams) -> None:
            """Handle document close."""
            uri = params.text_document.uri
            if uri in self.documents:
                del self.documents[uri]

        return _did_close

    def completion_handler(
        self,
    ) -> Callable[[CompletionParams], CompletionList]:
        def _completion(params: CompletionParams) -> CompletionList:
            """Provide completion suggestions."""
            uri = params.text_document.uri
            if uri not in self.documents:
                return CompletionList(is_incomplete=False, items=[])

            document = self.documents[uri]
            position = params.position
            items = document.get_completions(position.line, position.character)

            return CompletionList(is_incomplete=False, items=items)

        return _completion

    def hover_handler(self) -> Callable[[HoverParams], Optional[Hover]]:
        def _hover(params: HoverParams) -> Optional[Hover]:
            """Provide hover information."""
            uri = params.text_document.uri
            if uri not in self.documents:
                return None

            document = self.documents[uri]
            position = params.position
            return document.get_hover_info(position.line, position.character)

        return _hover

    def definition_handler(
        self,
    ) -> Callable[[TextDocumentPositionParams], Optional[Location]]:
        def _definition(
            params: TextDocumentPositionParams,
        ) -> Optional[Location]:
            """Go to definition."""
            uri = params.text_document.uri
            if uri not in self.documents:
                return None

            document = self.documents[uri]
            position = params.position
            symbol_info = document.get_symbol_at_position(
                position.line, position.character
            )

            if not symbol_info:
                return None

            symbol_name, *_ = symbol_info

            return document.get_definition_location(symbol_name)

        return _definition

    def references_handler(self) -> Callable[[ReferenceParams], List[Location]]:
        def _references(params: ReferenceParams) -> List[Location]:
            """Find references."""
            uri = params.text_document.uri
            if uri not in self.documents:
                return []

            document = self.documents[uri]
            position = params.position
            symbol_info = document.get_symbol_at_position(
                position.line, position.character
            )

            if not symbol_info:
                return []

            symbol_name, *_ = symbol_info

            if symbol_name:
                locations = document.get_references(symbol_name)
                # Include definition if requested
                if params.context.include_declaration:
                    definition_loc = document.get_definition_location(symbol_name)
                    if definition_loc:
                        locations.insert(0, definition_loc)
                return locations
            return []

        return _references

    def document_symbol_handler(
        self,
    ) -> Callable[[DocumentSymbolParams], List[DocumentSymbol]]:
        def _document_symbol(
            params: DocumentSymbolParams,
        ) -> List[DocumentSymbol]:
            """Provide document symbols for outline view."""
            uri = params.text_document.uri
            if uri not in self.documents:
                return []

            document = self.documents[uri]
            return document.get_document_symbols()

        return _document_symbol
