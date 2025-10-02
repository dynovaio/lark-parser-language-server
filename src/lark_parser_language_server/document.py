import logging
from typing import Dict, List, Optional, Tuple

from lark import Lark, LarkError, Tree
from lark.exceptions import (
    ParseError,
    UnexpectedCharacters,
    UnexpectedEOF,
    UnexpectedInput,
)
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

from .symbol_table import SymbolTable

logger = logging.getLogger(__name__)


class LarkDocument:
    def __init__(self, uri: str, source: str) -> None:
        self.uri = uri
        self.source = source
        self.lines = source.splitlines()
        self._symbol_table = SymbolTable()
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

    @staticmethod
    def _on_parse_error(error: UnexpectedInput) -> bool:
        logger.error("Parse error: %s", error)
        return True

    def _parse_grammar(self) -> None:
        """Parse the Lark grammar and extract basic structure."""
        try:
            # Try to parse with Lark's own grammar
            lark_parser = Lark.open_from_package(
                "lark",
                "grammars/lark.lark",
                parser="lalr",
            )
            self._parsed_tree = lark_parser.parse(
                self.source,
                on_error=self._on_parse_error,
            )
        except (ParseError, UnexpectedCharacters, UnexpectedEOF, LarkError) as e:
            # Extract position information from parse error
            if isinstance(e, (UnexpectedCharacters, UnexpectedEOF)):
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
        if self._parsed_tree:
            self._symbol_table.visit_topdown(self._parsed_tree)

    def _find_references(self) -> None:
        """Find all references to rules and terminals."""
        # for line_num, line in enumerate(self.lines):
        #     # Find rule references (lowercase identifiers)
        #     for match in re.finditer(r"\b([a-z_][a-z0-9_]*)\b", line):
        #         name = match.group(1)
        #         if name in self._rules:
        #             if name not in self._references:
        #                 self._references[name] = []
        #             self._references[name].append((line_num, match.start()))

        #     # Find terminal references (uppercase identifiers)
        #     for match in re.finditer(r"\b([A-Z_][A-Z0-9_]*)\b", line):
        #         name = match.group(1)
        #         if name in self._terminals:
        #             if name not in self._references:
        #                 self._references[name] = []
        #             self._references[name].append((line_num, match.start()))

    def _validate_references(self) -> None:
        """Validate that all referenced symbols are defined."""
        # defined_symbols = set(self._rules.keys()) | set(self._terminals.keys())

        # for line_num, line in enumerate(self.lines):
        #     # Check rule references
        #     for match in re.finditer(r"\b([a-z_][a-z0-9_]*)\b", line):
        #         name = match.group(1)
        #         # Skip keywords and common words
        #         if name in [
        #             "start",
        #             "import",
        #             "ignore",
        #             "override",
        #             "extend",
        #             "declare",
        #         ]:
        #             continue
        #         if name not in defined_symbols:
        #             self._add_diagnostic(
        #                 line_num,
        #                 match.start(),
        #                 f"Undefined rule '{name}'",
        #                 DiagnosticSeverity.Error,
        #             )

        #     # Check terminal references
        #     for match in re.finditer(r"\b([A-Z_][A-Z0-9_]*)\b", line):
        #         name = match.group(1)
        #         if name not in defined_symbols:
        #             self._add_diagnostic(
        #                 line_num,
        #                 match.start(),
        #                 f"Undefined terminal '{name}'",
        #                 DiagnosticSeverity.Error,
        #             )

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

    def get_definition_location(self, symbol_name: str) -> Optional[Location]:
        """Get the definition location of a symbol."""
        if symbol_name in self._symbol_table.symbols:
            symbol = self._symbol_table.symbols[symbol_name]
            return Location(
                uri=self.uri,
                range=symbol.range.to_lsp_range(),
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
        return [
            symbol.to_lsp_symbol() for symbol in self._symbol_table.symbols.values()
        ]

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
