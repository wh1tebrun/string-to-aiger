from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkCase:
    pattern: str
    bound: int
    positive_words: tuple[str, ...]
    negative_words: tuple[str, ...]


BENCHMARK_CASES = [
    BenchmarkCase(
        pattern="a*",
        bound=3,
        positive_words=("", "a", "aa", "aaa"),
        negative_words=("b", "ab", "ba"),
    ),
    BenchmarkCase(
        pattern="(ab)*",
        bound=6,
        positive_words=("", "ab", "abab", "ababab"),
        negative_words=("a", "b", "aba", "abb"),
    ),
    BenchmarkCase(
        pattern="(a|b)*",
        bound=4,
        positive_words=("", "a", "b", "ab", "ba", "abba"),
        negative_words=("abc",),
    ),
    BenchmarkCase(
        pattern="(a|ba)*",
        bound=5,
        positive_words=("", "a", "ba", "aba", "baa", "ababa"),
        negative_words=("b", "bb"),
    ),
    BenchmarkCase(
        pattern="(a|b)*&a*",
        bound=4,
        positive_words=("", "a", "aa", "aaa", "aaaa"),
        negative_words=("b", "ab", "ba"),
    ),
    BenchmarkCase(
        pattern="(ab)*&(a|b)*",
        bound=6,
        positive_words=("", "ab", "abab", "ababab"),
        negative_words=("a", "b", "aba", "abb"),
    ),
    BenchmarkCase(
        pattern="a*&b*",
        bound=4,
        positive_words=("",),
        negative_words=("a", "aa", "b", "bb", "ab", "ba"),
    ),
    BenchmarkCase(
        pattern="a{1,3}",
        bound=3,
        positive_words=("a", "aa", "aaa"),
        negative_words=("", "aaaa", "b"),
    ),
    BenchmarkCase(
        pattern="[ab]{2,}",
        bound=4,
        positive_words=("aa", "ab", "ba", "bb", "abba"),
        negative_words=("", "a", "ac"),
    ),
]


def iter_expected_words() -> list[tuple[str, int, str, bool]]:
    cases: list[tuple[str, int, str, bool]] = []

    for benchmark in BENCHMARK_CASES:
        for word in benchmark.positive_words:
            cases.append((benchmark.pattern, benchmark.bound, word, True))

        for word in benchmark.negative_words:
            cases.append((benchmark.pattern, benchmark.bound, word, False))

    return cases
