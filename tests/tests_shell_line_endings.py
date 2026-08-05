from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def shell_scripts() -> list[Path]:
    return sorted(
        path
        for path in ROOT_DIR.rglob("*.sh")
        if ".git" not in path.parts
    )


def test_shell_scripts_use_lf_line_endings() -> None:
    scripts = shell_scripts()
    assert scripts, "No shell scripts found"

    files_with_carriage_returns = [
        str(path.relative_to(ROOT_DIR))
        for path in scripts
        if b"\r" in path.read_bytes()
    ]

    assert not files_with_carriage_returns, (
        "Shell scripts must use LF line endings: "
        + ", ".join(files_with_carriage_returns)
    )


def test_gitattributes_enforces_lf_for_shell_scripts() -> None:
    attributes = (ROOT_DIR / ".gitattributes").read_text(encoding="utf-8")
    assert "*.sh text eol=lf" in attributes.splitlines()


def run_tests() -> None:
    test_shell_scripts_use_lf_line_endings()
    test_gitattributes_enforces_lf_for_shell_scripts()
    print("All shell line-ending tests passed.")


if __name__ == "__main__":
    run_tests()
