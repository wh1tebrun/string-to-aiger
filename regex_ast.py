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
class Star:
    """Represents Kleene star."""
    expr: "Regex"


Regex = Union[Empty, Char, Concat, UnionExpr, Star]