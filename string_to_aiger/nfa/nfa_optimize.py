from string_to_aiger.nfa.nfa import NFA
from string_to_aiger.nfa.nfa_prune import prune_unreachable_states


def deduplicate_transitions(nfa: NFA) -> NFA:
    """Return a copy of the NFA with duplicate transitions removed."""
    result = NFA(
        start=nfa.start,
        accepts=set(nfa.accepts),
    )

    for source in sorted(nfa.transitions.keys()):
        seen: set[tuple[str | None, int]] = set()

        for symbol, target in nfa.transitions[source]:
            transition = (symbol, target)

            if transition in seen:
                continue

            seen.add(transition)
            result.add_transition(source, symbol, target)

    return result


def optimize_nfa(nfa: NFA) -> NFA:
    """Apply basic NFA cleanup passes.

    This is not full automata minimization. It currently performs:
    - unreachable-state pruning
    - duplicate-transition elimination
    """
    pruned = prune_unreachable_states(nfa)
    return deduplicate_transitions(pruned)
