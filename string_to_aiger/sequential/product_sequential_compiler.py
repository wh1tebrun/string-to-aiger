from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa
from string_to_aiger.sequential.nfa_to_sequential import compile_nfa_to_sequential
from string_to_aiger.sequential.sequential_circuit import SequentialCircuit
from string_to_aiger.sequential.sequential_protocol import add_input_protocol_guard


def compile_regex_to_sequential_product(pattern: str) -> SequentialCircuit:
    """Compile a regex to a guarded sequential product-automaton circuit."""
    ast = parse_regex(pattern)
    nfa = build_product_aware_nfa(ast)
    raw_circuit = compile_nfa_to_sequential(nfa)

    return add_input_protocol_guard(raw_circuit)
