from dataclasses import dataclass


@dataclass(frozen=True)
class AigerHeader:
    max_var_index: int
    inputs: int
    latches: int
    outputs: int
    and_gates: int


def parse_header(line: str) -> AigerHeader:
    parts = line.split()

    if len(parts) != 6:
        raise ValueError(f"Invalid AIGER header field count: {line}")

    if parts[0] != "aag":
        raise ValueError(f"Expected ASCII AIGER header starting with 'aag': {line}")

    try:
        max_var_index = int(parts[1])
        inputs = int(parts[2])
        latches = int(parts[3])
        outputs = int(parts[4])
        and_gates = int(parts[5])
    except ValueError as error:
        raise ValueError(f"Invalid integer in AIGER header: {line}") from error

    values = [max_var_index, inputs, latches, outputs, and_gates]

    if any(value < 0 for value in values):
        raise ValueError(f"AIGER header values must be non-negative: {line}")

    return AigerHeader(
        max_var_index=max_var_index,
        inputs=inputs,
        latches=latches,
        outputs=outputs,
        and_gates=and_gates,
    )


def parse_literal(text: str, max_literal: int) -> int:
    try:
        literal = int(text)
    except ValueError as error:
        raise ValueError(f"Invalid AIGER literal: {text}") from error

    if literal < 0:
        raise ValueError(f"AIGER literal must be non-negative: {literal}")

    if literal > max_literal:
        raise ValueError(
            f"AIGER literal {literal} exceeds maximum allowed literal {max_literal}"
        )

    return literal


def validate_input_literal(literal: int) -> None:
    if literal == 0:
        raise ValueError("Input literal must not be constant false literal 0")

    if literal % 2 != 0:
        raise ValueError(f"Input literal must be even: {literal}")


def validate_latch_line(line: str, max_literal: int) -> None:
    parts = line.split()

    if len(parts) not in (2, 3):
        raise ValueError(f"Invalid latch line: {line}")

    lhs = parse_literal(parts[0], max_literal)
    rhs = parse_literal(parts[1], max_literal)

    if lhs == 0:
        raise ValueError("Latch current-state literal must not be 0")

    if lhs % 2 != 0:
        raise ValueError(f"Latch current-state literal must be even: {lhs}")

    if len(parts) == 3:
        init = parts[2]
        if init not in ("0", "1"):
            raise ValueError(f"Unsupported latch init value: {init}")

    # rhs is allowed to be 0 or 1, so no evenness check here.
    _ = rhs


def validate_output_line(line: str, max_literal: int) -> None:
    parts = line.split()

    if len(parts) != 1:
        raise ValueError(f"Invalid output line: {line}")

    parse_literal(parts[0], max_literal)


def validate_and_line(line: str, max_literal: int) -> None:
    parts = line.split()

    if len(parts) != 3:
        raise ValueError(f"Invalid AND gate line: {line}")

    lhs = parse_literal(parts[0], max_literal)
    rhs0 = parse_literal(parts[1], max_literal)
    rhs1 = parse_literal(parts[2], max_literal)

    if lhs == 0:
        raise ValueError("AND gate lhs literal must not be 0")

    if lhs % 2 != 0:
        raise ValueError(f"AND gate lhs literal must be even: {lhs}")

    # rhs0 and rhs1 may be inverted literals, so they may be odd.
    _ = rhs0
    _ = rhs1


def validate_symbol_or_comment_section(lines: list[str]) -> None:
    for line in lines:
        if line == "c":
            return

        if line.startswith(("i", "l", "o")):
            parts = line.split(maxsplit=1)

            if len(parts) != 2:
                raise ValueError(f"Invalid symbol line: {line}")

            index_text = parts[0][1:]

            if not index_text.isdigit():
                raise ValueError(f"Invalid symbol index in line: {line}")

            continue

        # Comment body lines after 'c' are accepted by returning above.
        # Unknown metadata before the comment section is rejected.
        raise ValueError(f"Invalid symbol/comment line before comment section: {line}")


def validate_aiger(aiger_text: str) -> AigerHeader:
    """Validate basic structural properties of an ASCII AIGER file.

    This is not a full semantic equivalence checker. It verifies that the
    generated ASCII AIGER text is structurally well-formed according to the
    header counts and literal bounds.
    """
    lines = aiger_text.splitlines()

    if not lines:
        raise ValueError("AIGER text is empty")

    header = parse_header(lines[0])
    max_literal = 2 * header.max_var_index + 1

    expected_body_lines = (
        header.inputs
        + header.latches
        + header.outputs
        + header.and_gates
    )

    if len(lines) < 1 + expected_body_lines:
        raise ValueError(
            "AIGER body is shorter than expected from the header counts"
        )

    body = lines[1:1 + expected_body_lines]
    remainder = lines[1 + expected_body_lines:]

    input_lines = body[:header.inputs]
    latch_start = header.inputs
    latch_end = latch_start + header.latches
    output_end = latch_end + header.outputs

    latch_lines = body[latch_start:latch_end]
    output_lines = body[latch_end:output_end]
    and_lines = body[output_end:]

    for line in input_lines:
        literal = parse_literal(line, max_literal)
        validate_input_literal(literal)

    for line in latch_lines:
        validate_latch_line(line, max_literal)

    for line in output_lines:
        validate_output_line(line, max_literal)

    for line in and_lines:
        validate_and_line(line, max_literal)

    validate_symbol_or_comment_section(remainder)

    return header
