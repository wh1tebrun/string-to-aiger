import csv
import itertools
import os
import sys
from dataclasses import dataclass

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
EVALUATION_DIR = os.path.dirname(__file__)

sys.path.append(ROOT_DIR)
os.makedirs(EVALUATION_DIR, exist_ok=True)

from evaluation.benchmark_cases import BENCHMARK_CASES  # noqa: E402
from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.regex.regex_alphabet import regex_alphabet  # noqa: E402
from string_to_aiger.regex.regex_bounded_compiler import compile_regex_bounded  # noqa: E402
from string_to_aiger.bounded.product_bounded_compiler import compile_regex_bounded_product  # noqa: E402
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa  # noqa: E402
from string_to_aiger.logic.evaluator import evaluate  # noqa: E402
from string_to_aiger.nfa.nfa_evaluator import accepts as nfa_accepts  # noqa: E402
from string_to_aiger.sequential.sequential_regex_compiler import compile_regex_to_sequential  # noqa: E402
from string_to_aiger.sequential.product_sequential_compiler import compile_regex_to_sequential_product  # noqa: E402
from string_to_aiger.sequential.sequential_simulator import simulate  # noqa: E402


@dataclass
class ExhaustiveResult:
    pattern: str
    bound: int
    word: str
    expected: bool
    bounded_structural: bool
    bounded_product: bool
    sequential_structural: bool
    sequential_product: bool
    status: str


@dataclass
class BenchmarkSummary:
    pattern: str
    bound: int
    alphabet: tuple[str, ...]
    checked_words: int
    passed: int
    failed: int


def word_to_trace(word: str) -> list[dict[str, bool]]:
    trace = []

    for ch in word:
        trace.append({
            f"is_{ch}": True,
            "end": False,
        })

    trace.append({
        "end": True,
    })

    return trace


def generate_words(alphabet: tuple[str, ...], bound: int) -> list[str]:
    words = [""]

    for length in range(1, bound + 1):
        for letters in itertools.product(alphabet, repeat=length):
            words.append("".join(letters))

    return words


def display_word(word: str) -> str:
    if word == "":
        return "ε"
    return word


def escape_markdown_cell(value: str) -> str:
    return value.replace("|", "\\|")


def evaluate_benchmark(
    pattern: str,
    bound: int,
) -> tuple[list[ExhaustiveResult], BenchmarkSummary]:
    ast = parse_regex(pattern)
    alphabet = tuple(sorted(regex_alphabet(ast)))

    expected_nfa = build_product_aware_nfa(ast)
    bounded_structural_expr = compile_regex_bounded(pattern, bound)
    bounded_product_expr = compile_regex_bounded_product(pattern, bound)
    sequential_structural_circuit = compile_regex_to_sequential(pattern)
    sequential_product_circuit = compile_regex_to_sequential_product(pattern)

    results: list[ExhaustiveResult] = []

    for word in generate_words(alphabet, bound):
        expected = nfa_accepts(expected_nfa, word)

        bounded_structural = evaluate(
            bounded_structural_expr,
            word,
        )
        bounded_product = evaluate(
            bounded_product_expr,
            word,
        )

        sequential_structural_outputs = simulate(
            sequential_structural_circuit,
            word_to_trace(word),
        )
        sequential_product_outputs = simulate(
            sequential_product_circuit,
            word_to_trace(word),
        )

        sequential_structural = sequential_structural_outputs[-1]["accept"]
        sequential_product = sequential_product_outputs[-1]["accept"]

        status = (
            "OK"
            if (
                expected == bounded_structural
                and expected == bounded_product
                and expected == sequential_structural
                and expected == sequential_product
            )
            else "FAIL"
        )

        results.append(
            ExhaustiveResult(
                pattern=pattern,
                bound=bound,
                word=word,
                expected=expected,
                bounded_structural=bounded_structural,
                bounded_product=bounded_product,
                sequential_structural=sequential_structural,
                sequential_product=sequential_product,
                status=status,
            )
        )

    failed = [
        result
        for result in results
        if result.status != "OK"
    ]

    summary = BenchmarkSummary(
        pattern=pattern,
        bound=bound,
        alphabet=alphabet,
        checked_words=len(results),
        passed=len(results) - len(failed),
        failed=len(failed),
    )

    return results, summary


def collect_results() -> tuple[list[ExhaustiveResult], list[BenchmarkSummary]]:
    all_results: list[ExhaustiveResult] = []
    summaries: list[BenchmarkSummary] = []

    for benchmark in BENCHMARK_CASES:
        results, summary = evaluate_benchmark(
            pattern=benchmark.pattern,
            bound=benchmark.bound,
        )

        all_results.extend(results)
        summaries.append(summary)

    return all_results, summaries


def result_headers() -> list[str]:
    return [
        "pattern",
        "bound",
        "word",
        "expected",
        "bounded_structural",
        "bounded_product",
        "sequential_structural",
        "sequential_product",
        "status",
    ]


def summary_headers() -> list[str]:
    return [
        "pattern",
        "bound",
        "alphabet",
        "checked_words",
        "passed",
        "failed",
    ]


def result_to_row(result: ExhaustiveResult) -> list[str]:
    return [
        result.pattern,
        str(result.bound),
        display_word(result.word),
        str(result.expected),
        str(result.bounded_structural),
        str(result.bounded_product),
        str(result.sequential_structural),
        str(result.sequential_product),
        result.status,
    ]


def summary_to_row(summary: BenchmarkSummary) -> list[str]:
    return [
        summary.pattern,
        str(summary.bound),
        "{" + ", ".join(summary.alphabet) + "}",
        str(summary.checked_words),
        str(summary.passed),
        str(summary.failed),
    ]


def print_summary_table(summaries: list[BenchmarkSummary]) -> None:
    headers = summary_headers()
    rows = [
        summary_to_row(summary)
        for summary in summaries
    ]

    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows))
        for i in range(len(headers))
    ]

    header_line = " | ".join(
        headers[i].ljust(widths[i])
        for i in range(len(headers))
    )

    separator = "-+-".join("-" * width for width in widths)

    print(header_line)
    print(separator)

    for row in rows:
        print(
            " | ".join(
                row[i].ljust(widths[i])
                for i in range(len(row))
            )
        )


def write_results_csv(results: list[ExhaustiveResult], path: str) -> None:
    headers = result_headers()

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for result in results:
            writer.writerow(result_to_row(result))


def write_summary_csv(summaries: list[BenchmarkSummary], path: str) -> None:
    headers = summary_headers()

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for summary in summaries:
            writer.writerow(summary_to_row(summary))


def write_markdown(
    results: list[ExhaustiveResult],
    summaries: list[BenchmarkSummary],
    path: str,
) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Exhaustive bounded language validation\n\n")

        f.write("This evaluation checks all words up to the configured bound ")
        f.write("over the extracted alphabet of each benchmark pattern.\n\n")

        f.write("For each generated word, the following results are compared:\n\n")
        f.write("- expected result from the product-aware NFA\n")
        f.write("- bounded backend with structural intersection encoding\n")
        f.write("- bounded backend with explicit product automata\n")
        f.write("- sequential backend with structural / parallel-composition intersection encoding\n")
        f.write("- sequential backend with explicit product automata\n\n")

        f.write("## Summary\n\n")

        summary_headers_list = summary_headers()
        f.write("| " + " | ".join(summary_headers_list) + " |\n")
        f.write("| " + " | ".join("---" for _ in summary_headers_list) + " |\n")

        for summary in summaries:
            row = [
                escape_markdown_cell(value)
                for value in summary_to_row(summary)
            ]
            f.write("| " + " | ".join(row) + " |\n")

        f.write("\n")
        f.write("## Detailed results\n\n")

        result_headers_list = result_headers()
        f.write("| " + " | ".join(result_headers_list) + " |\n")
        f.write("| " + " | ".join("---" for _ in result_headers_list) + " |\n")

        for result in results:
            row = [
                escape_markdown_cell(value)
                for value in result_to_row(result)
            ]
            f.write("| " + " | ".join(row) + " |\n")

        f.write("\n")
        f.write("## Notes\n\n")
        f.write("- The exhaustive search is bounded by the benchmark-specific bound.\n")
        f.write("- The alphabet is extracted from the regex AST.\n")
        f.write("- `OK` means that the expected NFA result and all backend/strategy results agree.\n")


def main() -> None:
    results, summaries = collect_results()

    results_csv_path = os.path.join(EVALUATION_DIR, "exhaustive_behavior.csv")
    summary_csv_path = os.path.join(EVALUATION_DIR, "exhaustive_behavior_summary.csv")
    markdown_path = os.path.join(EVALUATION_DIR, "exhaustive_behavior.md")

    print("\nExhaustive bounded language validation\n")
    print_summary_table(summaries)

    write_results_csv(results, results_csv_path)
    write_summary_csv(summaries, summary_csv_path)
    write_markdown(results, summaries, markdown_path)

    failed = [
        result
        for result in results
        if result.status != "OK"
    ]

    print()
    print(f"Written to {results_csv_path}")
    print(f"Written to {summary_csv_path}")
    print(f"Written to {markdown_path}")

    if failed:
        print()
        print(f"Exhaustive validation failed for {len(failed)} case(s).")
        raise SystemExit(1)

    print()
    print("All exhaustive bounded language checks passed.")


if __name__ == "__main__":
    main()
