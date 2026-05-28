from string_to_aiger.nfa.nfa import NFA, State
from string_to_aiger.logic.circuit import (
    BoolConst,
    LengthIs,
    CharAtIs,
    And,
    Or,
    Expr,
    or_all,
)


def is_false(expr: Expr) -> bool:
    return isinstance(expr, BoolConst) and expr.value is False


def is_true(expr: Expr) -> bool:
    return isinstance(expr, BoolConst) and expr.value is True


def or_two(left: Expr, right: Expr) -> Expr:
    if is_false(left):
        return right
    if is_false(right):
        return left
    if is_true(left) or is_true(right):
        return BoolConst(True)
    return Or(left, right)


def and_two(left: Expr, right: Expr) -> Expr:
    if is_false(left) or is_false(right):
        return BoolConst(False)
    if is_true(left):
        return right
    if is_true(right):
        return left
    return And(left, right)


def epsilon_reachability(nfa: NFA) -> dict[State, set[State]]:
    """Compute epsilon-reachable states for every state.

    The result maps each state to all states reachable from it by taking only
    epsilon transitions. This is precomputed once and then reused during the
    bounded unrolling.
    """
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


def epsilon_close_exprs(
    states: list[State],
    exprs: dict[State, Expr],
    epsilon_reachable: dict[State, set[State]],
) -> dict[State, Expr]:
    """Lift epsilon closure to symbolic reachability expressions.

    If a target state is epsilon-reachable from several source states, then the
    symbolic condition for reaching the target is the disjunction of the
    conditions for reaching those sources.
    """
    closed: dict[State, Expr] = {}

    for target in states:
        alternatives: list[Expr] = []

        for source in states:
            if target in epsilon_reachable[source]:
                alternatives.append(exprs[source])

        closed[target] = or_all(alternatives)

    return closed


def compile_nfa_bounded(nfa: NFA, bound: int) -> Expr:
    """Compile an NFA into a bounded combinational logical expression.

    The resulting expression accepts words of length at most `bound`.

    Strategy:
    - compute symbolic reachability expressions for every NFA state
    - start from the epsilon-closure of the initial state
    - for each input position, symbolically advance one transition step
    - after each step, apply epsilon closure again
    - at every length 0..bound, record whether an accepting state is reachable

    This unrolls potentially looping NFA behavior into a finite boolean formula.
    For unbounded languages such as `a*`, the encoding is intentionally complete
    only up to the selected bound.
    """
    if bound < 0:
        raise ValueError("Bound must be non-negative")

    states = sorted(nfa.states())
    epsilon_reachable = epsilon_reachability(nfa)

    current: dict[State, Expr] = {
        state: BoolConst(state == nfa.start)
        for state in states
    }

    # The empty word may already reach additional states through epsilon edges.
    current = epsilon_close_exprs(states, current, epsilon_reachable)

    accept_conditions: list[Expr] = []

    for position in range(bound + 1):
        accepting_now = or_all([
            current[state]
            for state in states
            if state in nfa.accepts
        ])

        accept_conditions.append(
            and_two(LengthIs(position), accepting_now)
        )

        if position == bound:
            break

        # moved[target] describes the condition under which `target` is reached
        # after consuming the symbol at the current input position.
        moved: dict[State, Expr] = {
            state: BoolConst(False)
            for state in states
        }

        for source in states:
            for symbol, target in nfa.transitions.get(source, []):
                if symbol is None:
                    continue

                # A symbol transition succeeds iff the source state is currently
                # reachable and the candidate word has the required character at
                # this position.
                transition_condition = and_two(
                    current[source],
                    CharAtIs(position, symbol),
                )

                # Several paths may reach the same target state.
                moved[target] = or_two(moved[target], transition_condition)

        current = epsilon_close_exprs(states, moved, epsilon_reachable)

    return or_all(accept_conditions)
