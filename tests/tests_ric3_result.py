import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATION_DIR = ROOT_DIR / "validation"
sys.path.insert(0, str(VALIDATION_DIR))

from ric3_result import (  # noqa: E402
    Ric3CommandError,
    Ric3ResultError,
    parse_ric3_result,
    run_ric3_command,
)


def assert_result_error(stdout: str, stderr: str) -> None:
    try:
        parse_ric3_result(stdout, stderr)
        assert False, "Expected Ric3ResultError"
    except Ric3ResultError:
        pass


def test_reachable_output_with_witness() -> None:
    stdout = "SAT\n1\nb0\n10001\n010\n001\n100\n.\n"
    stderr = "[15:32:18 INFO] IC3 found a counterexample at depth 2\n"

    assert parse_ric3_result(stdout, stderr) == "SAT"


def test_unreachable_output() -> None:
    stdout = "UNSAT\n0\n"
    stderr = "[15:32:20 INFO] IC3 proved the property\n"

    assert parse_ric3_result(stdout, stderr) == "UNSAT"


def test_result_on_stderr_is_supported() -> None:
    assert parse_ric3_result("witness text\n", "SAT\n") == "SAT"


def test_malformed_result_is_rejected() -> None:
    assert_result_error("[INFO]UNSAT\n", "")


def test_missing_result_is_rejected() -> None:
    assert_result_error("0\n", "[INFO] IC3 completed\n")


def test_conflicting_results_are_rejected() -> None:
    assert_result_error("SAT\n", "UNSAT\n")


def test_duplicate_results_are_rejected_as_ambiguous() -> None:
    assert_result_error("SAT\nSAT\n", "")


def test_nonzero_command_failure_preserves_raw_logs() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        stdout_log = Path(temp_dir) / "stdout.log"
        stderr_log = Path(temp_dir) / "stderr.log"
        command = [
            sys.executable,
            "-c",
            (
                "import sys; "
                "print('SAT'); "
                "print('solver failed', file=sys.stderr); "
                "raise SystemExit(7)"
            ),
        ]

        try:
            run_ric3_command(command, stdout_log, stderr_log)
            assert False, "Expected Ric3CommandError"
        except Ric3CommandError as error:
            assert error.returncode == 7

        assert stdout_log.read_text(encoding="utf-8") == "SAT\n"
        assert stderr_log.read_text(encoding="utf-8") == "solver failed\n"


def run_tests() -> None:
    test_reachable_output_with_witness()
    test_unreachable_output()
    test_result_on_stderr_is_supported()
    test_malformed_result_is_rejected()
    test_missing_result_is_rejected()
    test_conflicting_results_are_rejected()
    test_duplicate_results_are_rejected_as_ambiguous()
    test_nonzero_command_failure_preserves_raw_logs()
    print("All rIC3 result parsing tests passed.")


if __name__ == "__main__":
    run_tests()
