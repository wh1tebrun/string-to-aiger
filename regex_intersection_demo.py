from regex_bounded_compiler import compile_regex_bounded
from evaluator import evaluate
from pretty import pretty
from aiger import compile_expr_to_aiger


def run(pattern: str, bound: int, words: list[str]) -> None:
    expr = compile_regex_bounded(pattern, bound)

    print("Pattern:", pattern)
    print("Bound:", bound)

    print("\nBounded expression:")
    print(pretty(expr))

    print("\nEvaluation:")
    for word in words:
        print(f"  {word!r} -> {evaluate(expr, word)}")

    aiger_text = compile_expr_to_aiger(expr)

    filename = "intersection_output.aag"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(aiger_text)

    print(f"\nWritten to {filename}")
    print("-" * 60)


run(
    "(a|b)*&a*",
    4,
    ["", "a", "aa", "aaa", "b", "ab", "ba", "aaaa", "aaaaa"],
)
