import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import run_all_tests as runner  # noqa: E402


EXPECTED_EXTERNAL_AIGSIM_SCRIPTS = {
    "tests/tests_aigsim_bounded.py",
    "tests/tests_aigsim_sequential.py",
    "tests/tests_aigsim_product.py",
    "tests/tests_aigsim_bounded_fuzzer.py",
    "tests/tests_aigsim_sequential_fuzzer.py",
    "tests/tests_aigsim_cross_backend.py",
    "tests/tests_aigsim_negative_detection.py",
}


def assert_manifest_error(function, expected_text: str) -> None:
    try:
        function()
    except runner.ManifestError as error:
        assert expected_text in str(error), str(error)
        return
    raise AssertionError("Expected manifest validation to fail")


def test_manifest_accounts_for_every_executable_script_once() -> None:
    manifest = runner.validate_manifest()
    listed_paths = [spec.path for spec in manifest]
    discovered_paths = runner.discover_executable_test_paths(ROOT_DIR)
    executable_paths = discovered_paths - runner.HELPER_ONLY_TEST_MODULES

    assert set(listed_paths) == executable_paths
    assert len(listed_paths) == len(executable_paths)


def test_no_manifest_path_is_missing() -> None:
    manifest = runner.validate_manifest()
    missing = [
        spec.path for spec in manifest if not (ROOT_DIR / spec.path).is_file()
    ]
    assert missing == []


def test_no_manifest_path_is_duplicated() -> None:
    paths = [spec.path for spec in runner.validate_manifest()]
    assert len(paths) == len(set(paths))


def test_internal_and_external_classifications_are_disjoint() -> None:
    manifest = runner.validate_manifest()
    internal_paths = {
        spec.path
        for spec in manifest
        if spec.profile == runner.INTERNAL_PROFILE
    }
    external_paths = {
        spec.path
        for spec in manifest
        if spec.profile == runner.EXTERNAL_AIGSIM_PROFILE
    }

    assert internal_paths.isdisjoint(external_paths)
    assert internal_paths | external_paths == {spec.path for spec in manifest}


def test_internal_only_selects_every_and_only_internal_script() -> None:
    manifest = runner.validate_manifest()
    selected = runner.select_test_specs(manifest, internal_only=True)
    expected = tuple(
        spec for spec in manifest if spec.profile == runner.INTERNAL_PROFILE
    )

    assert selected == expected
    assert all(spec.profile == runner.INTERNAL_PROFILE for spec in selected)


def test_default_selection_includes_every_executable_script() -> None:
    manifest = runner.validate_manifest()
    assert runner.select_test_specs(manifest, internal_only=False) == manifest


def test_external_aigsim_scripts_are_excluded_from_internal_profile() -> None:
    manifest = runner.validate_manifest()
    external_paths = {
        spec.path
        for spec in manifest
        if spec.profile == runner.EXTERNAL_AIGSIM_PROFILE
    }
    internal_paths = {
        spec.path
        for spec in runner.select_test_specs(manifest, internal_only=True)
    }

    assert external_paths == EXPECTED_EXTERNAL_AIGSIM_SCRIPTS
    assert external_paths.isdisjoint(internal_paths)


def test_unlisted_executable_script_fails_manifest_validation() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repository_root = Path(temp_dir)
        tests_dir = repository_root / "tests"
        tests_dir.mkdir()
        (tests_dir / "tests_listed.py").write_text("pass\n", encoding="utf-8")
        (tests_dir / "tests_unlisted.py").write_text("pass\n", encoding="utf-8")
        manifest = (
            runner.TestSpec(
                1,
                "tests/tests_listed.py",
                runner.INTERNAL_PROFILE,
            ),
        )

        assert_manifest_error(
            lambda: runner.validate_manifest(
                manifest,
                repository_root,
                helper_only_modules=(),
            ),
            "tests/tests_unlisted.py",
        )


def test_duplicate_manifest_entry_fails_validation() -> None:
    duplicate = runner.TestSpec(
        len(runner.TEST_MANIFEST) + 1,
        runner.TEST_MANIFEST[0].path,
        runner.TEST_MANIFEST[0].profile,
    )
    assert_manifest_error(
        lambda: runner.validate_manifest(runner.TEST_MANIFEST + (duplicate,)),
        "Duplicate test manifest paths",
    )


def test_invalid_profile_fails_manifest_validation() -> None:
    invalid = runner.TestSpec(
        runner.TEST_MANIFEST[0].order,
        runner.TEST_MANIFEST[0].path,
        "network-dependent",
    )
    manifest = (invalid,) + runner.TEST_MANIFEST[1:]
    assert_manifest_error(
        lambda: runner.validate_manifest(manifest),
        "Invalid test manifest profiles",
    )


def test_subprocess_failure_propagates_to_nonzero_status() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repository_root = Path(temp_dir)
        tests_dir = repository_root / "tests"
        tests_dir.mkdir()
        failing_path = tests_dir / "tests_failure.py"
        failing_path.write_text("raise SystemExit(7)\n", encoding="utf-8")
        spec = runner.TestSpec(
            1,
            "tests/tests_failure.py",
            runner.INTERNAL_PROFILE,
        )

        assert runner.run_tests((spec,), repository_root) == 1


def test_runner_help_succeeds_and_documents_internal_only() -> None:
    environment = os.environ.copy()
    environment.pop("AIGSIM", None)
    result = subprocess.run(
        [sys.executable, str(ROOT_DIR / "run_all_tests.py"), "--help"],
        cwd=ROOT_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--internal-only" in result.stdout
    assert "internal tests that do not require real aigsim" in result.stdout


def main() -> int:
    test_manifest_accounts_for_every_executable_script_once()
    test_no_manifest_path_is_missing()
    test_no_manifest_path_is_duplicated()
    test_internal_and_external_classifications_are_disjoint()
    test_internal_only_selects_every_and_only_internal_script()
    test_default_selection_includes_every_executable_script()
    test_external_aigsim_scripts_are_excluded_from_internal_profile()
    test_unlisted_executable_script_fails_manifest_validation()
    test_duplicate_manifest_entry_fails_validation()
    test_invalid_profile_fails_manifest_validation()
    test_subprocess_failure_propagates_to_nonzero_status()
    test_runner_help_succeeds_and_documents_internal_only()
    print("All test-runner manifest tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
