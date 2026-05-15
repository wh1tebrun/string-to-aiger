import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")

sys.path.append(ROOT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

from string_to_aiger.regex.regex_bounded_compiler import compile_regex_bounded  # noqa: E402
from string_to_aiger.logic.evaluator import evaluate  # noqa: E402
from string_to_aiger.logic.pretty import pretty  # noqa: E402
from string_to_aiger.aiger.aiger import compile_expr_to_aiger  # noqa: E402


def pattern_to_filename(pattern: str) -> str:
    result = []

    for ch in pattern:
        if ch.isalnum():
            result.append(ch)
        elif ch == "*":
            result.append("star")
        elif ch == "|":
            result.append("or")
        elif ch == "&":
            result.append("and")
        else:
            result.append("_")

    return "".join(result)


def run(pattern: str, bound: int, words: list[str]) -> None:
    expr = compile_regex_bounded(pattern, bound)

    print("Pattern:", pattern)
    print("Bound:", bound)

    print("\nBounded expression:")
    print(pretty(expr))

    print("\nEvaluation:")
    for word in words:
        print(f"  {word!r} -> {evaluate(expr, word)}")

    filename = f"intersection_output_{pattern_to_filename(pattern)}.aag"
    output_path = os.path.join(OUTPUT_DIR, filename)

    aiger_text = compile_expr_to_aiger(expr)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(aiger_text)

    print(f"\nWritten to {output_path}")
    print("-" * 60)
    print()


def main():
    run(
        "(a|b)*&a*",
        4,
        ["", "a", "aa", "aaa", "aaaa", "b", "ab", "ba", "aaaaa"],
    )

    run(
        "(ab)*&(a|b)*",
        6,
        ["", "ab", "abab", "ababab", "a", "b", "aba", "abb"],
    )

    run(
        "a*&b*",
        4,
        ["", "a", "aa", "b", "bb", "ab", "ba"],
    )


if __name__ == "__main__":
    main()
