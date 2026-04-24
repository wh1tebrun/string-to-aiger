from dataclasses import dataclass
from typing import Union


@dataclass
class BoolConst:
    value: bool


@dataclass
class LengthIs:
    value: int


@dataclass
class CharAtIs:
    index: int
    char: str


@dataclass
class And:
    left: "Expr"
    right: "Expr"


@dataclass
class Or:
    left: "Expr"
    right: "Expr"


Expr = Union[BoolConst, LengthIs, CharAtIs, And, Or]


def and_all(expressions: list[Expr]) -> Expr:
    if not expressions:
        return BoolConst(True)

    result = expressions[0]
    for expr in expressions[1:]:
        result = And(result, expr)
    return result


def or_all(expressions: list[Expr]) -> Expr:
    if not expressions:
        return BoolConst(False)

    result = expressions[0]
    for expr in expressions[1:]:
        result = Or(result, expr)
    return result
