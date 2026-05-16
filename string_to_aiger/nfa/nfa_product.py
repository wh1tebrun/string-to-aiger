from collections import deque

from .nfa import NFA, State, Symbol


ProductState = tuple[State, State]


def intersect_nfa(left: NFA, right: NFA) -> NFA:
    """Build an explicit product NFA for language intersection.

    The constructed automaton accepts exactly the words that are accepted by
    both input NFAs.

    Epsilon transitions are handled asynchronously:
    - an epsilon step on the left NFA becomes an epsilon step in the product
    - an epsilon step on the right NFA becomes an epsilon step in the product
    - matching symbol transitions are synchronized
    """
    state_ids: dict[ProductState, State] = {}
    queue: deque[ProductState] = deque()

    def get_state_id(product_state: ProductState) -> State:
        if product_state not in state_ids:
            state_ids[product_state] = len(state_ids)
            queue.append(product_state)

        return state_ids[product_state]

    start_pair = (left.start, right.start)
    start_id = get_state_id(start_pair)

    product = NFA(
        start=start_id,
        accepts=set(),
    )

    processed: set[ProductState] = set()

    while queue:
        current_pair = queue.popleft()

        if current_pair in processed:
            continue

        processed.add(current_pair)

        left_state, right_state = current_pair
        current_id = get_state_id(current_pair)

        if left_state in left.accepts and right_state in right.accepts:
            product.accepts.add(current_id)

        left_edges = left.transitions.get(left_state, [])
        right_edges = right.transitions.get(right_state, [])

        add_left_epsilon_steps(
            product=product,
            get_state_id=get_state_id,
            current_id=current_id,
            left_edges=left_edges,
            right_state=right_state,
        )

        add_right_epsilon_steps(
            product=product,
            get_state_id=get_state_id,
            current_id=current_id,
            left_state=left_state,
            right_edges=right_edges,
        )

        add_synchronized_symbol_steps(
            product=product,
            get_state_id=get_state_id,
            current_id=current_id,
            left_edges=left_edges,
            right_edges=right_edges,
        )

    return product


def add_left_epsilon_steps(
    product: NFA,
    get_state_id,
    current_id: State,
    left_edges: list[tuple[Symbol, State]],
    right_state: State,
) -> None:
    for symbol, left_target in left_edges:
        if symbol is not None:
            continue

        target_pair = (left_target, right_state)
        target_id = get_state_id(target_pair)

        product.add_transition(current_id, None, target_id)


def add_right_epsilon_steps(
    product: NFA,
    get_state_id,
    current_id: State,
    left_state: State,
    right_edges: list[tuple[Symbol, State]],
) -> None:
    for symbol, right_target in right_edges:
        if symbol is not None:
            continue

        target_pair = (left_state, right_target)
        target_id = get_state_id(target_pair)

        product.add_transition(current_id, None, target_id)


def add_synchronized_symbol_steps(
    product: NFA,
    get_state_id,
    current_id: State,
    left_edges: list[tuple[Symbol, State]],
    right_edges: list[tuple[Symbol, State]],
) -> None:
    for left_symbol, left_target in left_edges:
        if left_symbol is None:
            continue

        for right_symbol, right_target in right_edges:
            if right_symbol is None:
                continue

            if left_symbol != right_symbol:
                continue

            target_pair = (left_target, right_target)
            target_id = get_state_id(target_pair)

            product.add_transition(current_id, left_symbol, target_id)
