from parser import parse
from model import build_model
from matcher import matches_or
from compiler import compile_or
from pretty import pretty
from evaluator import evaluate
from netlist_builder import NetlistBuilder
from netlist_pretty import pretty_netlist
from aiger import compile_expr_to_aiger


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

    with open("output.aag", "w", encoding="utf-8") as f:
        f.write(aiger_text)

    print("\nWritten to output.aag")


if __name__ == "__main__":
    main()
