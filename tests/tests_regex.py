import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.regex.regex_pretty import pretty_regex  # noqa: E402
from string_to_aiger.nfa.nfa_builder import build_nfa  # noqa: E402
from string_to_aiger.nfa.nfa_evaluator import accepts  # noqa: E402
from string_to_aiger.bounded.bounded_nfa_encoding import compile_nfa_bounded  # noqa: E402
from string_to_aiger.logic.evaluator import evaluate  # noqa: E402
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger  # noqa: E402


def test_regex_parser_basic():
    ast = parse_regex("a")
    assert pretty_regex(ast) == "a"


def test_regex_parser_concat():
    ast = parse_regex("ab")
    assert pretty_regex(ast) == "(ab)"


def test_regex_parser_union():
    ast = parse_regex("a|b")
    assert pretty_regex(ast) == "(a | b)"


def test_regex_parser_star():
    ast = parse_regex("a*")
    assert pretty_regex(ast) == "(a)*"


def test_regex_parser_character_class_simple():
    ast = parse_regex("[ab]")
    assert pretty_regex(ast) == "(a | b)"


def test_regex_parser_character_class_range():
    ast = parse_regex("[a-c]")
    assert pretty_regex(ast) == "((a | b) | c)"


def test_regex_parser_character_class_mixed():
    ast = parse_regex("[a-cx]")
    assert pretty_regex(ast) == "(((a | b) | c) | x)"


def test_regex_parser_character_class_in_concat():
    ast = parse_regex("x[ab]")
    assert pretty_regex(ast) == "(x(a | b))"


def test_regex_parser_rejects_empty_character_class():
    try:
        parse_regex("[]")
        assert False, "Expected ValueError for empty character class"
    except ValueError:
        pass


def test_regex_parser_rejects_unterminated_character_class():
    try:
        parse_regex("[ab")
        assert False, "Expected ValueError for unterminated character class"
    except ValueError:
        pass


def test_regex_parser_rejects_invalid_character_range():
    try:
        parse_regex("[c-a]")
        assert False, "Expected ValueError for invalid character range"
    except ValueError:
        pass


def test_regex_parser_rejects_trailing_escape():
    try:
        parse_regex("a\\")
        assert False, "Expected ValueError for trailing escape"
    except ValueError:
        pass


def test_regex_parser_rejects_trailing_escape_in_character_class():
    try:
        parse_regex("[a\\")
        assert False, "Expected ValueError for trailing escape in character class"
    except ValueError:
        pass


def test_nfa_accepts_star():
    ast = parse_regex("a*")
    nfa = build_nfa(ast)

    assert accepts(nfa, "") is True
    assert accepts(nfa, "a") is True
    assert accepts(nfa, "aa") is True
    assert accepts(nfa, "aaa") is True
    assert accepts(nfa, "b") is False
    assert accepts(nfa, "ab") is False


def test_nfa_accepts_ab_star():
    ast = parse_regex("(ab)*")
    nfa = build_nfa(ast)

    assert accepts(nfa, "") is True
    assert accepts(nfa, "ab") is True
    assert accepts(nfa, "abab") is True
    assert accepts(nfa, "a") is False
    assert accepts(nfa, "abb") is False
    assert accepts(nfa, "aba") is False


def test_nfa_accepts_character_class_star():
    ast = parse_regex("[ab]*")
    nfa = build_nfa(ast)

    assert accepts(nfa, "") is True
    assert accepts(nfa, "a") is True
    assert accepts(nfa, "b") is True
    assert accepts(nfa, "ab") is True
    assert accepts(nfa, "ba") is True
    assert accepts(nfa, "abba") is True

    assert accepts(nfa, "c") is False
    assert accepts(nfa, "abc") is False


def test_nfa_accepts_character_class_range():
    ast = parse_regex("[a-c]*")
    nfa = build_nfa(ast)

    assert accepts(nfa, "") is True
    assert accepts(nfa, "a") is True
    assert accepts(nfa, "b") is True
    assert accepts(nfa, "c") is True
    assert accepts(nfa, "abc") is True
    assert accepts(nfa, "cba") is True

    assert accepts(nfa, "d") is False
    assert accepts(nfa, "abd") is False


def test_nfa_accepts_escaped_star_literal():
    ast = parse_regex("a\\*")
    nfa = build_nfa(ast)

    assert accepts(nfa, "a*") is True

    assert accepts(nfa, "") is False
    assert accepts(nfa, "a") is False
    assert accepts(nfa, "aa") is False


def test_nfa_accepts_escaped_union_literal():
    ast = parse_regex("a\\|b")
    nfa = build_nfa(ast)

    assert accepts(nfa, "a|b") is True

    assert accepts(nfa, "a") is False
    assert accepts(nfa, "b") is False
    assert accepts(nfa, "ab") is False


def test_nfa_accepts_escaped_intersection_literal():
    ast = parse_regex("a\\&b")
    nfa = build_nfa(ast)

    assert accepts(nfa, "a&b") is True

    assert accepts(nfa, "a") is False
    assert accepts(nfa, "b") is False
    assert accepts(nfa, "ab") is False


def test_nfa_accepts_escaped_parentheses_literals():
    ast = parse_regex("\\(ab\\)")
    nfa = build_nfa(ast)

    assert accepts(nfa, "(ab)") is True

    assert accepts(nfa, "ab") is False
    assert accepts(nfa, "(a)") is False


def test_nfa_accepts_escaped_bracket_literals():
    ast = parse_regex("\\[ab\\]")
    nfa = build_nfa(ast)

    assert accepts(nfa, "[ab]") is True

    assert accepts(nfa, "ab") is False
    assert accepts(nfa, "[a]") is False


def test_nfa_accepts_escaped_backslash_literal():
    ast = parse_regex("\\\\")
    nfa = build_nfa(ast)

    assert accepts(nfa, "\\") is True

    assert accepts(nfa, "") is False
    assert accepts(nfa, "\\\\") is False


def test_nfa_accepts_escaped_dash_inside_character_class():
    ast = parse_regex("[a\\-c]")
    nfa = build_nfa(ast)

    assert accepts(nfa, "a") is True
    assert accepts(nfa, "-") is True
    assert accepts(nfa, "c") is True

    assert accepts(nfa, "b") is False
    assert accepts(nfa, "ac") is False


def test_nfa_accepts_escaped_closing_bracket_inside_character_class():
    ast = parse_regex("[a\\]]")
    nfa = build_nfa(ast)

    assert accepts(nfa, "a") is True
    assert accepts(nfa, "]") is True

    assert accepts(nfa, "b") is False
    assert accepts(nfa, "a]") is False


def test_bounded_encoding_a_star():
    ast = parse_regex("a*")
    nfa = build_nfa(ast)
    expr = compile_nfa_bounded(nfa, bound=3)

    assert evaluate(expr, "") is True
    assert evaluate(expr, "a") is True
    assert evaluate(expr, "aa") is True
    assert evaluate(expr, "aaa") is True

    # Rejected because the bound is 3.
    assert evaluate(expr, "aaaa") is False

    assert evaluate(expr, "b") is False
    assert evaluate(expr, "ab") is False


def test_bounded_encoding_ab_star():
    ast = parse_regex("(ab)*")
    nfa = build_nfa(ast)
    expr = compile_nfa_bounded(nfa, bound=6)

    assert evaluate(expr, "") is True
    assert evaluate(expr, "ab") is True
    assert evaluate(expr, "abab") is True
    assert evaluate(expr, "ababab") is True

    assert evaluate(expr, "a") is False
    assert evaluate(expr, "abb") is False
    assert evaluate(expr, "aba") is False
    assert evaluate(expr, "abababa") is False


def test_bounded_encoding_character_class_range():
    ast = parse_regex("[a-c]*")
    nfa = build_nfa(ast)
    expr = compile_nfa_bounded(nfa, bound=3)

    assert evaluate(expr, "") is True
    assert evaluate(expr, "a") is True
    assert evaluate(expr, "b") is True
    assert evaluate(expr, "c") is True
    assert evaluate(expr, "abc") is True
    assert evaluate(expr, "cba") is True

    # Rejected because the bound is 3.
    assert evaluate(expr, "abca") is False

    assert evaluate(expr, "d") is False
    assert evaluate(expr, "abd") is False


def test_bounded_encoding_escaped_star_literal():
    ast = parse_regex("a\\*")
    nfa = build_nfa(ast)
    expr = compile_nfa_bounded(nfa, bound=2)

    assert evaluate(expr, "a*") is True

    assert evaluate(expr, "") is False
    assert evaluate(expr, "a") is False
    assert evaluate(expr, "aa") is False


def test_regex_to_aiger_output():
    aiger_text = compile_regex_to_aiger("a*", bound=3)

    assert aiger_text.startswith("aag ")
    assert "o0 accept" in aiger_text
    assert "generated by string-to-aiger" in aiger_text


def run_tests():
    test_regex_parser_basic()
    test_regex_parser_concat()
    test_regex_parser_union()
    test_regex_parser_star()
    test_regex_parser_character_class_simple()
    test_regex_parser_character_class_range()
    test_regex_parser_character_class_mixed()
    test_regex_parser_character_class_in_concat()
    test_regex_parser_rejects_empty_character_class()
    test_regex_parser_rejects_unterminated_character_class()
    test_regex_parser_rejects_invalid_character_range()
    test_regex_parser_rejects_trailing_escape()
    test_regex_parser_rejects_trailing_escape_in_character_class()
    test_nfa_accepts_star()
    test_nfa_accepts_ab_star()
    test_nfa_accepts_character_class_star()
    test_nfa_accepts_character_class_range()
    test_nfa_accepts_escaped_star_literal()
    test_nfa_accepts_escaped_union_literal()
    test_nfa_accepts_escaped_intersection_literal()
    test_nfa_accepts_escaped_parentheses_literals()
    test_nfa_accepts_escaped_bracket_literals()
    test_nfa_accepts_escaped_backslash_literal()
    test_nfa_accepts_escaped_dash_inside_character_class()
    test_nfa_accepts_escaped_closing_bracket_inside_character_class()
    test_bounded_encoding_a_star()
    test_bounded_encoding_ab_star()
    test_bounded_encoding_character_class_range()
    test_bounded_encoding_escaped_star_literal()
    test_regex_to_aiger_output()

    print("All regex tests passed.")


if __name__ == "__main__":
    run_tests()
