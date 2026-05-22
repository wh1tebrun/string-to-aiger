import os
import sys
import tempfile

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.aiger.aiger import compile_expr_to_aiger  # noqa: E402
from string_to_aiger.aiger.external_aiger_validator import (  # noqa: E402
    build_external_command,
    require_external_aiger_validation,
    validate_aiger_with_external_tool,
)
from string_to_aiger.regex.regex_bounded_compiler import compile_regex_bounded  # noqa: E402


def compile_sample_aiger() -> str:
    expr = compile_regex_bounded("a*", bound=3)
    return compile_expr_to_aiger(expr)


def write_sample_aiger(temp_dir: str) -> str:
    path = os.path.join(temp_dir, "sample.aag")

    with open(path, "w", encoding="utf-8") as f:
        f.write(compile_sample_aiger())

    return path


def write_python_script(temp_dir: str, name: str, body: str) -> str:
    path = os.path.join(temp_dir, name)

    with open(path, "w", encoding="utf-8") as f:
        f.write(body)

    return path


def test_build_external_command_appends_path_when_no_placeholder():
    command = build_external_command(
        ["checker", "--flag"],
        "outputs/sample.aag",
    )

    assert command == (
        "checker",
        "--flag",
        "outputs/sample.aag",
    )


def test_build_external_command_replaces_placeholder():
    command = build_external_command(
        ["checker", "--input", "{path}"],
        "outputs/sample.aag",
    )

    assert command == (
        "checker",
        "--input",
        "outputs/sample.aag",
    )


def test_validate_skips_when_no_command_is_configured():
    with tempfile.TemporaryDirectory() as temp_dir:
        aiger_path = write_sample_aiger(temp_dir)

        result = validate_aiger_with_external_tool(
            aiger_path=aiger_path,
            command=None,
        )

        assert result.skipped is True
        assert result.passed is False
        assert result.failed is False


def test_validate_skips_when_executable_is_missing():
    with tempfile.TemporaryDirectory() as temp_dir:
        aiger_path = write_sample_aiger(temp_dir)

        result = validate_aiger_with_external_tool(
            aiger_path=aiger_path,
            command=["definitely_missing_aiger_validator_binary"],
        )

        assert result.skipped is True
        assert "not found" in result.message


def test_validate_passes_when_external_command_returns_zero():
    with tempfile.TemporaryDirectory() as temp_dir:
        aiger_path = write_sample_aiger(temp_dir)

        script_path = write_python_script(
            temp_dir,
            "pass_validator.py",
            "\n".join([
                "import sys",
                "with open(sys.argv[1], 'r', encoding='utf-8') as f:",
                "    text = f.read()",
                "assert text.startswith('aag ')",
                "print('external validator passed')",
                "raise SystemExit(0)",
            ]),
        )

        result = validate_aiger_with_external_tool(
            aiger_path=aiger_path,
            command=[sys.executable, script_path],
        )

        assert result.passed is True
        assert result.returncode == 0
        assert "external validator passed" in result.stdout


def test_validate_fails_when_external_command_returns_nonzero():
    with tempfile.TemporaryDirectory() as temp_dir:
        aiger_path = write_sample_aiger(temp_dir)

        script_path = write_python_script(
            temp_dir,
            "fail_validator.py",
            "\n".join([
                "import sys",
                "print('external validator failed')",
                "raise SystemExit(7)",
            ]),
        )

        result = validate_aiger_with_external_tool(
            aiger_path=aiger_path,
            command=[sys.executable, script_path],
        )

        assert result.failed is True
        assert result.returncode == 7
        assert "external validator failed" in result.stdout


def test_validate_supports_path_placeholder():
    with tempfile.TemporaryDirectory() as temp_dir:
        aiger_path = write_sample_aiger(temp_dir)

        script_path = write_python_script(
            temp_dir,
            "placeholder_validator.py",
            "\n".join([
                "import sys",
                "path = sys.argv[1]",
                "with open(path, 'r', encoding='utf-8') as f:",
                "    text = f.read()",
                "assert text.startswith('aag ')",
                "raise SystemExit(0)",
            ]),
        )

        result = validate_aiger_with_external_tool(
            aiger_path=aiger_path,
            command=[sys.executable, script_path, "{path}"],
        )

        assert result.passed is True


def test_require_external_validation_allows_skipped_validation():
    with tempfile.TemporaryDirectory() as temp_dir:
        aiger_path = write_sample_aiger(temp_dir)

        result = require_external_aiger_validation(
            aiger_path=aiger_path,
            command=None,
        )

        assert result.skipped is True


def test_require_external_validation_raises_on_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        aiger_path = write_sample_aiger(temp_dir)

        script_path = write_python_script(
            temp_dir,
            "fail_validator.py",
            "\n".join([
                "raise SystemExit(1)",
            ]),
        )

        try:
            require_external_aiger_validation(
                aiger_path=aiger_path,
                command=[sys.executable, script_path],
            )
            assert False, "Expected ValueError for failing external validation"
        except ValueError:
            pass


def run_tests():
    test_build_external_command_appends_path_when_no_placeholder()
    test_build_external_command_replaces_placeholder()
    test_validate_skips_when_no_command_is_configured()
    test_validate_skips_when_executable_is_missing()
    test_validate_passes_when_external_command_returns_zero()
    test_validate_fails_when_external_command_returns_nonzero()
    test_validate_supports_path_placeholder()
    test_require_external_validation_allows_skipped_validation()
    test_require_external_validation_raises_on_failure()

    print("All external AIGER validator tests passed.")


if __name__ == "__main__":
    run_tests()
