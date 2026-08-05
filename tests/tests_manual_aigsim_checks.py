from __future__ import annotations

import csv
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from validation import generate_manual_aigsim_checks as manual  # noqa: E402


DEMO_SCRIPT = ROOT_DIR / "scripts" / "demo_manual_aigsim_checks.sh"


@contextmanager
def patched_generator_root(root: Path) -> Iterator[None]:
    names = ["ROOT", "ARTIFACT_ROOT", "AIGER_DIR", "STIMULUS_DIR", "OUTPUT_DIR"]
    previous = {name: getattr(manual, name) for name in names}

    manual.ROOT = root
    manual.ARTIFACT_ROOT = root / "artifacts" / "manual_aigsim_checks"
    manual.AIGER_DIR = manual.ARTIFACT_ROOT / "aiger"
    manual.STIMULUS_DIR = manual.ARTIFACT_ROOT / "stimuli"
    manual.OUTPUT_DIR = manual.ARTIFACT_ROOT / "outputs"
    manual.ensure_dirs()

    try:
        yield
    finally:
        for name, value in previous.items():
            setattr(manual, name, value)


def write_executable(path: Path, content: str) -> None:
    manual.write_lf_text(path, content)
    path.chmod(
        path.stat().st_mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )


def write_unit_fake_aigsim(root: Path) -> Path:
    script = root / "fake tools" / "fake aigsim.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    write_executable(
        script,
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import sys
            from pathlib import Path

            mode = sys.argv[1]
            aag_path = Path(sys.argv[2])
            header = aag_path.read_text(encoding="utf-8").splitlines()[0].split()
            num_inputs = int(header[2])
            num_latches = int(header[3])
            stimulus = sys.stdin.read()
            lines = stimulus.splitlines()
            assert lines and lines[-1] == "."
            vectors = lines[:-1]
            assert all(len(vector) == num_inputs for vector in vectors)

            def emit(actual):
                for index, vector in enumerate(vectors):
                    output = actual if index == len(vectors) - 1 else "0"
                    if num_latches:
                        state = "0" * num_latches
                        print(state, vector, output, state)
                    else:
                        print(vector, output)

            if mode == "missing":
                raise SystemExit(0)
            if mode == "malformed":
                print("not-a-valid-aigsim-line")
                raise SystemExit(0)

            actual = "0" if mode == "reject" else "1"
            emit(actual)

            if mode == "extra":
                print("unexpected extra output")
            if mode == "stderr":
                print(
                    "*** [aigsim] line 2: pos 1: expected '0' or '1'",
                    file=sys.stderr,
                )
            if mode == "nonzero":
                print("simulator failed after producing output", file=sys.stderr)
                raise SystemExit(7)
            """
        ),
    )
    return script


def write_bounded_fixture() -> tuple[Path, Path]:
    aag_path = manual.AIGER_DIR / "fixture.aag"
    stimulus_path = manual.STIMULUS_DIR / "fixture.stim"
    manual.write_lf_text(
        aag_path,
        "aag 1 1 0 1 0\n2\n2\ni0 input_bit\no0 result\nc\nfixture\n",
    )
    manual.write_lf_text(stimulus_path, "1\n.\n")
    return aag_path, stimulus_path


def run_unit_fake(
    root: Path,
    mode: str,
) -> manual.AigsimExecution:
    aag_path, stimulus_path = write_bounded_fixture()
    fake = write_unit_fake_aigsim(root)
    return manual.run_aigsim(
        aag_path,
        stimulus_path,
        [sys.executable, str(fake), mode],
    )


def assert_execution_failed(execution: manual.AigsimExecution) -> None:
    assert execution.execution_valid is False
    assert manual.evaluate_execution(execution, "1", True) == (
        "N/A",
        "NO",
        "EXECUTION FAILED",
    )


def write_shell_fake_aigsim(root: Path) -> Path:
    script = root / "tools" / "fake-aigsim"
    script.parent.mkdir(parents=True, exist_ok=True)
    write_executable(
        script,
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import os
            import sys
            from pathlib import Path

            aag_path = Path(sys.argv[1])
            stimulus = sys.stdin.read()
            artifact_root = Path("artifacts/manual_aigsim_checks")
            stimulus_root = artifact_root / "stimuli"

            log_path = Path(os.environ["FAKE_AIGSIM_LOG"])
            with log_path.open("a", encoding="utf-8", newline="\\n") as log:
                log.write(aag_path.name + "\\n")

            bounded_accept = (
                stimulus_root / "bounded_accept_ab.stim"
            ).read_text(encoding="utf-8")
            sequential_accepts = {
                (stimulus_root / name).read_text(encoding="utf-8")
                for name in [
                    "sequential_accept_empty.stim",
                    "sequential_accept_bc.stim",
                    "sequential_accept_bcbc.stim",
                ]
            }

            if (
                os.environ.get("FAKE_AIGSIM_FAIL") == "bounded_accept_ab"
                and aag_path.name == "bounded_ab_or_bc_correct.aag"
                and stimulus == bounded_accept
            ):
                print("injected simulator failure", file=sys.stderr)
                raise SystemExit(7)

            if "output_forced_false" in aag_path.name:
                actual = "0"
            elif aag_path.name == "bounded_ab_or_bc_correct.aag":
                actual = "1" if stimulus == bounded_accept else "0"
            elif aag_path.name == "sequential_bc_star_correct.aag":
                actual = "1" if stimulus in sequential_accepts else "0"
            else:
                print("unknown test AIGER", file=sys.stderr)
                raise SystemExit(9)

            header = aag_path.read_text(encoding="utf-8").splitlines()[0].split()
            num_inputs = int(header[2])
            num_latches = int(header[3])
            lines = stimulus.splitlines()
            assert lines and lines[-1] == "."
            vectors = lines[:-1]

            for index, vector in enumerate(vectors):
                assert len(vector) == num_inputs
                output = actual if index == len(vectors) - 1 else "0"
                if num_latches:
                    state = "0" * num_latches
                    print(state, vector, output, state)
                else:
                    print(vector, output)
            """
        ),
    )
    return script


def shell_case_lines(stdout: str) -> list[str]:
    return [
        line
        for line in stdout.splitlines()
        if re.match(r"^MAN[0-9]{3}\s*\|", line)
    ]


def test_bounded_stimulus_has_exact_lf_terminator() -> None:
    aag_text = (
        "aag 3 3 0 1 0\n"
        "2\n4\n6\n2\n"
        "i0 len_is_1\n"
        "i1 x_0_is_a\n"
        "i2 x_0_is_b\n"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "bounded.stim"
        manual.write_lf_text(path, manual.make_bounded_stimulus(aag_text, "a"))
        stimulus, vectors = manual.read_stimulus(path, 3)

        assert path.read_bytes() == b"110\n.\n"
        assert b"\r" not in path.read_bytes()
        assert stimulus == "110\n.\n"
        assert vectors == ["110"]


def test_sequential_stimulus_terminator_is_not_a_trace_step() -> None:
    aag_text = (
        "aag 4 3 1 1 0\n"
        "2\n4\n6\n8 0\n2\n"
        "i0 end\n"
        "i1 is_b\n"
        "i2 is_c\n"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "sequential.stim"
        manual.write_lf_text(path, manual.make_sequential_stimulus(aag_text, "bc"))
        stimulus, vectors = manual.read_stimulus(path, 3)

        assert path.read_bytes() == b"010\n001\n100\n.\n"
        assert b"\r" not in path.read_bytes()
        assert stimulus.count("\n.\n") == 1
        assert vectors == ["010", "001", "100"]
        assert "." not in vectors


def test_clean_accepting_and_rejecting_cases_pass() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        with patched_generator_root(root):
            accepting = run_unit_fake(root, "accept")
            rejecting = run_unit_fake(root, "reject")

            assert accepting.execution_valid is True
            assert accepting.exit_code == 0
            assert accepting.stderr == ""
            assert accepting.actual_output == "1"
            assert manual.evaluate_execution(accepting, "1", True) == (
                "YES",
                "NO",
                "OK",
            )

            assert rejecting.execution_valid is True
            assert rejecting.exit_code == 0
            assert rejecting.stderr == ""
            assert rejecting.actual_output == "0"
            assert manual.evaluate_execution(rejecting, "0", True) == (
                "YES",
                "NO",
                "OK",
            )

            assert accepting.command[-1] == str(
                (manual.AIGER_DIR / "fixture.aag").relative_to(root)
            )
            assert "fake tools" in accepting.command[1]


def test_clean_negative_control_mismatch_passes() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        with patched_generator_root(root):
            execution = run_unit_fake(root, "reject")

            assert execution.execution_valid is True
            assert execution.actual_output == "0"
            assert manual.evaluate_execution(execution, "1", False) == (
                "NO",
                "YES",
                "MISMATCH DETECTED",
            )


def test_negative_control_without_mismatch_fails() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        with patched_generator_root(root):
            execution = run_unit_fake(root, "accept")

            assert manual.evaluate_execution(execution, "1", False) == (
                "YES",
                "NO",
                "UNEXPECTED",
            )

            try:
                manual.evaluate_execution(execution, "0", False)
                assert False, "Expected a negative-control reference-witness error"
            except AssertionError as error:
                assert "accepting witness" in str(error)


def test_nonzero_exit_fails_and_preserves_raw_output() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        with patched_generator_root(root):
            execution = run_unit_fake(root, "nonzero")

            assert execution.exit_code == 7
            assert execution.stdout == "1 1\n"
            assert execution.stderr == "simulator failed after producing output\n"
            assert "status 7" in execution.execution_error
            assert "stderr was not empty" in execution.execution_error
            assert_execution_failed(execution)


def test_stderr_parse_warning_fails_a_semantic_match() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        with patched_generator_root(root):
            execution = run_unit_fake(root, "stderr")

            assert execution.exit_code == 0
            assert execution.actual_output == "1"
            assert "expected '0' or '1'" in execution.stderr
            assert "stderr was not empty" in execution.execution_error
            assert_execution_failed(execution)


def test_missing_malformed_and_ambiguous_output_fail() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        with patched_generator_root(root):
            executions = {
                mode: run_unit_fake(root, mode)
                for mode in ["missing", "malformed", "extra"]
            }

            assert "expected 1, got 0" in executions["missing"].execution_error
            assert "malformed or conflicting" in executions["malformed"].execution_error
            assert "expected 1, got 2" in executions["extra"].execution_error

            for execution in executions.values():
                assert execution.exit_code == 0
                assert execution.stderr == ""
                assert execution.actual_output == ""
                assert_execution_failed(execution)


def test_unexpected_ordinary_semantic_mismatch_fails() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        with patched_generator_root(root):
            execution = run_unit_fake(root, "reject")

            assert execution.execution_valid is True
            assert manual.evaluate_execution(execution, "1", True) == (
                "NO",
                "YES",
                "UNEXPECTED",
            )


def test_run_case_metadata_records_expected_negative_control_mismatch() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        with patched_generator_root(root):
            aag_path, stimulus_path = write_bounded_fixture()
            fake = write_unit_fake_aigsim(root)
            row = manual.run_case(
                "TEST001",
                "bounded negative control",
                "fixture",
                "forced-false fixture disagrees on an accepting witness",
                aag_path,
                stimulus_path,
                "fixture witness",
                "1",
                False,
                [sys.executable, str(fake), "reject"],
            )

            headers = list(row)
            csv_path = manual.ARTIFACT_ROOT / "manual_aigsim_checks.csv"
            markdown_path = manual.ARTIFACT_ROOT / "manual_aigsim_checks.md"
            manual.write_csv(csv_path, headers, [row])
            manual.write_lf_text(
                markdown_path,
                manual.make_markdown_table(headers, [row]),
            )

            assert row["aigsim_exit_code"] == 0
            assert row["execution_valid"] == "YES"
            assert row["stderr_empty"] == "YES"
            assert row["expected_semantic_output"] == "1"
            assert row["aigsim_actual_output"] == "0"
            assert row["matches_expected_semantics"] == "NO"
            assert row["mismatch_detected"] == "YES"
            assert row["verdict"] == "MISMATCH DETECTED"

            with csv_path.open(newline="", encoding="utf-8") as csv_file:
                csv_row = next(csv.DictReader(csv_file))

            for name in [
                "aigsim_exit_code",
                "execution_valid",
                "expected_semantic_output",
                "aigsim_actual_output",
                "matches_expected_semantics",
                "mismatch_detected",
                "verdict",
            ]:
                assert csv_row[name] == str(row[name])

            markdown = markdown_path.read_text(encoding="utf-8")
            assert "| aigsim_exit_code |" in markdown
            assert "| TEST001 |" in markdown
            assert "MISMATCH DETECTED" in markdown

            captured = (
                manual.OUTPUT_DIR / "TEST001_aigsim_output.txt"
            ).read_text(encoding="utf-8")
            assert "Exit code:\n0" in captured
            assert "Execution valid:\nYES" in captured
            assert "Expected semantic output:\n1" in captured
            assert "Actual output:\n0" in captured
            assert "Matches expected semantics:\nNO" in captured
            assert "Mismatch detected:\nYES" in captured
            assert "Final verdict:\nMISMATCH DETECTED" in captured
            assert "stdout:\n1 0" in captured
            assert "stderr:\n\n" in captured


def test_shell_demo_passes_all_cases_and_aggregates_failures() -> None:
    bash = shutil.which("bash")
    assert bash is not None, "The shell aggregation test requires bash"

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        scripts_dir = root / "scripts"
        scripts_dir.mkdir(parents=True)
        copied_demo = scripts_dir / DEMO_SCRIPT.name
        shutil.copyfile(DEMO_SCRIPT, copied_demo)

        with patched_generator_root(root):
            manual.generate_bounded_files()
            manual.generate_sequential_files()

        fake = write_shell_fake_aigsim(root)
        call_log = root / "fake-aigsim-calls.log"
        environment = os.environ.copy()
        environment["AIGSIM"] = str(fake)
        environment["FAKE_AIGSIM_LOG"] = str(call_log)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"

        success = subprocess.run(
            [bash, str(copied_demo)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )

        success_lines = shell_case_lines(success.stdout)
        assert success.returncode == 0, success.stderr
        assert success.stderr == ""
        assert len(success_lines) == 9
        assert sum(line.rstrip().endswith("| MATCH") for line in success_lines) == 7
        assert sum(
            line.rstrip().endswith("| MISMATCH DETECTED")
            for line in success_lines
        ) == 2
        assert "All 9 manual aigsim checks passed." in success.stdout
        assert len(call_log.read_text(encoding="utf-8").splitlines()) == 9

        call_log.unlink()
        failing_environment = environment.copy()
        failing_environment["FAKE_AIGSIM_FAIL"] = "bounded_accept_ab"
        failure = subprocess.run(
            [bash, str(copied_demo)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
            env=failing_environment,
        )

        assert failure.returncode != 0
        assert "aigsim exited with status 7" in failure.stderr
        assert "injected simulator failure" in failure.stderr
        assert "Manual aigsim checks failed: 1 required case(s)." in failure.stderr
        assert len(call_log.read_text(encoding="utf-8").splitlines()) == 9
        assert "MAN009" in failure.stdout


def run_tests() -> None:
    test_bounded_stimulus_has_exact_lf_terminator()
    test_sequential_stimulus_terminator_is_not_a_trace_step()
    test_clean_accepting_and_rejecting_cases_pass()
    test_clean_negative_control_mismatch_passes()
    test_negative_control_without_mismatch_fails()
    test_nonzero_exit_fails_and_preserves_raw_output()
    test_stderr_parse_warning_fails_a_semantic_match()
    test_missing_malformed_and_ambiguous_output_fail()
    test_unexpected_ordinary_semantic_mismatch_fails()
    test_run_case_metadata_records_expected_negative_control_mismatch()
    test_shell_demo_passes_all_cases_and_aggregates_failures()
    print("All manual aigsim fail-closed tests passed.")


if __name__ == "__main__":
    run_tests()
