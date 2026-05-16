import subprocess
import sys


TEST_COMMANDS = [
    ["tests/tests.py"],
    ["tests/tests_regex.py"],
    ["tests/tests_sequential.py"],
    ["tests/tests_intersection.py"],
    ["tests/tests_sequential_intersection.py"],
    ["tests/tests_cli.py"],
    ["tests/tests_evaluation.py"],
    ["tests/tests_nfa_product.py"],
]


def run_test(command: list[str]) -> bool:
    full_command = [sys.executable] + command

    print("=" * 60)
    print("Running:", " ".join(full_command))
    print("=" * 60)

    result = subprocess.run(full_command)

    if result.returncode != 0:
        print("\nFAILED:", " ".join(command))
        return False

    print("\nPASSED:", " ".join(command))
    return True


def main() -> int:
    all_passed = True

    for command in TEST_COMMANDS:
        if not run_test(command):
            all_passed = False
            break

    print("=" * 60)

    if all_passed:
        print("All tests passed.")
        return 0

    print("Some tests failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
