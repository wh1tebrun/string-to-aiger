import re
import subprocess
from pathlib import Path

from aigsim_test_utils import require_aigsim
from string_to_aiger.nfa.nfa_evaluator import accepts
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter
from string_to_aiger.sequential.sequential_regex_compiler import (
    compile_regex_to_sequential,
)


def parse_aiger_header(aag_text: str) -> tuple[int, int, int, int, int]:
    """Parse the ASCII AIGER header.

    Returns:

        M, I, L, O, A
    """
    first_line = aag_text.splitlines()[0]
    parts = first_line.split()

    if len(parts) != 6 or parts[0] != "aag":
        raise AssertionError(f"Invalid AIGER header: {first_line}")

    return tuple(int(value) for value in parts[1:])  # type: ignore[return-value]


def corrupt_first_output_to_false(aag_text: str) -> str:
    """Return a syntactically valid but semantically corrupted AIGER file.

    The first output literal is replaced by constant false.

    This keeps the file structurally valid, but changes the behavior of circuits
    that should accept at least one tested word. The negative test then checks
    that the semantic validation infrastructure observes the wrong behavior.
    """
    lines = aag_text.splitlines()

    _max_var, num_inputs, num_latches, num_outputs, _num_ands = parse_aiger_header(
        aag_text
    )

    if num_outputs < 1:
        raise AssertionError("Cannot corrupt AIGER without outputs.")

    first_output_line_index = 1 + num_inputs + num_latches
    lines[first_output_line_index] = "0"

    return "\n".join(lines) + "\n"


def parse_aiger_input_names(aag_text: str) -> list[str]:
    """Read AIGER symbol lines and return input names in i0, i1, ... order."""
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
    """Encode one candidate word as a bounded AIGER input vector."""
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
    """Encode one sequential step.

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
    """Encode a candidate word as a sequential aigsim trace."""
    vectors = [encode_sequential_step(char, input_names) for char in candidate]

    # Final step: end = true, all symbol inputs false.
    vectors.append(encode_sequential_step(None, input_names))

    return vectors


def parse_bounded_aigsim_outputs(stdout: str) -> list[int]:
    """Parse combinational aigsim output."""
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
    """Extract the final output bit from sequential aigsim output."""
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


def expected_unbounded(pattern: str, candidate: str) -> int:
    """Reference regex semantics."""
    ast = parse_regex(pattern)
    nfa = build_product_aware_nfa(ast)

    return 1 if accepts(nfa, candidate) else 0


def expected_bounded(pattern: str, bound: int, candidate: str) -> int:
    """Reference bounded semantics."""
    if len(candidate) > bound:
        return 0

    return expected_unbounded(pattern, candidate)


def run_bounded_aigsim(aag_text: str, candidates: list[str], stem: str) -> list[int]:
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    aag_path = output_dir / f"test_negative_{stem}.aag"
    stim_path = output_dir / f"test_negative_{stem}.stim"

    aag_path.write_text(aag_text, encoding="utf-8")

    input_names = parse_aiger_input_names(aag_text)
    vectors = [
        encode_bounded_candidate(candidate, input_names)
        for candidate in candidates
    ]

    stim_path.write_text("\n".join(vectors) + "\n.\n", encoding="utf-8")

    result = subprocess.run(
        [aigsim, str(aag_path), str(stim_path)],
        check=False,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise AssertionError(
            "aigsim failed during bounded negative detection test\n"
            f"stem: {stem}\n"
            f"input names: {input_names}\n"
            f"vectors: {vectors}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    outputs = parse_bounded_aigsim_outputs(result.stdout)

    assert len(outputs) == len(candidates), (
        "bounded output count mismatch\n"
        f"stem: {stem}\n"
        f"candidates: {candidates}\n"
        f"outputs: {outputs}\n"
        f"stdout:\n{result.stdout}"
    )

    return outputs


def run_sequential_aigsim(
    aag_text: str,
    candidates: list[str],
    stem: str,
) -> list[int]:
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    aag_path = output_dir / f"test_negative_{stem}.aag"
    aag_path.write_text(aag_text, encoding="utf-8")

    input_names = parse_aiger_input_names(aag_text)
    outputs: list[int] = []

    for index, candidate in enumerate(candidates):
        stim_path = output_dir / f"test_negative_{stem}_{index}.stim"

        vectors = encode_sequential_trace(candidate, input_names)
        stim_path.write_text("\n".join(vectors) + "\n.\n", encoding="utf-8")

        result = subprocess.run(
            [aigsim, str(aag_path), str(stim_path)],
            check=False,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            raise AssertionError(
                "aigsim failed during sequential negative detection test\n"
                f"stem: {stem}\n"
                f"candidate: {candidate!r}\n"
                f"input names: {input_names}\n"
                f"vectors: {vectors}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

        outputs.append(parse_final_sequential_aigsim_output(result.stdout))

    return outputs


def compile_sequential_aiger(pattern: str) -> str:
    circuit = compile_regex_to_sequential(pattern)
    return SequentialAigerWriter(circuit).write()


def test_negative_detection_bounded_output_corruption() -> None:
    """Check that the validation infrastructure detects a corrupted bounded AIGER."""
    pattern = "a*"
    bound = 3
    candidates = ["", "a", "aa", "aaa", "b", "ab", "ba", "aaaa"]

    correct_aag = compile_regex_to_aiger(pattern, bound)
    corrupted_aag = corrupt_first_output_to_false(correct_aag)

    expected = [
        expected_bounded(pattern, bound, candidate)
        for candidate in candidates
    ]

    correct_outputs = run_bounded_aigsim(
        correct_aag,
        candidates,
        "bounded_correct",
    )

    corrupted_outputs = run_bounded_aigsim(
        corrupted_aag,
        candidates,
        "bounded_corrupted",
    )

    assert correct_outputs == expected, (
        "sanity check failed: correct bounded AIGER does not match semantics\n"
        f"expected: {expected}\n"
        f"actual:   {correct_outputs}"
    )

    assert corrupted_outputs != expected, (
        "negative detection failed: corrupted bounded AIGER still matched "
        "the expected semantics\n"
        f"expected: {expected}\n"
        f"actual:   {corrupted_outputs}"
    )


def test_negative_detection_sequential_output_corruption() -> None:
    """Check that the validation infrastructure detects a corrupted sequential AIGER."""
    pattern = "a*"
    candidates = ["", "a", "aa", "aaa", "b", "ab", "ba", "aaaa"]

    correct_aag = compile_sequential_aiger(pattern)
    corrupted_aag = corrupt_first_output_to_false(correct_aag)

    expected = [
        expected_unbounded(pattern, candidate)
        for candidate in candidates
    ]

    correct_outputs = run_sequential_aigsim(
        correct_aag,
        candidates,
        "sequential_correct",
    )

    corrupted_outputs = run_sequential_aigsim(
        corrupted_aag,
        candidates,
        "sequential_corrupted",
    )

    assert correct_outputs == expected, (
        "sanity check failed: correct sequential AIGER does not match semantics\n"
        f"expected: {expected}\n"
        f"actual:   {correct_outputs}"
    )

    assert corrupted_outputs != expected, (
        "negative detection failed: corrupted sequential AIGER still matched "
        "the expected semantics\n"
        f"expected: {expected}\n"
        f"actual:   {corrupted_outputs}"
    )


def run_tests() -> None:
    test_negative_detection_bounded_output_corruption()
    test_negative_detection_sequential_output_corruption()
    print("All aigsim negative detection tests passed.")


if __name__ == "__main__":
    run_tests()
