from dataclasses import dataclass

from string_to_aiger.regex.regex_ast import (
    Empty,
    Char,
    Concat,
    UnionExpr,
    Intersect,
    Star,
    Regex,
)


@dataclass(frozen=True)
class LengthInfo:
    min_length: int
    max_length: int | None
    exact: bool = True

    @property
    def is_finite(self) -> bool:
        return self.max_length is not None


def regex_length(expr: Regex) -> LengthInfo:
    """Compute length information for a regex AST.

    For ordinary regex operators, the result is exact.

    For intersection, the result is conservative because exact intersection
    length analysis generally requires automata-based reasoning.
    """
    if isinstance(expr, Empty):
        return LengthInfo(
            min_length=0,
            max_length=0,
        )

    if isinstance(expr, Char):
        return LengthInfo(
            min_length=1,
            max_length=1,
        )

    if isinstance(expr, Concat):
        left = regex_length(expr.left)
        right = regex_length(expr.right)

        return LengthInfo(
            min_length=left.min_length + right.min_length,
            max_length=add_optional_lengths(left.max_length, right.max_length),
            exact=left.exact and right.exact,
        )

    if isinstance(expr, UnionExpr):
        left = regex_length(expr.left)
        right = regex_length(expr.right)

        return LengthInfo(
            min_length=min(left.min_length, right.min_length),
            max_length=max_optional_lengths(left.max_length, right.max_length),
            exact=left.exact and right.exact,
        )

    if isinstance(expr, Intersect):
        left = regex_length(expr.left)
        right = regex_length(expr.right)

        return LengthInfo(
            min_length=max(left.min_length, right.min_length),
            max_length=intersection_max_length(left.max_length, right.max_length),
            exact=False,
        )

    if isinstance(expr, Star):
        inner = regex_length(expr.expr)

        if inner.max_length == 0:
            max_length = 0
        else:
            max_length = None

        return LengthInfo(
            min_length=0,
            max_length=max_length,
            exact=inner.exact,
        )

    raise TypeError(f"Unknown regex AST node: {type(expr)}")


def add_optional_lengths(
    left: int | None,
    right: int | None,
) -> int | None:
    if left is None or right is None:
        return None

    return left + right


def max_optional_lengths(
    left: int | None,
    right: int | None,
) -> int | None:
    if left is None or right is None:
        return None

    return max(left, right)


def intersection_max_length(
    left: int | None,
    right: int | None,
) -> int | None:
    if left is not None and right is not None:
        return min(left, right)

    if left is not None:
        return left

    if right is not None:
        return right

    return None


def is_bound_complete(expr: Regex, bound: int) -> bool:
    """Return True if the bound covers all possible accepted word lengths."""
    if bound < 0:
        raise ValueError("Bound must be non-negative")

    info = regex_length(expr)

    return info.max_length is not None and bound >= info.max_length
