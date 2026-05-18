import csv
import os
import sys
from dataclasses import dataclass

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
EVALUATION_DIR = os.path.dirname(__file__)

sys.path.append(ROOT_DIR)
os.makedirs(EVALUATION_DIR, exist_ok=True)

from evaluation.benchmark_cases import BENCHMARK_CASES  # noqa: E402
from string_to_aiger.regex.regex_bounded_compiler import compile_regex_bounded  # noqa: E402
from string_to_aiger.bounded.product_bounded_compiler import compile_regex_bounded_product  # noqa: E402
from string_to_aiger.aiger.aiger import compile_expr_to_aiger  # noqa: E402
from string_to_aiger.aiger.aiger_validator import validate_aiger  # noqa: E402
from string_to_aiger.sequential.sequential_regex_compiler import compile_regex_to_sequential  # noqa: E402
from string_to_aiger.sequential.product_sequential_compiler import compile_regex_to_sequential_product  # noqa: E402
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter  # noqa: E402


INTERSECTION_STRATEGIES = ("structural", "product")


@dataclass
class AigerStats:
    pattern: str
    backend: str
    intersection_strategy: str
    bound: str
    max_var_index: int
    inputs: int
    latches: int
    outputs: int
    and_gates: int
    file_size_bytes: int


def parse_aiger_stats(
    pattern: str,
    backend: str,
    intersection_strategy: str,
    bound: str,
    aiger_text: str,
) -> AigerStats:
    """Parse and validate ASCII AIGER header statistics."""
    header = validate_aiger(aiger_text)

    return AigerStats(
        pattern=pattern,
        backend=backend,
        intersection_strategy=intersection_strategy,
        bound=bound,
        max_var_index=header.max_var_index,
        inputs=header.inputs,
        latches=header.latches,
        outputs=header.outputs,
        and_gates=header.and_gates,
        file_size_bytes=len(aiger_text.encode("utf-8")),
    )


def compile_bounded_stats(
    pattern: str,
    bound: int,
    intersection_strategy: str,
) -> AigerStats:
    if intersection_strategy == "product":
        expr = compile_regex_bounded_product(pattern, bound)
    else:
        expr = compile_regex_bounded(pattern, bound)

    aiger_text = compile_expr_to_aiger(expr)

    return parse_aiger_stats(
        pattern=pattern,
        backend="bounded",
        intersection_strategy=intersection_strategy,
        bound=str(bound),
        aiger_text=aiger_text,
    )


def compile_sequential_stats(
    pattern: str,
    intersection_strategy: str,
) -> AigerStats:
    if intersection_strategy == "product":
        circuit = compile_regex_to_sequential_product(pattern)
    else:
        circuit = compile_regex_to_sequential(pattern)

    writer = SequentialAigerWriter(circuit)
    aiger_text = writer.write()

    return parse_aiger_stats(
        pattern=pattern,
        backend="sequential",
        intersection_strategy=intersection_strategy,
        bound="-",
        aiger_text=aiger_text,
    )


def table_headers() -> list[str]:
    return [
        "pattern",
        "backend",
        "strategy",
        "bound",
        "M",
        "I",
        "L",
        "O",
        "A",
        "size(bytes)",
    ]


def stats_to_rows(stats: list[AigerStats]) -> list[list[str]]:
    return [
        [
            stat.pattern,
            stat.backend,
            stat.intersection_strategy,
            stat.bound,
            str(stat.max_var_index),
            str(stat.inputs),
            str(stat.latches),
            str(stat.outputs),
            str(stat.and_gates),
            str(stat.file_size_bytes),
        ]
        for stat in stats
    ]


def print_table(stats: list[AigerStats]) -> None:
    headers = table_headers()
    rows = stats_to_rows(stats)

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


def write_csv(stats: list[AigerStats], path: str) -> None:
    headers = table_headers()
    rows = stats_to_rows(stats)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def escape_markdown_cell(value: str) -> str:
    return value.replace("|", "\\|")


def write_markdown(stats: list[AigerStats], path: str) -> None:
    headers = table_headers()
    rows = stats_to_rows(stats)

    with open(path, "w", encoding="utf-8") as f:
        f.write("# AIGER statistics comparison\n\n")

        f.write("This table compares generated ASCII AIGER header statistics ")
        f.write("for both compilation backends and both intersection strategies.\n\n")

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
        f.write("- `M` is the maximum variable index in the AIGER header.\n")
        f.write("- `I` is the number of inputs.\n")
        f.write("- `L` is the number of latches.\n")
        f.write("- `O` is the number of outputs.\n")
        f.write("- `A` is the number of AND gates.\n")
        f.write("- Bounded encodings are combinational and therefore have `L = 0`.\n")
        f.write("- Sequential encodings use latches and therefore have `L > 0`.\n")
        f.write("- `structural` compiles intersection structurally.\n")
        f.write("- `product` compiles intersection through explicit product automata.\n")
        f.write("- Every generated AIGER text is checked by the internal structural validator before statistics are recorded.\n")


def collect_stats() -> list[AigerStats]:
    all_stats: list[AigerStats] = []

    for benchmark in BENCHMARK_CASES:
        for strategy in INTERSECTION_STRATEGIES:
            all_stats.append(
                compile_bounded_stats(
                    pattern=benchmark.pattern,
                    bound=benchmark.bound,
                    intersection_strategy=strategy,
                )
            )

            all_stats.append(
                compile_sequential_stats(
                    pattern=benchmark.pattern,
                    intersection_strategy=strategy,
                )
            )

    return all_stats


def main() -> None:
    all_stats = collect_stats()

    csv_path = os.path.join(EVALUATION_DIR, "aiger_stats.csv")
    markdown_path = os.path.join(EVALUATION_DIR, "aiger_stats.md")

    print("\nAIGER statistics comparison\n")
    print_table(all_stats)

    write_csv(all_stats, csv_path)
    write_markdown(all_stats, markdown_path)

    print()
    print(f"Written to {csv_path}")
    print(f"Written to {markdown_path}")


if __name__ == "__main__":
    main()
