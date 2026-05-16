from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa
from string_to_aiger.sequential.nfa_to_sequential import compile_nfa_to_sequential
from string_to_aiger.sequential.sequential_circuit import SequentialCircuit


def compile_regex_to_sequential_product(pattern: str) -> SequentialCircuit:
    """Compile a regex to a sequential circuit using product automata for &."""
    ast = parse_regex(pattern)
    nfa = build_product_aware_nfa(ast)

    return compile_nfa_to_sequential(nfa)
