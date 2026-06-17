from .regex_bounded_compiler import compile_regex_bounded
from string_to_aiger.aiger.aiger import compile_expr_to_aiger


def compile_regex_to_aiger(pattern: str, bound: int) -> str:
    """Compile a regular expression into ASCII AIGER using bounded encoding.

    This entry point uses the intersection-aware bounded compiler.

    For ordinary regexes, the compiler builds an NFA and then creates the
    bounded logical encoding.

    For intersections such as A & B, the bounded compiler handles the
    Intersect AST node structurally by compiling both sides and combining
    their encodings with AND.
    """
    expr = compile_regex_bounded(pattern, bound)
    return compile_expr_to_aiger(expr)
