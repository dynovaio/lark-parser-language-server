from typing import Callable, Optional

from lark_parser_language_server.symbol_table.errors import (
    DefinitionNotFoundError,
    DefinitionNotFoundForReferenceError,
    MultipleDefinitionsError,
    ShadowedDefinitionError,
)
from lark_parser_language_server.symbol_table.symbol import Definition, Reference
from lark_parser_language_server.syntax_tree.nodes import Import, Rule


def validate_single_definition(
    name: str,
    definitions: list[Definition],
    error_handler: Optional[Callable[[Exception, Optional[Definition]], None]] = None,
) -> None:
    if len(definitions) == 1:
        return

    error: Optional[Exception] = None

    if len(definitions) < 1:
        error = DefinitionNotFoundError(f"No definitions found with name '{name}'.")

        if error_handler:
            error_handler(error, None)
            return

        raise error

    for definition in definitions[1:]:
        error = MultipleDefinitionsError(
            definition.name, position=definition.selection_range.start
        )

        if error_handler:
            error_handler(error, definition)
        else:
            raise error


def validate_shadowed_definition(
    definition: Definition,
    definitions: dict[str, list[Definition]],
    error_handler: Optional[Callable[[Exception, Optional[Definition]], None]] = None,
) -> None:
    if definition.name in definitions:
        error = ShadowedDefinitionError(
            definition.name, position=definition.selection_range.start
        )

        if error_handler:
            error_handler(error, definition)
        else:
            raise error


def _reference_is_in_local_scope(
    name: str,
    reference: Reference,
    definitions: dict[str, list[Definition]],
) -> bool:
    ast_node = getattr(reference, "ast_node", None)

    if isinstance(ast_node, (Rule, Import)):
        if isinstance(ast_node, Rule):
            definition = definitions.get(str(ast_node.name), [None])[0]
            is_in_range = reference.range in getattr(definition, "range", [])
            is_in_children = name in getattr(definition, "children", {})

            return is_in_range or is_in_children

        if isinstance(ast_node, Import):
            alias = ast_node.alias
            definition = definitions.get(str(alias), [None])[0] if alias else None
            is_in_range = reference.range in getattr(definition, "range", [])
            is_in_children = name in getattr(definition, "children", {})

            return is_in_range or is_in_children

    return False


def validate_undefined_reference(
    name: str,
    references: list[Reference],
    definitions: dict[str, list[Definition]],
    error_handler: Optional[
        Callable[[Exception, Optional[Reference], Optional[Definition]], None]
    ] = None,
) -> None:
    if name in definitions:
        return

    for reference in references:
        if _reference_is_in_local_scope(name, reference, definitions):
            continue

        error = DefinitionNotFoundForReferenceError(name, position=reference.position)

        if error_handler:
            error_handler(error, reference, None)
        else:
            raise error
