from string_to_aiger.regex.regex_ast import (
    Empty,
    Char,
    Concat,
    UnionExpr,
    Intersect,
    Star,
    Regex,
    contains_intersection,
)
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa
from string_to_aiger.nfa.nfa_builder import build_nfa
from .nfa_to_sequential import compile_nfa_to_sequential
from .sequential_circuit import SequentialCircuit
from .sequential_intersection import merge_for_intersection


def compile_regex_ast_to_sequential(expr: Regex) -> SequentialCircuit:
    """Compile a regex AST into a sequential circuit.

    Top-level intersections are compiled structurally by running the two
    sides in parallel and combining their accept outputs.

    If an Intersect node occurs nested inside another regex construct, for
    example inside concatenation or Kleene star, the expression is compiled
    through the product-aware NFA builder. This avoids passing Intersect nodes
    to the basic Thompson-style NFA builder.
    """
    if isinstance(expr, Intersect):
        left_circuit = compile_regex_ast_to_sequential(expr.left)
        right_circuit = compile_regex_ast_to_sequential(expr.right)
        return merge_for_intersection(left_circuit, right_circuit)

    if contains_intersection(expr):
        nfa = build_product_aware_nfa(expr)
    else:
        nfa = build_nfa(expr)

    return compile_nfa_to_sequential(nfa)


def compile_regex_to_sequential(pattern: str) -> SequentialCircuit:
    """Parse a regex pattern and compile it into a sequential circuit."""
    ast = parse_regex(pattern)
    return compile_regex_ast_to_sequential(ast)
