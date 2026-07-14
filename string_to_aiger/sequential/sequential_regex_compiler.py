from string_to_aiger.regex.regex_ast import (
    Intersect,
    Regex,
    contains_intersection,
)
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa
from string_to_aiger.nfa.nfa_builder import build_nfa
from .nfa_to_sequential import compile_nfa_to_sequential
from .sequential_circuit import SequentialCircuit
from .sequential_intersection import merge_for_intersection
from .sequential_protocol import add_input_protocol_guard


def compile_regex_ast_to_sequential_raw(expr: Regex) -> SequentialCircuit:
    """Compile a regex AST without adding the final input-protocol latch.

    This raw helper is used recursively for structural intersections so that
    the final composed circuit receives exactly one shared protocol latch.
    """
    if isinstance(expr, Intersect):
        left_circuit = compile_regex_ast_to_sequential_raw(expr.left)
        right_circuit = compile_regex_ast_to_sequential_raw(expr.right)
        return merge_for_intersection(left_circuit, right_circuit)

    if contains_intersection(expr):
        nfa = build_product_aware_nfa(expr)
    else:
        nfa = build_nfa(expr)

    return compile_nfa_to_sequential(nfa)


def compile_regex_ast_to_sequential(expr: Regex) -> SequentialCircuit:
    """Compile a regex AST and enforce the sequential input protocol."""
    raw_circuit = compile_regex_ast_to_sequential_raw(expr)
    return add_input_protocol_guard(raw_circuit)


def compile_regex_to_sequential(pattern: str) -> SequentialCircuit:
    """Parse a regex pattern and compile it into a guarded sequential circuit."""
    ast = parse_regex(pattern)
    return compile_regex_ast_to_sequential(ast)
