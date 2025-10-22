import logging
from typing import Optional, cast

from lark import Token, Tree, ast_utils
from lark.tree import Meta

logger = logging.getLogger(__name__)


def _meta_repr(self) -> str:
    if self.empty:
        return "Meta(empty=True)"

    return (
        "Meta("
        f"line={self.line}, "
        f"column={self.column}, "
        f"end_line={self.end_line}, "
        f"end_column={self.end_column})"
    )


Meta.__repr__ = _meta_repr


class BaseAstNode(ast_utils.Ast, ast_utils.AsList):
    def __post_init__(self):
        pass


class AstNode(BaseAstNode):
    _tree: Tree

    meta: Meta

    def __init__(self, tree: Tree):
        self._tree = tree
        self.meta = tree.meta if hasattr(tree, "meta") else Meta()

        self.__post_init__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(meta={self.meta})"


class Range(AstNode):
    start: str
    end: str

    def __post_init__(self):
        self.start = str(self._tree.children[0])
        self.end = str(self._tree.children[1])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(meta={self.meta!r}, start={self.start!r}, end={self.end!r})"


class TemplateUsage(AstNode):
    rule: Token
    arguments: list["str | Token | Range | TemplateUsage"]

    def __post_init__(self):
        self.rule = cast(Token, self._tree.children[0])
        self.arguments = cast(
            list[str | Token | Range | TemplateUsage], self._tree.children[1:]
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meta={self.meta!r}, "
            f"rule={self.rule!r}, "
            f"arguments={self.arguments!r})"
        )


class Maybe(AstNode):
    expansions: list["Expansion"]

    def __post_init__(self):
        self.expansions = [
            item.to_expansion() if isinstance(item, Alias) else item
            for item in cast(list[Expansion | Alias], self._tree.children[0])
        ]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(meta={self.meta!r}, expansions={self.expansions!r})"


class Expansion(AstNode):
    expressions: list["Expr"]
    alias: Optional[Token] = None

    def __post_init__(self):
        self.expressions = cast(list[Expr], self._tree.children)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meta={self.meta!r}, "
            f"expressions={self.expressions!r}, "
            f"alias={self.alias!r})"
        )

    @property
    def is_aliased(self) -> bool:
        return self.alias is not None


class Alias(AstNode):
    expansion: Expansion
    name: Optional[Token] = None

    def __post_init__(self):
        self.expansion = cast(Expansion, self._tree.children[0])
        self.name = cast(Token, self._tree.children[1])

    def to_expansion(self) -> "Expansion":
        expansion = self.expansion
        expansion.meta = self.meta
        expansion.alias = self.name

        return expansion

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meta={self.meta!r}, "
            f"name={self.name!r}, "
            f"expansion={self.expansion!r})"
        )


class Expr(AstNode):
    atom: str | Token | list[Expansion] | Maybe | TemplateUsage | Range
    operators: Optional[list[Token]] = None

    def __post_init__(self):
        self.atom = cast(
            str | Token | list[Expansion] | Maybe | TemplateUsage | Range,
            self._tree.children[0],
        )
        self.operators = cast(list[Token], self._tree.children[1:])

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meta={self.meta!r}, "
            f"atom={self.atom!r}, "
            f"operators={self.operators!r})"
        )


class Term(AstNode):
    modifiers: list[str]
    name: Token
    priority: int = 0
    expansions: list[Expansion]

    def __post_init__(self):
        self.modifiers = []
        self.name = cast(Token, self._tree.children[0])

        if len(self._tree.children) == 3:
            self.priority = cast(int, self._tree.children[1] or 0)

        self.expansions = [
            item.to_expansion() if isinstance(item, Alias) else item
            for item in cast(list[Expansion | Alias], self._tree.children[-1])
        ]

        if str(self.name).startswith("_"):
            self.modifiers.append("_")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meta={self.meta!r}, "
            f"modifiers={self.modifiers!r}, "
            f"name={self.name!r}, "
            f"priority={self.priority!r}, "
            f"expansions={self.expansions!r})"
        )


class Rule(AstNode):
    modifiers: list[str]
    name: Token
    parameters: list[Token]
    priority: int = 0
    expansions: list[Expansion]

    def __post_init__(self):
        self.modifiers = cast(list[str], self._tree.children[0]) or []
        self.name = cast(Token, self._tree.children[1])
        self.parameters = cast(list[Token], self._tree.children[2]) or []
        self.priority = cast(int, self._tree.children[3] or 0)
        self.expansions = [
            item.to_expansion() if isinstance(item, Alias) else item
            for item in cast(list[Expansion | Alias], self._tree.children[4])
        ]
        if str(self.name).startswith("_"):
            self.modifiers.append("_")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meta={self.meta!r}, "
            f"modifiers={self.modifiers!r}, "
            f"name={self.name!r}, "
            f"parameters={self.parameters!r}, "
            f"priority={self.priority!r}, "
            f"expansions={self.expansions!r})"
        )


class Declare(AstNode):
    symbols: list[Token]

    def __post_init__(self):
        self.symbols = cast(list[Token], self._tree.children)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meta={self.meta!r}, symbols={self.symbols!r})"
        )


class Import(AstNode):
    path: str
    symbols: list[Token]
    alias: Optional[Token] = None

    def __post_init__(self):
        if len(self._tree.children) == 1:
            self.path = cast(list[str], self._tree.children[0])[0]
            self.symbols = [cast(list[Token], self._tree.children[0])[1]]
            return

        if len(self._tree.children) == 2 and isinstance(self._tree.children[1], Token):
            self.path = ".".join(cast(list[Token], self._tree.children[0])[:-1])
            self.symbols = [cast(list[Token], self._tree.children[0])[-1]]
            self.alias = cast(Token, self._tree.children[1])
            return

        self.path = "".join(cast(list[Token], self._tree.children[0]))
        self.symbols = cast(list[Token], self._tree.children[1])

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meta={self.meta!r}, "
            f"path={self.path!r}, "
            f"symbols={self.symbols!r}, "
            f"alias={self.alias!r})"
        )


class Override(AstNode):
    definition: Rule | Term

    def __post_init__(self):
        self.definition = cast(Rule | Term, self._tree.children[0])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(meta={self.meta!r}, definition={self.definition!r})"


class Extend(AstNode):
    definition: Rule | Term

    def __post_init__(self):
        self.definition = cast(Rule | Term, self._tree.children[0])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(meta={self.meta!r}, definition={self.definition!r})"


class Comment(AstNode):
    content: Token

    def __post_init__(self):
        self.content = (
            cast(Token, self._tree.children[0])
            if self._tree.children
            else Token("COMMENT", "")
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meta={self.meta!r}, content={self.content!r})"
        )


class Ignore(AstNode):
    expansions: list[Expansion]

    def __post_init__(self):
        self.expansions = [
            expansion.to_expansion() if isinstance(expansion, Alias) else expansion
            for expansion in cast(
                list[Expansion | Alias],
                self._tree.children[0],
            )
        ]

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meta={self.meta!r}, "
            f"expansions={self.expansions!r})"
        )


class Ast(AstNode):
    statements: list[AstNode]

    def __post_init__(self):
        self.statements = [
            child for child in self._tree.children if isinstance(child, AstNode)
        ]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(meta={self.meta!r}, statements={self.statements!r})"

    def __getitem__(self, index: int) -> AstNode:
        return self.statements[index]

    def __len__(self) -> int:
        return len(self.statements)
