from circuit import BoolConst, LengthIs, CharAtIs, And, Or, Expr


def pretty(expr: Expr) -> str:
    if isinstance(expr, BoolConst):
        return "true" if expr.value else "false"

    if isinstance(expr, LengthIs):
        return f"(len == {expr.value})"

    if isinstance(expr, CharAtIs):
        return f"(x[{expr.index}] == '{expr.char}')"

    if isinstance(expr, And):
        return f"({pretty(expr.left)} AND {pretty(expr.right)})"

    if isinstance(expr, Or):
        return f"({pretty(expr.left)} OR {pretty(expr.right)})"

    raise TypeError(f"Unknown expression type: {type(expr)}")
