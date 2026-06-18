import re
import subprocess
from pathlib import Path

from string_to_aiger.regex.regex_ast import Intersect, Regex
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.nfa.nfa_builder import build_nfa
from string_to_aiger.nfa.nfa_evaluator import accepts
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger
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


def encode_candidate(candidate: str, input_names: list[str]) -> str:
    """Encode one candidate word according to generated AIGER input names.

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

        if name.startswith("x_") and "_is_" in name:
            left, char = name.split("_is_", maxsplit=1)
            position = int(left.removeprefix("x_"))

            bit = position < len(candidate) and candidate[position] == char
            bits.append("1" if bit else "0")
            continue

        raise ValueError(f"Unsupported AIGER input name: {name}")

    return "".join(bits)


def parse_aigsim_outputs(stdout: str) -> list[int]:
    """Parse combinational aigsim output lines.

    For ordinary combinational circuits, aigsim prints:

        input_vector output

    For constant or zero-input circuits, aigsim may print only:

        output
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
        raise AssertionError(f"Could not parse aigsim output:\n{stdout}")

    return outputs


def accepts_regex_ast(expr: Regex, candidate: str) -> bool:
    """Reference regex semantics used by the aigsim tests.

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


def expected_by_reference(pattern: str, bound: int, candidates: list[str]) -> list[int]:
    """Compute reference accept/reject results.

    The bounded backend only represents words up to the selected bound.
    Therefore, words longer than the bound are expected to be rejected even
    if the unbounded regex language would accept them.
    """
    ast = parse_regex(pattern)

    return [
        1 if len(candidate) <= bound and accepts_regex_ast(ast, candidate) else 0
        for candidate in candidates
    ]


def safe_file_stem(pattern: str) -> str:
    """Create a readable and filesystem-safe stem from a regex pattern."""
    stem = re.sub(r"[^A-Za-z0-9]+", "_", pattern).strip("_")
    return stem or "empty_pattern"


def run_aigsim_case(pattern: str, bound: int, candidates: list[str]) -> None:
    """Compile one bounded AIGER and compare aigsim output with reference semantics."""
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    stem = safe_file_stem(pattern)
    aag_path = output_dir / f"test_aigsim_{stem}_bounded.aag"
    stim_path = output_dir / f"test_aigsim_{stem}_bounded.stim"

    aag_text = compile_regex_to_aiger(pattern, bound)
    aag_path.write_text(aag_text, encoding="utf-8")

    input_names = parse_aiger_input_names(aag_text)
    vectors = [encode_candidate(candidate, input_names) for candidate in candidates]

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
            f"bound: {bound}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    expected = expected_by_reference(pattern, bound, candidates)
    actual = parse_aigsim_outputs(result.stdout)

    assert actual == expected, (
        f"aigsim output mismatch for {pattern!r}\n"
        f"bound:       {bound}\n"
        f"input names: {input_names}\n"
        f"candidates:  {candidates}\n"
        f"vectors:     {vectors}\n"
        f"expected:    {expected}\n"
        f"actual:      {actual}\n"
        f"stdout:\n{result.stdout}"
    )


def test_aigsim_bounded_astar() -> None:
    run_aigsim_case(
        pattern="a*",
        bound=3,
        candidates=["", "a", "aa", "aaa", "aaaa", "b", "ab"],
    )


def test_aigsim_bounded_abstar() -> None:
    run_aigsim_case(
        pattern="(ab)*",
        bound=4,
        candidates=["", "ab", "abab", "ababab", "a", "aba", "ba", "abb"],
    )


def test_aigsim_bounded_union_star() -> None:
    run_aigsim_case(
        pattern="(a|b)*",
        bound=3,
        candidates=["", "a", "b", "ab", "ba", "aaa", "bbb", "c", "ac"],
    )


def test_aigsim_bounded_union_concat_star() -> None:
    run_aigsim_case(
        pattern="(a|ba)*",
        bound=4,
        candidates=["", "a", "ba", "aba", "baa", "baba", "b", "ab", "bb"],
    )


def test_aigsim_bounded_optional() -> None:
    run_aigsim_case(
        pattern="a?",
        bound=2,
        candidates=["", "a", "aa", "b"],
    )


def test_aigsim_bounded_plus() -> None:
    run_aigsim_case(
        pattern="a+",
        bound=3,
        candidates=["", "a", "aa", "aaa", "aaaa", "b", "ab"],
    )


def test_aigsim_bounded_exact_repetition() -> None:
    run_aigsim_case(
        pattern="a{2}",
        bound=3,
        candidates=["", "a", "aa", "aaa", "b", "ab"],
    )


def test_aigsim_bounded_character_class_star() -> None:
    run_aigsim_case(
        pattern="[ab]*",
        bound=3,
        candidates=["", "a", "b", "ab", "ba", "aaa", "bbb", "c", "ac"],
    )


def test_aigsim_bounded_intersection_astar() -> None:
    run_aigsim_case(
        pattern="(a|b)*&a*",
        bound=3,
        candidates=["", "a", "aa", "aaa", "b", "ab", "ba", "bbb"],
    )


def test_aigsim_bounded_intersection_empty_except_epsilon() -> None:
    run_aigsim_case(
        pattern="a*&b*",
        bound=3,
        candidates=["", "a", "b", "aa", "bb", "ab", "ba"],
    )


def test_aigsim_bounded_intersection_abstar_subset() -> None:
    run_aigsim_case(
        pattern="(ab)*&(a|b)*",
        bound=4,
        candidates=["", "ab", "abab", "a", "b", "aba", "ba", "abb"],
    )


def run_tests() -> None:
    test_aigsim_bounded_astar()
    test_aigsim_bounded_abstar()
    test_aigsim_bounded_union_star()
    test_aigsim_bounded_union_concat_star()
    test_aigsim_bounded_optional()
    test_aigsim_bounded_plus()
    test_aigsim_bounded_exact_repetition()
    test_aigsim_bounded_character_class_star()
    test_aigsim_bounded_intersection_astar()
    test_aigsim_bounded_intersection_empty_except_epsilon()
    test_aigsim_bounded_intersection_abstar_subset()
    print("All aigsim bounded semantic tests passed.")


if __name__ == "__main__":
    run_tests()
