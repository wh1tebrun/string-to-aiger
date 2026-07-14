from string_to_aiger.logic.circuit import (
    BoolConst,
    InputVar,
    LengthIs,
    CharAtIs,
    And,
    Or,
)
from string_to_aiger.logic.evaluator import evaluate

from .sequential_circuit import Not, SequentialCircuit, SequentialExpr
from .sequential_trace import validate_trace


def evaluate_sequential_expr(
    expr: SequentialExpr,
    env: dict[str, bool],
) -> bool:
    """Evaluate sequential expressions, including protocol negation."""
    if isinstance(expr, BoolConst):
        return expr.value

    if isinstance(expr, InputVar):
        return env.get(expr.name, False)

    if isinstance(expr, Not):
        return not evaluate_sequential_expr(expr.operand, env)

    if isinstance(expr, And):
        return evaluate_sequential_expr(
            expr.left,  # type: ignore[arg-type]
            env,
        ) and evaluate_sequential_expr(
            expr.right,  # type: ignore[arg-type]
            env,
        )

    if isinstance(expr, Or):
        return evaluate_sequential_expr(
            expr.left,  # type: ignore[arg-type]
            env,
        ) or evaluate_sequential_expr(
            expr.right,  # type: ignore[arg-type]
            env,
        )

    if isinstance(expr, (LengthIs, CharAtIs)):
        return evaluate(expr, candidate="", env=env)

    raise TypeError(f"Unsupported sequential expression: {type(expr)}")


def build_env(
    circuit: SequentialCircuit,
    latch_values: dict[str, bool],
    inputs: dict[str, bool],
) -> dict[str, bool]:
    env: dict[str, bool] = {}

    for name in circuit.inputs:
        # Missing inputs default to False. This keeps traces compact and also
        # means that symbols not present in the circuit alphabet are naturally
        # rejected because their corresponding input signal is never true.
        env[name] = inputs.get(name, False)

    for name in circuit.latches:
        env[name] = latch_values[name]

    return env


def initial_latch_values(circuit: SequentialCircuit) -> dict[str, bool]:
    return {
        name: latch.init
        for name, latch in circuit.latches.items()
    }


def simulate(
    circuit: SequentialCircuit,
    trace: list[dict[str, bool]],
    validate: bool = True,
) -> list[dict[str, bool]]:
    """Simulate a sequential circuit over a finite input trace."""
    if validate:
        validate_trace(circuit, trace)

    latch_values = initial_latch_values(circuit)
    outputs_per_step: list[dict[str, bool]] = []

    for inputs in trace:
        env = build_env(circuit, latch_values, inputs)

        outputs = {
            name: evaluate_sequential_expr(expr, env)
            for name, expr in circuit.outputs.items()
        }
        outputs_per_step.append(outputs)

        next_latch_values = {
            name: evaluate_sequential_expr(latch.next_expr, env)
            for name, latch in circuit.latches.items()
        }

        latch_values = next_latch_values

    return outputs_per_step
