import os
import subprocess
from pathlib import Path

from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.nfa.nfa_builder import build_nfa
from string_to_aiger.nfa.nfa_evaluator import accepts
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger


AIGSIM_ENV_VAR = "AIGSIM"


def require_aigsim() -> str:
    """Return the configured aigsim path or skip the test.

    This test is optional because aigsim is an external tool.

    Example WSL setup:

        export AIGSIM=/home/egetekin/tools/aiger/aigsim
    """
    aigsim = os.environ.get(AIGSIM_ENV_VAR)

    if not aigsim:
        print("SKIPPED: AIGSIM environment variable is not set.")
        raise SystemExit(0)

    if not Path(aigsim).exists():
        raise AssertionError(f"AIGSIM does not exist: {aigsim}")

    return aigsim


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
    """Extract one output bit per stimulus vector from aigsim output."""
    outputs: list[int] = []

    for line in stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("Trace is a witness"):
            continue

        parts = line.split()

        if len(parts) != 2:
            continue

        vector, output = parts

        if set(vector) <= {"0", "1"} and output in {"0", "1"}:
            outputs.append(int(output))

    return outputs


def expected_by_nfa(pattern: str, candidates: list[str]) -> list[int]:
    """Compute reference accept/reject results with the direct NFA evaluator."""
    ast = parse_regex(pattern)
    nfa = build_nfa(ast)

    return [1 if accepts(nfa, candidate) else 0 for candidate in candidates]


def run_aigsim_case(pattern: str, bound: int, candidates: list[str]) -> None:
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    safe_name = (
        pattern.replace("*", "star")
        .replace("|", "or")
        .replace("(", "")
        .replace(")", "")
        .replace("&", "and")
        .replace("/", "_")
    )

    aag_path = output_dir / f"test_aigsim_{safe_name}_bounded.aag"
    stim_path = output_dir / f"test_aigsim_{safe_name}_bounded.stim"

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
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    expected = expected_by_nfa(pattern, candidates)
    actual = parse_aigsim_outputs(result.stdout)

    assert actual == expected, (
        f"aigsim output mismatch for {pattern!r}\n"
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
        candidates=["", "a", "aa", "aaa", "b", "ab"],
    )


def test_aigsim_bounded_abstar() -> None:
    run_aigsim_case(
        pattern="(ab)*",
        bound=4,
        candidates=["", "ab", "abab", "a", "aba", "ba", "abb"],
    )


def run_tests() -> None:
    test_aigsim_bounded_astar()
    test_aigsim_bounded_abstar()
    print("All aigsim bounded semantic tests passed.")


if __name__ == "__main__":
    run_tests()
