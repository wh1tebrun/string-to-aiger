import os
import subprocess
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


MEETING_COMMANDS = [
    {
        "title": "Milestone 1 tests: fixed-string disjunction pipeline",
        "command": [sys.executable, "tests/tests.py"],
    },
    {
        "title": "Milestone 2 tests: regex parser, NFA, bounded AIGER output",
        "command": [sys.executable, "tests/tests_regex.py"],
    },
    {
        "title": "Regex parser demo: expression to regex AST",
        "command": [sys.executable, "demos/regex_parser_demo.py"],
    },
    {
        "title": "NFA demo: regex AST to NFA",
        "command": [sys.executable, "demos/nfa_demo.py"],
    },
    {
        "title": "NFA evaluator demo: direct language behavior check",
        "command": [sys.executable, "demos/nfa_evaluator_demo.py"],
    },
    {
        "title": "Bounded AIGER demo: regex to bounded ASCII AIGER",
        "command": [sys.executable, "demos/regex_to_aiger_demo.py"],
    },
    {
        "title": "CLI bounded example: a* with bound 3",
        "command": [
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
    },
    {
        "title": "CLI sequential example: a* with latch-based backend",
        "command": [
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
    },
    {
        "title": "CLI bounded example: (ab)* with bound 6",
        "command": [
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
    },
]


def run_command(title: str, command: list[str]) -> bool:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print("Running:", " ".join(command))
    print()

    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
    )

    if result.returncode != 0:
        print()
        print("FAILED:", title)
        print("Command:", " ".join(command))
        print("Return code:", result.returncode)
        return False

    print()
    print("PASSED:", title)
    return True


def main() -> int:
    print("=" * 80)
    print("string-to-aiger meeting demo")
    print("=" * 80)
    print()
    print("Focus:")
    print("- Milestone 1: fixed-string disjunctions -> AIGER")
    print("- Milestone 2: regex / Kleene star -> AST -> NFA -> AIGER")
    print()

    all_passed = True

    for entry in MEETING_COMMANDS:
        if not run_command(entry["title"], entry["command"]):
            all_passed = False
            break

    print()
    print("=" * 80)

    if all_passed:
        print("Meeting demo completed successfully.")
        print()
        print("Generated demo outputs:")
        print("- outputs/meeting_demo_astar_bounded.aag")
        print("- outputs/meeting_demo_astar_sequential.aag")
        print("- outputs/meeting_demo_abstar_bounded.aag")
        print("=" * 80)
        return 0

    print("Meeting demo failed.")
    print("=" * 80)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
