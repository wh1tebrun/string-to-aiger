from dataclasses import dataclass
from typing import Union


@dataclass
class Input:
    name: str


@dataclass
class Const:
    value: bool


@dataclass
class AndGate:
    left: int
    right: int


@dataclass
class OrGate:
    left: int
    right: int


Node = Union[Input, Const, AndGate, OrGate]
