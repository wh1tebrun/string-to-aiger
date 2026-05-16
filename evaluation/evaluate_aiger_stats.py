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
from string_to_aiger.aiger.aiger import compile_expr_to_aiger  # noqa: E402
from string_to_aiger.sequential.sequential_regex_compiler import compile_regex_to_sequential  # noqa: E402
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter  # noqa: E402


@dataclass
class AigerStats:
    pattern: str
    backend: str
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
    bound: str,
    aiger_text: str,
) -> AigerStats:
    """Parse the ASCII AIGER header.

    Header format:
        aag M I L O A

    M: maximum variable index
    I: number of inputs
    L: number of latches
    O: number of outputs
    A: number of AND gates
    """
    first_line = aiger_text.splitlines()[0]
    parts = first_line.split()

    if len(parts) != 6 or parts[0] != "aag":
        raise ValueError(f"Invalid AIGER header: {first_line}")

    return AigerStats(
        pattern=pattern,
        backend=backend,
        bound=bound,
        max_var_index=int(parts[1]),
        inputs=int(parts[2]),
        latches=int(parts[3]),
        outputs=int(parts[4]),
        and_gates=int(parts[5]),
        file_size_bytes=len(aiger_text.encode("utf-8")),
    )


def compile_bounded_stats(pattern: str, bound: int) -> AigerStats:
    expr = compile_regex_bounded(pattern, bound)
    aiger_text = compile_expr_to_aiger(expr)

    return parse_aiger_stats(
        pattern=pattern,
        backend="bounded",
        bound=str(bound),
        aiger_text=aiger_text,
    )


def compile_sequential_stats(pattern: str) -> AigerStats:
    circuit = compile_regex_to_sequential(pattern)
    writer = SequentialAigerWriter(circuit)
    aiger_text = writer.write()

    return parse_aiger_stats(
        pattern=pattern,
        backend="sequential",
        bound="-",
        aiger_text=aiger_text,
    )


def stats_to_rows(stats: list[AigerStats]) -> list[list[str]]:
    return [
        [
            stat.pattern,
            stat.backend,
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


def table_headers() -> list[str]:
    return [
        "pattern",
        "backend",
        "bound",
        "M",
        "I",
        "L",
        "O",
        "A",
        "size(bytes)",
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


def write_markdown(stats: list[AigerStats], path: str) -> None:
    headers = table_headers()
    rows = stats_to_rows(stats)

    with open(path, "w", encoding="utf-8") as f:
        f.write("# AIGER statistics comparison\n\n")

        f.write("| " + " | ".join(headers) + " |\n")
        f.write("| " + " | ".join("---" for _ in headers) + " |\n")

        for row in rows:
            f.write("| " + " | ".join(row) + " |\n")

        f.write("\n")
        f.write("## Notes\n\n")
        f.write("- `M` is the maximum variable index in the AIGER header.\n")
        f.write("- `I` is the number of inputs.\n")
        f.write("- `L` is the number of latches.\n")
        f.write("- `O` is the number of outputs.\n")
        f.write("- `A` is the number of AND gates.\n")
        f.write("- Bounded encodings are combinational and therefore have `L = 0`.\n")
        f.write("- Sequential encodings use latches and therefore have `L > 0`.\n")


def collect_stats() -> list[AigerStats]:
    all_stats: list[AigerStats] = []

    for benchmark in BENCHMARK_CASES:
        all_stats.append(
            compile_bounded_stats(
                benchmark.pattern,
                benchmark.bound,
            )
        )

        all_stats.append(
            compile_sequential_stats(
                benchmark.pattern,
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
