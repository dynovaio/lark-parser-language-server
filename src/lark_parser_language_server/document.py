import logging
import traceback
from typing import Callable, Dict, List, Optional, Tuple

from lark import Lark, Tree
from lsprotocol.types import (
    CompletionItem,
    Diagnostic,
    DiagnosticSeverity,
    DocumentSymbol,
    FormattingOptions,
    Hover,
    Location,
    Position,
    Range,
    TextEdit,
)

from lark_parser_language_server.formatter import FORMATTER
from lark_parser_language_server.parser import PARSER
from lark_parser_language_server.symbol_table import SymbolTable
from lark_parser_language_server.symbol_table.symbol import KEYWORDS, Reference
from lark_parser_language_server.syntax_tree import AST_BUILDER, Ast

logger = logging.getLogger(__name__)


class LarkDocument:
    uri: str
    source: str
    lines: list[str]
    _symbol_table: SymbolTable
    _parsed_tree: Optional[Tree]
    _references: Dict[str, List[Reference]]
    _diagnostics: List[Diagnostic]
    _ast: Optional[Ast]

    def __init__(self, uri: str, source: str) -> None:
        self.uri = uri
        self.source = source
        self.lines = source.splitlines()
        self._symbol_table = SymbolTable()
        self._parsed_tree = None
        self._references = {}
        self._diagnostics = []
        self._ast = None
        self._analyze()

    def _analyze(self) -> None:
        try:
            self._parse_grammar()
            self._build_ast()
            self._collect_definitions()
            self._validate_definitions()
            self._collect_references()
            self._validate_references()
            # Load the grammar to catch any additional errors
            self._load_document_grammar()
        except Exception as error:  # pylint: disable=broad-except
            logger.exception("Error analyzing document %s", self.uri)
            logger.debug("Traceback: %s", traceback.format_exc())
            self._add_diagnostic(
                error,
                message=f"Error analyzing document: {str(error)}",
            )

    def _on_parse_error_handler(self) -> Callable[[Exception], bool]:
        def _on_parse_error(error: Exception) -> bool:
            self._add_diagnostic(
                error,
                message=f"Parse error: {str(error)}",
            )

            return True

        return _on_parse_error

    def _load_document_grammar(self) -> None:
        # There are some error that are not caught during parsing,
        # but they are caught during grammar loading using Lark's internal
        # mechanisms with Lark class.
        Lark(
            self.source,
            parser="lalr",
            start="start",
            source_path=str(self.uri),
        )

    def _parse_grammar(self) -> None:
        """Parse the Lark grammar and extract basic structure."""
        self._parsed_tree = PARSER.parse(
            self.source,
            on_error=self._on_parse_error_handler(),
        )

    def _build_ast(self) -> None:
        """Transform the parse tree into an AST."""
        if self._parsed_tree:
            self._ast = AST_BUILDER.build(self._parsed_tree)

    def _collect_definitions(self) -> None:
        """Extract rules, terminals, and imports from the source."""
        if self._ast:
            self._symbol_table.collect_definitions(self._ast)

    def _validate_definitions(self) -> None:
        self._symbol_table.validate_definitions()

        for error, _ in self._symbol_table.definition_errors:
            self._add_diagnostic(
                error,
                message=str(error),
            )

    def _collect_references(self) -> None:
        if self._ast:
            self._symbol_table.collect_references(self._ast)

    def _validate_references(self) -> None:
        self._symbol_table.validate_references()

        for error, *_ in self._symbol_table.reference_errors:
            self._add_diagnostic(
                error,
                message=str(error),
            )

    def _add_diagnostic(
        self,
        error: Exception,
        severity: Optional[DiagnosticSeverity] = DiagnosticSeverity.Error,
        message: Optional[str] = None,
    ) -> None:
        """Add a diagnostic to the list."""
        # Ensure line and column are within bounds
        line = max(0, getattr(error, "line", 0))
        if self.lines:
            line = min(line, len(self.lines) - 1)
            line_text = self.lines[line]
        else:
            line = 0
            line_text = ""

        col = max(0, getattr(error, "column", 0))
        col = min(col, len(line_text))

        width = getattr(error, "width", 1)

        diagnostic = Diagnostic(
            range=Range(
                start=Position(line=line, character=col),
                end=Position(line=line, character=col + width),
            ),
            message=(
                message if message else str(error) + "\n" + str(error.__traceback__)
            ),
            severity=severity,
            source="lark-parser-language-server",
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
        definition = self._symbol_table.get_definition(symbol_name)

        return definition.to_lsp_location(uri=self.uri) if definition else None

    def get_references(self, symbol_name: str) -> List[Location]:
        """Get all reference locations of a symbol."""
        if symbol_name not in self._references:
            return []

        return [
            reference.to_lsp_location(uri=self.uri)
            for reference in self._references[symbol_name]
        ]

    def get_document_symbols(self) -> List[DocumentSymbol]:
        """Get document symbols for outline view."""
        return [
            definition.to_lsp_document_symbol()
            for symbol_definitions in self._symbol_table.definitions.values()
            for definition in symbol_definitions
        ]

    def get_completions(  # pylint: disable=unused-argument
        self, line: int, col: int
    ) -> List[CompletionItem]:
        """Get completion suggestions at the given position."""
        completions = [
            definition.to_lsp_completion_item()
            for definitions in self._symbol_table.definitions.values()
            for definition in definitions
        ]

        for keyword in KEYWORDS:
            completions.append(
                keyword.to_lsp_completion_item(),
            )

        return completions

    def get_hover_info(self, line: int, column: int) -> Optional[Hover]:
        """Get hover information for the symbol at the given position."""
        symbol_info = self.get_symbol_at_position(line, column)

        if symbol_info is None:
            return None

        symbol_name, start_column, end_column = symbol_info

        symbols = self._symbol_table[symbol_name]

        if symbols is None:
            return None

        symbol = symbols[0]

        return symbol.to_lsp_hover_info(
            range_=Range(
                start=Position(line=line, character=start_column),
                end=Position(line=line, character=end_column),
            )
        )

    def format(
        self, options: FormattingOptions
    ) -> TextEdit:  # pylint: disable=unused-argument
        """Format the document according to the given options."""
        if self._ast:
            # {"tabSize":4,"insertSpaces":true,"trimTrailingWhitespace":true,"trimFinalNewlines":true,"insertFinalNewline":true}
            tab_size = options.tab_size
            insert_spaces = options.insert_spaces
            insert_final_newline = options.insert_final_newline

            indent = " " * tab_size if insert_spaces else "\t"

            new_text = FORMATTER.format(self._ast, indent=indent) + (
                "\n" if insert_final_newline else ""
            )

            lines = new_text.split("\n")

            range_ = Range(
                start=Position(
                    line=0,
                    character=0,
                ),
                end=Position(
                    line=len(lines),
                    character=len(lines[-1]),
                ),
            )
            return TextEdit(
                new_text=new_text,
                range=range_,
            )

        return TextEdit(
            new_text=self.source,
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=len(self.source.split("\n")) + 1, character=0),
            ),
        )
