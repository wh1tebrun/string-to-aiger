from __future__ import annotations

from collections.abc import Iterable

from string_to_aiger.logic.circuit import BoolConst, InputVar, And, Or

from .sequential_circuit import Not, SequentialCircuit, SequentialExpr


PROTOCOL_VALID_LATCH = "protocol_valid"


def and_all(expressions: Iterable[SequentialExpr]) -> SequentialExpr:
    """Build a conjunction that is true for an empty input collection."""
    result: SequentialExpr = BoolConst(True)

    for expression in expressions:
        result = And(result, expression)  # type: ignore[arg-type]

    return result


def or_all(expressions: Iterable[SequentialExpr]) -> SequentialExpr:
    """Build a disjunction that is false for an empty input collection."""
    result: SequentialExpr = BoolConst(False)

    for expression in expressions:
        result = Or(result, expression)  # type: ignore[arg-type]

    return result


def negate(expression: SequentialExpr) -> SequentialExpr:
    """Create a small simplified negation expression."""
    if isinstance(expression, BoolConst):
        return BoolConst(not expression.value)

    if isinstance(expression, Not):
        return expression.operand

    return Not(expression)


def protocol_step_expressions(
    circuit: SequentialCircuit,
) -> tuple[SequentialExpr, SequentialExpr, SequentialExpr]:
    """Return (valid_character_step, valid_end_step, valid_current_step).

    A valid character step has end=false and exactly one known symbol input
    active.  A valid end step has end=true and no symbol input active.
    """
    if "end" not in circuit.inputs:
        raise ValueError("Sequential circuit must contain an 'end' input")

    symbol_names = sorted(
        name
        for name in circuit.inputs
        if name.startswith("is_")
    )
    symbol_vars = [InputVar(name) for name in symbol_names]

    exactly_one_alternatives: list[SequentialExpr] = []

    for active_index, active_symbol in enumerate(symbol_vars):
        terms: list[SequentialExpr] = [active_symbol]

        for other_index, other_symbol in enumerate(symbol_vars):
            if other_index != active_index:
                terms.append(negate(other_symbol))

        exactly_one_alternatives.append(and_all(terms))

    exactly_one_symbol = or_all(exactly_one_alternatives)
    no_symbol = and_all(negate(symbol) for symbol in symbol_vars)

    valid_character_step = and_all([
        negate(InputVar("end")),
        exactly_one_symbol,
    ])
    valid_end_step = and_all([
        InputVar("end"),
        no_symbol,
    ])
    valid_current_step = or_all([
        valid_character_step,
        valid_end_step,
    ])

    return valid_character_step, valid_end_step, valid_current_step


def add_input_protocol_guard(circuit: SequentialCircuit) -> SequentialCircuit:
    """Add one persistent latch that rejects invalid input encodings.

    The generated AIGER exposes one Boolean input for every alphabet symbol.
    Without an in-circuit protocol guard, a model checker may activate two
    symbol inputs simultaneously.  That vector does not represent a string,
    but it may advance several NFA transitions at once and create a false
    accepting trace.

    The protocol_valid latch is initialized to true and remains true only
    while every previous input step was valid.  The accept output additionally
    checks that the current final step is a valid end step.

    This transformation is idempotent and must be applied once to the final
    sequential circuit, after structural intersection composition.
    """
    if PROTOCOL_VALID_LATCH in circuit.latches:
        return circuit

    if "accept" not in circuit.outputs:
        raise ValueError("Sequential circuit must contain an 'accept' output")

    _valid_character_step, valid_end_step, valid_current_step = (
        protocol_step_expressions(circuit)
    )

    protocol_valid = InputVar(PROTOCOL_VALID_LATCH)
    protocol_valid_next = and_all([
        protocol_valid,
        valid_current_step,
    ])

    original_accept = circuit.outputs["accept"]

    circuit.add_latch(
        PROTOCOL_VALID_LATCH,
        protocol_valid_next,
        init=True,
    )
    circuit.outputs["accept"] = and_all([
        original_accept,
        protocol_valid,
        valid_end_step,
    ])

    return circuit
