from __future__ import annotations
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger
from string_to_aiger.sequential.sequential_regex_compiler import compile_regex_to_sequential
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter

import csv
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

AIGSIM = Path(os.environ.get("AIGSIM", "/path/to/aiger/aigsim"))

ARTIFACT_ROOT = ROOT / "artifacts" / "manual_aigsim_checks"
AIGER_DIR = ARTIFACT_ROOT / "aiger"
STIMULUS_DIR = ARTIFACT_ROOT / "stimuli"
OUTPUT_DIR = ARTIFACT_ROOT / "outputs"


def ensure_dirs() -> None:
    for directory in [AIGER_DIR, STIMULUS_DIR, OUTPUT_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def require_tools() -> None:
    if not AIGSIM.exists():
        raise AssertionError(
            "aigsim not found. Set AIGSIM explicitly, for example:\n"
            "export AIGSIM=/path/to/aiger/aigsim"
        )


def parse_aiger_header(aag_text: str) -> tuple[int, int, int, int, int]:
    first_line = aag_text.splitlines()[0]
    parts = first_line.split()

    if len(parts) != 6 or parts[0] != "aag":
        raise AssertionError(f"Invalid AIGER header: {first_line}")

    return tuple(int(value) for value in parts[1:])  # type: ignore[return-value]


def parse_input_symbols(aag_text: str) -> list[str]:
    _max_var, num_inputs, _num_latches, _num_outputs, _num_ands = parse_aiger_header(aag_text)
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
    _max_var, num_inputs, num_latches, num_outputs, _num_ands = parse_aiger_header(aag_text)

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

    return "".join(bits) + "\n"


def make_sequential_stimulus(aag_text: str, word: str) -> str:
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

    return "\n".join(lines) + "\n"


def run_aigsim(aag_path: Path, stimulus_path: Path) -> tuple[str, str, str]:
    stimulus = stimulus_path.read_text(encoding="utf-8")
    aag_text = aag_path.read_text(encoding="utf-8")
    _max_var, _num_inputs, num_latches, _num_outputs, _num_ands = parse_aiger_header(aag_text)

    result = subprocess.run(
        [str(AIGSIM), str(aag_path)],
        input=stimulus,
        text=True,
        capture_output=True,
        check=False,
    )

    stdout = result.stdout
    stderr = result.stderr
    output_lines = [line for line in stdout.splitlines() if line.strip()]

    if not output_lines:
        actual_output = ""
    else:
        last_parts = output_lines[-1].split()

        if num_latches > 0 and len(last_parts) >= 3:
            actual_output = last_parts[2]
        else:
            actual_output = last_parts[-1]

    return actual_output, stdout, stderr


def write_output_file(
    path: Path,
    command: str,
    stimulus: str,
    stdout: str,
    stderr: str,
    note: str,
) -> None:
    content = (
        f"# {path.name}\n\n"
        f"Command:\n{command}\n\n"
        f"Stimulus:\n{stimulus}\n"
        f"stdout:\n{stdout}\n"
        f"stderr:\n{stderr}\n"
        f"Note:\n{note}\n"
    )

    path.write_text(content, encoding="utf-8")


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

    stimuli["accept_ab"].write_text(make_bounded_stimulus(correct_aag, "ab"), encoding="utf-8")
    stimuli["reject_ac"].write_text(make_bounded_stimulus(correct_aag, "ac"), encoding="utf-8")

    return correct_path, corrupted_path, stimuli


def generate_sequential_files() -> tuple[Path, Path, dict[str, Path]]:
    circuit = compile_regex_to_sequential("(bc)*")
    correct_aag = SequentialAigerWriter(circuit).write()

    correct_path = AIGER_DIR / "sequential_bc_star_correct.aag"
    corrupted_path = AIGER_DIR / "sequential_bc_star_output_forced_false.aag"

    correct_path.write_text(correct_aag, encoding="utf-8")
    corrupted_path.write_text(force_first_output_false(correct_aag), encoding="utf-8")

    stimuli = {
        "accept_bc": STIMULUS_DIR / "sequential_accept_bc.stim",
        "reject_b": STIMULUS_DIR / "sequential_reject_b.stim",
    }

    stimuli["accept_bc"].write_text(make_sequential_stimulus(correct_aag, "bc"), encoding="utf-8")
    stimuli["reject_b"].write_text(make_sequential_stimulus(correct_aag, "b"), encoding="utf-8")

    return correct_path, corrupted_path, stimuli


def run_case(
    case_id: str,
    description: str,
    aag_path: Path,
    stimulus_path: Path,
    word_or_trace: str,
    expected_semantic_output: str,
    should_match_semantics: bool,
) -> dict[str, object]:
    command = (
        f"$AIGSIM {artifact_relative(aag_path)} "
        f"< {artifact_relative(stimulus_path)}"
    )

    actual_output, stdout, stderr = run_aigsim(aag_path, stimulus_path)
    matches_expected = actual_output == expected_semantic_output
    mismatch_detected = not matches_expected

    if should_match_semantics:
        verdict = "OK" if matches_expected else "UNEXPECTED"
    else:
        verdict = "MISMATCH DETECTED" if mismatch_detected else "UNEXPECTED"

    output_path = OUTPUT_DIR / f"{case_id}_aigsim_output.txt"
    note = (
        "This is a direct manual aigsim check. "
        "For deliberately corrupted AIGERs, a mismatch is expected and useful."
    )

    write_output_file(
        output_path,
        command,
        stimulus_path.read_text(encoding="utf-8"),
        stdout,
        stderr,
        note,
    )

    return {
        "case_id": case_id,
        "description": description,
        "aag_file": artifact_relative(aag_path),
        "stimulus_file": artifact_relative(stimulus_path),
        "word_or_trace": word_or_trace,
        "expected_semantic_output": expected_semantic_output,
        "aigsim_actual_output": actual_output,
        "matches_expected_semantics": "YES" if matches_expected else "NO",
        "mismatch_detected": "YES" if mismatch_detected else "NO",
        "verdict": verdict,
        "manual_command": command,
        "captured_output_file": artifact_relative(output_path),
    }


def write_readme() -> None:
    content = """# Manual aigsim checks

This directory contains small, manually inspectable `aigsim` checks.

The goal is to make the AIGER validation easy to inspect from the command line:

```text
AAG file + STIM file -> aigsim -> actual output
```

## Important terminology

`output_forced_false` means a deliberately modified AIGER used as a negative-control example.

It is not meant to be a real compiler output. It is produced by taking a correct AIGER and forcing its output literal to constant false. This should make accepting witnesses fail, so the validation pipeline should detect a mismatch.

## How to read the table

For correct AIGER files:

```text
matches_expected_semantics = YES
```

For deliberately corrupted AIGER files:

```text
matches_expected_semantics = NO
mismatch_detected = YES
```

So corrupted examples should not be described as “matching”. The useful result is that the mismatch is visible and detected.

## Re-run examples

From the repository root:

```bash
export AIGSIM=/path/to/aiger/aigsim

$AIGSIM artifacts/manual_aigsim_checks/aiger/bounded_ab_or_bc_correct.aag < artifacts/manual_aigsim_checks/stimuli/bounded_accept_ab.stim
$AIGSIM artifacts/manual_aigsim_checks/aiger/bounded_ab_or_bc_output_forced_false.aag < artifacts/manual_aigsim_checks/stimuli/bounded_accept_ab.stim
$AIGSIM artifacts/manual_aigsim_checks/aiger/sequential_bc_star_correct.aag < artifacts/manual_aigsim_checks/stimuli/sequential_accept_bc.stim
```

The captured stdout/stderr files are stored in `artifacts/manual_aigsim_checks/outputs/`.
"""

    (ARTIFACT_ROOT / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    require_tools()
    ensure_dirs()

    bounded_correct, bounded_corrupted, bounded_stimuli = generate_bounded_files()
    sequential_correct, sequential_corrupted, sequential_stimuli = generate_sequential_files()

    rows = [
        run_case(
            "MAN001",
            "correct bounded AIGER accepts ab for pattern ab|bc",
            bounded_correct,
            bounded_stimuli["accept_ab"],
            "ab",
            "1",
            True,
        ),
        run_case(
            "MAN002",
            "correct bounded AIGER rejects ac for pattern ab|bc",
            bounded_correct,
            bounded_stimuli["reject_ac"],
            "ac",
            "0",
            True,
        ),
        run_case(
            "MAN003",
            "output-forced-false bounded AIGER disagrees on accepting witness ab",
            bounded_corrupted,
            bounded_stimuli["accept_ab"],
            "ab",
            "1",
            False,
        ),
        run_case(
            "MAN004",
            "correct sequential AIGER accepts trace b,c,end for pattern (bc)*",
            sequential_correct,
            sequential_stimuli["accept_bc"],
            "b, c, end",
            "1",
            True,
        ),
        run_case(
            "MAN005",
            "correct sequential AIGER rejects trace b,end for pattern (bc)*",
            sequential_correct,
            sequential_stimuli["reject_b"],
            "b, end",
            "0",
            True,
        ),
        run_case(
            "MAN006",
            "output-forced-false sequential AIGER disagrees on accepting trace b,c,end",
            sequential_corrupted,
            sequential_stimuli["accept_bc"],
            "b, c, end",
            "1",
            False,
        ),
    ]

    headers = [
        "case_id",
        "description",
        "aag_file",
        "stimulus_file",
        "word_or_trace",
        "expected_semantic_output",
        "aigsim_actual_output",
        "matches_expected_semantics",
        "mismatch_detected",
        "verdict",
        "manual_command",
        "captured_output_file",
    ]

    write_csv(ARTIFACT_ROOT / "manual_aigsim_checks.csv", headers, rows)
    (ARTIFACT_ROOT / "manual_aigsim_checks.md").write_text(
        "# Manual aigsim checks\n\n"
        + make_markdown_table(headers, rows),
        encoding="utf-8",
    )
    write_readme()

    unexpected_rows = [row for row in rows if row["verdict"] == "UNEXPECTED"]

    if unexpected_rows:
        raise AssertionError(f"Unexpected manual aigsim results: {unexpected_rows}")

    print(f"Wrote manual aigsim checks to: {ARTIFACT_ROOT}")
    print(f"Rows: {len(rows)}")

    for row in rows:
        print(
            f"{row['case_id']}: expected={row['expected_semantic_output']} "
            f"actual={row['aigsim_actual_output']} "
            f"matches={row['matches_expected_semantics']} "
            f"verdict={row['verdict']}"
        )


if __name__ == "__main__":
    main()
