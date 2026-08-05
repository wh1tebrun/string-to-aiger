from __future__ import annotations

import csv
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter
from string_to_aiger.sequential.sequential_regex_compiler import (
    compile_regex_to_sequential,
)


AIGSIM = Path(os.environ.get("AIGSIM", "/path/to/aiger/aigsim"))

ARTIFACT_ROOT = ROOT / "artifacts" / "manual_aigsim_checks"
AIGER_DIR = ARTIFACT_ROOT / "aiger"
STIMULUS_DIR = ARTIFACT_ROOT / "stimuli"
OUTPUT_DIR = ARTIFACT_ROOT / "outputs"


@dataclass(frozen=True)
class AigsimExecution:
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    actual_output: str
    execution_valid: bool
    execution_error: str


def write_lf_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(content)


def ensure_dirs() -> None:
    for directory in [AIGER_DIR, STIMULUS_DIR, OUTPUT_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def require_tools() -> None:
    if not AIGSIM.is_file() or not os.access(AIGSIM, os.X_OK):
        raise AssertionError(
            "aigsim not found or not executable. Set AIGSIM explicitly, for example:\n"
            "export AIGSIM=/path/to/aiger/aigsim"
        )


def parse_aiger_header(aag_text: str) -> tuple[int, int, int, int, int]:
    first_line = aag_text.splitlines()[0]
    parts = first_line.split()

    if len(parts) != 6 or parts[0] != "aag":
        raise AssertionError(f"Invalid AIGER header: {first_line}")

    return tuple(int(value) for value in parts[1:])  # type: ignore[return-value]


def parse_input_symbols(aag_text: str) -> list[str]:
    _max_var, num_inputs, _num_latches, _num_outputs, _num_ands = (
        parse_aiger_header(aag_text)
    )
    symbols = [f"input_{index}" for index in range(num_inputs)]

    for line in aag_text.splitlines():
        line = line.strip()

        if not line.startswith("i"):
            continue

        parts = line.split(maxsplit=1)

        if len(parts) != 2:
            continue

        index_text, symbol = parts

        if index_text[1:].isdigit():
            index = int(index_text[1:])

            if index < num_inputs:
                symbols[index] = symbol

    return symbols


def force_first_output_false(aag_text: str) -> str:
    _max_var, num_inputs, num_latches, num_outputs, _num_ands = (
        parse_aiger_header(aag_text)
    )

    if num_outputs < 1:
        raise AssertionError("Cannot corrupt AIGER without outputs")

    lines = aag_text.splitlines()
    first_output_index = 1 + num_inputs + num_latches
    lines[first_output_index] = "0"

    return "\n".join(lines) + "\n"


def make_bounded_stimulus(aag_text: str, word: str) -> str:
    inputs = parse_input_symbols(aag_text)
    bits: list[str] = []

    for symbol in inputs:
        if symbol == f"len_is_{len(word)}":
            bits.append("1")
        elif symbol.startswith("len_is_"):
            bits.append("0")
        elif symbol.startswith("x_"):
            parts = symbol.split("_")

            if len(parts) >= 4 and parts[1].isdigit() and parts[2] == "is":
                position = int(parts[1])
                char = "_".join(parts[3:])

                if position < len(word) and word[position] == char:
                    bits.append("1")
                else:
                    bits.append("0")
            else:
                bits.append("0")
        else:
            bits.append("0")

    return "".join(bits) + "\n.\n"


def make_sequential_stimulus(aag_text: str, word: str) -> str:
    """Encode one character per step, followed by a final end step.

    The empty word is therefore represented by the end step alone.
    """
    inputs = parse_input_symbols(aag_text)
    lines: list[str] = []

    for char in word:
        bits: list[str] = []

        for symbol in inputs:
            if symbol == "end":
                bits.append("0")
            elif symbol == f"is_{char}":
                bits.append("1")
            else:
                bits.append("0")

        lines.append("".join(bits))

    final_bits = ["1" if symbol == "end" else "0" for symbol in inputs]
    lines.append("".join(final_bits))

    return "\n".join([*lines, "."]) + "\n"


def read_stimulus(path: Path, num_inputs: int) -> tuple[str, list[str]]:
    stimulus_bytes = path.read_bytes()

    if b"\r" in stimulus_bytes:
        raise AssertionError(f"Stimulus contains a carriage return: {path}")

    try:
        stimulus = stimulus_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AssertionError(f"Stimulus is not valid UTF-8: {path}") from error

    if not stimulus.endswith(".\n"):
        raise AssertionError(
            f"Stimulus must end with a standalone '.' line and one LF: {path}"
        )

    lines = stimulus[:-1].split("\n")

    if lines.count(".") != 1 or lines[-1] != ".":
        raise AssertionError(f"Stimulus must contain exactly one final terminator: {path}")

    vectors = lines[:-1]

    if not vectors:
        raise AssertionError(f"Stimulus contains no semantic input vectors: {path}")

    for vector in vectors:
        if len(vector) != num_inputs or re.fullmatch(r"[01]+", vector) is None:
            raise AssertionError(
                f"Malformed {num_inputs}-bit stimulus vector {vector!r}: {path}"
            )

    return stimulus, vectors


def parse_aigsim_output(
    stdout: str,
    vectors: list[str],
    num_inputs: int,
    num_latches: int,
) -> str:
    if "\r" in stdout:
        raise ValueError("aigsim stdout contains a carriage return")

    semantic_lines: list[str] = []
    witness_seen = False

    for raw_line in stdout.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if re.fullmatch(r"Trace is a witness for: \{[^}]*\}", line):
            if witness_seen:
                raise ValueError("aigsim stdout contains duplicate witness summaries")
            witness_seen = True
            continue

        if witness_seen:
            raise ValueError("aigsim stdout contains output after its witness summary")

        semantic_lines.append(line)

    if len(semantic_lines) != len(vectors):
        raise ValueError(
            "aigsim output-line count does not match stimulus vectors: "
            f"expected {len(vectors)}, got {len(semantic_lines)}"
        )

    outputs: list[str] = []

    for index, (line, vector) in enumerate(zip(semantic_lines, vectors), start=1):
        parts = line.split()

        if num_latches > 0:
            valid = (
                len(parts) == 4
                and len(parts[0]) == num_latches
                and re.fullmatch(r"[01]+", parts[0]) is not None
                and parts[1] == vector
                and len(parts[1]) == num_inputs
                and parts[2] in {"0", "1"}
                and len(parts[3]) == num_latches
                and re.fullmatch(r"[01]+", parts[3]) is not None
            )
            output_index = 2
        else:
            valid = (
                len(parts) == 2
                and parts[0] == vector
                and len(parts[0]) == num_inputs
                and parts[1] in {"0", "1"}
            )
            output_index = 1

        if not valid:
            raise ValueError(f"malformed or conflicting aigsim output line {index}: {line!r}")

        outputs.append(parts[output_index])

    return outputs[-1]


def run_aigsim(
    aag_path: Path,
    stimulus_path: Path,
    command_prefix: Sequence[str] | None = None,
) -> AigsimExecution:
    aag_text = aag_path.read_text(encoding="utf-8")
    _max_var, num_inputs, num_latches, num_outputs, _num_ands = (
        parse_aiger_header(aag_text)
    )

    if num_outputs != 1:
        raise AssertionError(f"Manual check requires exactly one AIGER output: {aag_path}")

    stimulus, vectors = read_stimulus(stimulus_path, num_inputs)
    prefix = list(command_prefix) if command_prefix is not None else [str(AIGSIM)]
    command = tuple([*prefix, artifact_relative(aag_path)])

    result = subprocess.run(
        list(command),
        cwd=ROOT,
        input=stimulus,
        text=True,
        capture_output=True,
        check=False,
    )

    errors: list[str] = []

    if result.returncode != 0:
        errors.append(f"aigsim exited with status {result.returncode}")

    if result.stderr:
        errors.append("aigsim stderr was not empty")

    try:
        actual_output = parse_aigsim_output(
            result.stdout,
            vectors,
            num_inputs,
            num_latches,
        )
    except ValueError as error:
        actual_output = ""
        errors.append(str(error))

    return AigsimExecution(
        command=command,
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        actual_output=actual_output,
        execution_valid=not errors,
        execution_error="; ".join(errors),
    )


def write_output_file(
    path: Path,
    command: str,
    stimulus: str,
    execution: AigsimExecution,
    expected_semantic_output: str,
    matches_expected_semantics: str,
    mismatch_detected: str,
    verdict: str,
    note: str,
) -> None:
    content = (
        f"# {path.name}\n\n"
        f"Command:\n{command}\n\n"
        f"Exit code:\n{execution.exit_code}\n\n"
        f"Execution valid:\n{'YES' if execution.execution_valid else 'NO'}\n\n"
        f"Execution error:\n{execution.execution_error}\n\n"
        f"Stimulus:\n{stimulus}\n"
        f"stdout:\n{execution.stdout}\n"
        f"stderr:\n{execution.stderr}\n"
        f"Expected semantic output:\n{expected_semantic_output}\n\n"
        f"Actual output:\n{execution.actual_output}\n\n"
        f"Matches expected semantics:\n{matches_expected_semantics}\n\n"
        f"Mismatch detected:\n{mismatch_detected}\n\n"
        f"Final verdict:\n{verdict}\n\n"
        f"Note:\n{note}\n"
    )

    write_lf_text(path, content)


def artifact_relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def clean_markdown(value: object) -> str:
    text = str(value)
    text = text.replace("\n", "<br>")
    text = text.replace("|", "\\|")
    return text


def make_markdown_table(headers: list[str], rows: list[dict[str, object]]) -> str:
    lines: list[str] = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")

    for row in rows:
        lines.append(
            "| "
            + " | ".join(clean_markdown(row.get(header, "")) for header in headers)
            + " |"
        )

    return "\n".join(lines) + "\n"


def evaluate_execution(
    execution: AigsimExecution,
    expected_semantic_output: str,
    should_match_semantics: bool,
) -> tuple[str, str, str]:
    if expected_semantic_output not in {"0", "1"}:
        raise AssertionError(
            f"Expected semantic output must be Boolean: {expected_semantic_output!r}"
        )

    if not should_match_semantics and expected_semantic_output != "1":
        raise AssertionError(
            "Negative controls require a reference-semantics accepting witness"
        )

    if not execution.execution_valid:
        return "N/A", "NO", "EXECUTION FAILED"

    matches_expected = execution.actual_output == expected_semantic_output
    matches_text = "YES" if matches_expected else "NO"
    mismatch_text = "NO" if matches_expected else "YES"

    if should_match_semantics:
        verdict = "OK" if matches_expected else "UNEXPECTED"
    else:
        verdict = "UNEXPECTED" if matches_expected else "MISMATCH DETECTED"

    return matches_text, mismatch_text, verdict


def generate_bounded_files() -> tuple[Path, Path, dict[str, Path]]:
    correct_aag = compile_regex_to_aiger("ab|bc", 2)

    correct_path = AIGER_DIR / "bounded_ab_or_bc_correct.aag"
    corrupted_path = AIGER_DIR / "bounded_ab_or_bc_output_forced_false.aag"

    correct_path.write_text(correct_aag, encoding="utf-8")
    corrupted_path.write_text(force_first_output_false(correct_aag), encoding="utf-8")

    stimuli = {
        "accept_ab": STIMULUS_DIR / "bounded_accept_ab.stim",
        "reject_ac": STIMULUS_DIR / "bounded_reject_ac.stim",
    }

    write_lf_text(stimuli["accept_ab"], make_bounded_stimulus(correct_aag, "ab"))
    write_lf_text(stimuli["reject_ac"], make_bounded_stimulus(correct_aag, "ac"))

    return correct_path, corrupted_path, stimuli


def generate_sequential_files() -> tuple[Path, Path, dict[str, Path]]:
    circuit = compile_regex_to_sequential("(bc)*")
    correct_aag = SequentialAigerWriter(circuit).write()

    correct_path = AIGER_DIR / "sequential_bc_star_correct.aag"
    corrupted_path = AIGER_DIR / "sequential_bc_star_output_forced_false.aag"

    correct_path.write_text(correct_aag, encoding="utf-8")
    corrupted_path.write_text(force_first_output_false(correct_aag), encoding="utf-8")

    stimuli = {
        "accept_empty": STIMULUS_DIR / "sequential_accept_empty.stim",
        "accept_bc": STIMULUS_DIR / "sequential_accept_bc.stim",
        "accept_bcbc": STIMULUS_DIR / "sequential_accept_bcbc.stim",
        "reject_b": STIMULUS_DIR / "sequential_reject_b.stim",
        "reject_bcb": STIMULUS_DIR / "sequential_reject_bcb.stim",
    }

    words = {
        "accept_empty": "",
        "accept_bc": "bc",
        "accept_bcbc": "bcbc",
        "reject_b": "b",
        "reject_bcb": "bcb",
    }

    for name, word in words.items():
        write_lf_text(stimuli[name], make_sequential_stimulus(correct_aag, word))

    return correct_path, corrupted_path, stimuli


def run_case(
    case_id: str,
    backend: str,
    pattern: str,
    description: str,
    aag_path: Path,
    stimulus_path: Path,
    word_or_trace: str,
    expected_semantic_output: str,
    should_match_semantics: bool,
    command_prefix: Sequence[str] | None = None,
) -> dict[str, object]:
    execution = run_aigsim(aag_path, stimulus_path, command_prefix)
    command = (
        f"$AIGSIM {shlex.quote(artifact_relative(aag_path))} "
        f"< {shlex.quote(artifact_relative(stimulus_path))}"
    )
    matches_expected, mismatch_detected, verdict = evaluate_execution(
        execution,
        expected_semantic_output,
        should_match_semantics,
    )

    output_path = OUTPUT_DIR / f"{case_id}_aigsim_output.txt"
    note = (
        "This is a direct manual aigsim check. "
        "For deliberately corrupted AIGERs, a mismatch is expected and useful."
    )

    write_output_file(
        output_path,
        command,
        stimulus_path.read_text(encoding="utf-8"),
        execution,
        expected_semantic_output,
        matches_expected,
        mismatch_detected,
        verdict,
        note,
    )

    return {
        "case_id": case_id,
        "backend": backend,
        "pattern": pattern,
        "description": description,
        "aag_file": artifact_relative(aag_path),
        "stimulus_file": artifact_relative(stimulus_path),
        "word_or_trace": word_or_trace,
        "aigsim_exit_code": execution.exit_code,
        "execution_valid": "YES" if execution.execution_valid else "NO",
        "stderr_empty": "YES" if not execution.stderr else "NO",
        "execution_error": execution.execution_error,
        "expected_semantic_output": expected_semantic_output,
        "aigsim_actual_output": execution.actual_output,
        "matches_expected_semantics": matches_expected,
        "mismatch_detected": mismatch_detected,
        "verdict": verdict,
        "manual_command": command,
        "captured_output_file": artifact_relative(output_path),
    }


def write_readme() -> None:
    content = """# Manual aigsim checks

This directory contains small, manually inspectable `aigsim` checks.

The main validation path is:

```text
AAG file + STIM file -> aigsim -> actual output
```

`aigsim` performs concrete simulation for the supplied stimulus trace. These
checks are intentionally small enough to inspect manually.

## Sequential trace family

The sequential example uses `(bc)*`, analogously to an `(ab)*` example. The
same generated sequential AIGER is simulated on traces of different lengths:

| word | stimulus meaning | expected output |
| --- | --- | --- |
| `<empty>` | `end` | 1 |
| `bc` | `b, c, end` | 1 |
| `bcbc` | `b, c, b, c, end` | 1 |
| `b` | `b, end` | 0 |
| `bcb` | `b, c, b, end` | 0 |

This demonstrates zero repetitions, one repetition, multiple repetitions, and
incomplete rejecting traces.

## Important terminology

`output_forced_false` means a deliberately modified AIGER used as a
negative-control example.

It is not a real compiler output. It is produced by taking a correct AIGER and
forcing its output literal to constant false. This should make accepting
witnesses fail, so the validation pipeline should detect a mismatch.

## How to read the table

For correct AIGER files:

```text
matches_expected_semantics = YES
```

For deliberately modified negative-control AIGER files:

```text
matches_expected_semantics = NO
mismatch_detected = YES
```

The useful result in a negative-control case is that the mismatch is visible
and detected.

## Re-run all manual examples

From the repository root:

```bash
export AIGSIM=/path/to/aiger/aigsim
bash scripts/demo_manual_aigsim_checks.sh
```

Individual examples can also be run directly:

```bash
$AIGSIM artifacts/manual_aigsim_checks/aiger/sequential_bc_star_correct.aag < artifacts/manual_aigsim_checks/stimuli/sequential_accept_bcbc.stim
$AIGSIM artifacts/manual_aigsim_checks/aiger/sequential_bc_star_output_forced_false.aag < artifacts/manual_aigsim_checks/stimuli/sequential_accept_bc.stim
```

The detailed file paths, commands, and captured stdout/stderr files are stored
in the CSV and in `artifacts/manual_aigsim_checks/outputs/`.
"""

    (ARTIFACT_ROOT / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    require_tools()
    ensure_dirs()

    bounded_correct, bounded_corrupted, bounded_stimuli = generate_bounded_files()
    sequential_correct, sequential_corrupted, sequential_stimuli = (
        generate_sequential_files()
    )

    rows = [
        run_case(
            "MAN001",
            "bounded",
            "ab|bc",
            "correct bounded AIGER accepts ab",
            bounded_correct,
            bounded_stimuli["accept_ab"],
            "ab",
            "1",
            True,
        ),
        run_case(
            "MAN002",
            "bounded",
            "ab|bc",
            "correct bounded AIGER rejects ac",
            bounded_correct,
            bounded_stimuli["reject_ac"],
            "ac",
            "0",
            True,
        ),
        run_case(
            "MAN003",
            "bounded negative control",
            "ab|bc",
            "output-forced-false AIGER disagrees on accepting witness ab",
            bounded_corrupted,
            bounded_stimuli["accept_ab"],
            "ab",
            "1",
            False,
        ),
        run_case(
            "MAN004",
            "sequential",
            "(bc)*",
            "correct sequential AIGER accepts the empty trace",
            sequential_correct,
            sequential_stimuli["accept_empty"],
            "<empty> -> end",
            "1",
            True,
        ),
        run_case(
            "MAN005",
            "sequential",
            "(bc)*",
            "correct sequential AIGER accepts one repetition",
            sequential_correct,
            sequential_stimuli["accept_bc"],
            "b, c, end",
            "1",
            True,
        ),
        run_case(
            "MAN006",
            "sequential",
            "(bc)*",
            "correct sequential AIGER accepts two repetitions",
            sequential_correct,
            sequential_stimuli["accept_bcbc"],
            "b, c, b, c, end",
            "1",
            True,
        ),
        run_case(
            "MAN007",
            "sequential",
            "(bc)*",
            "correct sequential AIGER rejects an incomplete repetition",
            sequential_correct,
            sequential_stimuli["reject_b"],
            "b, end",
            "0",
            True,
        ),
        run_case(
            "MAN008",
            "sequential",
            "(bc)*",
            "correct sequential AIGER rejects a longer incomplete repetition",
            sequential_correct,
            sequential_stimuli["reject_bcb"],
            "b, c, b, end",
            "0",
            True,
        ),
        run_case(
            "MAN009",
            "sequential negative control",
            "(bc)*",
            "output-forced-false AIGER disagrees on accepting trace bc",
            sequential_corrupted,
            sequential_stimuli["accept_bc"],
            "b, c, end",
            "1",
            False,
        ),
    ]

    headers = [
        "case_id",
        "backend",
        "pattern",
        "description",
        "aag_file",
        "stimulus_file",
        "word_or_trace",
        "aigsim_exit_code",
        "execution_valid",
        "stderr_empty",
        "execution_error",
        "expected_semantic_output",
        "aigsim_actual_output",
        "matches_expected_semantics",
        "mismatch_detected",
        "verdict",
        "manual_command",
        "captured_output_file",
    ]

    markdown_headers = [
        "case_id",
        "backend",
        "pattern",
        "word_or_trace",
        "aigsim_exit_code",
        "execution_valid",
        "stderr_empty",
        "expected_semantic_output",
        "aigsim_actual_output",
        "matches_expected_semantics",
        "mismatch_detected",
        "verdict",
    ]

    write_csv(ARTIFACT_ROOT / "manual_aigsim_checks.csv", headers, rows)
    (ARTIFACT_ROOT / "manual_aigsim_checks.md").write_text(
        "# Manual aigsim checks\n\n"
        "Detailed file paths, commands, and captured output files are in the CSV.\n\n"
        + make_markdown_table(markdown_headers, rows),
        encoding="utf-8",
    )
    write_readme()

    passing_verdicts = {"OK", "MISMATCH DETECTED"}
    failed_rows = [row for row in rows if row["verdict"] not in passing_verdicts]

    if failed_rows:
        raise AssertionError(f"Failed manual aigsim results: {failed_rows}")

    print(f"Wrote manual aigsim checks to: {ARTIFACT_ROOT}")
    print(f"Rows: {len(rows)}")

    for row in rows:
        print(
            f"{row['case_id']}: expected={row['expected_semantic_output']} "
            f"actual={row['aigsim_actual_output']} "
            f"exit={row['aigsim_exit_code']} "
            f"execution_valid={row['execution_valid']} "
            f"matches={row['matches_expected_semantics']} "
            f"verdict={row['verdict']}"
        )


if __name__ == "__main__":
    main()
