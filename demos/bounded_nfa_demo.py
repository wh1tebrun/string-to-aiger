import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")

sys.path.append(ROOT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

from regex_parser import parse_regex  # noqa: E402
from nfa_builder import build_nfa  # noqa: E402
from bounded_nfa_encoding import compile_nfa_bounded  # noqa: E402
from evaluator import evaluate  # noqa: E402
from pretty import pretty  # noqa: E402
from aiger import compile_expr_to_aiger  # noqa: E402


def run(pattern: str, bound: int, words: list[str]) -> None:
    ast = parse_regex(pattern)
    nfa = build_nfa(ast)
    expr = compile_nfa_bounded(nfa, bound)

    print("Pattern:", pattern)
    print("Bound:", bound)
    print("\nBounded expression:")
    print(pretty(expr))

    print("\nEvaluation:")
    for word in words:
        print(f"  {word!r} -> {evaluate(expr, word)}")

    aiger_text = compile_expr_to_aiger(expr)

    filename = f"bounded_output_{pattern_to_filename(pattern)}.aag"
    output_path = os.path.join(OUTPUT_DIR, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(aiger_text)

    print(f"\nWritten to {output_path}")
    print("-" * 60)
    print()


def pattern_to_filename(pattern: str) -> str:
    result = []

    for ch in pattern:
        if ch.isalnum():
            result.append(ch)
        elif ch == "*":
            result.append("star")
        elif ch == "|":
            result.append("or")
        else:
            result.append("_")

    return "".join(result)


run("a*", 3, ["", "a", "aa", "aaa", "aaaa", "b", "ab"])

run("(ab)*", 6, ["", "ab", "abab", "ababab", "a", "abb", "aba", "abababa"])

run("(a|b)*", 4, ["", "a", "b", "ab", "ba", "abba", "abc", "aaaaa"])

run("(a|ba)*", 5, ["", "a", "ba", "aba", "baa", "ababa", "b", "bb"])
