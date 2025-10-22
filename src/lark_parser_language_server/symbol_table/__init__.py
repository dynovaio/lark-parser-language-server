import logging
from typing import Optional, cast

from lark_parser_language_server.symbol_table.flags import Kind
from lark_parser_language_server.symbol_table.symbol import Definition, Reference
from lark_parser_language_server.symbol_table.syntax_tree import (
    definitions_from_ast_node,
    references_from_ast_node,
)
from lark_parser_language_server.symbol_table.validators import (
    validate_shadowed_definition,
    validate_single_definition,
    validate_undefined_reference,
)
from lark_parser_language_server.syntax_tree.nodes import Ast, Import, Rule

logger = logging.getLogger(__name__)


class SymbolTable:
    definitions: dict[str, list[Definition]]
    references: dict[str, list[Reference]]

    definition_errors: list[tuple[Exception, Optional[Definition]]]
    reference_errors: list[tuple[Exception, Optional[Reference], Optional[Definition]]]

    _all_references: list[Reference]
    _all_definitions: list[Definition]

    def __init__(self):
        self.definitions = {}
        self.references = {}

        self.definition_errors = []
        self.reference_errors = []

        self._all_references = []
        self._all_definitions = []

    def __getitem__(self, name: str) -> Optional[list[Definition]]:
        return self.definitions.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self.definitions

    def _register_definition(self, definition: Definition) -> None:
        if definition.name not in self.definitions:
            self.definitions[definition.name] = []

        self.definitions[definition.name].append(definition)

    def _register_definition_error(
        self,
        error: Exception,
        definition: Optional[Definition] = None,
    ) -> None:
        self.definition_errors.append((error, definition))

    def _register_reference(self, reference: Reference) -> None:
        if reference.name not in self.references:
            self.references[reference.name] = []

        self.references[reference.name].append(reference)

    def _register_reference_error(
        self,
        error: Exception,
        reference: Optional[Reference] = None,
        definition: Optional[Definition] = None,
    ) -> None:
        self.reference_errors.append((error, reference, definition))

    def get_rule_definitions(self) -> list[Definition]:
        return [
            definition
            for definitions in self.definitions.values()
            for definition in definitions
            if definition.kind == Kind.RULE
        ]

    def get_terminal_definitions(self) -> list[Definition]:
        return [
            definition
            for definitions in self.definitions.values()
            for definition in definitions
            if definition.kind == Kind.TERMINAL
        ]

    def get_all_definitions(self) -> list[Definition]:
        if not self._all_definitions:
            template_parameters: list[Definition] = [
                cast(Definition, parameter)
                for rule in self.get_rule_definitions()
                for parameter in getattr(rule, "children", {}).items()
                if rule.children
            ]

            self._all_definitions = [
                *[
                    definition
                    for definitions in self.definitions.values()
                    for definition in definitions
                ],
                *template_parameters,
            ]

        return self._all_definitions

    def get_definition(self, name: str) -> Optional[Definition]:
        definitions = self.definitions.get(name)

        if definitions:
            return definitions[0]

        references = self.references.get(name) or []

        for reference in references:
            ast_node = getattr(reference, "ast_node", None)
            definitions = []

            if isinstance(ast_node, Rule):
                parent_name = str(ast_node.name)
                definitions = self.definitions.get(parent_name) or []

            if isinstance(ast_node, Import):
                parent_name = str(ast_node.alias) if ast_node.alias else ""
                definitions = self.definitions.get(parent_name) or []

            definition = definitions[0] if definitions else None
            if definition:
                return definition

        return None

    def get_all_references(self) -> list[Reference]:
        if not self._all_references:
            self._all_references = [
                reference
                for references in self.references.values()
                for reference in references
            ]

        return self._all_references

    def collect_definitions(self, ast: Ast) -> None:
        for statement in ast.statements:
            for definition in definitions_from_ast_node(statement):
                self._register_definition(definition)

    def validate_definitions(self):
        for name, definitions in self.definitions.items():
            validate_single_definition(
                name,
                definitions,
                self._register_definition_error,
            )

        child_definitions = [
            child_definition
            for rule in self.get_rule_definitions()
            for child_definition in getattr(rule, "children", {}).items()
            if rule.children
        ]

        for name, definitions in child_definitions:
            validate_single_definition(
                name,
                definitions,
                self._register_definition_error,
            )
            for definition in definitions:
                validate_shadowed_definition(
                    definition,
                    self.definitions,
                    self._register_definition_error,
                )

    def collect_references(self, ast: Ast) -> None:
        for statement in ast.statements:
            for reference in references_from_ast_node(statement):
                self._register_reference(reference)

    def validate_references(self):
        for name, references in self.references.items():
            validate_undefined_reference(
                name,
                references,
                self.definitions,
                self._register_reference_error,
            )
