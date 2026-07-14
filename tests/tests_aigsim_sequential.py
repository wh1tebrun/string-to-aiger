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
from aigsim_test_utils import (
    require_aigsim,
    parse_aiger_input_names,
    encode_sequential_trace,
    encode_sequential_assignment,
    parse_aiger_header,
    parse_final_sequential_aigsim_output,
)


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

        vectors = encode_sequential_trace(candidate, input_names)

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
        actual = parse_final_sequential_aigsim_output(result.stdout)

        assert actual == expected, (
            f"aigsim output mismatch for {pattern!r}\n"
            f"candidate:   {candidate!r}\n"
            f"input names: {input_names}\n"
            f"vectors:     {vectors}\n"
            f"expected:    {expected}\n"
            f"actual:      {actual}\n"
            f"stdout:\n{result.stdout}"
        )



def run_raw_vector_case(
    pattern: str,
    assignments: list[set[str]],
    expected: int,
    suffix: str,
) -> None:
    """Run arbitrary, possibly invalid, input vectors through aigsim."""
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    stem = safe_file_stem(pattern)
    aag_path = output_dir / f"test_aigsim_{stem}_{suffix}.aag"
    stim_path = output_dir / f"test_aigsim_{stem}_{suffix}.stim"

    aag_text = compile_sequential_aiger(pattern)
    aag_path.write_text(aag_text, encoding="utf-8")

    input_names = parse_aiger_input_names(aag_text)
    vectors = [
        encode_sequential_assignment(assignment, input_names)
        for assignment in assignments
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
            "aigsim failed for raw sequential vectors\n"
            f"pattern: {pattern}\n"
            f"assignments: {assignments}\n"
            f"input names: {input_names}\n"
            f"vectors: {vectors}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    actual = parse_final_sequential_aigsim_output(result.stdout)

    assert actual == expected, (
        "sequential protocol guard mismatch\n"
        f"pattern: {pattern}\n"
        f"assignments: {assignments}\n"
        f"input names: {input_names}\n"
        f"vectors: {vectors}\n"
        f"expected: {expected}\n"
        f"actual:   {actual}\n"
        f"stdout:\n{result.stdout}"
    )


def test_sequential_protocol_adds_exactly_one_validity_latch() -> None:
    circuit = compile_regex_to_sequential("b&c")
    assert "protocol_valid" in circuit.latches

    aag_text = SequentialAigerWriter(circuit).write()
    _max_var, _inputs, num_latches, _outputs, _ands = parse_aiger_header(aag_text)

    assert num_latches == len(circuit.latches)
    assert sum(
        1
        for line in aag_text.splitlines()
        if line.startswith("l") and line.endswith(" protocol_valid")
    ) == 1


def test_aigsim_sequential_rejects_two_active_symbols() -> None:
    # Without the protocol latch, this invalid vector can make the left side
    # consume b and the right side consume c in the same clock step, causing
    # the unsatisfiable intersection b&c to be accepted.
    run_raw_vector_case(
        pattern="b&c",
        assignments=[{"is_b", "is_c"}, {"end"}],
        expected=0,
        suffix="invalid_two_symbols",
    )


def test_aigsim_sequential_rejects_symbol_on_end_step() -> None:
    # a* accepts epsilon, so the old output end & accepting_state incorrectly
    # accepted an end step that also asserted is_a.
    run_raw_vector_case(
        pattern="a*",
        assignments=[{"end", "is_a"}],
        expected=0,
        suffix="invalid_end_with_symbol",
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


def test_aigsim_sequential_long_exact_repetition() -> None:
    run_aigsim_case(
        pattern="a{5}",
        candidates=[
            "",
            "a",
            "aaaa",
            "aaaaa",
            "aaaaaa",
            "aaaab",
            "baaaa",
        ],
    )


def test_aigsim_sequential_long_abstar() -> None:
    run_aigsim_case(
        pattern="(ab)*",
        candidates=[
            "",
            "ab",
            "abab",
            "ababab",
            "abababab",
            "a",
            "aba",
            "abababa",
            "abb",
            "ba",
        ],
    )


def test_aigsim_sequential_long_intersection() -> None:
    run_aigsim_case(
        pattern="(a|b)*&a*",
        candidates=[
            "",
            "a",
            "aaaa",
            "aaaaaa",
            "b",
            "ab",
            "aaaab",
            "baaaa",
            "bbbbbb",
        ],
    )


def test_aigsim_sequential_long_mixed_union_concat_star() -> None:
    run_aigsim_case(
        pattern="(a|ba)*",
        candidates=[
            "",
            "a",
            "ba",
            "baba",
            "bababa",
            "abababa",
            "babababa",
            "b",
            "ab",
            "bab",
            "bb",
            "babab",
        ],
    )


def run_tests() -> None:
    test_sequential_protocol_adds_exactly_one_validity_latch()
    test_aigsim_sequential_rejects_two_active_symbols()
    test_aigsim_sequential_rejects_symbol_on_end_step()
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
    test_aigsim_sequential_long_exact_repetition()
    test_aigsim_sequential_long_abstar()
    test_aigsim_sequential_long_intersection()
    test_aigsim_sequential_long_mixed_union_concat_star()
    print("All aigsim sequential semantic tests passed.")


if __name__ == "__main__":
    run_tests()
