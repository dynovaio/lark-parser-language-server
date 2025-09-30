"""Core Lark Language Server implementation."""

import logging
import re
from typing import Dict, List, Optional, Tuple

from lark import Lark, LarkError, Tree
from lark.exceptions import ParseError, UnexpectedCharacters, UnexpectedEOF
from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentSymbol,
    DocumentSymbolParams,
    Hover,
    HoverParams,
    Location,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
    ReferenceParams,
    SymbolKind,
    TextDocumentPositionParams,
)
from pygls.server import LanguageServer

logger = logging.getLogger(__name__)


class LarkDocument:
    def __init__(self, uri: str, source: str) -> None:
        self.uri = uri
        self.source = source
        self.lines = source.splitlines()
        self._parsed_tree: Optional[Tree] = None
        self._rules: Dict[str, Tuple[int, int]] = {}  # name -> (line, column)
        self._terminals: Dict[str, Tuple[int, int]] = {}  # name -> (line, column)
        self._imports: Dict[str, Tuple[int, int]] = {}  # name -> (line, column)
        self._references: Dict[str, List[Tuple[int, int]]] = (
            {}
        )  # name -> [(line, col), ...]
        self._diagnostics: List[Diagnostic] = []
        self._analyze()

    def _analyze(self) -> None:
        """Analyze the document for symbols, references, and diagnostics."""
        try:
            self._parse_grammar()
            self._extract_symbols()
            self._find_references()
            self._validate_references()
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Error analyzing document %s", self.uri)
            self._add_diagnostic(
                0, 0, f"Analysis error: {str(e)}", DiagnosticSeverity.Error
            )

    def _parse_grammar(self) -> None:
        """Parse the Lark grammar and extract basic structure."""
        try:
            # Try to parse with Lark's own grammar
            lark_parser = Lark.open_from_package(
                "lark", "grammars/lark.lark", parser="lalr"
            )
            self._parsed_tree = lark_parser.parse(self.source)
        except (ParseError, UnexpectedCharacters, UnexpectedEOF, LarkError) as e:
            # Extract position information from parse error
            if hasattr(e, "line") and hasattr(e, "column"):
                line = e.line - 1  # Convert to 0-based
                col = e.column - 1 if e.column else 0
                self._add_diagnostic(
                    line, col, f"Parse error: {str(e)}", DiagnosticSeverity.Error
                )
            else:
                self._add_diagnostic(
                    0, 0, f"Parse error: {str(e)}", DiagnosticSeverity.Error
                )

    def _extract_symbols(self) -> None:
        """Extract rules, terminals, and imports from the source."""
        for line_num, line in enumerate(self.lines):
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            # Rule definitions (lowercase)
            rule_match = re.match(r"^([?!]?)([a-z_][a-z0-9_]*)\s*:", line)
            if rule_match:
                rule_name = rule_match.group(2)
                col = line.find(rule_name)
                self._rules[rule_name] = (line_num, col)
                continue

            # Terminal definitions (uppercase)
            terminal_match = re.match(r"^([A-Z_][A-Z0-9_]*)\s*:", line)
            if terminal_match:
                terminal_name = terminal_match.group(1)
                col = line.find(terminal_name)
                self._terminals[terminal_name] = (line_num, col)
                continue

            # Import statements
            import_match = re.match(r"%import\s+([a-zA-Z_][a-zA-Z0-9_.]*)", line)
            if import_match:
                import_name = import_match.group(1)
                col = line.find(import_name)
                self._imports[import_name] = (line_num, col)

    def _find_references(self) -> None:
        """Find all references to rules and terminals."""
        for line_num, line in enumerate(self.lines):
            # Find rule references (lowercase identifiers)
            for match in re.finditer(r"\b([a-z_][a-z0-9_]*)\b", line):
                name = match.group(1)
                if name in self._rules:
                    if name not in self._references:
                        self._references[name] = []
                    self._references[name].append((line_num, match.start()))

            # Find terminal references (uppercase identifiers)
            for match in re.finditer(r"\b([A-Z_][A-Z0-9_]*)\b", line):
                name = match.group(1)
                if name in self._terminals:
                    if name not in self._references:
                        self._references[name] = []
                    self._references[name].append((line_num, match.start()))

    def _validate_references(self) -> None:
        """Validate that all referenced symbols are defined."""
        defined_symbols = set(self._rules.keys()) | set(self._terminals.keys())

        for line_num, line in enumerate(self.lines):
            # Check rule references
            for match in re.finditer(r"\b([a-z_][a-z0-9_]*)\b", line):
                name = match.group(1)
                # Skip keywords and common words
                if name in [
                    "start",
                    "import",
                    "ignore",
                    "override",
                    "extend",
                    "declare",
                ]:
                    continue
                if name not in defined_symbols:
                    self._add_diagnostic(
                        line_num,
                        match.start(),
                        f"Undefined rule '{name}'",
                        DiagnosticSeverity.Error,
                    )

            # Check terminal references
            for match in re.finditer(r"\b([A-Z_][A-Z0-9_]*)\b", line):
                name = match.group(1)
                if name not in defined_symbols:
                    self._add_diagnostic(
                        line_num,
                        match.start(),
                        f"Undefined terminal '{name}'",
                        DiagnosticSeverity.Error,
                    )

    def _add_diagnostic(
        self, line: int, col: int, message: str, severity: DiagnosticSeverity
    ) -> None:
        """Add a diagnostic to the list."""
        # Ensure line and column are within bounds
        line = max(0, line)
        line = min(line, len(self.lines) - 1)

        line_text = self.lines[line]

        col = max(0, col)
        col = min(col, len(line_text))

        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=line, character=col),
                end=Position(line=line, character=col + 1),
            ),
            message=message,
            severity=severity,
            source="lark-language-server",
        )
        self._diagnostics.append(diagnostic)

    def get_diagnostics(self) -> List[Diagnostic]:
        """Get all diagnostics for this document."""
        return self._diagnostics

    def get_symbol_at_position(self, line: int, col: int) -> Optional[str]:
        """Get the symbol at the given position."""
        if line >= len(self.lines):
            return None

        line_text = self.lines[line]
        if col >= len(line_text):
            return None

        # Find word boundaries
        start = col
        while start > 0 and (
            line_text[start - 1].isalnum() or line_text[start - 1] == "_"
        ):
            start -= 1

        end = col
        while end < len(line_text) and (
            line_text[end].isalnum() or line_text[end] == "_"
        ):
            end += 1

        if start == end:
            return None

        return line_text[start:end]

    def get_definition_location(self, symbol: str) -> Optional[Location]:
        """Get the definition location of a symbol."""
        if symbol in self._rules:
            line, col = self._rules[symbol]
            return Location(
                uri=self.uri,
                range=Range(
                    start=Position(line=line, character=col),
                    end=Position(line=line, character=col + len(symbol)),
                ),
            )

        if symbol in self._terminals:
            line, col = self._terminals[symbol]
            return Location(
                uri=self.uri,
                range=Range(
                    start=Position(line=line, character=col),
                    end=Position(line=line, character=col + len(symbol)),
                ),
            )

        return None

    def get_references(self, symbol: str) -> List[Location]:
        """Get all reference locations of a symbol."""
        locations = []
        if symbol in self._references:
            for line, col in self._references[symbol]:
                locations.append(
                    Location(
                        uri=self.uri,
                        range=Range(
                            start=Position(line=line, character=col),
                            end=Position(line=line, character=col + len(symbol)),
                        ),
                    )
                )

        return locations

    def get_document_symbols(self) -> List[DocumentSymbol]:
        """Get document symbols for outline view."""
        symbols = []

        # Add rules
        for rule_name, (line, col) in self._rules.items():
            symbol = DocumentSymbol(
                name=rule_name,
                kind=SymbolKind.Function,
                range=Range(
                    start=Position(line=line, character=0),
                    end=Position(line=line + 1, character=0),
                ),
                selection_range=Range(
                    start=Position(line=line, character=col),
                    end=Position(line=line, character=col + len(rule_name)),
                ),
            )
            symbols.append(symbol)

        # Add terminals
        for terminal_name, (line, col) in self._terminals.items():
            symbol = DocumentSymbol(
                name=terminal_name,
                kind=SymbolKind.Constant,
                range=Range(
                    start=Position(line=line, character=0),
                    end=Position(line=line + 1, character=0),
                ),
                selection_range=Range(
                    start=Position(line=line, character=col),
                    end=Position(line=line, character=col + len(terminal_name)),
                ),
            )
            symbols.append(symbol)

        return symbols

    def get_completions(  # pylint: disable=unused-argument
        self, line: int, col: int
    ) -> List[CompletionItem]:
        """Get completion suggestions at the given position."""
        completions = []

        # Add all defined rules
        for rule_name in self._rules:
            completions.append(
                CompletionItem(
                    label=rule_name,
                    kind=CompletionItemKind.Function,
                    detail="Rule",
                    documentation=f"Grammar rule: {rule_name}",
                )
            )

        # Add all defined terminals
        for terminal_name in self._terminals:
            completions.append(
                CompletionItem(
                    label=terminal_name,
                    kind=CompletionItemKind.Constant,
                    detail="Terminal",
                    documentation=f"Terminal symbol: {terminal_name}",
                )
            )

        # Add Lark keywords and operators
        keywords = ["start", "import", "ignore", "override", "extend", "declare"]
        for keyword in keywords:
            completions.append(
                CompletionItem(
                    label=keyword,
                    kind=CompletionItemKind.Keyword,
                    detail="Keyword",
                    documentation=f"Lark keyword: {keyword}",
                )
            )

        return completions

    def get_hover_info(self, line: int, col: int) -> Optional[Hover]:
        """Get hover information for the symbol at the given position."""
        symbol = self.get_symbol_at_position(line, col)
        if not symbol:
            return None

        content = ""
        if symbol in self._rules:
            content = f"**Rule:** `{symbol}`\n\nA grammar rule definition."
        elif symbol in self._terminals:
            content = f"**Terminal:** `{symbol}`\n\nA terminal symbol definition."
        else:
            return None

        return Hover(
            contents=MarkupContent(kind=MarkupKind.Markdown, value=content),
            range=Range(
                start=Position(line=line, character=col),
                end=Position(line=line, character=col + len(symbol)),
            ),
        )


class LarkLanguageServer(LanguageServer):
    """Language Server for Lark grammar files."""

    def __init__(self) -> None:
        super().__init__("lark-language-server", "0.1.0")
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
