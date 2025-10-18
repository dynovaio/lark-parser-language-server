import logging
from pathlib import Path

from lark import Lark

logger = logging.getLogger(__name__)


def _get_parser() -> Lark:
    try:
        return getattr(_get_parser, "cache")
    except AttributeError:
        grammar_path = Path(__file__).parent / "grammars" / "lark4ls.lark"
        grammar = grammar_path.read_text(encoding="utf-8")

        parser = Lark(
            grammar,
            parser="lalr",
            lexer="basic",
            propagate_positions=True,
            maybe_placeholders=False,
            start="start",
            source_path=str(grammar_path),
        )
        setattr(_get_parser, "cache", parser)

        return getattr(_get_parser, "cache")


PARSER = _get_parser()
