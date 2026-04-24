def parse(expr: str) -> list[str]:
    """Parse a disjunction of concrete strings separated by '|'."""
    if expr is None:
        raise ValueError("Expression must not be None")

    expr = expr.strip()
    if not expr:
        raise ValueError("Expression must not be empty")

    parts = expr.split("|")
    strings = [p.strip() for p in parts]

    if any(s == "" for s in strings):
        raise ValueError("Empty alternative in disjunction is not allowed")

    return strings
