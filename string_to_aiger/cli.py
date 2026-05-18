import argparse
import os

from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_length import regex_length, is_bound_complete
from string_to_aiger.regex.regex_bounded_compiler import compile_regex_bounded
from string_to_aiger.bounded.product_bounded_compiler import compile_regex_bounded_product
from string_to_aiger.aiger.aiger import compile_expr_to_aiger
from string_to_aiger.aiger.aiger_pipeline import (
    validate_and_write_aiger,
    write_aiger_without_validation,
)
from string_to_aiger.sequential.sequential_regex_compiler import compile_regex_to_sequential
from string_to_aiger.sequential.product_sequential_compiler import (
    compile_regex_to_sequential_product,
)
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter


def compile_bounded(
    pattern: str,
    bound: int,
    intersection_strategy: str,
) -> str:
    if intersection_strategy == "product":
        expr = compile_regex_bounded_product(pattern, bound)
    else:
        expr = compile_regex_bounded(pattern, bound)

    return compile_expr_to_aiger(expr)


def compile_sequential(
    pattern: str,
    intersection_strategy: str,
) -> str:
    if intersection_strategy == "product":
        circuit = compile_regex_to_sequential_product(pattern)
    else:
        circuit = compile_regex_to_sequential(pattern)

    writer = SequentialAigerWriter(circuit)
    return writer.write()


def read_pattern_from_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        pattern = f.read().strip()

    if not pattern:
        raise ValueError(f"Input file is empty: {path}")

    return pattern


def max_length_text(max_length: int | None) -> str:
    if max_length is None:
        return "unbounded"

    return str(max_length)


def yes_no(value: bool) -> str:
    if value:
        return "yes"

    return "no"


def length_analysis_lines(pattern: str, bound: int) -> list[str]:
    ast = parse_regex(pattern)
    info = regex_length(ast)
    complete = is_bound_complete(ast, bound)

    return [
        "Length analysis:",
        f"  min length: {info.min_length}",
        f"  max length: {max_length_text(info.max_length)}",
        f"  exact: {yes_no(info.exact)}",
        f"  bound complete: {yes_no(complete)}",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="string-to-aiger",
        description="Compile small string / regex fragments to ASCII AIGER.",
    )

    pattern_source = parser.add_mutually_exclusive_group(required=True)

    pattern_source.add_argument(
        "--pattern",
        help="Input pattern, for example: '(a|b)*&a*'",
    )

    pattern_source.add_argument(
        "--input-file",
        help="Path to a text file containing the input pattern.",
    )

    parser.add_argument(
        "--backend",
        choices=["bounded", "sequential"],
        default="bounded",
        help="Compilation backend to use.",
    )

    parser.add_argument(
        "--intersection-strategy",
        choices=["structural", "product"],
        default="structural",
        help=(
            "Strategy for compiling regex intersection. "
            "'structural' uses the existing structural encoding; "
            "'product' builds an explicit product automaton."
        ),
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

    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip internal structural validation of the generated AIGER text.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.bound < 0:
        parser.error("--bound must be non-negative")

    try:
        if args.input_file is not None:
            pattern = read_pattern_from_file(args.input_file)
        elif args.pattern is not None:
            pattern = args.pattern
        else:
            parser.error("Either --pattern or --input-file must be provided")

        analysis_lines: list[str] = []

        if args.backend == "bounded":
            analysis_lines = length_analysis_lines(pattern, args.bound)
            aiger_text = compile_bounded(
                pattern=pattern,
                bound=args.bound,
                intersection_strategy=args.intersection_strategy,
            )
        else:
            aiger_text = compile_sequential(
                pattern=pattern,
                intersection_strategy=args.intersection_strategy,
            )

        if args.skip_validation:
            write_aiger_without_validation(args.output, aiger_text)
            validation_status = "skipped"
        else:
            validate_and_write_aiger(args.output, aiger_text)
            validation_status = "passed"

    except ValueError as error:
        parser.error(str(error))

    print("Pattern:", pattern)
    print("Backend:", args.backend)
    print("Intersection strategy:", args.intersection_strategy)

    if args.backend == "bounded":
        print("Bound:", args.bound)

        for line in analysis_lines:
            print(line)

    print("AIGER validation:", validation_status)
    print("Written to:", args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
