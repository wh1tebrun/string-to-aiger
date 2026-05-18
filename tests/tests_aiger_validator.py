import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.aiger.aiger_validator import validate_aiger  # noqa: E402
from string_to_aiger.regex.regex_bounded_compiler import compile_regex_bounded  # noqa: E402
from string_to_aiger.aiger.aiger import compile_expr_to_aiger  # noqa: E402
from string_to_aiger.sequential.sequential_regex_compiler import compile_regex_to_sequential  # noqa: E402
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter  # noqa: E402


def compile_bounded_aiger(pattern: str, bound: int) -> str:
    expr = compile_regex_bounded(pattern, bound)
    return compile_expr_to_aiger(expr)


def compile_sequential_aiger(pattern: str) -> str:
    circuit = compile_regex_to_sequential(pattern)
    writer = SequentialAigerWriter(circuit)
    return writer.write()


def test_validate_bounded_aiger_output():
    aiger_text = compile_bounded_aiger("(a|b)*&a*", bound=4)
    header = validate_aiger(aiger_text)

    assert header.outputs == 1
    assert header.latches == 0
    assert header.and_gates >= 0


def test_validate_sequential_aiger_output():
    aiger_text = compile_sequential_aiger("(a|b)*&a*")
    header = validate_aiger(aiger_text)

    assert header.outputs == 1
    assert header.latches > 0
    assert header.and_gates >= 0


def test_validate_rejects_empty_text():
    try:
        validate_aiger("")
        assert False, "Expected ValueError for empty AIGER text"
    except ValueError:
        pass


def test_validate_rejects_invalid_header_keyword():
    aiger_text = "\n".join([
        "bad 1 1 0 1 0",
        "2",
        "0",
    ])

    try:
        validate_aiger(aiger_text)
        assert False, "Expected ValueError for invalid header keyword"
    except ValueError:
        pass


def test_validate_rejects_short_body():
    aiger_text = "aag 2 1 0 1 1\n2\n4"

    try:
        validate_aiger(aiger_text)
        assert False, "Expected ValueError for short body"
    except ValueError:
        pass


def test_validate_rejects_literal_above_max():
    aiger_text = "\n".join([
        "aag 1 1 0 1 0",
        "4",
        "0",
    ])

    try:
        validate_aiger(aiger_text)
        assert False, "Expected ValueError for literal above max"
    except ValueError:
        pass


def test_validate_rejects_invalid_and_line():
    aiger_text = "\n".join([
        "aag 3 1 0 1 1",
        "2",
        "6",
        "6 2",
    ])

    try:
        validate_aiger(aiger_text)
        assert False, "Expected ValueError for invalid AND line"
    except ValueError:
        pass


def run_tests():
    test_validate_bounded_aiger_output()
    test_validate_sequential_aiger_output()
    test_validate_rejects_empty_text()
    test_validate_rejects_invalid_header_keyword()
    test_validate_rejects_short_body()
    test_validate_rejects_literal_above_max()
    test_validate_rejects_invalid_and_line()

    print("All AIGER validator tests passed.")


if __name__ == "__main__":
    run_tests()
