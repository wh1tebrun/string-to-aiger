import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.regex.regex_pretty import pretty_regex  # noqa: E402
from string_to_aiger.nfa.nfa_builder import build_nfa  # noqa: E402


PATTERNS = [
    "a*",
    "(ab)*",
    "(a|b)*",
    "(a|ba)*",
]


def symbol_text(symbol: str | None) -> str:
    if symbol is None:
        return "eps"

    return symbol


def print_nfa(pattern: str) -> None:
    ast = parse_regex(pattern)
    nfa = build_nfa(ast)

    print("=" * 80)
    print("Pattern:", pattern)
    print("AST:", pretty_regex(ast))
    print("Start state:", nfa.start)
    print("Accepting states:", sorted(nfa.accepts))
    print("States:", sorted(nfa.states()))
    print()
    print("Transitions:")

    for source in sorted(nfa.transitions):
        edges = sorted(
            nfa.transitions[source],
            key=lambda edge: ("" if edge[0] is None else edge[0], edge[1]),
        )

        for symbol, target in edges:
            print(f"  {source} --{symbol_text(symbol)}--> {target}")

    print()


def main() -> None:
    print("Meeting NFA demo")
    print()
    print("This demo focuses only on Milestone 2 regex examples.")
    print("It parses regular expressions, builds NFAs, and prints their structure.")
    print()

    for pattern in PATTERNS:
        print_nfa(pattern)

    print("Meeting NFA demo completed successfully.")


if __name__ == "__main__":
    main()
