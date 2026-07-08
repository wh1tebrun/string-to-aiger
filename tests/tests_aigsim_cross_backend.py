import re
import subprocess
from pathlib import Path

from aigsim_test_utils import (
    require_aigsim,
    parse_aiger_input_names,
    encode_bounded_candidate,
    encode_sequential_trace,
    parse_bounded_aigsim_outputs,
    parse_final_sequential_aigsim_output,
)
from string_to_aiger.aiger.aiger import compile_expr_to_aiger
from string_to_aiger.bounded.product_bounded_compiler import (
    compile_regex_bounded_product,
)
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger
from string_to_aiger.sequential.product_sequential_compiler import (
    compile_regex_to_sequential_product,
)
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter
from string_to_aiger.sequential.sequential_regex_compiler import (
    compile_regex_to_sequential,
)


BOUND = 4


def run_bounded_aigsim(aag_text: str, candidates: list[str], stem: str) -> list[int]:
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    aag_path = output_dir / f"test_cross_backend_{stem}.aag"
    stim_path = output_dir / f"test_cross_backend_{stem}.stim"

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
            "aigsim failed for bounded cross-backend case\n"
            f"stem: {stem}\n"
            f"input names: {input_names}\n"
            f"vectors: {vectors}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    outputs = parse_bounded_aigsim_outputs(result.stdout)

    assert len(outputs) == len(candidates), (
        "bounded cross-backend output count mismatch\n"
        f"stem: {stem}\n"
        f"candidates: {candidates}\n"
        f"outputs: {outputs}\n"
        f"stdout:\n{result.stdout}"
    )

    return outputs


def run_sequential_aigsim(aag_text: str, candidates: list[str], stem: str) -> list[int]:
    aigsim = require_aigsim()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    aag_path = output_dir / f"test_cross_backend_{stem}.aag"
    aag_path.write_text(aag_text, encoding="utf-8")

    input_names = parse_aiger_input_names(aag_text)
    outputs: list[int] = []

    for index, candidate in enumerate(candidates):
        stim_path = output_dir / f"test_cross_backend_{stem}_{index}.stim"

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
                "aigsim failed for sequential cross-backend case\n"
                f"stem: {stem}\n"
                f"candidate: {candidate!r}\n"
                f"input names: {input_names}\n"
                f"vectors: {vectors}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

        outputs.append(parse_final_sequential_aigsim_output(result.stdout))

    return outputs


def compile_bounded_structural(pattern: str) -> str:
    return compile_regex_to_aiger(pattern, BOUND)


def compile_bounded_product(pattern: str) -> str:
    expr = compile_regex_bounded_product(pattern, BOUND)
    return compile_expr_to_aiger(expr)


def compile_sequential_structural(pattern: str) -> str:
    circuit = compile_regex_to_sequential(pattern)
    return SequentialAigerWriter(circuit).write()


def compile_sequential_product(pattern: str) -> str:
    circuit = compile_regex_to_sequential_product(pattern)
    return SequentialAigerWriter(circuit).write()


def safe_stem(text: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return stem or "case"


def run_cross_backend_case(pattern: str, candidates: list[str]) -> None:
    """Check that all major backends agree on the same regex/candidates."""
    assert all(len(candidate) <= BOUND for candidate in candidates), (
        "Cross-backend consistency only compares words within the bounded "
        "backend's configured bound."
    )

    stem = safe_stem(pattern)

    bounded_structural = run_bounded_aigsim(
        compile_bounded_structural(pattern),
        candidates,
        f"{stem}_bounded_structural",
    )

    bounded_product = run_bounded_aigsim(
        compile_bounded_product(pattern),
        candidates,
        f"{stem}_bounded_product",
    )

    sequential_structural = run_sequential_aigsim(
        compile_sequential_structural(pattern),
        candidates,
        f"{stem}_sequential_structural",
    )

    sequential_product = run_sequential_aigsim(
        compile_sequential_product(pattern),
        candidates,
        f"{stem}_sequential_product",
    )

    assert bounded_structural == bounded_product, (
        "bounded structural and bounded product disagree\n"
        f"pattern: {pattern}\n"
        f"candidates: {candidates}\n"
        f"bounded structural: {bounded_structural}\n"
        f"bounded product:    {bounded_product}"
    )

    assert bounded_structural == sequential_structural, (
        "bounded structural and sequential structural disagree\n"
        f"pattern: {pattern}\n"
        f"candidates: {candidates}\n"
        f"bounded structural:    {bounded_structural}\n"
        f"sequential structural: {sequential_structural}"
    )

    assert bounded_structural == sequential_product, (
        "bounded structural and sequential product disagree\n"
        f"pattern: {pattern}\n"
        f"candidates: {candidates}\n"
        f"bounded structural: {bounded_structural}\n"
        f"sequential product: {sequential_product}"
    )


def test_cross_backend_a_or_b_star_and_a_star() -> None:
    run_cross_backend_case(
        pattern="(a|b)*&a*",
        candidates=["", "a", "b", "aa", "ab", "ba", "aaa", "aaaa"],
    )


def test_cross_backend_disjoint_except_empty() -> None:
    run_cross_backend_case(
        pattern="a*&b*",
        candidates=["", "a", "b", "aa", "bb", "ab", "ba", "abab"],
    )


def test_cross_backend_ab_star_inside_alphabet_star() -> None:
    run_cross_backend_case(
        pattern="(ab)*&(a|b)*",
        candidates=["", "a", "b", "ab", "aba", "abb", "abab", "baba"],
    )


def test_cross_backend_mixed_concat_union_star() -> None:
    run_cross_backend_case(
        pattern="(a|ba)*&(a|b)*",
        candidates=["", "a", "b", "aa", "ba", "aba", "baba", "aaaa"],
    )


def run_tests() -> None:
    test_cross_backend_a_or_b_star_and_a_star()
    test_cross_backend_disjoint_except_empty()
    test_cross_backend_ab_star_inside_alphabet_star()
    test_cross_backend_mixed_concat_union_star()

    print("All aigsim cross-backend consistency tests passed.")


if __name__ == "__main__":
    run_tests()
