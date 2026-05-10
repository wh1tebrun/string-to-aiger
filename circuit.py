from dataclasses import dataclass
from typing import Union


@dataclass
class BoolConst:
    value: bool


@dataclass
class InputVar:
    """Generic boolean input variable used by later encodings."""
    name: str


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


Expr = Union[BoolConst, InputVar, LengthIs, CharAtIs, And, Or]


def is_true(expr: Expr) -> bool:
    return isinstance(expr, BoolConst) and expr.value is True


def is_false(expr: Expr) -> bool:
    return isinstance(expr, BoolConst) and expr.value is False


def and_all(expressions: list[Expr]) -> Expr:
    filtered: list[Expr] = []

    for expr in expressions:
        if is_false(expr):
            return BoolConst(False)

        if is_true(expr):
            continue

        filtered.append(expr)

    if not filtered:
        return BoolConst(True)

    result = filtered[0]
    for expr in filtered[1:]:
        result = And(result, expr)

    return result


def or_all(expressions: list[Expr]) -> Expr:
    filtered: list[Expr] = []

    for expr in expressions:
        if is_true(expr):
            return BoolConst(True)

        if is_false(expr):
            continue

        filtered.append(expr)

    if not filtered:
        return BoolConst(False)

    result = filtered[0]
    for expr in filtered[1:]:
        result = Or(result, expr)

    return result
