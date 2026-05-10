from nfa import NFA, State
from circuit import BoolConst, LengthIs, CharAtIs, And, Or, Expr, or_all


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


def epsilon_close_exprs(
    states: list[State],
    exprs: dict[State, Expr],
    epsilon_reachable: dict[State, set[State]],
) -> dict[State, Expr]:
    """Lift epsilon closure to symbolic expressions."""
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
    """
    if bound < 0:
        raise ValueError("Bound must be non-negative")

    states = sorted(nfa.states())
    epsilon_reachable = epsilon_reachability(nfa)

    current: dict[State, Expr] = {
        state: BoolConst(state == nfa.start)
        for state in states
    }

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

        moved: dict[State, Expr] = {
            state: BoolConst(False)
            for state in states
        }

        for source in states:
            for symbol, target in nfa.transitions.get(source, []):
                if symbol is None:
                    continue

                transition_condition = and_two(
                    current[source],
                    CharAtIs(position, symbol),
                )

                moved[target] = or_two(moved[target], transition_condition)

        current = epsilon_close_exprs(states, moved, epsilon_reachable)

    return or_all(accept_conditions)