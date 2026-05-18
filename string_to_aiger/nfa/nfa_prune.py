from string_to_aiger.nfa.nfa import NFA, State


def reachable_states(nfa: NFA) -> set[State]:
    """Return all states reachable from the NFA start state."""
    reachable = {nfa.start}
    stack = [nfa.start]

    while stack:
        state = stack.pop()

        for _symbol, target in nfa.transitions.get(state, []):
            if target not in reachable:
                reachable.add(target)
                stack.append(target)

    return reachable


def prune_unreachable_states(nfa: NFA) -> NFA:
    """Return a copy of the NFA without states unreachable from the start state."""
    reachable = reachable_states(nfa)

    pruned = NFA(
        start=nfa.start,
        accepts={
            state
            for state in nfa.accepts
            if state in reachable
        },
    )

    for source, edges in nfa.transitions.items():
        if source not in reachable:
            continue

        for symbol, target in edges:
            if target not in reachable:
                continue

            pruned.add_transition(source, symbol, target)

    return pruned
