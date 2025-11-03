import logging
from dataclasses import dataclass
from textwrap import dedent
from typing import Optional

from lark import Token, Tree
from lark.tree import Meta
from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    DocumentSymbol,
    Hover,
    Location,
    MarkupContent,
    MarkupKind,
)
from lsprotocol.types import Position as LspPosition
from lsprotocol.types import Range as LspRange
from lsprotocol.types import SymbolKind

from lark_parser_language_server.formatter import FORMATTER
from lark_parser_language_server.symbol_table.flags import Directives, Kind, Modifiers
from lark_parser_language_server.syntax_tree.nodes import AstNode

logger = logging.getLogger(__name__)


@dataclass
class Position:
    line: int
    column: int

    @classmethod
    def from_token(cls, token: Token, use_clean_name: bool = True) -> "Position":
        offset = 0

        if use_clean_name:
            name = token.value.lstrip("?!")
            offset = len(token.value) - len(name)

        line = (token.line - 1) if token.line else 0
        column = (token.column - 1 + offset) if token.column else 0

        return cls(
            line=line,
            column=column,
        )

    def to_lsp_position(self) -> LspPosition:
        return LspPosition(
            line=self.line,
            character=self.column,
        )


@dataclass
class Range:
    start: Position
    end: Position

    @classmethod
    def from_token(cls, token: Token, use_clean_name: bool = True) -> "Range":
        offset = len(token.value)

        if use_clean_name:
            name = token.value.lstrip("?!")
            offset = len(name)

        start = Position.from_token(
            token,
            use_clean_name=use_clean_name,
        )
        end = Position(
            line=start.line,
            column=start.column + offset,
        )
        return cls(start=start, end=end)

    @classmethod
    def from_tree(cls, tree: Tree) -> "Range":
        tokens = list(tree.scan_values(lambda v: isinstance(v, Token)))
        if not tokens:
            raise ValueError("Tree does not contain any tokens")

        start_token = tokens[0]
        end_token = tokens[-1]

        start = Position.from_token(start_token, use_clean_name=False)
        end = Position.from_token(end_token, use_clean_name=False)
        end.column += len(end_token.value)

        return cls(start=start, end=end)

    @classmethod
    def from_meta(cls, meta: Meta) -> "Range":
        start = Position(
            line=getattr(meta, "line", 1) - 1,
            column=getattr(meta, "column", 1) - 1,
        )
        end = Position(
            line=getattr(meta, "end_line", 1) - 1,
            column=getattr(meta, "end_column", 1) - 1,
        )

        return cls(start=start, end=end)

    def _contains_position(self, position: Position) -> bool:
        if position.line < self.start.line or position.line > self.end.line:
            return False

        if position.line == self.start.line and position.column < self.start.column:
            return False

        if position.line == self.end.line and position.column > self.end.column:
            return False

        return True

    def __contains__(self, other: "Position | Range") -> bool:
        if isinstance(other, Range):
            return self._contains_position(other.start) and self._contains_position(
                other.end
            )

        if isinstance(other, Position):
            return self._contains_position(other)

        raise TypeError(f"Unsupported type for containment check: {type(other)}")

    def to_lsp_range(self) -> LspRange:
        return LspRange(
            start=self.start.to_lsp_position(),
            end=self.end.to_lsp_position(),
        )


@dataclass
class Definition:
    name: str
    kind: Kind
    range: Range
    selection_range: Range

    parent: Optional["Definition"] = None
    children: Optional[dict[str, list["Definition"]]] = None

    directives: Directives = Directives(0)
    modifiers: Modifiers = Modifiers(0)

    ast_node: Optional[AstNode] = None
    container: Optional["Definition"] = None

    def __post_init__(self):
        if self.children is None:
            self.children = {}

    def _lsp_kind(self) -> SymbolKind:
        kind_mapping = {
            Kind.RULE: SymbolKind.Method,
            Kind.TERMINAL: SymbolKind.Constant,
        }
        return (
            kind_mapping.get(self.kind, SymbolKind.Null)
            if self.parent is None
            else SymbolKind.Variable
        )

    def _lsp_completion_item_kind(self) -> CompletionItemKind:
        kind_mapping = {
            Kind.RULE: CompletionItemKind.Function,
            Kind.TERMINAL: CompletionItemKind.Variable,
        }

        return kind_mapping.get(self.kind, CompletionItemKind.Text)

    @property
    def documentation(self) -> str:
        definition = "No definition available."

        if self.ast_node:
            definition = dedent(
                "\n".join(["```lark", FORMATTER.format_ast_node(self.ast_node), "```"])
            ).strip()

        summary = (
            f"Grammar rule: {self.name}"
            if self.kind == Kind.RULE
            else f"Grammar terminal: {self.name}"
        )

        detail_predicates = [
            (
                f"* Imported from `{getattr(self.ast_node, 'path')}`"
                if self.directives & Directives.IMPORTED and self.ast_node
                else ""
            ),
            "* Declared." if self.directives & Directives.DECLARED else "",
            (
                "* Conditionally inlined."
                if self.modifiers & Modifiers.CONDITIONALLY_INLINED
                else ""
            ),
            "* Inlined." if self.modifiers & Modifiers.INLINED else "",
            "* Pinned." if self.modifiers & Modifiers.PINNED else "",
        ]
        detail = "\n".join([line for line in detail_predicates if line])

        return "\n\n".join([definition, "---", summary, "---", detail])

    def append_child(self, child: "Definition") -> None:
        if self.children is None:
            self.children = {}

        child.parent = self

        if child.name not in self.children:
            self.children[child.name] = []

        self.children[child.name].append(child)

    def to_lsp_document_symbol(self) -> DocumentSymbol:
        return DocumentSymbol(
            name=self.name,
            kind=self._lsp_kind(),
            range=self.range.to_lsp_range(),
            selection_range=self.selection_range.to_lsp_range(),
            children=(
                [
                    child.to_lsp_document_symbol()
                    for child_name in self.children
                    for child in self.children[child_name]
                ]
                if self.children
                else None
            ),
        )

    def to_lsp_completion_item(self) -> CompletionItem:
        return CompletionItem(
            label=self.name,
            kind=self._lsp_completion_item_kind(),
            detail=self.kind.capitalize(),
            documentation=(
                f"Grammar rule: {self.name}"
                if self.kind == Kind.RULE
                else f"Grammar terminal: {self.name}"
            ),
        )

    def to_lsp_hover_info(self, range_: Optional[Range | LspRange] = None) -> Hover:
        if range_ is None:
            range_ = self.range

        if isinstance(range_, Range):
            range_ = range_.to_lsp_range()

        return Hover(
            contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=self.documentation,
            ),
            range=range_,
        )

    def to_lsp_location(self, uri: str) -> Location:
        return Location(
            uri=uri,
            range=self.range.to_lsp_range(),
        )


@dataclass
class Reference:
    name: str
    position: Position
    range: Range
    kind: Optional[Kind] = None
    ast_node: Optional[AstNode] = None

    @classmethod
    def from_token(
        cls, token: Token, ast_node: Optional[AstNode] = None
    ) -> "Reference":
        return cls(
            name=str(token),
            position=Position.from_token(token),
            range=Range.from_token(token),
            kind=Kind.RULE if token.type == "RULE" else Kind.TERMINAL,
            ast_node=ast_node,
        )

    def to_lsp_location(self, uri: str) -> Location:
        return Location(
            uri=uri,
            range=self.range.to_lsp_range(),
        )


@dataclass
class Keyword:
    name: str

    def to_lsp_completion_item(self) -> CompletionItem:
        return CompletionItem(
            label=self.name,
            kind=CompletionItemKind.Keyword,
            detail="Keyword",
            documentation=(f"Lark keyword: {self.name}"),
        )


KEYWORDS = [
    Keyword(name="import"),
    Keyword(name="ignore"),
    Keyword(name="override"),
    Keyword(name="extend"),
    Keyword(name="declare"),
]
