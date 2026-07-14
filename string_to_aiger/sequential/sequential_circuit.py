from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

from string_to_aiger.logic.circuit import Expr


@dataclass(frozen=True)
class Not:
    """Boolean negation used by sequential-only protocol logic.

    The original shared expression language only needs positive AND/OR
    expressions for the existing compiler stages.  The sequential input
    protocol additionally needs negation in order to express one-hot symbol
    inputs and a symbol-free end step.
    """

    operand: "SequentialExpr"


SequentialExpr: TypeAlias = Expr | Not


@dataclass(frozen=True)
class Latch:
    """A state-holding element of a sequential circuit."""

    name: str
    next_expr: SequentialExpr
    init: bool = False


@dataclass
class SequentialCircuit:
    """Intermediate representation for sequential circuits.

    Inputs are external boolean signals.
    Latches represent state.
    Outputs are boolean expressions over inputs and latch values.
    """

    inputs: set[str] = field(default_factory=set)
    latches: dict[str, Latch] = field(default_factory=dict)
    outputs: dict[str, SequentialExpr] = field(default_factory=dict)

    def add_input(self, name: str) -> None:
        self.inputs.add(name)

    def add_latch(
        self,
        name: str,
        next_expr: SequentialExpr,
        init: bool = False,
    ) -> None:
        if name in self.latches:
            raise ValueError(f"Latch already exists: {name}")

        self.latches[name] = Latch(
            name=name,
            next_expr=next_expr,
            init=init,
        )

    def add_output(self, name: str, expr: SequentialExpr) -> None:
        if name in self.outputs:
            raise ValueError(f"Output already exists: {name}")

        self.outputs[name] = expr
