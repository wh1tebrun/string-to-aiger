import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.regex.regex_ast import Intersect  # noqa: E402
from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.nfa.nfa_builder import build_nfa  # noqa: E402
from string_to_aiger.nfa.nfa_evaluator import accepts  # noqa: E402
from string_to_aiger.nfa.nfa_product import intersect_nfa  # noqa: E402


def build_product_from_intersection(pattern: str):
    ast = parse_regex(pattern)

    assert isinstance(ast, Intersect)

    left_nfa = build_nfa(ast.left)
    right_nfa = build_nfa(ast.right)

    return intersect_nfa(left_nfa, right_nfa)


def test_product_a_or_b_star_and_a_star():
    product = build_product_from_intersection("(a|b)*&a*")

    assert accepts(product, "") is True
    assert accepts(product, "a") is True
    assert accepts(product, "aa") is True
    assert accepts(product, "aaa") is True

    assert accepts(product, "b") is False
    assert accepts(product, "ab") is False
    assert accepts(product, "ba") is False


def test_product_ab_star_and_a_or_b_star():
    product = build_product_from_intersection("(ab)*&(a|b)*")

    assert accepts(product, "") is True
    assert accepts(product, "ab") is True
    assert accepts(product, "abab") is True
    assert accepts(product, "ababab") is True

    assert accepts(product, "a") is False
    assert accepts(product, "b") is False
    assert accepts(product, "aba") is False
    assert accepts(product, "abb") is False


def test_product_disjoint_a_star_and_b_star():
    product = build_product_from_intersection("a*&b*")

    assert accepts(product, "") is True

    assert accepts(product, "a") is False
    assert accepts(product, "aa") is False
    assert accepts(product, "b") is False
    assert accepts(product, "bb") is False
    assert accepts(product, "ab") is False
    assert accepts(product, "ba") is False


def test_product_nfa_has_valid_structure():
    product = build_product_from_intersection("(a|b)*&a*")

    assert product.start in product.states()
    assert len(product.states()) > 0
    assert len(product.accepts) > 0

    for source, edges in product.transitions.items():
        assert source in product.states()

        for _symbol, target in edges:
            assert target in product.states()


def run_tests():
    test_product_a_or_b_star_and_a_star()
    test_product_ab_star_and_a_or_b_star()
    test_product_disjoint_a_star_and_b_star()
    test_product_nfa_has_valid_structure()

    print("All NFA product tests passed.")


if __name__ == "__main__":
    run_tests()
