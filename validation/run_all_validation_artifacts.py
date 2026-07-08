import subprocess
import sys


VALIDATION_SCRIPTS = [
    "validation/generate_validation_artifacts.py",
    "validation/generate_model_checking_artifacts.py",
    "validation/generate_sequential_model_checking_artifacts.py",
    "validation/generate_bounded_reference_equivalence_artifacts.py",
    "validation/generate_manual_aigsim_checks.py",
]

_ENV_HELP = """\
Required environment variables:
  export AIGER_TOOLS=/path/to/aiger
  export AIGSIM=/path/to/aiger/aigsim"""


def run_script(script: str) -> bool:
    command = [sys.executable, script]

    print("=" * 60)
    print("Running:", " ".join(command))
    print("=" * 60)

    result = subprocess.run(command)

    if result.returncode != 0:
        print("\nFAILED:", script)
        return False

    print("\nPASSED:", script)
    return True


def main() -> int:
    print("Regenerating all validation artifacts.")
    print()
    print(_ENV_HELP)
    print()

    for script in VALIDATION_SCRIPTS:
        if not run_script(script):
            print("=" * 60)
            print("Artifact generation failed.")
            print()
            print(_ENV_HELP)
            return 1

    print("=" * 60)
    print("All validation artifacts regenerated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
