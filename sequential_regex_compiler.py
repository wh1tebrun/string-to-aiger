from regex_ast import Intersect, Regex
from regex_parser import parse_regex
from nfa_builder import build_nfa
from nfa_to_sequential import compile_nfa_to_sequential
from sequential_circuit import SequentialCircuit
from sequential_intersection import merge_for_intersection


def compile_regex_ast_to_sequential(expr: Regex) -> SequentialCircuit:
    """Compile a regex AST into a sequential circuit.

    Intersections are compiled by running the two sides in parallel
    and combining their accept outputs.
    """
    if isinstance(expr, Intersect):
        left_circuit = compile_regex_ast_to_sequential(expr.left)
        right_circuit = compile_regex_ast_to_sequential(expr.right)
        return merge_for_intersection(left_circuit, right_circuit)

    nfa = build_nfa(expr)
    return compile_nfa_to_sequential(nfa)


def compile_regex_to_sequential(pattern: str) -> SequentialCircuit:
    """Parse a regex pattern and compile it into a sequential circuit."""
    ast = parse_regex(pattern)
    return compile_regex_ast_to_sequential(ast)
