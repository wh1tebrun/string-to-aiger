import argparse
import ast
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parent
INTERNAL_PROFILE = "internal"
EXTERNAL_AIGSIM_PROFILE = "external-aigsim"
VALID_PROFILES = frozenset({INTERNAL_PROFILE, EXTERNAL_AIGSIM_PROFILE})

# This module supplies shared helpers to the real-aigsim scripts.  It is not a
# directly executable test script and therefore must not appear in the manifest.
HELPER_ONLY_TEST_MODULES = frozenset({"tests/aigsim_test_utils.py"})


@dataclass(frozen=True)
class TestSpec:
    order: int
    path: str
    profile: str


TEST_MANIFEST = (
    TestSpec(1, "tests/tests.py", INTERNAL_PROFILE),
    TestSpec(2, "tests/tests_regex.py", INTERNAL_PROFILE),
    TestSpec(3, "tests/tests_regex_length.py", INTERNAL_PROFILE),
    TestSpec(4, "tests/tests_sequential.py", INTERNAL_PROFILE),
    TestSpec(5, "tests/tests_sequential_trace.py", INTERNAL_PROFILE),
    TestSpec(6, "tests/tests_intersection.py", INTERNAL_PROFILE),
    TestSpec(7, "tests/tests_sequential_intersection.py", INTERNAL_PROFILE),
    TestSpec(8, "tests/tests_cli.py", INTERNAL_PROFILE),
    TestSpec(9, "tests/tests_evaluation.py", INTERNAL_PROFILE),
    TestSpec(10, "tests/tests_generated_benchmarks.py", INTERNAL_PROFILE),
    TestSpec(11, "tests/tests_nfa_product.py", INTERNAL_PROFILE),
    TestSpec(12, "tests/tests_product_backend.py", INTERNAL_PROFILE),
    TestSpec(13, "tests/tests_alphabet.py", INTERNAL_PROFILE),
    TestSpec(14, "tests/tests_nfa_prune.py", INTERNAL_PROFILE),
    TestSpec(15, "tests/tests_nfa_optimize.py", INTERNAL_PROFILE),
    TestSpec(16, "tests/tests_aiger_validator.py", INTERNAL_PROFILE),
    TestSpec(17, "tests/tests_aiger_pipeline.py", INTERNAL_PROFILE),
    TestSpec(18, "tests/tests_manual_aigsim_checks.py", INTERNAL_PROFILE),
    TestSpec(19, "tests/tests_external_aiger_validator.py", INTERNAL_PROFILE),
    TestSpec(20, "tests/tests_ric3_result.py", INTERNAL_PROFILE),
    TestSpec(21, "tests/tests_shell_line_endings.py", INTERNAL_PROFILE),
    TestSpec(22, "tests/tests_runner.py", INTERNAL_PROFILE),
    TestSpec(23, "tests/tests_aigsim_bounded.py", EXTERNAL_AIGSIM_PROFILE),
    TestSpec(24, "tests/tests_aigsim_sequential.py", EXTERNAL_AIGSIM_PROFILE),
    TestSpec(25, "tests/tests_aigsim_product.py", EXTERNAL_AIGSIM_PROFILE),
    TestSpec(26, "tests/tests_aigsim_bounded_fuzzer.py", EXTERNAL_AIGSIM_PROFILE),
    TestSpec(27, "tests/tests_aigsim_sequential_fuzzer.py", EXTERNAL_AIGSIM_PROFILE),
    TestSpec(28, "tests/tests_aigsim_cross_backend.py", EXTERNAL_AIGSIM_PROFILE),
    TestSpec(29, "tests/tests_aigsim_negative_detection.py", EXTERNAL_AIGSIM_PROFILE),
)


class ManifestError(ValueError):
    pass


def discover_executable_test_paths(repository_root: Path) -> frozenset[str]:
    tests_dir = repository_root / "tests"
    candidates = list(tests_dir.glob("tests_*.py"))
    legacy_test_script = tests_dir / "tests.py"
    if legacy_test_script.is_file():
        candidates.append(legacy_test_script)
    return frozenset(
        path.relative_to(repository_root).as_posix()
        for path in candidates
        if path.is_file()
    )


def validate_manifest(
    manifest: Iterable[TestSpec] = TEST_MANIFEST,
    repository_root: Path = REPOSITORY_ROOT,
    helper_only_modules: Iterable[str] = HELPER_ONLY_TEST_MODULES,
) -> tuple[TestSpec, ...]:
    specs = tuple(manifest)
    paths = [spec.path for spec in specs]
    orders = [spec.order for spec in specs]

    duplicate_paths = sorted(
        path for path in set(paths) if paths.count(path) > 1
    )
    if duplicate_paths:
        raise ManifestError(
            "Duplicate test manifest paths: " + ", ".join(duplicate_paths)
        )

    expected_orders = list(range(1, len(specs) + 1))
    if sorted(orders) != expected_orders:
        raise ManifestError(
            "Test manifest order values must be unique and contiguous from 1"
        )

    invalid_profiles = sorted(
        {spec.profile for spec in specs} - VALID_PROFILES
    )
    if invalid_profiles:
        raise ManifestError(
            "Invalid test manifest profiles: " + ", ".join(invalid_profiles)
        )

    invalid_paths = sorted(
        path
        for path in paths
        if PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
        or PurePosixPath(path).as_posix() != path
    )
    if invalid_paths:
        raise ManifestError(
            "Manifest paths must be normalized repository-relative paths: "
            + ", ".join(invalid_paths)
        )

    helper_paths = frozenset(helper_only_modules)
    helpers_in_manifest = sorted(set(paths) & helper_paths)
    if helpers_in_manifest:
        raise ManifestError(
            "Helper-only modules must not be executable manifest entries: "
            + ", ".join(helpers_in_manifest)
        )

    missing_helpers = sorted(
        path for path in helper_paths if not (repository_root / path).is_file()
    )
    if missing_helpers:
        raise ManifestError(
            "Missing helper-only test modules: " + ", ".join(missing_helpers)
        )

    missing_paths = sorted(
        path for path in paths if not (repository_root / path).is_file()
    )
    if missing_paths:
        raise ManifestError(
            "Missing test manifest paths: " + ", ".join(missing_paths)
        )

    discovered_paths = discover_executable_test_paths(repository_root)
    listed_paths = frozenset(paths)
    unlisted_paths = sorted(discovered_paths - listed_paths - helper_paths)
    if unlisted_paths:
        raise ManifestError(
            "Executable test scripts are missing from the manifest: "
            + ", ".join(unlisted_paths)
        )

    non_executable_paths = sorted(listed_paths - discovered_paths)
    if non_executable_paths:
        raise ManifestError(
            "Manifest entries are not executable test scripts: "
            + ", ".join(non_executable_paths)
        )

    return tuple(sorted(specs, key=lambda spec: spec.order))


def select_test_specs(
    manifest: Iterable[TestSpec] = TEST_MANIFEST,
    *,
    internal_only: bool,
) -> tuple[TestSpec, ...]:
    specs = tuple(sorted(manifest, key=lambda spec: spec.order))
    if internal_only:
        return tuple(
            spec for spec in specs if spec.profile == INTERNAL_PROFILE
        )
    return specs


def count_explicit_tests(
    specs: Iterable[TestSpec],
    repository_root: Path = REPOSITORY_ROOT,
) -> int:
    count = 0
    for spec in specs:
        syntax_tree = ast.parse(
            (repository_root / spec.path).read_text(encoding="utf-8"),
            filename=spec.path,
        )
        count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in syntax_tree.body
        )
    return count


def run_test(spec: TestSpec, repository_root: Path = REPOSITORY_ROOT) -> bool:
    full_command = [sys.executable, spec.path]

    print("=" * 60, flush=True)
    print("Running:", " ".join(full_command), flush=True)
    print("=" * 60, flush=True)

    result = subprocess.run(full_command, cwd=repository_root)

    if result.returncode != 0:
        print("\nFAILED:", spec.path)
        return False

    print("\nPASSED:", spec.path)
    return True


def run_tests(
    specs: Iterable[TestSpec],
    repository_root: Path = REPOSITORY_ROOT,
) -> int:
    for spec in specs:
        if not run_test(spec, repository_root):
            print("=" * 60)
            print("Some tests failed.")
            return 1

    print("=" * 60)
    print("All tests passed.")
    return 0


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the repository's direct-script test manifest."
    )
    parser.add_argument(
        "--internal-only",
        action="store_true",
        help="run internal tests that do not require real aigsim",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)

    try:
        manifest = validate_manifest()
    except (ManifestError, OSError, SyntaxError) as error:
        print(f"Test manifest validation failed: {error}", file=sys.stderr)
        return 2

    selected_specs = select_test_specs(
        manifest,
        internal_only=args.internal_only,
    )
    profile_name = "internal-only" if args.internal_only else "full"

    try:
        explicit_test_count = count_explicit_tests(selected_specs)
    except (OSError, SyntaxError) as error:
        print(f"Could not count explicit tests: {error}", file=sys.stderr)
        return 2

    print(f"Test profile: {profile_name}")
    print(f"Test scripts: {len(selected_specs)}")
    print(f"Explicit test functions: {explicit_test_count}")

    return run_tests(selected_specs)


if __name__ == "__main__":
    raise SystemExit(main())
