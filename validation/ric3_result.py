from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Sequence


RESULT_LINE = re.compile(r"^(SAT|UNSAT)$")


class Ric3ResultError(RuntimeError):
    """Raised when rIC3 output does not contain one unambiguous result."""


class Ric3CommandError(RuntimeError):
    """Raised when the rIC3 command itself exits unsuccessfully."""

    def __init__(self, returncode: int):
        super().__init__(f"rIC3 command exited with status {returncode}")
        self.returncode = returncode


def _result_markers(stream_name: str, text: str) -> list[tuple[str, str]]:
    markers: list[tuple[str, str]] = []

    for line in text.splitlines():
        stripped = line.strip()

        if RESULT_LINE.fullmatch(stripped):
            markers.append((stream_name, stripped))

    return markers


def parse_ric3_result(stdout: str, stderr: str) -> str:
    """Return the sole exact SAT/UNSAT marker across both captured streams."""
    markers = _result_markers("stdout", stdout) + _result_markers("stderr", stderr)

    if not markers:
        raise Ric3ResultError("rIC3 output contains no exact SAT or UNSAT result line")

    if len(markers) != 1:
        rendered = ", ".join(f"{stream}:{result}" for stream, result in markers)
        raise Ric3ResultError(
            f"rIC3 output contains multiple or conflicting result lines: {rendered}"
        )

    return markers[0][1]


def _write_log(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(text)


def run_ric3_command(
    command: Sequence[str],
    stdout_log: Path,
    stderr_log: Path,
) -> str:
    """Run rIC3, retain both raw streams, and return one strict result marker."""
    completed = subprocess.run(
        list(command),
        check=False,
        text=True,
        capture_output=True,
    )

    _write_log(stdout_log, completed.stdout)
    _write_log(stderr_log, completed.stderr)

    sys.stdout.write(completed.stdout)
    sys.stdout.flush()
    sys.stderr.write(completed.stderr)
    sys.stderr.flush()

    if completed.returncode != 0:
        raise Ric3CommandError(completed.returncode)

    return parse_ric3_result(completed.stdout, completed.stderr)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run rIC3 with separated raw logs and strict result parsing."
    )
    parser.add_argument("--stdout-log", type=Path, required=True)
    parser.add_argument("--stderr-log", type=Path, required=True)
    parser.add_argument("--result-file", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    command = list(args.command)

    if command and command[0] == "--":
        command = command[1:]

    if not command:
        print("ERROR: no rIC3 command was provided", file=sys.stderr)
        return 2

    try:
        result = run_ric3_command(command, args.stdout_log, args.stderr_log)
    except Ric3CommandError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return error.returncode if 1 <= error.returncode <= 125 else 1
    except Ric3ResultError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    _write_log(args.result_file, result + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
