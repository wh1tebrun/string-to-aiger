import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from evaluation.benchmark_cases import BENCHMARK_CASES, iter_expected_words  # noqa: E402
from evaluation.evaluate_aiger_stats import collect_stats, table_headers as stats_headers  # noqa: E402
from evaluation.evaluate_language_behavior import collect_results as collect_language_results  # noqa: E402
from evaluation.evaluate_exhaustive_behavior import collect_results as collect_exhaustive_results  # noqa: E402


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

    expected_count = sum(
        len(benchmark.positive_words) + len(benchmark.negative_words)
        for benchmark in BENCHMARK_CASES
    )

    assert len(expected_words) == expected_count


def test_aiger_stats_headers_include_strategy():
    headers = stats_headers()

    assert "pattern" in headers
    assert "backend" in headers
    assert "strategy" in headers
    assert "bound" in headers
    assert "M" in headers
    assert "I" in headers
    assert "L" in headers
    assert "O" in headers
    assert "A" in headers
    assert "size(bytes)" in headers


def test_aiger_stats_collection_contains_all_backend_strategy_combinations():
    stats = collect_stats()

    expected_count = len(BENCHMARK_CASES) * 4
    assert len(stats) == expected_count

    combinations = {
        (stat.backend, stat.intersection_strategy)
        for stat in stats
    }

    assert ("bounded", "structural") in combinations
    assert ("bounded", "product") in combinations
    assert ("sequential", "structural") in combinations
    assert ("sequential", "product") in combinations


def test_aiger_stats_have_valid_header_values():
    stats = collect_stats()

    for stat in stats:
        assert stat.max_var_index >= 0
        assert stat.inputs >= 0
        assert stat.latches >= 0
        assert stat.outputs == 1
        assert stat.and_gates >= 0
        assert stat.file_size_bytes > 0

        if stat.backend == "bounded":
            assert stat.latches == 0
            assert stat.bound != "-"

        if stat.backend == "sequential":
            assert stat.latches > 0
            assert stat.bound == "-"


def test_language_behavior_results_all_pass():
    results = collect_language_results()

    assert len(results) == len(iter_expected_words())

    for result in results:
        assert result.status == "OK"
        assert result.bounded_structural == result.expected
        assert result.bounded_product == result.expected
        assert result.sequential_structural == result.expected
        assert result.sequential_product == result.expected


def test_exhaustive_behavior_results_all_pass():
    results, summaries = collect_exhaustive_results()

    assert len(results) > 0
    assert len(summaries) == len(BENCHMARK_CASES)

    for result in results:
        assert result.status == "OK"
        assert result.bounded_structural == result.expected
        assert result.bounded_product == result.expected
        assert result.sequential_structural == result.expected
        assert result.sequential_product == result.expected

    for summary in summaries:
        assert summary.checked_words > 0
        assert summary.failed == 0
        assert summary.passed == summary.checked_words


def run_tests():
    test_benchmark_cases_are_not_empty()
    test_benchmark_cases_have_valid_bounds()
    test_benchmark_cases_have_examples()
    test_expected_word_iterator_matches_benchmark_cases()
    test_aiger_stats_headers_include_strategy()
    test_aiger_stats_collection_contains_all_backend_strategy_combinations()
    test_aiger_stats_have_valid_header_values()
    test_language_behavior_results_all_pass()
    test_exhaustive_behavior_results_all_pass()

    print("All evaluation tests passed.")


if __name__ == "__main__":
    run_tests()
