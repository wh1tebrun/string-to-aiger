import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.regex.regex_alphabet import regex_alphabet  # noqa: E402
from string_to_aiger.nfa.nfa_builder import build_nfa  # noqa: E402
from string_to_aiger.nfa.nfa_alphabet import nfa_alphabet  # noqa: E402
from string_to_aiger.sequential.nfa_to_sequential import compile_nfa_to_sequential  # noqa: E402
from string_to_aiger.sequential.sequential_simulator import simulate  # noqa: E402


def word_to_trace(word: str) -> list[dict[str, bool]]:
    trace = []

    for ch in word:
        trace.append({
            f"is_{ch}": True,
            "end": False,
        })

    trace.append({
        "end": True,
    })

    return trace


def test_regex_alphabet_basic_char():
    ast = parse_regex("a")
    assert regex_alphabet(ast) == {"a"}


def test_regex_alphabet_concat():
    ast = parse_regex("abc")
    assert regex_alphabet(ast) == {"a", "b", "c"}


def test_regex_alphabet_union():
    ast = parse_regex("a|b")
    assert regex_alphabet(ast) == {"a", "b"}


def test_regex_alphabet_star():
    ast = parse_regex("(a|b)*")
    assert regex_alphabet(ast) == {"a", "b"}


def test_regex_alphabet_intersection():
    ast = parse_regex("(a|b)*&a*")
    assert regex_alphabet(ast) == {"a", "b"}


def test_regex_alphabet_character_class():
    ast = parse_regex("[a-cx]")
    assert regex_alphabet(ast) == {"a", "b", "c", "x"}


def test_regex_alphabet_escaped_literals():
    ast = parse_regex("a\\*\\+\\?")
    assert regex_alphabet(ast) == {"a", "*", "+", "?"}


def test_nfa_alphabet_basic():
    ast = parse_regex("(a|b)*")
    nfa = build_nfa(ast)

    assert nfa_alphabet(nfa) == {"a", "b"}


def test_nfa_alphabet_character_class_range():
    ast = parse_regex("[a-c]*")
    nfa = build_nfa(ast)

    assert nfa_alphabet(nfa) == {"a", "b", "c"}


def test_nfa_alphabet_escaped_literals():
    ast = parse_regex("a\\*")
    nfa = build_nfa(ast)

    assert nfa_alphabet(nfa) == {"a", "*"}


def test_sequential_backend_uses_extracted_alphabet():
    ast = parse_regex("[a-c]*")
    nfa = build_nfa(ast)
    circuit = compile_nfa_to_sequential(nfa)

    outputs = simulate(circuit, word_to_trace("abc"))
    assert outputs[-1]["accept"] is True

    outputs = simulate(circuit, word_to_trace("abd"))
    assert outputs[-1]["accept"] is False


def run_tests():
    test_regex_alphabet_basic_char()
    test_regex_alphabet_concat()
    test_regex_alphabet_union()
    test_regex_alphabet_star()
    test_regex_alphabet_intersection()
    test_regex_alphabet_character_class()
    test_regex_alphabet_escaped_literals()
    test_nfa_alphabet_basic()
    test_nfa_alphabet_character_class_range()
    test_nfa_alphabet_escaped_literals()
    test_sequential_backend_uses_extracted_alphabet()

    print("All alphabet tests passed.")


if __name__ == "__main__":
    run_tests()
