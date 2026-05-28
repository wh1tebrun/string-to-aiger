from string_to_aiger.nfa.nfa import NFA, State
from string_to_aiger.nfa.nfa_alphabet import nfa_alphabet
from string_to_aiger.logic.circuit import InputVar, And, Expr, and_all, or_all
from .sequential_circuit import SequentialCircuit


def latch_name(state: State) -> str:
    return f"state_{state}"


def symbol_input_name(symbol: str) -> str:
    return f"is_{symbol}"


def epsilon_reachability(nfa: NFA) -> dict[State, set[State]]:
    """Compute epsilon-reachable states for every state."""
    result: dict[State, set[State]] = {}

    for start in nfa.states():
        reachable = {start}
        stack = [start]

        while stack:
            state = stack.pop()

            for symbol, target in nfa.transitions.get(state, []):
                if symbol is None and target not in reachable:
                    reachable.add(target)
                    stack.append(target)

        result[start] = reachable

    return result


def compile_nfa_to_sequential(nfa: NFA) -> SequentialCircuit:
    """Compile an NFA into a latch-based sequential circuit.

    Each NFA state is represented by one latch. A latch is true exactly when
    the corresponding NFA state is currently active.

    Input protocol:
    - In each normal step, exactly one symbol input such as is_a / is_b is true.
    - In the final step, end is true.
    - The accept output is true iff end is true and an accepting state is active.
    """
    circuit = SequentialCircuit()
    states = sorted(nfa.states())
    eps = epsilon_reachability(nfa)

    circuit.add_input("end")

    for symbol in sorted(nfa_alphabet(nfa)):
        circuit.add_input(symbol_input_name(symbol))

    initial_states = eps[nfa.start]

    next_exprs: dict[State, Expr] = {}

    for target_state in states:
        # incoming_after_symbol[intermediate] collects all symbolic conditions
        # under which `intermediate` can be reached after consuming exactly one
        # input symbol from the currently active NFA states.
        incoming_after_symbol: dict[State, list[Expr]] = {
            state: []
            for state in states
        }

        for source in states:
            for symbol, direct_target in nfa.transitions.get(source, []):
                if symbol is None:
                    continue

                # A symbol transition can be taken iff the source state is
                # active and the corresponding symbol input is true.
                condition = and_all([
                    InputVar(latch_name(source)),
                    InputVar(symbol_input_name(symbol)),
                ])

                incoming_after_symbol[direct_target].append(condition)

        alternatives: list[Expr] = []

        for source_after_symbol in states:
            # After taking one symbol transition, epsilon transitions may move
            # the NFA further without consuming additional input. Therefore,
            # target_state is reachable if it is in the epsilon closure of any
            # intermediate state reached by a symbol transition.
            if target_state in eps[source_after_symbol]:
                alternatives.append(or_all(incoming_after_symbol[source_after_symbol]))

        next_exprs[target_state] = or_all(alternatives)

    for state in states:
        # Initial latch values represent the epsilon closure of the NFA start
        # state. This is important for expressions such as a*, where the empty
        # word may already be accepted before reading any symbol.
        circuit.add_latch(
            latch_name(state),
            next_exprs[state],
            init=state in initial_states,
        )

    accepting_states: list[Expr] = [
        InputVar(latch_name(state))
        for state in states
        if state in nfa.accepts
    ]

    # Accept only on the final step, and only if some accepting NFA state is
    # active at that point.
    accept_expr = And(
        InputVar("end"),
        or_all(accepting_states),
    )

    circuit.add_output("accept", accept_expr)

    return circuit
