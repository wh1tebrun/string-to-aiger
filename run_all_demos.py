import subprocess
import sys


DEMO_COMMANDS = [
    ["main.py"],
    ["demos/regex_parser_demo.py"],
    ["demos/nfa_demo.py"],
    ["demos/nfa_evaluator_demo.py"],
    ["demos/bounded_nfa_demo.py"],
    ["demos/regex_to_aiger_demo.py"],
    ["demos/sequential_astar_demo.py"],
    ["demos/sequential_astar_sim_demo.py"],
    ["demos/nfa_to_sequential_demo.py"],
    ["demos/regex_intersection_demo.py"],
    ["demos/sequential_intersection_demo.py"],
]


def run_demo(command: list[str]) -> bool:
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

    for command in DEMO_COMMANDS:
        if not run_demo(command):
            all_passed = False
            break

    print("=" * 60)

    if all_passed:
        print("All demos completed successfully.")
        return 0

    print("Some demos failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
