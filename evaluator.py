from circuit import BoolConst, InputVar, LengthIs, CharAtIs, And, Or, Expr


def evaluate(expr: Expr, candidate: str, env: dict[str, bool] | None = None) -> bool:
    """Evaluate a logical expression on a candidate string.

    Generic InputVar nodes are read from env.
    LengthIs and CharAtIs are evaluated directly on the candidate string.
    """
    if env is None:
        env = {}

    if isinstance(expr, BoolConst):
        return expr.value

    if isinstance(expr, InputVar):
        if expr.name not in env:
            raise ValueError(f"Missing value for input variable: {expr.name}")
        return env[expr.name]

    if isinstance(expr, LengthIs):
        return len(candidate) == expr.value

    if isinstance(expr, CharAtIs):
        if expr.index >= len(candidate):
            return False
        return candidate[expr.index] == expr.char

    if isinstance(expr, And):
        return evaluate(expr.left, candidate, env) and evaluate(expr.right, candidate, env)

    if isinstance(expr, Or):
        return evaluate(expr.left, candidate, env) or evaluate(expr.right, candidate, env)

    raise TypeError(f"Unknown expression type: {type(expr)}")
