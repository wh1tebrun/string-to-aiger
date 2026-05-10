from circuit import Expr
from evaluator import evaluate
from sequential_circuit import SequentialCircuit


def build_env(
    circuit: SequentialCircuit,
    latch_values: dict[str, bool],
    inputs: dict[str, bool],
) -> dict[str, bool]:
    env: dict[str, bool] = {}

    for name in circuit.inputs:
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
) -> list[dict[str, bool]]:
    """Simulate a sequential circuit over a finite input trace."""
    latch_values = initial_latch_values(circuit)
    outputs_per_step: list[dict[str, bool]] = []

    for inputs in trace:
        env = build_env(circuit, latch_values, inputs)

        outputs = {
            name: evaluate(expr, candidate="", env=env)
            for name, expr in circuit.outputs.items()
        }
        outputs_per_step.append(outputs)

        next_latch_values = {
            name: evaluate(latch.next_expr, candidate="", env=env)
            for name, latch in circuit.latches.items()
        }

        latch_values = next_latch_values

    return outputs_per_step