from string_to_aiger.regex.regex_ast import (
    Empty,
    Char,
    Concat,
    UnionExpr,
    Intersect,
    Star,
    Regex,
)


def regex_alphabet(expr: Regex) -> set[str]:
    """Return all concrete symbols used by a regex AST."""
    if isinstance(expr, Empty):
        return set()

    if isinstance(expr, Char):
        return {expr.value}

    if isinstance(expr, Concat):
        return regex_alphabet(expr.left) | regex_alphabet(expr.right)

    if isinstance(expr, UnionExpr):
        return regex_alphabet(expr.left) | regex_alphabet(expr.right)

    if isinstance(expr, Intersect):
        return regex_alphabet(expr.left) | regex_alphabet(expr.right)

    if isinstance(expr, Star):
        return regex_alphabet(expr.expr)

    raise TypeError(f"Unknown regex AST node: {type(expr)}")
