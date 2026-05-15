from .regex_ast import Intersect, Regex
from .regex_parser import parse_regex
from string_to_aiger.nfa.nfa_builder import build_nfa
from string_to_aiger.bounded.bounded_nfa_encoding import compile_nfa_bounded
from string_to_aiger.logic.circuit import And, Expr


def compile_regex_ast_bounded(expr: Regex, bound: int) -> Expr:
    """Compile a regex AST into a bounded logical expression.

    Intersections are compiled structurally by compiling both sides
    and combining their bounded encodings with AND.
    """
    if isinstance(expr, Intersect):
        left_expr = compile_regex_ast_bounded(expr.left, bound)
        right_expr = compile_regex_ast_bounded(expr.right, bound)
        return And(left_expr, right_expr)

    nfa = build_nfa(expr)
    return compile_nfa_bounded(nfa, bound)


def compile_regex_bounded(pattern: str, bound: int) -> Expr:
    """Parse and compile a regex pattern into a bounded logical expression."""
    ast = parse_regex(pattern)
    return compile_regex_ast_bounded(ast, bound)
