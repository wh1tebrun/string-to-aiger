import argparse
import os

from string_to_aiger.regex.regex_bounded_compiler import compile_regex_bounded
from string_to_aiger.aiger.aiger import compile_expr_to_aiger
from string_to_aiger.sequential.sequential_regex_compiler import compile_regex_to_sequential
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter


def compile_bounded(pattern: str, bound: int) -> str:
    expr = compile_regex_bounded(pattern, bound)
    return compile_expr_to_aiger(expr)


def compile_sequential(pattern: str) -> str:
    circuit = compile_regex_to_sequential(pattern)
    writer = SequentialAigerWriter(circuit)
    return writer.write()


def write_output(path: str, aiger_text: str) -> None:
    output_dir = os.path.dirname(path)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(aiger_text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="string-to-aiger",
        description="Compile small string / regex fragments to ASCII AIGER.",
    )

    parser.add_argument(
        "--pattern",
        required=True,
        help="Input pattern, for example: '(a|b)*&a*'",
    )

    parser.add_argument(
        "--backend",
        choices=["bounded", "sequential"],
        default="bounded",
        help="Compilation backend to use.",
    )

    parser.add_argument(
        "--bound",
        type=int,
        default=4,
        help="Maximum word length for the bounded backend.",
    )

    parser.add_argument(
        "--output",
        default=os.path.join("outputs", "cli_output.aag"),
        help="Output path for the generated ASCII AIGER file.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.bound < 0:
        parser.error("--bound must be non-negative")

    if args.backend == "bounded":
        aiger_text = compile_bounded(args.pattern, args.bound)
    else:
        aiger_text = compile_sequential(args.pattern)

    write_output(args.output, aiger_text)

    print("Pattern:", args.pattern)
    print("Backend:", args.backend)

    if args.backend == "bounded":
        print("Bound:", args.bound)

    print("Written to:", args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
