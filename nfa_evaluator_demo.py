from regex_parser import parse_regex
from nfa_builder import build_nfa
from nfa_evaluator import accepts


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