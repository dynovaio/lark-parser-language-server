import logging
from functools import partial
from typing import Optional, cast

from lark import Transformer, Tree, ast_utils, v_args

import lark_parser_language_server.syntax_tree.nodes as ast_nodes_module

logger = logging.getLogger(__name__)

Ast = ast_nodes_module.Ast
AstNode = ast_nodes_module.AstNode


@v_args(tree=True)
class AstBuilder(Transformer):
    def rule_modifiers(self, tree):
        items = tree.children
        return (
            list(value)
            if items and (value := getattr(items[0], "value", None))
            else None
        )

    def template_params(self, tree):
        items = tree.children
        return items if items else None

    def priority(self, tree):
        items = tree.children
        return (
            int(value)
            if items and (value := getattr(items[0], "value", None))
            else None
        )

    def import_lib(self, tree):
        items = tree.children
        return [".".join(items[:-1]), items[-1]]

    def import_rel(self, tree):
        items = tree.children
        return ["." + ".".join(items[:-1]), items[-1]]

    def name_list(self, tree):
        items = tree.children
        return items if items else None

    def literal(self, tree):
        items = tree.children
        return items[0]

    def value(self, tree):
        items = tree.children
        return items[0]

    def expansions(self, tree):
        items = tree.children
        return items

    def nonterminal(self, tree):
        items = tree.children
        return items[0]

    def terminal(self, tree):
        items = tree.children
        return items[0]

    def start(self, tree):
        return Ast(tree=tree)

    def build(self, tree: Tree) -> AstNode:
        return self.transform(tree=tree)


def _get_ast_builder() -> AstBuilder:  # type: ignore
    if not getattr(_get_ast_builder, "cache", None):
        builder = ast_utils.create_transformer(
            ast_nodes_module,
            AstBuilder(),
            decorator_factory=partial(v_args, tree=True),
        )

        setattr(_get_ast_builder, "cache", cast(AstBuilder, builder))  # type: ignore

    return getattr(_get_ast_builder, "cache")


_get_ast_builder.cache: Optional[AstBuilder] = None  # type: ignore

AST_BUILDER: AstBuilder = _get_ast_builder()  # type: ignore
