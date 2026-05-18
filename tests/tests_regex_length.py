import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.regex.regex_length import regex_length, is_bound_complete  # noqa: E402


def assert_length(
    pattern: str,
    min_length: int,
    max_length: int | None,
    exact: bool = True,
) -> None:
    ast = parse_regex(pattern)
    info = regex_length(ast)

    assert info.min_length == min_length
    assert info.max_length == max_length
    assert info.exact is exact
    assert info.is_finite is (max_length is not None)


def test_length_single_char():
    assert_length("a", min_length=1, max_length=1)


def test_length_concat():
    assert_length("abc", min_length=3, max_length=3)


def test_length_union():
    assert_length("a|bc", min_length=1, max_length=2)


def test_length_star():
    assert_length("a*", min_length=0, max_length=None)


def test_length_star_of_empty():
    assert_length("a{0}*", min_length=0, max_length=0)


def test_length_plus():
    assert_length("a+", min_length=1, max_length=None)


def test_length_optional():
    assert_length("a?", min_length=0, max_length=1)


def test_length_character_class():
    assert_length("[a-c]", min_length=1, max_length=1)


def test_length_character_class_star():
    assert_length("[a-c]*", min_length=0, max_length=None)


def test_length_exact_bounded_repetition():
    assert_length("a{3}", min_length=3, max_length=3)


def test_length_zero_exact_bounded_repetition():
    assert_length("a{0}", min_length=0, max_length=0)


def test_length_range_bounded_repetition():
    assert_length("a{1,3}", min_length=1, max_length=3)


def test_length_zero_lower_range_bounded_repetition():
    assert_length("a{0,2}", min_length=0, max_length=2)


def test_length_open_ended_bounded_repetition():
    assert_length("a{2,}", min_length=2, max_length=None)


def test_length_zero_lower_open_ended_bounded_repetition():
    assert_length("a{0,}", min_length=0, max_length=None)


def test_length_group_exact_bounded_repetition():
    assert_length("(ab){2}", min_length=4, max_length=4)


def test_length_group_range_bounded_repetition():
    assert_length("(ab){1,3}", min_length=2, max_length=6)


def test_length_group_open_ended_bounded_repetition():
    assert_length("(ab){2,}", min_length=4, max_length=None)


def test_length_character_class_range_bounded_repetition():
    assert_length("[ab]{2,4}", min_length=2, max_length=4)


def test_length_escaped_literal():
    assert_length("a\\*\\+", min_length=3, max_length=3)


def test_length_intersection_is_conservative():
    assert_length("(a|b)*&a*", min_length=0, max_length=None, exact=False)


def test_length_intersection_with_finite_side_has_finite_upper_bound():
    assert_length("(a|b)*&a{1,3}", min_length=1, max_length=3, exact=False)


def test_bound_complete_for_finite_regex():
    ast = parse_regex("a{1,3}")

    assert is_bound_complete(ast, 0) is False
    assert is_bound_complete(ast, 2) is False
    assert is_bound_complete(ast, 3) is True
    assert is_bound_complete(ast, 4) is True


def test_bound_complete_for_infinite_regex():
    ast = parse_regex("a*")

    assert is_bound_complete(ast, 0) is False
    assert is_bound_complete(ast, 100) is False


def test_bound_complete_for_open_ended_repetition():
    ast = parse_regex("a{2,}")

    assert is_bound_complete(ast, 0) is False
    assert is_bound_complete(ast, 2) is False
    assert is_bound_complete(ast, 100) is False


def test_bound_complete_rejects_negative_bound():
    ast = parse_regex("a")

    try:
        is_bound_complete(ast, -1)
        assert False, "Expected ValueError for negative bound"
    except ValueError:
        pass


def run_tests():
    test_length_single_char()
    test_length_concat()
    test_length_union()
    test_length_star()
    test_length_star_of_empty()
    test_length_plus()
    test_length_optional()
    test_length_character_class()
    test_length_character_class_star()
    test_length_exact_bounded_repetition()
    test_length_zero_exact_bounded_repetition()
    test_length_range_bounded_repetition()
    test_length_zero_lower_range_bounded_repetition()
    test_length_open_ended_bounded_repetition()
    test_length_zero_lower_open_ended_bounded_repetition()
    test_length_group_exact_bounded_repetition()
    test_length_group_range_bounded_repetition()
    test_length_group_open_ended_bounded_repetition()
    test_length_character_class_range_bounded_repetition()
    test_length_escaped_literal()
    test_length_intersection_is_conservative()
    test_length_intersection_with_finite_side_has_finite_upper_bound()
    test_bound_complete_for_finite_regex()
    test_bound_complete_for_infinite_regex()
    test_bound_complete_for_open_ended_repetition()
    test_bound_complete_rejects_negative_bound()

    print("All regex length tests passed.")


if __name__ == "__main__":
    run_tests()
