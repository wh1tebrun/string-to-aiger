import os
import sys
import tempfile

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_DIR)

from string_to_aiger.aiger.aiger_pipeline import validate_and_write_aiger, write_aiger_without_validation  # noqa: E402
from string_to_aiger.regex.regex_bounded_compiler import compile_regex_bounded  # noqa: E402
from string_to_aiger.aiger.aiger import compile_expr_to_aiger  # noqa: E402


def compile_sample_aiger() -> str:
    expr = compile_regex_bounded("a*", bound=3)
    return compile_expr_to_aiger(expr)


def assert_lf_bytes(path: str, expected_text: str) -> None:
    with open(path, "rb") as f:
        written = f.read()

    assert written == expected_text.encode("utf-8")
    assert b"\r" not in written
    assert b"\n" in written
    assert written.endswith(b"\n")
    assert not written.endswith(b"\n\n")


def test_validate_and_write_aiger_writes_valid_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "valid.aag")
        aiger_text = compile_sample_aiger()

        header = validate_and_write_aiger(output_path, aiger_text)

        assert header.outputs == 1
        assert os.path.exists(output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            written = f.read()

        assert written == aiger_text


def test_validate_and_write_aiger_writes_lf_bytes():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "valid_lf.aag")
        aiger_text = compile_sample_aiger()

        validate_and_write_aiger(output_path, aiger_text)

        assert_lf_bytes(output_path, aiger_text)


def test_validate_and_write_aiger_creates_parent_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "nested", "valid.aag")
        aiger_text = compile_sample_aiger()

        validate_and_write_aiger(output_path, aiger_text)

        assert os.path.exists(output_path)


def test_validate_and_write_aiger_rejects_invalid_text():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "invalid.aag")

        try:
            validate_and_write_aiger(output_path, "not a valid aiger")
            assert False, "Expected ValueError for invalid AIGER text"
        except ValueError:
            pass

        assert not os.path.exists(output_path)


def test_write_aiger_without_validation_allows_raw_text():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "raw.aag")
        raw_text = "not a valid aiger"

        write_aiger_without_validation(output_path, raw_text)

        assert os.path.exists(output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            written = f.read()

        assert written == raw_text


def test_write_aiger_without_validation_writes_lf_bytes():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "raw_lf.aag")
        raw_text = "not a valid aiger\nsecond line\n"

        write_aiger_without_validation(output_path, raw_text)

        assert_lf_bytes(output_path, raw_text)


def run_tests():
    test_validate_and_write_aiger_writes_valid_file()
    test_validate_and_write_aiger_writes_lf_bytes()
    test_validate_and_write_aiger_creates_parent_directory()
    test_validate_and_write_aiger_rejects_invalid_text()
    test_write_aiger_without_validation_allows_raw_text()
    test_write_aiger_without_validation_writes_lf_bytes()

    print("All AIGER pipeline tests passed.")


if __name__ == "__main__":
    run_tests()
