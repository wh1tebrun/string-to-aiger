from dataclasses import dataclass


@dataclass
class ExactStringMatcher:
    word: str


@dataclass
class OrMatcher:
    options: list[ExactStringMatcher]


def build_model(strings: list[str]) -> OrMatcher:
    """Build the internal matcher model from parsed strings."""
    matchers = [ExactStringMatcher(s) for s in strings]
    return OrMatcher(matchers)
