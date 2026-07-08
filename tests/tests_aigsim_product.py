import re
import subprocess
from pathlib import Path

from string_to_aiger.aiger.aiger import compile_expr_to_aiger
from string_to_aiger.bounded.product_bounded_compiler import (
    compile_regex_bounded_product,
)
from string_to_aiger.nfa.nfa_builder import build_nfa
from string_to_aiger.nfa.nfa_evaluator import accepts
from string_to_aiger.regex.regex_ast import Intersect, Regex
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.sequential.product_sequential_compiler import (
    compile_regex_to_sequential_product,
)
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter
from aigsim_test_utils import (
    require_aigsim,
    parse_aiger_input_names,
    encode_bounded_candidate,
    parse_bounded_aigsim_outputs,
    encode_sequential_trace,
    parse_final_sequential_aigsim_output,
)


def safe_file_stem(pattern: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9]+", "_", pattern).strip("_")
    return stem or "empty_pattern"


def accepts_regex_ast(expr: Regex, candidate: str) -> bool:
    """Reference semantics for regexes.

    Intersections are evaluated structurally:
    A & B accepts a word iff both A and B accept it.
    """
    if isinstance(expr, Intersect):
        return accepts_regex_ast(expr.left, candidate) and accepts_regex_ast(
            expr.right, candidate
        )

    nfa = build_nfa(expr)
    return accepts(nfa, candidate)


def expected_unbounded(pattern: str, candidate: str) -> int:
    ast = parse_regex(pattern)
    return 1 if accepts_regex_ast(ast, candidate) else 0


def expected_bounded(pattern: str, bound: int, candidate: str) -> int:
    if len(candidate) > bound:
        return 0

    return expected_unbounded(pattern, candidate)


# ---------------------------------------------------------------------------
# Bounded product AIGER helpers
# ---------------------------------------------------------------------------


def compile_bounded_product_aiger(pattern: str, bound: int) -> str:
    expr = compile_regex_bounded_product(pattern, bound)
    return compile_expr_to_aiger(expr)


def run_bounded_product_aigsim_case(
    pattern: str,
    bound: int,
    candidates: list[str],
) -> None:
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    stem = safe_file_stem(pattern)
    aag_path = output_dir / f"test_aigsim_product_{stem}_bounded.aag"
    stim_path = output_dir / f"test_aigsim_product_{stem}_bounded.stim"

    aag_text = compile_bounded_product_aiger(pattern, bound)
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
            "aigsim failed for bounded product case\n"
            f"pattern: {pattern}\n"
            f"bound: {bound}\n"
            f"input names: {input_names}\n"
            f"vectors: {vectors}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    actual_outputs = parse_bounded_aigsim_outputs(result.stdout)
    expected_outputs = [
        expected_bounded(pattern, bound, candidate)
        for candidate in candidates
    ]

    assert actual_outputs == expected_outputs, (
        "bounded product aigsim mismatch\n"
        f"pattern: {pattern}\n"
        f"bound: {bound}\n"
        f"candidates: {candidates}\n"
        f"input names: {input_names}\n"
        f"vectors: {vectors}\n"
        f"expected: {expected_outputs}\n"
        f"actual:   {actual_outputs}\n"
        f"stdout:\n{result.stdout}"
    )


# ---------------------------------------------------------------------------
# Sequential product AIGER helpers
# ---------------------------------------------------------------------------


def compile_sequential_product_aiger(pattern: str) -> str:
    circuit = compile_regex_to_sequential_product(pattern)
    return SequentialAigerWriter(circuit).write()


def run_sequential_product_aigsim_case(
    pattern: str,
    candidates: list[str],
) -> None:
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    stem = safe_file_stem(pattern)
    aag_path = output_dir / f"test_aigsim_product_{stem}_sequential.aag"

    aag_text = compile_sequential_product_aiger(pattern)
    aag_path.write_text(aag_text, encoding="utf-8")

    input_names = parse_aiger_input_names(aag_text)

    for index, candidate in enumerate(candidates):
        stim_path = output_dir / (
            f"test_aigsim_product_{stem}_sequential_{index}.stim"
        )

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
                "aigsim failed for sequential product case\n"
                f"pattern: {pattern}\n"
                f"candidate: {candidate!r}\n"
                f"input names: {input_names}\n"
                f"vectors: {vectors}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

        actual = parse_final_sequential_aigsim_output(result.stdout)
        expected = expected_unbounded(pattern, candidate)

        assert actual == expected, (
            "sequential product aigsim mismatch\n"
            f"pattern: {pattern}\n"
            f"candidate: {candidate!r}\n"
            f"input names: {input_names}\n"
            f"vectors: {vectors}\n"
            f"expected: {expected}\n"
            f"actual:   {actual}\n"
            f"stdout:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# Product strategy tests
# ---------------------------------------------------------------------------


def test_aigsim_product_bounded_a_or_b_star_and_a_star() -> None:
    run_bounded_product_aigsim_case(
        pattern="(a|b)*&a*",
        bound=4,
        candidates=["", "a", "aa", "aaa", "aaaa", "b", "ab", "ba", "aaaaa"],
    )


def test_aigsim_product_sequential_a_or_b_star_and_a_star() -> None:
    run_sequential_product_aigsim_case(
        pattern="(a|b)*&a*",
        candidates=["", "a", "aa", "aaa", "aaaa", "b", "ab", "ba"],
    )


def test_aigsim_product_bounded_ab_star_and_a_or_b_star() -> None:
    run_bounded_product_aigsim_case(
        pattern="(ab)*&(a|b)*",
        bound=6,
        candidates=["", "ab", "abab", "ababab", "a", "b", "aba", "abb"],
    )


def test_aigsim_product_sequential_ab_star_and_a_or_b_star() -> None:
    run_sequential_product_aigsim_case(
        pattern="(ab)*&(a|b)*",
        candidates=["", "ab", "abab", "ababab", "a", "b", "aba", "abb"],
    )


def test_aigsim_product_bounded_disjoint_except_empty() -> None:
    run_bounded_product_aigsim_case(
        pattern="a*&b*",
        bound=4,
        candidates=["", "a", "aa", "b", "bb", "ab", "ba"],
    )


def test_aigsim_product_sequential_disjoint_except_empty() -> None:
    run_sequential_product_aigsim_case(
        pattern="a*&b*",
        candidates=["", "a", "aa", "b", "bb", "ab", "ba"],
    )


def run_tests() -> None:
    test_aigsim_product_bounded_a_or_b_star_and_a_star()
    test_aigsim_product_sequential_a_or_b_star_and_a_star()
    test_aigsim_product_bounded_ab_star_and_a_or_b_star()
    test_aigsim_product_sequential_ab_star_and_a_or_b_star()
    test_aigsim_product_bounded_disjoint_except_empty()
    test_aigsim_product_sequential_disjoint_except_empty()

    print("All aigsim product semantic tests passed.")


if __name__ == "__main__":
    run_tests()
