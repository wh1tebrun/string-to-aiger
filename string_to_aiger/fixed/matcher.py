from .model import ExactStringMatcher, OrMatcher


def matches_exact(matcher: ExactStringMatcher, candidate: str) -> bool:
    return matcher.word == candidate


def matches_or(matcher: OrMatcher, candidate: str) -> bool:
    for option in matcher.options:
        if matches_exact(option, candidate):
            return True
    return False
