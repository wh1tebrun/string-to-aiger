import argparse
import os
import subprocess
import sys
from dataclasses import dataclass


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")
LOG_DIR = os.path.join(OUTPUT_DIR, "meeting_demo_logs")
REPORT_PATH = os.path.join(OUTPUT_DIR, "meeting_demo_report.md")


@dataclass(frozen=True)
class DemoCommand:
    title: str
    command: list[str]
    generated_files: tuple[str, ...] = ()


@dataclass(frozen=True)
class DemoResult:
    title: str
    command: list[str]
    returncode: int
    log_path: str
    generated_files: tuple[str, ...]


MEETING_COMMANDS = [
    DemoCommand(
        title="Milestone 1 tests: fixed-string disjunction pipeline",
        command=[sys.executable, "tests/tests.py"],
    ),
    DemoCommand(
        title="Milestone 2 tests: regex parser, NFA, bounded AIGER output",
        command=[sys.executable, "tests/tests_regex.py"],
    ),
    DemoCommand(
        title="Milestone 2 tests: sequential backend",
        command=[sys.executable, "tests/tests_sequential.py"],
    ),
    DemoCommand(
        title="Milestone 3 tests: bounded intersection",
        command=[sys.executable, "tests/tests_intersection.py"],
    ),
    DemoCommand(
        title="Milestone 3 tests: sequential intersection",
        command=[sys.executable, "tests/tests_sequential_intersection.py"],
    ),
    DemoCommand(
        title="Milestone 3 tests: product automaton construction",
        command=[sys.executable, "tests/tests_nfa_product.py"],
    ),
    DemoCommand(
        title="Milestone 3 tests: product backend compilation",
        command=[sys.executable, "tests/tests_product_backend.py"],
    ),
    DemoCommand(
        title="Regex parser demo: expression to regex AST",
        command=[sys.executable, "demos/regex_parser_demo.py"],
    ),
    DemoCommand(
        title="NFA demo: regex AST to NFA",
        command=[sys.executable, "scripts/meeting_nfa_demo.py"],
    ),
    DemoCommand(
        title="NFA evaluator demo: direct language behavior check",
        command=[sys.executable, "demos/nfa_evaluator_demo.py"],
    ),
    DemoCommand(
        title="Bounded AIGER demo: regex to bounded ASCII AIGER",
        command=[sys.executable, "demos/regex_to_aiger_demo.py"],
    ),
    DemoCommand(
        title="Milestone 3 demo: bounded regex intersection",
        command=[sys.executable, "demos/regex_intersection_demo.py"],
    ),
    DemoCommand(
        title="Milestone 3 demo: sequential regex intersection",
        command=[sys.executable, "demos/sequential_intersection_demo.py"],
    ),
    DemoCommand(
        title="CLI bounded example: a* with bound 3",
        command=[
            sys.executable,
            "-m",
            "string_to_aiger",
            "--pattern",
            "a*",
            "--backend",
            "bounded",
            "--bound",
            "3",
            "--output",
            os.path.join("outputs", "meeting_demo_astar_bounded.aag"),
        ],
        generated_files=("outputs/meeting_demo_astar_bounded.aag",),
    ),
    DemoCommand(
        title="CLI sequential example: a* with latch-based backend",
        command=[
            sys.executable,
            "-m",
            "string_to_aiger",
            "--pattern",
            "a*",
            "--backend",
            "sequential",
            "--output",
            os.path.join("outputs", "meeting_demo_astar_sequential.aag"),
        ],
        generated_files=("outputs/meeting_demo_astar_sequential.aag",),
    ),
    DemoCommand(
        title="CLI bounded example: (ab)* with bound 6",
        command=[
            sys.executable,
            "-m",
            "string_to_aiger",
            "--pattern",
            "(ab)*",
            "--backend",
            "bounded",
            "--bound",
            "6",
            "--output",
            os.path.join("outputs", "meeting_demo_abstar_bounded.aag"),
        ],
        generated_files=("outputs/meeting_demo_abstar_bounded.aag",),
    ),
    DemoCommand(
        title="CLI bounded structural intersection: (a|b)*&a*",
        command=[
            sys.executable,
            "-m",
            "string_to_aiger",
            "--pattern",
            "(a|b)*&a*",
            "--backend",
            "bounded",
            "--intersection-strategy",
            "structural",
            "--bound",
            "4",
            "--output",
            os.path.join(
                "outputs",
                "meeting_demo_intersection_bounded_structural.aag",
            ),
        ],
        generated_files=(
            "outputs/meeting_demo_intersection_bounded_structural.aag",
        ),
    ),
    DemoCommand(
        title="CLI bounded product intersection: (a|b)*&a*",
        command=[
            sys.executable,
            "-m",
            "string_to_aiger",
            "--pattern",
            "(a|b)*&a*",
            "--backend",
            "bounded",
            "--intersection-strategy",
            "product",
            "--bound",
            "4",
            "--output",
            os.path.join(
                "outputs",
                "meeting_demo_intersection_bounded_product.aag",
            ),
        ],
        generated_files=(
            "outputs/meeting_demo_intersection_bounded_product.aag",
        ),
    ),
    DemoCommand(
        title="CLI sequential structural intersection: (a|b)*&a*",
        command=[
            sys.executable,
            "-m",
            "string_to_aiger",
            "--pattern",
            "(a|b)*&a*",
            "--backend",
            "sequential",
            "--intersection-strategy",
            "structural",
            "--output",
            os.path.join(
                "outputs",
                "meeting_demo_intersection_sequential_structural.aag",
            ),
        ],
        generated_files=(
            "outputs/meeting_demo_intersection_sequential_structural.aag",
        ),
    ),
    DemoCommand(
        title="CLI sequential product intersection: (a|b)*&a*",
        command=[
            sys.executable,
            "-m",
            "string_to_aiger",
            "--pattern",
            "(a|b)*&a*",
            "--backend",
            "sequential",
            "--intersection-strategy",
            "product",
            "--output",
            os.path.join(
                "outputs",
                "meeting_demo_intersection_sequential_product.aag",
            ),
        ],
        generated_files=(
            "outputs/meeting_demo_intersection_sequential_product.aag",
        ),
    ),
]


def ensure_directories() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)


def safe_filename(title: str) -> str:
    chars = []

    for ch in title.lower():
        if ch.isalnum():
            chars.append(ch)
        elif ch in (" ", "-", "_"):
            chars.append("_")

    filename = "".join(chars)

    while "__" in filename:
        filename = filename.replace("__", "_")

    return filename.strip("_") + ".log"


def relative(path: str) -> str:
    return os.path.relpath(path, ROOT_DIR).replace(os.sep, "/")


def command_text(command: list[str]) -> str:
    return " ".join(command)


def read_aiger_header(relative_path: str) -> str:
    path = os.path.join(ROOT_DIR, relative_path)

    if not os.path.exists(path):
        return "missing"

    with open(path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()

    if not first_line:
        return "empty file"

    return first_line


def run_demo_command(entry: DemoCommand, verbose: bool) -> DemoResult:
    log_path = os.path.join(LOG_DIR, safe_filename(entry.title))

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    completed = subprocess.run(
        entry.command,
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("TITLE\n")
        f.write(entry.title)
        f.write("\n\nCOMMAND\n")
        f.write(command_text(entry.command))
        f.write("\n\nRETURN CODE\n")
        f.write(str(completed.returncode))
        f.write("\n\nSTDOUT\n")
        f.write(completed.stdout)
        f.write("\n\nSTDERR\n")
        f.write(completed.stderr)

    status = "PASS" if completed.returncode == 0 else "FAIL"
    print(f"[{status}] {entry.title}")

    if verbose:
        print()
        print(completed.stdout)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)

    return DemoResult(
        title=entry.title,
        command=entry.command,
        returncode=completed.returncode,
        log_path=log_path,
        generated_files=entry.generated_files,
    )


def write_report(results: list[DemoResult]) -> None:
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Meeting demo report\n\n")

        f.write(
            "This report summarizes the Milestone 1, Milestone 2, "
            "and Milestone 3 meeting demo.\n\n"
        )

        f.write("The focus is:\n\n")
        f.write("```text\n")
        f.write("Milestone 1: fixed-string disjunctions -> AIGER\n")
        f.write("Milestone 2: regex / Kleene star -> AST -> NFA -> AIGER\n")
        f.write("Milestone 3: regex conjunction / intersection -> bounded or sequential AIGER\n")
        f.write("```\n\n")

        f.write("---\n\n")
        f.write("## Summary\n\n")

        total = len(results)
        passed = sum(1 for result in results if result.returncode == 0)
        failed = total - passed

        f.write("| Metric | Value |\n")
        f.write("|---|---|\n")
        f.write(f"| Total commands | {total} |\n")
        f.write(f"| Passed | {passed} |\n")
        f.write(f"| Failed | {failed} |\n\n")

        f.write("---\n\n")
        f.write("## Commands\n\n")

        f.write("| Status | Demo step | Command | Log |\n")
        f.write("|---|---|---|---|\n")

        for result in results:
            status = "PASS" if result.returncode == 0 else "FAIL"
            log_path = relative(result.log_path)
            command = command_text(result.command).replace("|", "\\|")
            title = result.title.replace("|", "\\|")

            f.write(
                f"| {status} | {title} | `{command}` | `{log_path}` |\n"
            )

        f.write("\n---\n\n")
        f.write("## Generated AIGER files\n\n")

        generated_any = any(result.generated_files for result in results)

        if not generated_any:
            f.write("No generated AIGER files were registered for this demo.\n\n")
        else:
            f.write("| File | AIGER header |\n")
            f.write("|---|---|\n")

            for result in results:
                for generated_file in result.generated_files:
                    header = read_aiger_header(generated_file)
                    f.write(f"| `{generated_file}` | `{header}` |\n")

            f.write("\n")

        f.write("---\n\n")
        f.write("## How to present this report\n\n")
        f.write("Suggested meeting flow:\n\n")
        f.write("```text\n")
        f.write("1. Open docs/meeting_demo.md for the explanation.\n")
        f.write("2. Run python scripts/run_meeting_demo.py.\n")
        f.write("3. Open outputs/meeting_demo_report.md.\n")
        f.write("4. Show the PASS summary and generated AIGER headers.\n")
        f.write("5. For Milestone 3, compare structural and product intersection outputs.\n")
        f.write("6. Open one generated .aag file if the professor wants to inspect the raw output.\n")
        f.write("```\n\n")

        f.write("---\n\n")
        f.write("## Notes\n\n")
        f.write("- Full command outputs are stored in `outputs/meeting_demo_logs/`.\n")
        f.write("- The terminal output is intentionally compact to avoid scrolling during the meeting.\n")
        f.write("- The detailed explanation is in `docs/meeting_demo.md`.\n")
        f.write("- Milestone 3 demonstrates both structural and product-based intersection compilation.\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a compact meeting demo for Milestone 1, "
            "Milestone 2, and Milestone 3."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full command output to the terminal.",
    )
    args = parser.parse_args()

    ensure_directories()

    print("=" * 80)
    print("string-to-aiger meeting demo")
    print("=" * 80)
    print("Focus:")
    print("- Milestone 1: fixed-string disjunctions -> AIGER")
    print("- Milestone 2: regex / Kleene star -> AST -> NFA -> AIGER")
    print("- Milestone 3: regex conjunction / intersection")
    print()
    print("Running compact demo. Full logs will be written to:")
    print(relative(LOG_DIR))
    print()

    results: list[DemoResult] = []

    for entry in MEETING_COMMANDS:
        result = run_demo_command(entry, verbose=args.verbose)
        results.append(result)

        if result.returncode != 0:
            break

    write_report(results)

    print()
    print("=" * 80)
    print("Report written to:", relative(REPORT_PATH))

    failed = [
        result
        for result in results
        if result.returncode != 0
    ]

    if failed:
        print("Meeting demo failed.")
        print("=" * 80)
        return 1

    print("Meeting demo completed successfully.")
    print("Open this file in VS Code:")
    print(relative(REPORT_PATH))
    print("=" * 80)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
