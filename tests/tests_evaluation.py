import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from evaluation.benchmark_cases import BENCHMARK_CASES, iter_expected_words  # noqa: E402
from evaluation.evaluate_aiger_stats import parse_aiger_stats  # noqa: E402
from evaluation.evaluate_language_behavior import collect_results  # noqa: E402


def test_benchmark_cases_are_not_empty():
    assert len(BENCHMARK_CASES) > 0


def test_benchmark_cases_have_valid_bounds():
    for benchmark in BENCHMARK_CASES:
        assert benchmark.bound >= 0


def test_benchmark_cases_have_examples():
    for benchmark in BENCHMARK_CASES:
        assert len(benchmark.positive_words) + len(benchmark.negative_words) > 0


def test_expected_word_iterator_matches_benchmark_cases():
    expected_words = iter_expected_words()

    assert len(expected_words) > 0

    for pattern, bound, word, expected in expected_words:
        assert isinstance(pattern, str)
        assert isinstance(bound, int)
        assert isinstance(word, str)
        assert isinstance(expected, bool)


def test_parse_aiger_stats_valid_header():
    aiger_text = "\n".join([
        "aag 5 2 1 1 2",
        "2",
        "4",
        "6 8 1",
        "10",
        "8 6 4",
        "10 2 6",
    ])

    stats = parse_aiger_stats(
        pattern="a*",
        backend="sequential",
        bound="-",
        aiger_text=aiger_text,
    )

    assert stats.pattern == "a*"
    assert stats.backend == "sequential"
    assert stats.bound == "-"
    assert stats.max_var_index == 5
    assert stats.inputs == 2
    assert stats.latches == 1
    assert stats.outputs == 1
    assert stats.and_gates == 2
    assert stats.file_size_bytes > 0


def test_language_behavior_results_are_ok():
    results = collect_results()

    assert len(results) > 0
    assert all(result.status == "OK" for result in results)


def run_tests():
    test_benchmark_cases_are_not_empty()
    test_benchmark_cases_have_valid_bounds()
    test_benchmark_cases_have_examples()
    test_expected_word_iterator_matches_benchmark_cases()
    test_parse_aiger_stats_valid_header()
    test_language_behavior_results_are_ok()

    print("All evaluation tests passed.")


if __name__ == "__main__":
    run_tests()
