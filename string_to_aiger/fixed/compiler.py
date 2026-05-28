from .model import OrMatcher, ExactStringMatcher
from string_to_aiger.logic.circuit import LengthIs, CharAtIs, and_all, or_all, Expr


def compile_exact_string(matcher: ExactStringMatcher) -> Expr:
    """Compile one concrete string into logical constraints.

    A concrete word is encoded as a conjunction of:

    - one length constraint
    - one character-position constraint for every character

    For example, the word "abba" becomes:

        len == 4
        x[0] == 'a'
        x[1] == 'b'
        x[2] == 'b'
        x[3] == 'a'

    This turns fixed-string matching into a boolean expression that can later be
    translated into a netlist and then into ASCII AIGER.
    """
    constraints: list[Expr] = [LengthIs(len(matcher.word))]

    for i, ch in enumerate(matcher.word):
        constraints.append(CharAtIs(i, ch))

    return and_all(constraints)


def compile_or(matcher: OrMatcher) -> Expr:
    """Compile a disjunction of exact-string matchers.

    Each concrete string is compiled independently, and the final expression is
    the disjunction of all alternatives.
    """
    compiled_options = [
        compile_exact_string(option)
        for option in matcher.options
    ]

    return or_all(compiled_options)
