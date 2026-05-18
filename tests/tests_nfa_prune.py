import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.nfa.nfa import NFA  # noqa: E402
from string_to_aiger.nfa.nfa_prune import reachable_states, prune_unreachable_states  # noqa: E402
from string_to_aiger.nfa.nfa_evaluator import accepts  # noqa: E402
from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.nfa.nfa_builder import build_nfa  # noqa: E402
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa  # noqa: E402


def build_nfa_with_unreachable_states() -> NFA:
    nfa = NFA(
        start=0,
        accepts={2, 5},
    )

    # Reachable part:
    # 0 --a--> 1 --b--> 2
    nfa.add_transition(0, "a", 1)
    nfa.add_transition(1, "b", 2)

    # Unreachable part:
    # 3 --x--> 4 --y--> 5
    nfa.add_transition(3, "x", 4)
    nfa.add_transition(4, "y", 5)

    return nfa


def test_reachable_states():
    nfa = build_nfa_with_unreachable_states()

    assert reachable_states(nfa) == {0, 1, 2}


def test_prune_removes_unreachable_states():
    nfa = build_nfa_with_unreachable_states()
    pruned = prune_unreachable_states(nfa)

    assert pruned.states() == {0, 1, 2}
    assert pruned.start == 0
    assert pruned.accepts == {2}

    assert 3 not in pruned.transitions
    assert 4 not in pruned.transitions


def test_pruned_nfa_preserves_language_for_reachable_part():
    nfa = build_nfa_with_unreachable_states()
    pruned = prune_unreachable_states(nfa)

    assert accepts(nfa, "ab") is True
    assert accepts(pruned, "ab") is True

    assert accepts(nfa, "") is False
    assert accepts(pruned, "") is False

    assert accepts(nfa, "a") is False
    assert accepts(pruned, "a") is False

    # The unreachable accepting branch must not affect the language.
    assert accepts(nfa, "xy") is False
    assert accepts(pruned, "xy") is False


def test_prune_regular_regex_nfa_preserves_language():
    ast = parse_regex("(a|b)*")
    nfa = build_nfa(ast)
    pruned = prune_unreachable_states(nfa)

    words = ["", "a", "aa", "b", "ab", "ba", "abba", "abc"]

    for word in words:
        assert accepts(nfa, word) == accepts(pruned, word)


def test_prune_product_regex_nfa_preserves_language():
    ast = parse_regex("(a|b)*&a*")
    nfa = build_product_aware_nfa(ast)
    pruned = prune_unreachable_states(nfa)

    words = ["", "a", "aa", "b", "ab", "ba", "aaa"]

    for word in words:
        assert accepts(nfa, word) == accepts(pruned, word)


def test_prune_does_not_change_already_reachable_nfa():
    ast = parse_regex("(ab)*")
    nfa = build_nfa(ast)
    pruned = prune_unreachable_states(nfa)

    assert pruned.states() == nfa.states()
    assert pruned.start == nfa.start
    assert pruned.accepts == nfa.accepts

    words = ["", "ab", "abab", "a", "aba", "abb"]

    for word in words:
        assert accepts(nfa, word) == accepts(pruned, word)


def run_tests():
    test_reachable_states()
    test_prune_removes_unreachable_states()
    test_pruned_nfa_preserves_language_for_reachable_part()
    test_prune_regular_regex_nfa_preserves_language()
    test_prune_product_regex_nfa_preserves_language()
    test_prune_does_not_change_already_reachable_nfa()

    print("All NFA prune tests passed.")


if __name__ == "__main__":
    run_tests()
