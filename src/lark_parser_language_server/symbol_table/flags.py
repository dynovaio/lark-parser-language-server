import logging
from enum import Flag, StrEnum, auto

logger = logging.getLogger(__name__)


class Directives(Flag):
    OVERRIDED = auto()
    EXTENDED = auto()
    IGNORED = auto()
    DECLARED = auto()
    IMPORTED = auto()


class Kind(StrEnum):
    RULE = "rule"
    TERMINAL = "terminal"

    def __repr__(self) -> str:
        return f"Kind.{self.name}"


class Modifiers(Flag):
    INLINED = auto()
    CONDITIONALLY_INLINED = auto()
    PINNED = auto()

    @classmethod
    def from_char(cls, char: str) -> "Modifiers":
        return {
            "_": cls.INLINED,
            "?": cls.CONDITIONALLY_INLINED,
            "!": cls.PINNED,
        }.get(char, cls(0))

    @classmethod
    def to_char(cls, modifier: "Modifiers") -> str:
        return {
            cls.INLINED: "_",
            cls.CONDITIONALLY_INLINED: "?",
            cls.PINNED: "!",
        }.get(modifier, "")
