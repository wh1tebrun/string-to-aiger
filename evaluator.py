from circuit import BoolConst, LengthIs, CharAtIs, And, Or, Expr


def evaluate(expr: Expr, candidate: str) -> bool:
    if isinstance(expr, BoolConst):
        return expr.value

    if isinstance(expr, LengthIs):
        return len(candidate) == expr.value

    if isinstance(expr, CharAtIs):
        if expr.index >= len(candidate):
            return False
        return candidate[expr.index] == expr.char

    if isinstance(expr, And):
        return evaluate(expr.left, candidate) and evaluate(expr.right, candidate)

    if isinstance(expr, Or):
        return evaluate(expr.left, candidate) or evaluate(expr.right, candidate)

    raise TypeError("Unknown expression")