import logging
from typing import Callable, Dict, List, Optional, Tuple

from lark import Lark, Token, Tree
from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    Diagnostic,
    DiagnosticSeverity,
    DocumentSymbol,
    Hover,
    Location,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
)

from lark_parser_language_server.symbol_table import Symbol, SymbolTable

logger = logging.getLogger(__name__)


class LarkDocument:
    def __init__(self, uri: str, source: str) -> None:
        self.uri = uri
        self.source = source
        self.lines = source.splitlines()
        self._symbol_table = SymbolTable()
        self._parsed_tree: Optional[Tree] = None
        self._references: Dict[str, List[Symbol]] = {}  # name -> [(line, col), ...]
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
                0,
                0,
                f"Analysis error: {str(e)}",
                DiagnosticSeverity.Error,
            )

    def _on_parse_error_handler(self) -> Callable[[Exception], bool]:
        def _on_parse_error(e: Exception) -> bool:
            """Handle parse errors and add diagnostics."""
            line = 0
            column = 0

            if error_line := getattr(e, "line", None):
                line = error_line - 1  # Convert to 0-based

            if error_column := getattr(e, "column", None):
                column = error_column - 1  # Convert to 0-based

            self._add_diagnostic(
                line,
                column,
                f"Parse error: {str(e)}",
                DiagnosticSeverity.Error,
            )
            return True

        return _on_parse_error

    def _parse_grammar(self) -> None:
        """Parse the Lark grammar and extract basic structure."""
        lark_parser = Lark.open_from_package(
            "lark",
            "grammars/lark.lark",
            parser="lalr",
        )
        self._parsed_tree = lark_parser.parse(
            self.source,
            on_error=self._on_parse_error_handler(),
        )

    def _extract_symbols(self) -> None:
        """Extract rules, terminals, and imports from the source."""
        if self._parsed_tree:
            self._symbol_table.visit_topdown(self._parsed_tree)

    def _find_references(self) -> None:
        """Find all references to rules and terminals."""
        if self._parsed_tree:
            symbols = [
                Symbol(token)
                for token in list(
                    self._parsed_tree.scan_values(
                        lambda v: isinstance(v, Token) and v.type in ("RULE", "TOKEN")
                    )
                )
            ]

            import_path_symbols = [
                symbol
                for import_statement in self._parsed_tree.find_pred(
                    lambda t: t.data in ("import", "multi_import")
                )
                for symbol in self._extract_symbols_from_import_path(import_statement)
            ]

            for symbol in symbols:
                if symbol in import_path_symbols:
                    continue

                if symbol.name not in self._references:
                    self._references[symbol.name] = []

                self._references[symbol.name].append(symbol)

    def _extract_symbols_from_import_path(self, tree: Tree) -> list[Symbol]:
        if tree.data not in ("import", "multi_import"):
            return []

        import_path, alias = tree.children

        if tree.data == "multi_import":
            alias = None

        import_path_tokens = list(
            import_path.scan_values(
                lambda v: isinstance(v, Token) and v.type in ("RULE", "TOKEN")
            )
        )

        if alias is None:
            import_path_tokens = import_path_tokens[:-1]

        return [Symbol(token) for token in import_path_tokens]

    def _validate_references(self) -> None:
        """Validate that all referenced symbols are defined."""
        defined_symbols = self._symbol_table.symbols.keys()
        referenced_symbols = self._references.keys()

        for symbol_name in referenced_symbols:
            if symbol_name not in defined_symbols:
                for symbol in self._references[symbol_name]:
                    self._add_diagnostic(
                        symbol.position.line,
                        symbol.position.column,
                        f"Undefined {symbol.kind} '{symbol.name}'",
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

    def get_symbol_at_position(
        self, line: int, column: int
    ) -> Optional[Tuple[str, int, int]]:
        """Get the symbol at the given position."""
        if line >= len(self.lines):
            return None

        line_text = self.lines[line]
        if column >= len(line_text):
            return None

        # Find word boundaries
        start = column
        while start > 0 and (
            line_text[start - 1].isalnum() or line_text[start - 1] == "_"
        ):
            start -= 1

        end = column
        while end < len(line_text) and (
            line_text[end].isalnum() or line_text[end] == "_"
        ):
            end += 1

        if start == end:
            return None

        return (line_text[start:end], start, end)

    def get_definition_location(self, symbol_name: str) -> Optional[Location]:
        """Get the definition location of a symbol."""
        if symbol_name not in self._symbol_table.symbols:
            return None

        symbol = self._symbol_table.symbols[symbol_name]

        return Location(
            uri=self.uri,
            range=symbol.range.to_lsp_range(),
        )

    def get_references(self, symbol_name: str) -> List[Location]:
        """Get all reference locations of a symbol."""
        if symbol_name not in self._references:
            return []

        return [
            Location(
                uri=self.uri,
                range=symbol.range.to_lsp_range(),
            )
            for symbol in self._references[symbol_name]
        ]

    def get_document_symbols(self) -> List[DocumentSymbol]:
        """Get document symbols for outline view."""
        return [
            symbol.to_lsp_symbol() for symbol in self._symbol_table.symbols.values()
        ]

    def get_completions(  # pylint: disable=unused-argument
        self, line: int, col: int
    ) -> List[CompletionItem]:
        """Get completion suggestions at the given position."""
        completions = [
            CompletionItem(
                label=symbol.name,
                kind=(
                    CompletionItemKind.Function
                    if symbol.is_rule
                    else CompletionItemKind.Variable
                ),
                detail=symbol.kind.capitalize(),
                documentation=(
                    f"Grammar rule: {symbol.name}"
                    if symbol.is_rule
                    else f"Grammar terminal: {symbol.name}"
                ),
            )
            for symbol in self._symbol_table.symbols.values()
        ]

        # Add Lark keywords and operators
        keywords = [
            "start",
            "import",
            "ignore",
            "override",
            "extend",
            "declare",
        ]
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

    def get_hover_info(self, line: int, column: int) -> Optional[Hover]:
        """Get hover information for the symbol at the given position."""
        symbol_info = self.get_symbol_at_position(line, column)

        if symbol_info is None:
            return None

        symbol_name, start_column, end_column = symbol_info

        symbol = self._symbol_table.symbols.get(symbol_name, None)

        if symbol is None:
            return None

        return Hover(
            contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=symbol.documentation,
            ),
            range=Range(
                start=Position(line=line, character=start_column),
                end=Position(line=line, character=end_column),
            ),
        )
