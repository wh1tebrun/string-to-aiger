from string_to_aiger.sequential.sequential_circuit import SequentialCircuit


def is_symbol_input(name: str) -> bool:
    return name.startswith("is_")


def validate_trace(
    circuit: SequentialCircuit,
    trace: list[dict[str, bool]],
) -> None:
    """Validate the stream-based input trace for a sequential circuit.

    Protocol:
    - The trace must not be empty.
    - The final step must have end = True.
    - All non-final steps must have end = False or omit end.
    - Each non-final step must activate exactly one symbol input.
    - The final step must not activate any symbol input.
    - Unknown symbol inputs such as is_c are allowed, so words outside the
      circuit alphabet can still be simulated and rejected naturally.
    - Unknown non-symbol inputs are rejected.
    """
    if not trace:
        raise ValueError("Trace must not be empty")

    if "end" not in circuit.inputs:
        raise ValueError("Sequential circuit must contain an 'end' input")

    known_inputs = set(circuit.inputs)

    for step_index, step in enumerate(trace):
        if not isinstance(step, dict):
            raise ValueError(f"Trace step {step_index} must be a dictionary")

        for name, value in step.items():
            if not isinstance(value, bool):
                raise ValueError(
                    f"Trace value for input '{name}' at step {step_index} must be bool"
                )

            if name not in known_inputs and not is_symbol_input(name):
                raise ValueError(
                    f"Unknown non-symbol input '{name}' at step {step_index}"
                )

    final_index = len(trace) - 1

    for step_index, step in enumerate(trace):
        is_final_step = step_index == final_index
        end_value = step.get("end", False)

        active_symbols = [
            name
            for name, value in step.items()
            if is_symbol_input(name) and value
        ]

        if is_final_step:
            if end_value is not True:
                raise ValueError("Final trace step must have end = True")

            if active_symbols:
                raise ValueError(
                    "Final trace step must not activate symbol inputs"
                )
        else:
            if end_value is True:
                raise ValueError(
                    f"Only the final trace step may have end = True; found at step {step_index}"
                )

            if len(active_symbols) != 1:
                raise ValueError(
                    f"Trace step {step_index} must activate exactly one symbol input"
                )
