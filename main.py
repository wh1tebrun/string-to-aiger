import os

from string_to_aiger.fixed.parser import parse
from string_to_aiger.fixed.model import build_model
from string_to_aiger.fixed.matcher import matches_or
from string_to_aiger.fixed.compiler import compile_or
from string_to_aiger.logic.pretty import pretty
from string_to_aiger.logic.evaluator import evaluate
from string_to_aiger.netlist.netlist_builder import NetlistBuilder
from string_to_aiger.netlist.netlist_pretty import pretty_netlist
from string_to_aiger.aiger.aiger import compile_expr_to_aiger


OUTPUT_DIR = "outputs"


def read_expression(path: str) -> str:
    """Read one expression from a text file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def main():
    expr = read_expression("examples/test1.txt")
    strings = parse(expr)
    model = build_model(strings)

    print("Expression:", expr)
    print("Parsed strings:", strings)
    print("Model:", model)

    # TODO: load evaluation examples from file
    tests = [
        "abba",
        "abb",
        "ab",
        "abbb",
        "abbaa",
        "xyz",
    ]

    print("\nMatcher evaluation:")
    for test in tests:
        result = matches_or(model, test)
        print(f"{test!r} -> {result}")

    compiled = compile_or(model)

    print("\nCompiled logic:")
    print(pretty(compiled))

    print("\nCompiled evaluation:")
    for test in tests:
        result = evaluate(compiled, test)
        print(f"{test!r} -> {result}")

    builder = NetlistBuilder()
    output_id = builder.compile_expr(compiled)

    print("\nNetlist:")
    print(pretty_netlist(builder.nodes))
    print(f"\nOutput node: {output_id}")

    aiger_text = compile_expr_to_aiger(compiled)

    print("\nAIGER:")
    print(aiger_text)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "output.aag")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(aiger_text)

    print(f"\nWritten to {output_path}")


if __name__ == "__main__":
    main()
