from model import ExactStringMatcher, OrMatcher
from circuit import Expr, LengthIs, CharAtIs, and_all, or_all


def compile_exact_string(matcher: ExactStringMatcher) -> Expr:
    """Compile one concrete string into logical constraints."""
    constraints: list[Expr] = [LengthIs(len(matcher.word))]

    for i, ch in enumerate(matcher.word):
        constraints.append(CharAtIs(i, ch))

    return and_all(constraints)


def compile_or(matcher: OrMatcher) -> Expr:
    """Compile a disjunction of matchers into one expression tree."""
    compiled_options = [compile_exact_string(option) for option in matcher.options]
    return or_all(compiled_options)

# TODO: support regex operators beyond fixed-string disjunction
