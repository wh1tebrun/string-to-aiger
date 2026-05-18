import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.nfa.nfa import NFA  # noqa: E402
from string_to_aiger.nfa.nfa_evaluator import accepts  # noqa: E402
from string_to_aiger.nfa.nfa_optimize import deduplicate_transitions, optimize_nfa  # noqa: E402
from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa  # noqa: E402


def build_nfa_with_duplicate_transitions() -> NFA:
    nfa = NFA(
        start=0,
        accepts={2},
    )

    nfa.add_transition(0, "a", 1)
    nfa.add_transition(0, "a", 1)
    nfa.add_transition(0, "a", 1)

    nfa.add_transition(1, "b", 2)
    nfa.add_transition(1, "b", 2)

    return nfa


def build_nfa_with_duplicates_and_unreachable_states() -> NFA:
    nfa = NFA(
        start=0,
        accepts={2, 5},
    )

    # Reachable part with duplicates.
    nfa.add_transition(0, "a", 1)
    nfa.add_transition(0, "a", 1)
    nfa.add_transition(1, "b", 2)
    nfa.add_transition(1, "b", 2)

    # Unreachable part with duplicates.
    nfa.add_transition(3, "x", 4)
    nfa.add_transition(3, "x", 4)
    nfa.add_transition(4, "y", 5)

    return nfa


def transition_count(nfa: NFA) -> int:
    return sum(
        len(edges)
        for edges in nfa.transitions.values()
    )


def test_deduplicate_transitions_removes_duplicates():
    nfa = build_nfa_with_duplicate_transitions()
    deduplicated = deduplicate_transitions(nfa)

    assert transition_count(nfa) == 5
    assert transition_count(deduplicated) == 2

    assert deduplicated.transitions[0] == [("a", 1)]
    assert deduplicated.transitions[1] == [("b", 2)]


def test_deduplicate_transitions_preserves_language():
    nfa = build_nfa_with_duplicate_transitions()
    deduplicated = deduplicate_transitions(nfa)

    words = ["", "a", "ab", "abb", "b"]

    for word in words:
        assert accepts(nfa, word) == accepts(deduplicated, word)


def test_optimize_nfa_prunes_and_deduplicates():
    nfa = build_nfa_with_duplicates_and_unreachable_states()
    optimized = optimize_nfa(nfa)

    assert optimized.states() == {0, 1, 2}
    assert optimized.accepts == {2}
    assert transition_count(optimized) == 2

    assert optimized.transitions[0] == [("a", 1)]
    assert optimized.transitions[1] == [("b", 2)]


def test_optimize_nfa_preserves_language_for_reachable_part():
    nfa = build_nfa_with_duplicates_and_unreachable_states()
    optimized = optimize_nfa(nfa)

    words = ["", "a", "ab", "abb", "xy"]

    for word in words:
        assert accepts(nfa, word) == accepts(optimized, word)


def test_optimize_product_nfa_preserves_language():
    ast = parse_regex("(a|b)*&a*")
    nfa = build_product_aware_nfa(ast)
    optimized = optimize_nfa(nfa)

    words = ["", "a", "aa", "aaa", "b", "ab", "ba", "aaaa"]

    for word in words:
        assert accepts(nfa, word) == accepts(optimized, word)


def run_tests():
    test_deduplicate_transitions_removes_duplicates()
    test_deduplicate_transitions_preserves_language()
    test_optimize_nfa_prunes_and_deduplicates()
    test_optimize_nfa_preserves_language_for_reachable_part()
    test_optimize_product_nfa_preserves_language()

    print("All NFA optimization tests passed.")


if __name__ == "__main__":
    run_tests()
