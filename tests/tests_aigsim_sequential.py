import re
import subprocess
from pathlib import Path

from string_to_aiger.regex.regex_ast import Intersect, Regex
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.nfa.nfa_builder import build_nfa
from string_to_aiger.nfa.nfa_evaluator import accepts
from string_to_aiger.sequential.sequential_regex_compiler import (
    compile_regex_to_sequential,
)
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter
from aigsim_test_utils import require_aigsim


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

        index = int(index_text[1:])
        names_by_index[index] = name

    return [names_by_index[i] for i in sorted(names_by_index)]


def encode_step(char: str | None, input_names: list[str]) -> str:
    """Encode one sequential input step.

    The sequential backend uses:

    - end = true only on the final step
    - is_X = true when the current input symbol is X

    For unknown symbols, all is_X inputs are false.
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


def encode_candidate_trace(candidate: str, input_names: list[str]) -> list[str]:
    """Encode a candidate word as a sequence of aigsim input vectors."""
    vectors = [encode_step(char, input_names) for char in candidate]

    # Final step: end = true, all symbol inputs false.
    vectors.append(encode_step(None, input_names))

    return vectors


def parse_final_aigsim_output(stdout: str) -> int:
    """Extract the final output bit from sequential aigsim output.

    For sequential circuits, aigsim prints lines of the form:

        current_latch_state input_vector output next_latch_state

    The final line corresponds to the final input vector, where end = true.
    """
    final_output: int | None = None

    for line in stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("Trace is a witness"):
            continue

        parts = line.split()

        if len(parts) != 4:
            continue

        _current_state, input_vector, output, _next_state = parts

        if set(input_vector) <= {"0", "1"} and output in {"0", "1"}:
            final_output = int(output)

    if final_output is None:
        raise AssertionError(f"Could not parse final aigsim output:\n{stdout}")

    return final_output


def accepts_regex_ast(expr: Regex, candidate: str) -> bool:
    """Reference regex semantics used by the aigsim sequential tests.

    For ordinary regex nodes, the direct NFA evaluator is used.
    For Intersect nodes, the semantics is evaluated structurally:
    the candidate must be accepted by both sides.
    """
    if isinstance(expr, Intersect):
        return accepts_regex_ast(expr.left, candidate) and accepts_regex_ast(
            expr.right, candidate
        )

    nfa = build_nfa(expr)
    return accepts(nfa, candidate)


def expected_by_reference(pattern: str, candidate: str) -> int:
    ast = parse_regex(pattern)
    return 1 if accepts_regex_ast(ast, candidate) else 0


def safe_file_stem(pattern: str) -> str:
    """Create a readable and filesystem-safe stem from a regex pattern."""
    stem = re.sub(r"[^A-Za-z0-9]+", "_", pattern).strip("_")
    return stem or "empty_pattern"


def compile_sequential_aiger(pattern: str) -> str:
    circuit = compile_regex_to_sequential(pattern)
    return SequentialAigerWriter(circuit).write()


def run_aigsim_case(pattern: str, candidates: list[str]) -> None:
    """Compile one sequential AIGER and compare aigsim output with reference semantics."""
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    stem = safe_file_stem(pattern)
    aag_path = output_dir / f"test_aigsim_{stem}_sequential.aag"

    aag_text = compile_sequential_aiger(pattern)
    aag_path.write_text(aag_text, encoding="utf-8")

    input_names = parse_aiger_input_names(aag_text)

    for index, candidate in enumerate(candidates):
        stim_path = output_dir / f"test_aigsim_{stem}_sequential_{index}.stim"

        vectors = encode_candidate_trace(candidate, input_names)

        # aigsim stimulus files are line based and must end with ".".
        stim_path.write_text("\n".join(vectors) + "\n.\n", encoding="utf-8")

        result = subprocess.run(
            [aigsim, str(aag_path), str(stim_path)],
            check=False,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            raise AssertionError(
                "aigsim failed\n"
                f"pattern: {pattern}\n"
                f"candidate: {candidate!r}\n"
                f"vectors: {vectors}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

        expected = expected_by_reference(pattern, candidate)
        actual = parse_final_aigsim_output(result.stdout)

        assert actual == expected, (
            f"aigsim output mismatch for {pattern!r}\n"
            f"candidate:   {candidate!r}\n"
            f"input names: {input_names}\n"
            f"vectors:     {vectors}\n"
            f"expected:    {expected}\n"
            f"actual:      {actual}\n"
            f"stdout:\n{result.stdout}"
        )


def test_aigsim_sequential_astar() -> None:
    run_aigsim_case(
        pattern="a*",
        candidates=["", "a", "aa", "aaa", "b", "ab", "ba"],
    )


def test_aigsim_sequential_abstar() -> None:
    run_aigsim_case(
        pattern="(ab)*",
        candidates=["", "ab", "abab", "a", "aba", "ba", "abb"],
    )


def test_aigsim_sequential_union_star() -> None:
    run_aigsim_case(
        pattern="(a|b)*",
        candidates=["", "a", "b", "ab", "ba", "aaa", "bbb", "c", "ac"],
    )


def test_aigsim_sequential_intersection_astar() -> None:
    run_aigsim_case(
        pattern="(a|b)*&a*",
        candidates=["", "a", "aa", "aaa", "b", "ab", "ba", "bbb"],
    )


def test_aigsim_sequential_intersection_empty_except_epsilon() -> None:
    run_aigsim_case(
        pattern="a*&b*",
        candidates=["", "a", "b", "aa", "bb", "ab", "ba"],
    )


def test_aigsim_sequential_optional() -> None:
    run_aigsim_case(
        pattern="a?",
        candidates=["", "a", "aa", "b", "ab", "ba"],
    )


def test_aigsim_sequential_plus() -> None:
    run_aigsim_case(
        pattern="a+",
        candidates=["", "a", "aa", "aaa", "b", "ab", "ba"],
    )


def test_aigsim_sequential_exact_repetition() -> None:
    run_aigsim_case(
        pattern="a{2}",
        candidates=["", "a", "aa", "aaa", "b", "ab", "ba", "aab"],
    )


def test_aigsim_sequential_character_class_star() -> None:
    run_aigsim_case(
        pattern="[ab]*",
        candidates=["", "a", "b", "ab", "ba", "aaa", "bbb", "c", "ac", "ca"],
    )


def test_aigsim_sequential_mixed_union_concat_star() -> None:
    run_aigsim_case(
        pattern="(a|ba)*",
        candidates=[
            "",
            "a",
            "ba",
            "aa",
            "aba",
            "baa",
            "baba",
            "b",
            "ab",
            "bab",
            "bb",
        ],
    )


def run_tests() -> None:
    test_aigsim_sequential_astar()
    test_aigsim_sequential_abstar()
    test_aigsim_sequential_union_star()
    test_aigsim_sequential_intersection_astar()
    test_aigsim_sequential_intersection_empty_except_epsilon()
    test_aigsim_sequential_optional()
    test_aigsim_sequential_plus()
    test_aigsim_sequential_exact_repetition()
    test_aigsim_sequential_character_class_star()
    test_aigsim_sequential_mixed_union_concat_star()
    print("All aigsim sequential semantic tests passed.")


if __name__ == "__main__":
    run_tests()
