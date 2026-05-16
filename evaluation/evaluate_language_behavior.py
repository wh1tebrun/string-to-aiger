import csv
import os
import sys
from dataclasses import dataclass

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
EVALUATION_DIR = os.path.dirname(__file__)

sys.path.append(ROOT_DIR)
os.makedirs(EVALUATION_DIR, exist_ok=True)

from evaluation.benchmark_cases import iter_expected_words  # noqa: E402
from string_to_aiger.regex.regex_bounded_compiler import compile_regex_bounded  # noqa: E402
from string_to_aiger.logic.evaluator import evaluate  # noqa: E402
from string_to_aiger.sequential.sequential_regex_compiler import compile_regex_to_sequential  # noqa: E402
from string_to_aiger.sequential.sequential_simulator import simulate  # noqa: E402


@dataclass
class BehaviorCase:
    pattern: str
    bound: int
    word: str
    expected: bool


@dataclass
class BehaviorResult:
    pattern: str
    bound: int
    word: str
    expected: bool
    bounded_result: bool
    sequential_result: bool
    status: str


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


def bounded_accepts(pattern: str, bound: int, word: str) -> bool:
    expr = compile_regex_bounded(pattern, bound)
    return evaluate(expr, word)


def sequential_accepts(pattern: str, word: str) -> bool:
    circuit = compile_regex_to_sequential(pattern)
    outputs = simulate(circuit, word_to_trace(word))
    return outputs[-1]["accept"]


def collect_cases() -> list[BehaviorCase]:
    return [
        BehaviorCase(
            pattern=pattern,
            bound=bound,
            word=word,
            expected=expected,
        )
        for pattern, bound, word, expected in iter_expected_words()
    ]


def evaluate_case(case: BehaviorCase) -> BehaviorResult:
    bounded_result = bounded_accepts(case.pattern, case.bound, case.word)
    sequential_result = sequential_accepts(case.pattern, case.word)

    status = (
        "OK"
        if bounded_result == case.expected and sequential_result == case.expected
        else "FAIL"
    )

    return BehaviorResult(
        pattern=case.pattern,
        bound=case.bound,
        word=case.word,
        expected=case.expected,
        bounded_result=bounded_result,
        sequential_result=sequential_result,
        status=status,
    )


def collect_results() -> list[BehaviorResult]:
    return [
        evaluate_case(case)
        for case in collect_cases()
    ]


def table_headers() -> list[str]:
    return [
        "pattern",
        "bound",
        "word",
        "expected",
        "bounded",
        "sequential",
        "status",
    ]


def display_word(word: str) -> str:
    if word == "":
        return "ε"
    return word


def result_to_row(result: BehaviorResult) -> list[str]:
    return [
        result.pattern,
        str(result.bound),
        display_word(result.word),
        str(result.expected),
        str(result.bounded_result),
        str(result.sequential_result),
        result.status,
    ]


def results_to_rows(results: list[BehaviorResult]) -> list[list[str]]:
    return [
        result_to_row(result)
        for result in results
    ]


def print_table(results: list[BehaviorResult]) -> None:
    headers = table_headers()
    rows = results_to_rows(results)

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


def write_csv(results: list[BehaviorResult], path: str) -> None:
    headers = table_headers()

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for result in results:
            writer.writerow(result_to_row(result))


def escape_markdown_cell(value: str) -> str:
    return value.replace("|", "\\|")


def write_markdown(results: list[BehaviorResult], path: str) -> None:
    headers = table_headers()
    rows = results_to_rows(results)

    with open(path, "w", encoding="utf-8") as f:
        f.write("# Language behavior validation\n\n")

        f.write("| " + " | ".join(headers) + " |\n")
        f.write("| " + " | ".join("---" for _ in headers) + " |\n")

        for row in rows:
            escaped_row = [
                escape_markdown_cell(value)
                for value in row
            ]
            f.write("| " + " | ".join(escaped_row) + " |\n")

        f.write("\n")
        f.write("## Notes\n\n")
        f.write("- `expected` is the manually specified expected language result.\n")
        f.write("- `bounded` is the result of the bounded combinational encoding.\n")
        f.write("- `sequential` is the result of the sequential latch-based encoding.\n")
        f.write("- `OK` means that both backends agree with the expected result.\n")
        f.write("- The selected positive examples are within the configured bound.\n")


def main() -> None:
    results = collect_results()

    csv_path = os.path.join(EVALUATION_DIR, "language_behavior.csv")
    markdown_path = os.path.join(EVALUATION_DIR, "language_behavior.md")

    print("\nLanguage behavior validation\n")
    print_table(results)

    write_csv(results, csv_path)
    write_markdown(results, markdown_path)

    failed = [
        result
        for result in results
        if result.status != "OK"
    ]

    print()
    print(f"Written to {csv_path}")
    print(f"Written to {markdown_path}")

    if failed:
        print()
        print(f"Validation failed for {len(failed)} case(s).")
        raise SystemExit(1)

    print()
    print("All language behavior checks passed.")


if __name__ == "__main__":
    main()
