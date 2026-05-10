from regex_parser import parse_regex
from nfa_builder import build_nfa
from bounded_nfa_encoding import compile_nfa_bounded
from aiger import compile_expr_to_aiger


def compile_regex_to_aiger(pattern: str, bound: int) -> str:
    """Compile a regular expression into ASCII AIGER using bounded encoding."""
    ast = parse_regex(pattern)
    nfa = build_nfa(ast)
    expr = compile_nfa_bounded(nfa, bound)
    return compile_expr_to_aiger(expr)