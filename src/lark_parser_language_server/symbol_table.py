import logging
import re
from dataclasses import dataclass
from enum import Flag, auto
from textwrap import dedent
from typing import Dict, List, Optional

from lark import Token, Tree
from lark.tree import Branch
from lark.visitors import Visitor
from lsprotocol.types import DocumentSymbol, Position, Range, SymbolKind

logger = logging.getLogger(__name__)

SYMBOL_MODIFIER_REGEX = re.compile("^[?!_]*")


class SymbolModifier(Flag):
    INLINED = auto()
    CONDITIONALLY_INLINED = auto()
    PINNED = auto()

    @classmethod
    def map(cls, char: str) -> "SymbolModifier":
        return {
            "_": cls.INLINED,
            "?": cls.CONDITIONALLY_INLINED,
            "!": cls.PINNED,
        }.get(char, cls(0))


@dataclass
class SymbolPosition:
    line: int
    column: int

    @classmethod
    def from_token(cls, token: Token, use_clean_name: bool = True) -> "SymbolPosition":
        offset = 0

        if use_clean_name:
            name = token.value.lstrip("?!")
            offset = len(token.value) - len(name)

        line = (token.line - 1) if token.line else 0
        column = (token.column - 1 + offset) if token.column else 0
        return cls(line=line, column=column)

    def to_lsp_position(self) -> Position:
        return Position(line=self.line, character=self.column)


@dataclass
class SymbolRange:
    start: SymbolPosition
    end: SymbolPosition

    @classmethod
    def from_token(cls, token: Token, use_clean_name: bool = True) -> "SymbolRange":
        offset = len(token.value)

        if use_clean_name:
            name = token.value.lstrip("?!")
            offset = len(name)

        start = SymbolPosition.from_token(
            token,
            use_clean_name=use_clean_name,
        )
        end = SymbolPosition(
            line=start.line,
            column=start.column + offset,
        )
        return cls(start=start, end=end)

    @classmethod
    def from_tree(cls, tree: Tree) -> "SymbolRange":
        tokens = list(tree.scan_values(lambda v: isinstance(v, Token)))
        if not tokens:
            raise ValueError("Tree does not contain any tokens")

        start_token = tokens[0]
        end_token = tokens[-1]

        start = SymbolPosition.from_token(start_token, use_clean_name=False)
        end = SymbolPosition.from_token(end_token, use_clean_name=False)
        end.column += len(end_token.value)

        return cls(start=start, end=end)

    def to_lsp_range(self) -> Range:
        return Range(
            start=self.start.to_lsp_position(),
            end=self.end.to_lsp_position(),
        )


class Symbol:
    _token: Token
    _alias: bool
    _directive: Optional[str]

    name: str
    position: SymbolPosition
    range: SymbolRange
    select_range: SymbolRange
    modifiers: SymbolModifier = SymbolModifier(0)

    def __init__(
        self,
        token: Token,
        *,
        tree: Optional[Tree] = None,
        alias: bool = False,
        directive: Optional[str] = None,
    ) -> None:
        self._token = token
        self._tree = tree
        self._alias = alias
        self._directive = directive
        self._process_token()

    def __repr__(self) -> str:
        return (
            f"Symbol(name={self.name!r}, position={self.position}, "
            f"range={self.range}, select_range={self.select_range}, "
            f"modifiers={self.modifiers}, alias={self._alias}, "
            f"directive={self._directive})"
        )

    @property
    def documentation(self) -> str:
        tag_line = (
            "Grammar rule definition."
            if self.is_rule
            else "Terminal symbol definition."
        )
        content = dedent(
            f"""
            ```lark
            {self.name}
            ```

            ---

            {tag_line}
            """
        )

        return content

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Symbol):
            return NotImplemented

        return (
            self.name == other.name
            and self.position == other.position
            and self.range == other.range
            and self.select_range == other.select_range
            and self.modifiers == other.modifiers
            and self._alias == other._alias
            and self._directive == other._directive
        )

    def _process_token(self):
        self.name = self._clean_name()
        self.position = SymbolPosition.from_token(self._token)
        self.select_range = SymbolRange.from_token(
            self._token,
            use_clean_name=True,
        )
        self.range = (
            SymbolRange.from_tree(self._tree) if self._tree else self.select_range
        )
        self._extract_modifiers()

    def _clean_name(self):
        return self.raw_name.lstrip("?!")

    def _extract_modifiers(self):
        prefix = SYMBOL_MODIFIER_REGEX.match(self._token.value)
        if not prefix:
            return

        for character in prefix.group(0):
            self.modifiers |= SymbolModifier.map(character)

    @property
    def raw_name(self) -> str:
        return self._token.value

    @property
    def kind(self) -> str:
        if self.name.isupper():
            return "terminal"

        if self.name.islower():
            return "rule"

        raise ValueError(f"Invalid symbol name: {self.name}")

    @property
    def is_terminal(self) -> bool:
        return self.kind == "terminal"

    @property
    def is_rule(self) -> bool:
        return self.kind == "rule"

    @property
    def is_inlined(self) -> bool:
        return bool(self.modifiers & SymbolModifier.INLINED)

    @property
    def is_conditionally_inlined(self) -> bool:
        return bool(self.modifiers & SymbolModifier.CONDITIONALLY_INLINED)

    @property
    def is_pinned(self) -> bool:
        return bool(self.modifiers & SymbolModifier.PINNED)

    @property
    def is_alias(self) -> bool:
        return self._alias

    @property
    def description(self) -> Optional[str]:
        descriptions = [self.kind.capitalize()]

        if self._directive:
            descriptions.append(self._directive.capitalize())

        if self.is_alias:
            descriptions.append("Alias")

        if self.is_inlined:
            descriptions.append("Inlined")

        if self.is_conditionally_inlined:
            descriptions.append("Conditionally Inlined")

        if self.is_pinned:
            descriptions.append("Pinned")

        return ", ".join(descriptions) if descriptions else None

    def get_lsp_kind(self) -> SymbolKind:
        if self.kind == "terminal":
            return SymbolKind.Constant
        if self.kind == "rule":
            return SymbolKind.Function

        return SymbolKind.Variable

    def to_lsp_symbol(self) -> DocumentSymbol:
        return DocumentSymbol(
            name=self.name,
            kind=self.get_lsp_kind(),
            detail=self.description,
            range=self.range.to_lsp_range(),
            selection_range=self.select_range.to_lsp_range(),
        )


class SymbolTable(Visitor):
    symbols: Dict[str, Symbol]
    references: Dict[str, List[Symbol]]

    def __init__(self):
        self.symbols = {}
        self.references = {}

    def __default__(self, tree: Tree):
        if tree.data == "import":
            self._handle_import(tree)

        if tree.data == "multi_import":
            self._handle_multi_import(tree)

        if tree.data == "declare":
            self._handle_declare(tree)

    def rule(self, tree: Tree):
        rule = tree.children[0]
        self._consume_symbol(tree, rule)

    def token(self, tree: Tree):
        token = tree.children[0]
        self._consume_symbol(tree, token)

    def alias(self, tree: Tree):
        alias = tree.children[-1]
        if alias:
            self._consume_symbol(tree, alias)

    def _handle_import(self, tree: Tree):
        import_path, alias = tree.children

        if alias:
            self._consume_symbol(
                tree, alias.children[0], alias=True, directive="import"
            )
        else:
            print(import_path)
            self._consume_symbol(
                tree, import_path.children[-1].children[0], directive="import"
            )

    def _handle_multi_import(self, tree: Tree):
        name_list = tree.children[-1]
        for name in name_list.children:
            self._consume_symbol(tree, name.children[0], directive="import")

    def _handle_declare(self, tree: Tree):
        for name in tree.children:
            self._consume_symbol(tree, name.children[0], directive="declare")

    def _consume_symbol(
        self, tree: Tree, token: Branch, *, alias=False, directive=None
    ):
        if isinstance(token, Token):
            symbol = Symbol(
                token,
                tree=tree,
                alias=alias,
                directive=directive,
            )
            self.symbols[symbol.name] = symbol

    def _clean_symbol_name(self, name: str) -> str:
        return name.lstrip("?!")

    def __getitem__(self, name: str) -> "Symbol":
        clean_name = self._clean_symbol_name(name)
        if clean_name in self.symbols:
            return self.symbols[clean_name]

        raise KeyError(f"Symbol '{name}' not found in symbol table")
