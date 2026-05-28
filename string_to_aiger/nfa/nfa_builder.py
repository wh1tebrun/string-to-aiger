from dataclasses import dataclass

from string_to_aiger.regex.regex_ast import Empty, Char, Concat, UnionExpr, Star, Regex
from .nfa import NFA, State


@dataclass
class NFAFragment:
    start: State
    accept: State


class NFABuilder:
    """Build NFAs from regex ASTs using Thompson-style construction.

    Each regex node is compiled into an NFA fragment with one start state and
    one accepting state. Larger expressions are built by connecting these
    fragments with epsilon transitions.

    This builder intentionally constructs an NFA directly from the AST. Cleanup
    passes such as duplicate-transition elimination or unreachable-state pruning
    can be applied separately with the NFA optimization utilities.
    """

    def __init__(self):
        self.next_state: State = 0
        self.nfa = NFA(start=0, accepts=set())

    def new_state(self) -> State:
        state = self.next_state
        self.next_state += 1
        return state

    def build(self, expr: Regex) -> NFA:
        fragment = self.build_fragment(expr)
        self.nfa.start = fragment.start
        self.nfa.accepts = {fragment.accept}
        return self.nfa

    def build_fragment(self, expr: Regex) -> NFAFragment:
        if isinstance(expr, Empty):
            return self.build_empty()

        if isinstance(expr, Char):
            return self.build_char(expr)

        if isinstance(expr, Concat):
            return self.build_concat(expr)

        if isinstance(expr, UnionExpr):
            return self.build_union(expr)

        if isinstance(expr, Star):
            return self.build_star(expr)

        raise TypeError(f"Unknown regex AST node: {type(expr)}")

    def build_empty(self) -> NFAFragment:
        start = self.new_state()
        accept = self.new_state()

        self.nfa.add_transition(start, None, accept)

        return NFAFragment(start, accept)

    def build_char(self, expr: Char) -> NFAFragment:
        start = self.new_state()
        accept = self.new_state()

        self.nfa.add_transition(start, expr.value, accept)

        return NFAFragment(start, accept)

    def build_concat(self, expr: Concat) -> NFAFragment:
        left = self.build_fragment(expr.left)
        right = self.build_fragment(expr.right)

        self.nfa.add_transition(left.accept, None, right.start)

        return NFAFragment(left.start, right.accept)

    def build_union(self, expr: UnionExpr) -> NFAFragment:
        start = self.new_state()
        accept = self.new_state()

        left = self.build_fragment(expr.left)
        right = self.build_fragment(expr.right)

        self.nfa.add_transition(start, None, left.start)
        self.nfa.add_transition(start, None, right.start)

        self.nfa.add_transition(left.accept, None, accept)
        self.nfa.add_transition(right.accept, None, accept)

        return NFAFragment(start, accept)

    def build_star(self, expr: Star) -> NFAFragment:
        start = self.new_state()
        accept = self.new_state()

        inner = self.build_fragment(expr.expr)

        self.nfa.add_transition(start, None, accept)
        self.nfa.add_transition(start, None, inner.start)

        self.nfa.add_transition(inner.accept, None, inner.start)
        self.nfa.add_transition(inner.accept, None, accept)

        return NFAFragment(start, accept)


def build_nfa(expr: Regex) -> NFA:
    """Build an NFA from a regex AST.

    The construction is Thompson-style and may produce epsilon transitions,
    duplicate transitions, or unreachable states. This is acceptable for the
    core construction; optional cleanup can be performed separately with
    optimize_nfa().
    """
    builder = NFABuilder()
    return builder.build(expr)
