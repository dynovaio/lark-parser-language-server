from lark import Token, Tree


def get_tokens(tree: Tree, include_placeholders=False):
    for child in tree.children:
        if isinstance(child, Tree):
            yield from get_tokens(child, include_placeholders)

        elif isinstance(child, Token):
            yield child

        elif child is not None:
            yield child

        elif include_placeholders:
            yield child
