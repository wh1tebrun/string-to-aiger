import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from evaluation.generated_benchmarks import (  # noqa: E402
    GENERATED_BENCHMARKS,
    collect_results,
    generate_words,
)


def test_generated_benchmarks_are_not_empty():
    assert len(GENERATED_BENCHMARKS) > 0


def test_generated_benchmarks_have_valid_bounds():
    for benchmark in GENERATED_BENCHMARKS:
        assert benchmark.bound >= 0


def test_generated_benchmarks_have_feature_descriptions():
    for benchmark in GENERATED_BENCHMARKS:
        assert benchmark.feature.strip() != ""


def test_generated_benchmarks_cover_regex_features():
    patterns = [
        benchmark.pattern
        for benchmark in GENERATED_BENCHMARKS
    ]

    assert any("*" in pattern for pattern in patterns)
    assert any("+" in pattern for pattern in patterns)
    assert any("?" in pattern for pattern in patterns)
    assert any("{" in pattern for pattern in patterns)
    assert any("[" in pattern for pattern in patterns)
    assert any("&" in pattern for pattern in patterns)


def test_generate_words_includes_empty_word():
    words = generate_words(("a", "b"), bound=2)

    assert "" in words
    assert "a" in words
    assert "b" in words
    assert "aa" in words
    assert "ab" in words
    assert "ba" in words
    assert "bb" in words


def test_generate_words_respects_bound():
    words = generate_words(("a", "b"), bound=2)

    for word in words:
        assert len(word) <= 2


def test_generated_benchmark_results_all_pass():
    results, summaries = collect_results()

    assert len(results) > 0
    assert len(summaries) == len(GENERATED_BENCHMARKS)

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
    test_generated_benchmarks_are_not_empty()
    test_generated_benchmarks_have_valid_bounds()
    test_generated_benchmarks_have_feature_descriptions()
    test_generated_benchmarks_cover_regex_features()
    test_generate_words_includes_empty_word()
    test_generate_words_respects_bound()
    test_generated_benchmark_results_all_pass()

    print("All generated benchmark tests passed.")


if __name__ == "__main__":
    run_tests()
