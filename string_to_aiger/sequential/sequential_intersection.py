from string_to_aiger.logic.circuit import (
    BoolConst,
    InputVar,
    LengthIs,
    CharAtIs,
    And,
    Or,
    Expr,
)
from .sequential_circuit import SequentialCircuit


def prefixed_name(prefix: str, name: str) -> str:
    """Return a prefixed variable name."""
    return f"{prefix}_{name}"


def rename_latch_vars(expr: Expr, latch_names: set[str], prefix: str) -> Expr:
    """Rename only latch variables inside an expression.

    Inputs such as is_a, is_b, and end are shared between circuits
    and must not be renamed.

    Latch variables such as state_0, state_1, ... are renamed with
    the given prefix.
    """
    if isinstance(expr, BoolConst):
        return expr

    if isinstance(expr, InputVar):
        if expr.name in latch_names:
            return InputVar(prefixed_name(prefix, expr.name))

        return expr

    if isinstance(expr, LengthIs):
        return expr

    if isinstance(expr, CharAtIs):
        return expr

    if isinstance(expr, And):
        return And(
            rename_latch_vars(expr.left, latch_names, prefix),
            rename_latch_vars(expr.right, latch_names, prefix),
        )

    if isinstance(expr, Or):
        return Or(
            rename_latch_vars(expr.left, latch_names, prefix),
            rename_latch_vars(expr.right, latch_names, prefix),
        )

    raise TypeError(f"Unknown expression type: {type(expr)}")


def add_prefixed_latches(
    target: SequentialCircuit,
    source: SequentialCircuit,
    prefix: str,
) -> None:
    """Copy latches from source to target with renamed latch variables."""
    latch_names = set(source.latches.keys())

    for name, latch in source.latches.items():
        new_name = prefixed_name(prefix, name)
        new_next_expr = rename_latch_vars(
            latch.next_expr,
            latch_names,
            prefix,
        )

        target.add_latch(
            new_name,
            new_next_expr,
            init=latch.init,
        )


def renamed_output_expr(
    source: SequentialCircuit,
    output_name: str,
    prefix: str,
) -> Expr:
    """Return a renamed output expression from a source circuit."""
    if output_name not in source.outputs:
        raise ValueError(f"Missing output: {output_name}")

    latch_names = set(source.latches.keys())

    return rename_latch_vars(
        source.outputs[output_name],
        latch_names,
        prefix,
    )


def merge_for_intersection(
    left: SequentialCircuit,
    right: SequentialCircuit,
) -> SequentialCircuit:
    """Merge two sequential circuits for language intersection.

    Both circuits read the same input stream.
    Their latches are renamed to avoid name collisions.
    The final accept output is left.accept AND right.accept.
    """
    combined = SequentialCircuit()

    for name in sorted(left.inputs | right.inputs):
        combined.add_input(name)

    add_prefixed_latches(combined, left, "left")
    add_prefixed_latches(combined, right, "right")

    left_accept = renamed_output_expr(left, "accept", "left")
    right_accept = renamed_output_expr(right, "accept", "right")

    combined.add_output(
        "accept",
        And(left_accept, right_accept),
    )

    return combined
