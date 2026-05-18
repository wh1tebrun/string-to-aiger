from string_to_aiger.nfa.nfa import NFA


def nfa_alphabet(nfa: NFA) -> set[str]:
    """Return all non-epsilon symbols used by an NFA."""
    symbols: set[str] = set()

    for edges in nfa.transitions.values():
        for symbol, _target in edges:
            if symbol is not None:
                symbols.add(symbol)

    return symbols
