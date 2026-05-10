from nfa import NFA, State


def epsilon_closure(nfa: NFA, states: set[State]) -> set[State]:
    """Return all states reachable through epsilon transitions."""
    closure = set(states)
    stack = list(states)

    while stack:
        state = stack.pop()

        for symbol, target in nfa.transitions.get(state, []):
            if symbol is None and target not in closure:
                closure.add(target)
                stack.append(target)

    return closure


def step(nfa: NFA, states: set[State], symbol: str) -> set[State]:
    """Consume one symbol from all current states."""
    result: set[State] = set()

    for state in states:
        for edge_symbol, target in nfa.transitions.get(state, []):
            if edge_symbol == symbol:
                result.add(target)

    return epsilon_closure(nfa, result)


def accepts(nfa: NFA, word: str) -> bool:
    """Return True iff the NFA accepts the given word."""
    current_states = epsilon_closure(nfa, {nfa.start})

    for symbol in word:
        current_states = step(nfa, current_states, symbol)

    return bool(current_states & nfa.accepts)