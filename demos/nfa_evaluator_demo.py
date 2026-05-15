import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.nfa.nfa_builder import build_nfa  # noqa: E402
from string_to_aiger.nfa.nfa_evaluator import accepts  # noqa: E402


def run(pattern: str, words: list[str]) -> None:
    ast = parse_regex(pattern)
    nfa = build_nfa(ast)

    print("Pattern:", pattern)
    for word in words:
        print(f"  {word!r} -> {accepts(nfa, word)}")
    print()


run("a*", ["", "a", "aa", "aaa", "b", "ab"])
run("(ab)*", ["", "ab", "abab", "a", "abb", "aba"])
run("(a|ba)*", ["", "a", "ba", "aba", "b", "baa"])
