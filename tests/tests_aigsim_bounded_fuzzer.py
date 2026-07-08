import itertools
import random
import subprocess
from pathlib import Path

from aigsim_test_utils import (
    require_aigsim,
    parse_aiger_input_names,
    encode_bounded_candidate,
    parse_bounded_aigsim_outputs,
)
from string_to_aiger.nfa.nfa_evaluator import accepts
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa


ALPHABET = ["a", "b", "c"]
BOUNDS = [2, 4, 6]

FUZZ_SEED = 12345
FUZZ_PATTERN_COUNT = 30
MAX_REGEX_DEPTH = 3

# Exhaustively testing all words up to length 6 over a 3-symbol alphabet would
# be much slower. We therefore exhaustively test small words and add selected
# longer words to exercise larger bounds and length encodings.
EXHAUSTIVE_WORD_LENGTH = 3


def expected_bounded(pattern: str, bound: int, candidate: str) -> int:
    """Expected bounded semantics."""
    if len(candidate) > bound:
        return 0

    ast = parse_regex(pattern)
    nfa = build_product_aware_nfa(ast)

    return 1 if accepts(nfa, candidate) else 0


def all_words(alphabet: list[str], max_length: int) -> list[str]:
    """Generate all words over alphabet up to max_length."""
    words = [""]

    for length in range(1, max_length + 1):
        for letters in itertools.product(alphabet, repeat=length):
            words.append("".join(letters))

    return words


def candidates_for_bound(bound: int) -> list[str]:
    """Generate deterministic candidate words for a given bound.

    The set contains:

    - all words up to a small exhaustive length,
    - selected longer words within the bound,
    - selected words just above the bound.
    """
    candidates = all_words(ALPHABET, min(bound, EXHAUSTIVE_WORD_LENGTH))

    selected = [
        "aaaa",
        "bbbb",
        "cccc",
        "abab",
        "bcbc",
        "abca",
        "cabc",
        "abcabc",
        "ababab",
        "aaaaaa",
        "bbbbbb",
        "cccccc",
        "abcabca",
        "aaaaaaa",
    ]

    # Explicitly exercise the exact bound and one-past-the-bound cases.
    selected += [
        "a" * bound,
        "b" * bound,
        "c" * bound,
        "a" * (bound + 1),
        "b" * (bound + 1),
        "c" * (bound + 1),
        ("abc" * ((bound // 3) + 2))[:bound],
        ("abc" * ((bound // 3) + 2))[: bound + 1],
    ]

    seen = set(candidates)

    for word in selected:
        if word in seen:
            continue

        # Keep the test compact while still checking beyond-bound rejection.
        if len(word) <= bound + 1:
            candidates.append(word)
            seen.add(word)

    return candidates


def generate_regex(rng: random.Random, depth: int) -> str:
    """Generate a small random regex over {a,b,c}.

    Generated grammar:

        atom  ::= a | b | c
        regex ::= atom
                | regex*
                | regex regex
                | regex | regex
                | regex & regex
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

    The fixed seed makes the fuzzer reproducible.
    """
    base_patterns = [
        "a",
        "b",
        "c",
        "a*",
        "b*",
        "c*",
        "(ab)*",
        "(bc)*",
        "(abc)*",
        "(a|b|c)*",
        "[abc]*",
        "(a|bc)*",
        "(a|b|c)*&a*",
        "(a|b|c)*&[abc]*",
        "a*&b*",
        "(ab)*&(a|b|c)*",
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


def run_fuzz_case(
    pattern: str,
    bound: int,
    candidates: list[str],
    case_index: int,
) -> None:
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    aag_path = output_dir / (
        f"test_aigsim_bounded_fuzzer_{case_index}_bound_{bound}.aag"
    )
    stim_path = output_dir / (
        f"test_aigsim_bounded_fuzzer_{case_index}_bound_{bound}.stim"
    )

    aag_text = compile_regex_to_aiger(pattern, bound)
    aag_path.write_text(aag_text, encoding="utf-8")

    input_names = parse_aiger_input_names(aag_text)
    vectors = [encode_bounded_candidate(candidate, input_names) for candidate in candidates]

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

    assert len(actual_outputs) == len(expected_outputs), (
        "aigsim output count mismatch\n"
        f"case index: {case_index}\n"
        f"pattern: {pattern}\n"
        f"bound: {bound}\n"
        f"expected count: {len(expected_outputs)}\n"
        f"actual count: {len(actual_outputs)}\n"
        f"stdout:\n{result.stdout}"
    )

    assert actual_outputs == expected_outputs, (
        "bounded fuzz semantic mismatch\n"
        f"case index: {case_index}\n"
        f"pattern: {pattern}\n"
        f"bound: {bound}\n"
        f"input names: {input_names}\n"
        f"candidates: {candidates}\n"
        f"vectors: {vectors}\n"
        f"expected: {expected_outputs}\n"
        f"actual:   {actual_outputs}\n"
        f"stdout:\n{result.stdout}"
    )


def test_aigsim_bounded_fuzzer() -> None:
    patterns = generate_fuzz_patterns()

    for case_index, pattern in enumerate(patterns):
        for bound in BOUNDS:
            run_fuzz_case(
                pattern=pattern,
                bound=bound,
                candidates=candidates_for_bound(bound),
                case_index=case_index,
            )


def run_tests() -> None:
    test_aigsim_bounded_fuzzer()
    print("All aigsim bounded fuzz tests passed.")


if __name__ == "__main__":
    run_tests()
