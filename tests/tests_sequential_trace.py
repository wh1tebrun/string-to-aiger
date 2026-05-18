import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.regex.regex_parser import parse_regex  # noqa: E402
from string_to_aiger.nfa.nfa_builder import build_nfa  # noqa: E402
from string_to_aiger.sequential.nfa_to_sequential import compile_nfa_to_sequential  # noqa: E402
from string_to_aiger.sequential.sequential_simulator import simulate  # noqa: E402
from string_to_aiger.sequential.sequential_trace import validate_trace  # noqa: E402


def build_circuit(pattern: str):
    ast = parse_regex(pattern)
    nfa = build_nfa(ast)
    return compile_nfa_to_sequential(nfa)


def test_validate_accepts_valid_nonempty_trace():
    circuit = build_circuit("(a|b)*")

    trace = [
        {"is_a": True, "end": False},
        {"is_b": True, "end": False},
        {"end": True},
    ]

    validate_trace(circuit, trace)


def test_validate_accepts_valid_empty_word_trace():
    circuit = build_circuit("a*")

    trace = [
        {"end": True},
    ]

    validate_trace(circuit, trace)


def test_simulate_valid_trace_still_works():
    circuit = build_circuit("a*")

    trace = [
        {"is_a": True, "end": False},
        {"is_a": True, "end": False},
        {"end": True},
    ]

    outputs = simulate(circuit, trace)

    assert outputs[-1]["accept"] is True


def test_unknown_symbol_input_is_allowed_and_rejected_naturally():
    circuit = build_circuit("(a|b)*")

    trace = [
        {"is_a": True, "end": False},
        {"is_c": True, "end": False},
        {"end": True},
    ]

    outputs = simulate(circuit, trace)

    assert outputs[-1]["accept"] is False


def test_validate_rejects_empty_trace():
    circuit = build_circuit("a*")

    try:
        validate_trace(circuit, [])
        assert False, "Expected ValueError for empty trace"
    except ValueError:
        pass


def test_validate_rejects_missing_final_end():
    circuit = build_circuit("a*")

    trace = [
        {"is_a": True, "end": False},
    ]

    try:
        validate_trace(circuit, trace)
        assert False, "Expected ValueError for missing final end"
    except ValueError:
        pass


def test_validate_rejects_early_end():
    circuit = build_circuit("a*")

    trace = [
        {"end": True},
        {"is_a": True, "end": False},
        {"end": True},
    ]

    try:
        validate_trace(circuit, trace)
        assert False, "Expected ValueError for early end"
    except ValueError:
        pass


def test_validate_rejects_multiple_active_symbols():
    circuit = build_circuit("(a|b)*")

    trace = [
        {"is_a": True, "is_b": True, "end": False},
        {"end": True},
    ]

    try:
        validate_trace(circuit, trace)
        assert False, "Expected ValueError for multiple active symbols"
    except ValueError:
        pass


def test_validate_rejects_no_active_symbol_in_normal_step():
    circuit = build_circuit("(a|b)*")

    trace = [
        {"end": False},
        {"end": True},
    ]

    try:
        validate_trace(circuit, trace)
        assert False, "Expected ValueError for missing symbol input"
    except ValueError:
        pass


def test_validate_rejects_symbol_input_on_final_step():
    circuit = build_circuit("a*")

    trace = [
        {"is_a": True, "end": True},
    ]

    try:
        validate_trace(circuit, trace)
        assert False, "Expected ValueError for symbol input on final step"
    except ValueError:
        pass


def test_validate_rejects_unknown_non_symbol_input():
    circuit = build_circuit("a*")

    trace = [
        {"foo": True, "end": False},
        {"end": True},
    ]

    try:
        validate_trace(circuit, trace)
        assert False, "Expected ValueError for unknown non-symbol input"
    except ValueError:
        pass


def test_validate_rejects_non_bool_value():
    circuit = build_circuit("a*")

    trace = [
        {"is_a": 1, "end": False},
        {"end": True},
    ]

    try:
        validate_trace(circuit, trace)
        assert False, "Expected ValueError for non-bool trace value"
    except ValueError:
        pass


def run_tests():
    test_validate_accepts_valid_nonempty_trace()
    test_validate_accepts_valid_empty_word_trace()
    test_simulate_valid_trace_still_works()
    test_unknown_symbol_input_is_allowed_and_rejected_naturally()
    test_validate_rejects_empty_trace()
    test_validate_rejects_missing_final_end()
    test_validate_rejects_early_end()
    test_validate_rejects_multiple_active_symbols()
    test_validate_rejects_no_active_symbol_in_normal_step()
    test_validate_rejects_symbol_input_on_final_step()
    test_validate_rejects_unknown_non_symbol_input()
    test_validate_rejects_non_bool_value()

    print("All sequential trace tests passed.")


if __name__ == "__main__":
    run_tests()
