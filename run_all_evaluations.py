import subprocess
import sys


EVALUATION_COMMANDS = [
    ["evaluation/evaluate_aiger_stats.py"],
    ["evaluation/evaluate_language_behavior.py"],
    ["evaluation/evaluate_exhaustive_behavior.py"],
]


def run_evaluation(command: list[str]) -> bool:
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

    for command in EVALUATION_COMMANDS:
        if not run_evaluation(command):
            all_passed = False
            break

    print("=" * 60)

    if all_passed:
        print("All evaluations completed successfully.")
        return 0

    print("Some evaluations failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
