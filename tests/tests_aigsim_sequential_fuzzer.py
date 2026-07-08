import itertools
import random
import subprocess
from pathlib import Path

from string_to_aiger.nfa.nfa_evaluator import accepts
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter
from string_to_aiger.sequential.sequential_regex_compiler import (
    compile_regex_to_sequential,
)
from aigsim_test_utils import (
    require_aigsim,
    parse_aiger_input_names,
    encode_sequential_trace,
    parse_final_sequential_aigsim_output,
)


ALPHABET = ["a", "b"]
FUZZ_SEED = 54321
FUZZ_PATTERN_COUNT = 25
MAX_REGEX_DEPTH = 3
MAX_WORD_LENGTH = 3


def expected_unbounded(pattern: str, candidate: str) -> int:
    """Reference regex semantics for the sequential fuzzer."""
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


def generate_regex(rng: random.Random, depth: int) -> str:
    """Generate a small random regex over {a,b}.

    Generated grammar:

        atom  ::= a | b
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
    """Generate deterministic regex patterns."""
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

        # Verify parser support before adding the pattern.
        parse_regex(pattern)

        patterns.append(pattern)
        seen.add(pattern)

    return patterns


def compile_sequential_aiger(pattern: str) -> str:
    circuit = compile_regex_to_sequential(pattern)
    return SequentialAigerWriter(circuit).write()


def run_fuzz_case(pattern: str, candidates: list[str], case_index: int) -> None:
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    aag_path = output_dir / f"test_aigsim_sequential_fuzzer_{case_index}.aag"

    aag_text = compile_sequential_aiger(pattern)
    aag_path.write_text(aag_text, encoding="utf-8")

    input_names = parse_aiger_input_names(aag_text)

    for candidate_index, candidate in enumerate(candidates):
        stim_path = output_dir / (
            f"test_aigsim_sequential_fuzzer_{case_index}_{candidate_index}.stim"
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
                "aigsim failed during sequential fuzz test\n"
                f"case index: {case_index}\n"
                f"candidate index: {candidate_index}\n"
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
            "sequential fuzz semantic mismatch\n"
            f"case index: {case_index}\n"
            f"candidate index: {candidate_index}\n"
            f"pattern: {pattern}\n"
            f"candidate: {candidate!r}\n"
            f"input names: {input_names}\n"
            f"vectors: {vectors}\n"
            f"expected: {expected}\n"
            f"actual:   {actual}\n"
            f"stdout:\n{result.stdout}"
        )


def test_aigsim_sequential_fuzzer() -> None:
    candidates = all_words(ALPHABET, MAX_WORD_LENGTH)

    # A few longer words are included because sequential circuits are not
    # bounded by construction.
    candidates += ["aaaa", "bbbb", "abab", "baba", "ababa", "babab"]

    patterns = generate_fuzz_patterns()

    for index, pattern in enumerate(patterns):
        run_fuzz_case(pattern, candidates, index)


def run_tests() -> None:
    test_aigsim_sequential_fuzzer()
    print("All aigsim sequential fuzz tests passed.")


if __name__ == "__main__":
    run_tests()
