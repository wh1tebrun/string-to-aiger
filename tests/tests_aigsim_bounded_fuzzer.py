import itertools
import random
import re
import subprocess
from pathlib import Path

from string_to_aiger.nfa.nfa_builder import build_nfa
from string_to_aiger.nfa.nfa_evaluator import accepts
from string_to_aiger.regex.regex_ast import Intersect, Regex
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa
from aigsim_test_utils import require_aigsim

ALPHABET = ["a", "b"]
BOUND = 4
FUZZ_SEED = 12345
FUZZ_PATTERN_COUNT = 40
MAX_REGEX_DEPTH = 3


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

            bit = (
                position < len(candidate)
                and candidate[position] == symbol
            )
            bits.append("1" if bit else "0")
            continue

        raise ValueError(f"Unsupported bounded input name: {name}")

    return "".join(bits)


def parse_aigsim_outputs(stdout: str) -> list[int]:
    """Parse combinational aigsim output lines.

    For ordinary combinational circuits, aigsim prints:

        input_vector output

    For constant or zero-input circuits, aigsim may print only:

        output

    The fuzzer can generate regexes such as a&b, whose language is empty.
    Such cases may compile to circuits without meaningful input symbols, so
    both formats are accepted here.
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
    """Reference regex semantics for fuzz tests.

    The fuzz generator may create nested intersections, for example inside
    concatenation, union, or Kleene star. The basic Thompson-style NFA builder
    does not support Intersect nodes, so the reference side also uses the
    product-aware NFA builder.
    """
    nfa = build_product_aware_nfa(expr)
    return accepts(nfa, candidate)


def expected_bounded(pattern: str, bound: int, candidate: str) -> int:
    """Expected bounded semantics.

    The bounded backend only accepts words whose length is at most bound.
    """
    if len(candidate) > bound:
        return 0

    ast = parse_regex(pattern)
    return 1 if accepts_regex_ast(ast, candidate) else 0


def all_words(alphabet: list[str], max_length: int) -> list[str]:
    """Generate all words over alphabet up to max_length."""
    words = [""]

    for length in range(1, max_length + 1):
        for letters in itertools.product(alphabet, repeat=length):
            words.append("".join(letters))

    return words


def generate_regex(rng: random.Random, depth: int) -> str:
    """Generate a small random regex over {a,b}.

    The generated grammar intentionally stays small and readable:

        atom        ::= a | b
        regex       ::= atom
                      | regex regex
                      | regex | regex
                      | regex & regex
                      | regex*

    Parentheses are inserted aggressively to avoid precedence ambiguity.
    """
    if depth <= 0:
        return rng.choice(ALPHABET)

    choice = rng.random()

    if choice < 0.20:
        return rng.choice(ALPHABET)

    if choice < 0.40:
        inner = generate_regex(rng, depth - 1)
        return f"({inner})*"

    if choice < 0.65:
        left = generate_regex(rng, depth - 1)
        right = generate_regex(rng, depth - 1)
        return f"({left}{right})"

    if choice < 0.85:
        left = generate_regex(rng, depth - 1)
        right = generate_regex(rng, depth - 1)
        return f"({left}|{right})"

    left = generate_regex(rng, depth - 1)
    right = generate_regex(rng, depth - 1)
    return f"({left}&{right})"


def generate_fuzz_patterns() -> list[str]:
    """Generate deterministic fuzz patterns.

    Fixed seed means the fuzzer is reproducible:
    the same regex set is generated on every test run.
    """
    base_patterns = [
        "a",
        "b",
        "a*",
        "b*",
        "(ab)*",
        "(ba)*",
        "(a|b)*",
        "(a|b)*&a*",
        "a*&b*",
        "(ab)*&(a|b)*",
    ]

    rng = random.Random(FUZZ_SEED)
    patterns = list(base_patterns)
    seen = set(patterns)

    while len(patterns) < FUZZ_PATTERN_COUNT:
        pattern = generate_regex(rng, MAX_REGEX_DEPTH)

        if pattern in seen:
            continue

        # Make sure the generated pattern is accepted by the parser.
        parse_regex(pattern)

        patterns.append(pattern)
        seen.add(pattern)

    return patterns


def run_fuzz_case(pattern: str, candidates: list[str], case_index: int) -> None:
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    aag_path = output_dir / f"test_aigsim_bounded_fuzzer_{case_index}.aag"
    stim_path = output_dir / f"test_aigsim_bounded_fuzzer_{case_index}.stim"

    aag_text = compile_regex_to_aiger(pattern, BOUND)
    aag_path.write_text(aag_text, encoding="utf-8")

    input_names = parse_aiger_input_names(aag_text)
    vectors = [encode_candidate(candidate, input_names) for candidate in candidates]

    stim_path.write_text("\n".join(vectors) + "\n.\n", encoding="utf-8")

    result = subprocess.run(
        [aigsim, str(aag_path), str(stim_path)],
        check=False,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise AssertionError(
            "aigsim failed during bounded fuzz test\n"
            f"case index: {case_index}\n"
            f"pattern: {pattern}\n"
            f"input names: {input_names}\n"
            f"vectors: {vectors}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    actual_outputs = parse_aigsim_outputs(result.stdout)
    expected_outputs = [
        expected_bounded(pattern, BOUND, candidate)
        for candidate in candidates
    ]

    assert len(actual_outputs) == len(expected_outputs), (
        "aigsim output count mismatch\n"
        f"case index: {case_index}\n"
        f"pattern: {pattern}\n"
        f"expected count: {len(expected_outputs)}\n"
        f"actual count: {len(actual_outputs)}\n"
        f"stdout:\n{result.stdout}"
    )

    assert actual_outputs == expected_outputs, (
        "bounded fuzz semantic mismatch\n"
        f"case index: {case_index}\n"
        f"pattern: {pattern}\n"
        f"bound: {BOUND}\n"
        f"input names: {input_names}\n"
        f"candidates: {candidates}\n"
        f"vectors: {vectors}\n"
        f"expected: {expected_outputs}\n"
        f"actual:   {actual_outputs}\n"
        f"stdout:\n{result.stdout}"
    )


def test_aigsim_bounded_fuzzer() -> None:
    candidates = all_words(ALPHABET, BOUND)

    # Also include a few words beyond the bound.
    # These must be rejected by the bounded backend, even if the regex itself
    # would accept them unboundedly.
    candidates += ["aaaaa", "bbbbb", "ababa", "babab"]

    patterns = generate_fuzz_patterns()

    for index, pattern in enumerate(patterns):
        run_fuzz_case(pattern, candidates, index)


def run_tests() -> None:
    test_aigsim_bounded_fuzzer()
    print("All aigsim bounded fuzz tests passed.")


if __name__ == "__main__":
    run_tests()
