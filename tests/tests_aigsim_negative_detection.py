import subprocess
from pathlib import Path

from aigsim_test_utils import (
    require_aigsim,
    parse_aiger_header,
    parse_aiger_input_names,
    encode_bounded_candidate,
    encode_sequential_trace,
    parse_bounded_aigsim_outputs,
    parse_final_sequential_aigsim_output,
)
from string_to_aiger.nfa.nfa_evaluator import accepts
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter
from string_to_aiger.sequential.sequential_regex_compiler import (
    compile_regex_to_sequential,
)


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
