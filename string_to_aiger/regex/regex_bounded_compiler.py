from .regex_ast import (
    Empty,
    Char,
    Concat,
    UnionExpr,
    Intersect,
    Star,
    Regex,
)
from .regex_parser import parse_regex
from .regex_to_product_nfa import build_product_aware_nfa
from string_to_aiger.nfa.nfa_builder import build_nfa
from string_to_aiger.bounded.bounded_nfa_encoding import compile_nfa_bounded
from string_to_aiger.logic.circuit import And, Expr


def contains_intersection(expr: Regex) -> bool:
    """Return whether a regex AST contains an Intersect node anywhere.

    The basic Thompson-style NFA builder does not support Intersect nodes.
    Therefore, if an intersection occurs inside another construct such as
    concatenation, union, or star, we need to use the product-aware NFA builder.
    """
    if isinstance(expr, Intersect):
        return True

    if isinstance(expr, Concat):
        return contains_intersection(expr.left) or contains_intersection(expr.right)

    if isinstance(expr, UnionExpr):
        return contains_intersection(expr.left) or contains_intersection(expr.right)

    if isinstance(expr, Star):
        return contains_intersection(expr.expr)

    if isinstance(expr, (Empty, Char)):
        return False

    raise TypeError(f"Unknown regex AST node: {type(expr)}")


def compile_regex_ast_bounded(expr: Regex, bound: int) -> Expr:
    """Compile a regex AST into a bounded logical expression.

    Top-level intersections are compiled structurally by compiling both sides
    and combining their bounded encodings with AND.

    If an Intersect node occurs nested inside another regex construct, for
    example inside concatenation or Kleene star, the expression is compiled
    through the product-aware NFA builder. This avoids passing Intersect nodes
    to the basic Thompson-style NFA builder, which does not support them.
    """
    if isinstance(expr, Intersect):
        left_expr = compile_regex_ast_bounded(expr.left, bound)
        right_expr = compile_regex_ast_bounded(expr.right, bound)
        return And(left_expr, right_expr)

    if contains_intersection(expr):
        nfa = build_product_aware_nfa(expr)
    else:
        nfa = build_nfa(expr)

    return compile_nfa_bounded(nfa, bound)


def compile_regex_bounded(pattern: str, bound: int) -> Expr:
    """Parse and compile a regex pattern into a bounded logical expression."""
    ast = parse_regex(pattern)
    return compile_regex_ast_bounded(ast, bound)
