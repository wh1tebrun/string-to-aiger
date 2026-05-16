from .nfa import NFA, State


def renumber_nfa(nfa: NFA, offset: int) -> tuple[NFA, int]:
    """Return a copy of the NFA whose states are renamed from offset upward."""
    states = sorted(nfa.states())
    mapping: dict[State, State] = {
        state: offset + index
        for index, state in enumerate(states)
    }

    renamed = NFA(
        start=mapping[nfa.start],
        accepts={
            mapping[state]
            for state in nfa.accepts
        },
    )

    for source, edges in nfa.transitions.items():
        for symbol, target in edges:
            renamed.add_transition(
                mapping[source],
                symbol,
                mapping[target],
            )

    next_offset = offset + len(states)
    return renamed, next_offset


def copy_transitions(source: NFA, target: NFA) -> None:
    """Copy all transitions from source into target."""
    for state, edges in source.transitions.items():
        for symbol, next_state in edges:
            target.add_transition(state, symbol, next_state)


def concat_nfa(left: NFA, right: NFA) -> NFA:
    """Construct an NFA for concatenation of two NFAs."""
    left_copy, next_offset = renumber_nfa(left, 0)
    right_copy, _next_offset = renumber_nfa(right, next_offset)

    result = NFA(
        start=left_copy.start,
        accepts=set(right_copy.accepts),
    )

    copy_transitions(left_copy, result)
    copy_transitions(right_copy, result)

    for accept in left_copy.accepts:
        result.add_transition(accept, None, right_copy.start)

    return result


def union_nfa(left: NFA, right: NFA) -> NFA:
    """Construct an NFA for union of two NFAs."""
    start = 0
    accept = 1

    left_copy, next_offset = renumber_nfa(left, 2)
    right_copy, _next_offset = renumber_nfa(right, next_offset)

    result = NFA(
        start=start,
        accepts={accept},
    )

    copy_transitions(left_copy, result)
    copy_transitions(right_copy, result)

    result.add_transition(start, None, left_copy.start)
    result.add_transition(start, None, right_copy.start)

    for left_accept in left_copy.accepts:
        result.add_transition(left_accept, None, accept)

    for right_accept in right_copy.accepts:
        result.add_transition(right_accept, None, accept)

    return result


def star_nfa(inner: NFA) -> NFA:
    """Construct an NFA for Kleene star of an NFA."""
    start = 0
    accept = 1

    inner_copy, _next_offset = renumber_nfa(inner, 2)

    result = NFA(
        start=start,
        accepts={accept},
    )

    copy_transitions(inner_copy, result)

    result.add_transition(start, None, accept)
    result.add_transition(start, None, inner_copy.start)

    for inner_accept in inner_copy.accepts:
        result.add_transition(inner_accept, None, inner_copy.start)
        result.add_transition(inner_accept, None, accept)

    return result
