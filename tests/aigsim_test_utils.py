import os
import re
from pathlib import Path


AIGSIM_ENV_VAR = "AIGSIM"


def require_aigsim() -> str:
    """Return the configured aigsim path.

    External semantic validation tests must not silently pass when aigsim is
    unavailable. These tests check generated AIGER files by actually invoking
    aigsim, so missing aigsim is a test setup error.

    Example:

        export AIGSIM=/path/to/aiger/aigsim
    """
    aigsim = os.environ.get(AIGSIM_ENV_VAR)

    if not aigsim:
        raise AssertionError(
            "AIGSIM environment variable is not set. "
            "Set it before running external semantic tests, for example: "
            "export AIGSIM=/path/to/aiger/aigsim"
        )

    if not Path(aigsim).exists():
        raise AssertionError(f"AIGSIM does not exist: {aigsim}")

    return aigsim


def parse_aiger_header(aag_text: str) -> tuple[int, int, int, int, int]:
    """Parse the ASCII AIGER header line and return (M, I, L, O, A)."""
    first_line = aag_text.splitlines()[0]
    parts = first_line.split()
    if len(parts) != 6 or parts[0] != "aag":
        raise AssertionError(f"Invalid AIGER header: {first_line}")
    return tuple(int(value) for value in parts[1:])  # type: ignore[return-value]


def parse_aiger_input_names(aag_text: str) -> list[str]:
    """Return input names in i0, i1, ... order from AIGER symbol lines."""
    names_by_index: dict[int, str] = {}
    for line in aag_text.splitlines():
        line = line.strip()
        if not line.startswith("i"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        index_text, name = parts
        if not index_text[1:].isdigit():
            continue
        names_by_index[int(index_text[1:])] = name
    return [names_by_index[i] for i in sorted(names_by_index)]


def encode_bounded_candidate(candidate: str, input_names: list[str]) -> str:
    """Encode one candidate word as a bounded AIGER input vector.

    Supported input-name conventions:

    - len_is_N
    - x_POS_is_CHAR
    """
    bits: list[str] = []
    for name in input_names:
        if name.startswith("len_is_"):
            length = int(name.removeprefix("len_is_"))
            bits.append("1" if len(candidate) == length else "0")
            continue
        match = re.fullmatch(r"x_(\d+)_is_(.+)", name)
        if match:
            position = int(match.group(1))
            symbol = match.group(2)
            bit = position < len(candidate) and candidate[position] == symbol
            bits.append("1" if bit else "0")
            continue
        raise ValueError(f"Unsupported bounded input name: {name}")
    return "".join(bits)


def encode_sequential_step(char: str | None, input_names: list[str]) -> str:
    """Encode one sequential input step.

    char is None for the final end step.
    """
    bits: list[str] = []
    for name in input_names:
        if name == "end":
            bits.append("1" if char is None else "0")
            continue
        if name.startswith("is_"):
            symbol = name.removeprefix("is_")
            bits.append("1" if char == symbol else "0")
            continue
        raise ValueError(f"Unsupported sequential input name: {name}")
    return "".join(bits)


def encode_sequential_trace(candidate: str, input_names: list[str]) -> list[str]:
    """Encode a candidate word as a sequential aigsim trace.

    Each character is encoded as one input vector, followed by a final
    end-step vector where end=1 and all symbol inputs are 0.
    """
    vectors = [encode_sequential_step(char, input_names) for char in candidate]
    # Final step: end = true, all symbol inputs false.
    vectors.append(encode_sequential_step(None, input_names))
    return vectors


def parse_bounded_aigsim_outputs(stdout: str) -> list[int]:
    """Parse combinational aigsim output lines and return the output bits.

    Handles both:
        input_vector output   (2-token lines)
        output                (1-token lines for zero-input circuits)
    """
    outputs: list[int] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("Trace is a witness"):
            continue
        parts = line.split()
        if len(parts) == 1 and parts[0] in {"0", "1"}:
            outputs.append(int(parts[0]))
            continue
        if len(parts) == 2 and parts[1] in {"0", "1"}:
            outputs.append(int(parts[1]))
            continue
    if not outputs:
        raise AssertionError(f"Could not parse bounded aigsim output:\n{stdout}")
    return outputs


def parse_final_sequential_aigsim_output(stdout: str) -> int:
    """Extract the final output bit from sequential aigsim output.

    Handles the standard 4-token format (current_state input output next_state)
    and degenerate shorter formats observed in edge cases.
    """
    final_output: int | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("Trace is a witness"):
            continue
        parts = line.split()
        if len(parts) == 4:
            _current_state, input_vector, output, _next_state = parts
            if set(input_vector) <= {"0", "1"} and output in {"0", "1"}:
                final_output = int(output)
            continue
        if len(parts) == 2:
            _input_vector, output = parts
            if output in {"0", "1"}:
                final_output = int(output)
            continue
        if len(parts) == 1 and parts[0] in {"0", "1"}:
            final_output = int(parts[0])
    if final_output is None:
        raise AssertionError(f"Could not parse sequential aigsim output:\n{stdout}")
    return final_output


def encode_sequential_assignment(
    active_inputs: set[str],
    input_names: list[str],
) -> str:
    """Encode an arbitrary sequential Boolean input assignment.

    Unlike encode_sequential_trace, this helper intentionally permits invalid
    vectors such as two simultaneously active symbol inputs.  It is used by
    protocol-regression tests to check that the generated AIGER rejects them.
    """
    unknown_inputs = active_inputs - set(input_names)

    if unknown_inputs:
        raise ValueError(
            f"Unknown active sequential inputs: {sorted(unknown_inputs)}"
        )

    return "".join(
        "1" if name in active_inputs else "0"
        for name in input_names
    )
