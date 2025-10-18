import logging
from dataclasses import dataclass
from enum import Flag, auto
from textwrap import dedent
from typing import Any, Callable, List, Optional

from lark import Token, Tree
from lark.tree import Branch
from lark.visitors import Visitor
from lsprotocol.types import (
    DiagnosticSeverity,
    DocumentSymbol,
    Position,
    Range,
    SymbolKind,
)

from lark_parser_language_server.symbol_table.symbol import Definition, Reference
from lark_parser_language_server.symbol_table.syntax_tree import (
    definitions_from_ast_node,
    references_from_ast_node,
)
from lark_parser_language_server.syntax_tree.nodes import Ast, AstNode

logger = logging.getLogger(__name__)


class SymbolTable:
    definitions: dict[str, list[Definition]]
    references: dict[str, list[Reference]]

    def __init__(self):
        self.definitions = {}
        self.references = {}

    def __getitem__(self, name: str) -> Optional[List[Definition]]:
        return self.definitions.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self.definitions

    def collect_definitions(self, ast: Ast) -> None:
        for statement in ast.statements:
            for definition in definitions_from_ast_node(statement):
                if definition.name not in self.definitions:
                    self.definitions[definition.name] = []

                self.definitions[definition.name].append(definition)

    def collect_references(self, ast: Ast) -> None:
        for statement in ast.statements:
            for reference in references_from_ast_node(statement):
                if reference.name not in self.references:
                    self.references[reference.name] = []

                self.references[reference.name].append(reference)
