from string_to_aiger.regex.regex_ast import (
    Empty,
    Char,
    Concat,
    UnionExpr,
    Intersect,
    Star,
    Regex,
)
from string_to_aiger.nfa.nfa import NFA
from string_to_aiger.nfa.nfa_builder import build_nfa
from string_to_aiger.nfa.nfa_operations import concat_nfa, union_nfa, star_nfa
from string_to_aiger.nfa.nfa_product import intersect_nfa


def build_product_aware_nfa(expr: Regex) -> NFA:
    """Build an NFA from a regex AST, using explicit product automata for &.

    Unlike the basic Thompson-style NFA builder, this function supports
    Intersect nodes by recursively constructing both sides and then building
    their product automaton.
    """
    if isinstance(expr, Empty):
        return build_nfa(expr)

    if isinstance(expr, Char):
        return build_nfa(expr)

    if isinstance(expr, Concat):
        left = build_product_aware_nfa(expr.left)
        right = build_product_aware_nfa(expr.right)
        return concat_nfa(left, right)

    if isinstance(expr, UnionExpr):
        left = build_product_aware_nfa(expr.left)
        right = build_product_aware_nfa(expr.right)
        return union_nfa(left, right)

    if isinstance(expr, Intersect):
        left = build_product_aware_nfa(expr.left)
        right = build_product_aware_nfa(expr.right)
        return intersect_nfa(left, right)

    if isinstance(expr, Star):
        inner = build_product_aware_nfa(expr.expr)
        return star_nfa(inner)

    raise TypeError(f"Unknown regex AST node: {type(expr)}")
