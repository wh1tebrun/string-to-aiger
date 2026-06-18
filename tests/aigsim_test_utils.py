import os
from pathlib import Path


AIGSIM_ENV_VAR = "AIGSIM"


def require_aigsim() -> str:
    """Return the configured aigsim path.

    External semantic validation tests must not silently pass when aigsim is
    unavailable. These tests check generated AIGER files by actually invoking
    aigsim, so missing aigsim is a test setup error.

    Example:

        export AIGSIM=/home/egetekin/tools/aiger/aigsim
    """
    aigsim = os.environ.get(AIGSIM_ENV_VAR)

    if not aigsim:
        raise AssertionError(
            "AIGSIM environment variable is not set. "
            "Set it before running external semantic tests, for example: "
            "export AIGSIM=/home/egetekin/tools/aiger/aigsim"
        )

    if not Path(aigsim).exists():
        raise AssertionError(f"AIGSIM does not exist: {aigsim}")

    return aigsim
