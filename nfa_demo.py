from regex_parser import parse_regex
from nfa_builder import build_nfa


def print_nfa(pattern: str) -> None:
    ast = parse_regex(pattern)
    nfa = build_nfa(ast)

    print("Pattern:", pattern)
    print("Start:", nfa.start)
    print("Accepts:", nfa.accepts)
    print("Transitions:")

    for source in sorted(nfa.transitions.keys()):
        for symbol, target in nfa.transitions[source]:
            label = "ε" if symbol is None else symbol
            print(f"  {source} --{label}--> {target}")

    print()


examples = [
    "a",
    "ab",
    "a|b",
    "a*",
    "(ab)*",
    "(a|ba)*",
]

for example in examples:
    print_nfa(example)