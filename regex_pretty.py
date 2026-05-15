from regex_ast import Empty, Char, Concat, UnionExpr, Intersect, Star, Regex


def pretty_regex(expr: Regex) -> str:
    """Return a readable representation of a regex AST."""
    if isinstance(expr, Empty):
        return "ε"

    if isinstance(expr, Char):
        return expr.value

    if isinstance(expr, Concat):
        return f"({pretty_regex(expr.left)}{pretty_regex(expr.right)})"

    if isinstance(expr, UnionExpr):
        return f"({pretty_regex(expr.left)} | {pretty_regex(expr.right)})"

    if isinstance(expr, Intersect):
        return f"({pretty_regex(expr.left)} & {pretty_regex(expr.right)})"

    if isinstance(expr, Star):
        return f"({pretty_regex(expr.expr)})*"

    raise TypeError(f"Unknown regex AST node: {type(expr)}")
