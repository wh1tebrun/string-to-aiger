import itertools
import os
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


AIGSIM_ENV_VAR = "AIGSIM"

ALPHABET = ["a", "b"]
FUZZ_SEED = 54321
FUZZ_PATTERN_COUNT = 25
MAX_REGEX_DEPTH = 3
MAX_WORD_LENGTH = 3


def require_aigsim() -> str:
    """Return the configured aigsim path or skip the test."""
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

        names_by_index[int(index_text[1:])] = name

    return [names_by_index[i] for i in sorted(names_by_index)]


def encode_step(char: str | None, input_names: list[str]) -> str:
    """Encode one sequential input step.

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


def encode_candidate_trace(candidate: str, input_names: list[str]) -> list[str]:
    """Encode a candidate word as a sequential aigsim trace."""
    vectors = [encode_step(char, input_names) for char in candidate]

    # Final step: end = true, all symbol inputs false.
    vectors.append(encode_step(None, input_names))

    return vectors


def parse_final_aigsim_output(stdout: str) -> int:
    """Extract final output from sequential aigsim output.

    Sequential aigsim usually prints:

        current_latch_state input_vector output next_latch_state

    In degenerate cases, it may print a simpler format, so this parser
    accepts all formats observed in our external tests.
    """
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
        raise AssertionError(f"Could not parse final aigsim output:\n{stdout}")

    return final_output


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

        vectors = encode_candidate_trace(candidate, input_names)
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

        actual = parse_final_aigsim_output(result.stdout)
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
