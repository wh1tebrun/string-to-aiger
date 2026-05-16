from string_to_aiger.logic.circuit import Expr
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa
from string_to_aiger.bounded.bounded_nfa_encoding import compile_nfa_bounded


def compile_regex_bounded_product(pattern: str, bound: int) -> Expr:
    """Compile a regex using explicit product automata for intersection."""
    ast = parse_regex(pattern)
    nfa = build_product_aware_nfa(ast)

    return compile_nfa_bounded(nfa, bound)
