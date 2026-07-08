from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Empty:
    """Represents the empty string ε."""
    pass


@dataclass(frozen=True)
class Char:
    """Represents one concrete character."""
    value: str


@dataclass(frozen=True)
class Concat:
    """Represents concatenation of two regular expressions."""
    left: "Regex"
    right: "Regex"


@dataclass(frozen=True)
class UnionExpr:
    """Represents disjunction / alternation."""
    left: "Regex"
    right: "Regex"


@dataclass(frozen=True)
class Intersect:
    """Represents conjunction / intersection of two regular expressions."""
    left: "Regex"
    right: "Regex"


@dataclass(frozen=True)
class Star:
    """Represents Kleene star."""
    expr: "Regex"


Regex = Union[Empty, Char, Concat, UnionExpr, Intersect, Star]


def contains_intersection(expr: Regex) -> bool:
    """Return whether a regex AST contains an Intersect node anywhere.

    The basic Thompson-style NFA builder does not support Intersect nodes.
    If an intersection occurs inside another construct such as concatenation,
    union, or star, the product-aware NFA builder must be used instead.
    """
    if isinstance(expr, Intersect):
        return True
    if isinstance(expr, Concat):
        return contains_intersection(expr.left) or contains_intersection(expr.right)
    if isinstance(expr, UnionExpr):
        return contains_intersection(expr.left) or contains_intersection(expr.right)
    if isinstance(expr, Star):
        return contains_intersection(expr.expr)
    if isinstance(expr, (Empty, Char)):
        return False
    raise TypeError(f"Unknown regex AST node: {type(expr)}")
