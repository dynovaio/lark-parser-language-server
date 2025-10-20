from typing import Optional

from lark_parser_language_server.symbol_table.symbol import Position


class SymbolTableError(Exception):
    """Base exception for symbol table errors."""

    line: int = 0
    column: int = 0
    width: int = 1

    def __init__(self, message: str, position: Optional[Position] = None):
        super().__init__(message)
        if position:
            self.line = position.line
            self.column = position.column


class DefinitionNotFoundError(SymbolTableError):
    """Exception raised when a symbol definition is not found."""

    def __init__(self, name: str, position: Optional[Position] = None):
        super().__init__(f"Definition for symbol '{name}' not found.", position)
        self.name = name
        self.width = len(name)


class ShadowedDefinitionError(SymbolTableError):
    """Exception raised when a symbol definition is shadowed."""

    def __init__(self, name: str, position: Optional[Position] = None):
        kind = "terminal" if name.isupper() else "rule"
        super().__init__(
            f"Template parameter '{name}' conflicts with existing {kind} '{name}'.",
            position,
        )
        self.name = name
        self.width = len(name)


class MultipleDefinitionsError(SymbolTableError):
    """Exception raised when multiple symbol definitions are found."""

    def __init__(self, name: str, position: Optional[Position] = None):
        kind = "terminal" if name.isupper() else "rule"
        super().__init__(f"Multiple definitions found for {kind} '{name}'.", position)
        self.name = name
        self.width = len(name)


class DefinitionNotFoundForReferenceError(SymbolTableError):
    """Exception raised when a reference has no corresponding definition."""

    def __init__(self, name: str, position: Optional[Position] = None):
        kind = "terminal" if name.isupper() else "rule"
        super().__init__(f"No definition found for {kind} '{name}'.", position)
        self.name = name
        self.width = len(name)
