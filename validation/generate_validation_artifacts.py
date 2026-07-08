from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
from pathlib import Path
from string_to_aiger.nfa.nfa_evaluator import accepts
from string_to_aiger.regex.regex_parser import parse_regex
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger
from string_to_aiger.regex.regex_to_product_nfa import build_product_aware_nfa
from string_to_aiger.sequential.sequential_aiger_writer import SequentialAigerWriter
from string_to_aiger.sequential.sequential_regex_compiler import compile_regex_to_sequential


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


ARTIFACT_ROOT = ROOT / "artifacts" / "validation"
AIGER_DIR = ARTIFACT_ROOT / "aiger"
WITNESS_DIR = ARTIFACT_ROOT / "witnesses"

VALIDATION_CASES = [
    {"case_id": "B001", "pattern": "ab|bc", "backend": "bounded", "intersection_strategy": "structural", "bound": 2, "candidates": ["ab", "bc", "", "a", "b", "aa", "ba", "abc"]},
    {"case_id": "B002", "pattern": "(bc)*", "backend": "bounded", "intersection_strategy": "structural", "bound": 4, "candidates": ["", "bc", "bcbc", "b", "c", "bcb", "bcbcbc"]},
    {"case_id": "B003", "pattern": "(a|b)*&a*", "backend": "bounded", "intersection_strategy": "structural", "bound": 4, "candidates": ["", "a", "aa", "aaaa", "b", "ab", "ba", "aaaaa"]},
    {"case_id": "S001", "pattern": "ab|bc", "backend": "sequential", "intersection_strategy": "structural", "bound": None, "candidates": ["ab", "bc", "", "a", "b", "aa", "ba", "abc"]},
    {"case_id": "S002", "pattern": "(bc)*", "backend": "sequential", "intersection_strategy": "structural", "bound": None, "candidates": ["", "bc", "bcbc", "bcbcbc", "b", "c", "bcb"]},
    {"case_id": "S003", "pattern": "(a|b)*&a*", "backend": "sequential", "intersection_strategy": "structural", "bound": None, "candidates": ["", "a", "aa", "aaaaaa", "b", "ab", "ba"]},
]

NEGATIVE_CASES = [
    {"case_id": "N001", "pattern": "ab|bc", "backend": "bounded", "bound": 2, "corruption_type": "output_forced_false", "witness": "ab"},
    {"case_id": "N002", "pattern": "ab|bc", "backend": "bounded", "bound": 2, "corruption_type": "output_forced_true", "witness": "aa"},
    {"case_id": "N003", "pattern": "ab|bc", "backend": "bounded", "bound": 2, "corruption_type": "output_inverted", "witness": "bc"},
    {"case_id": "N004", "pattern": "(bc)*", "backend": "sequential", "bound": None, "corruption_type": "output_forced_false", "witness": "bc"},
    {"case_id": "N005", "pattern": "(bc)*", "backend": "sequential", "bound": None, "corruption_type": "output_forced_true", "witness": "b"},
    {"case_id": "N006", "pattern": "(bc)*", "backend": "sequential", "bound": None, "corruption_type": "output_inverted", "witness": "bcbc"},
]

_NEGATIVE_DETECTION_PREAMBLE = """\
These cases use deliberately corrupted AIGER circuits as negative controls.
Each corrupted circuit is derived from a correct generated AIGER by applying one of the following modifications:

| corruption_type | Meaning |
| --- | --- |
| `output_forced_false` | The output literal is replaced by constant 0. The circuit always rejects. |
| `output_forced_true` | The output literal is replaced by constant 1. The circuit always accepts. |
| `output_inverted` | The output literal is bit-flipped (XOR 1). Accept and reject are swapped. |

The `witness_string` column shows the input used to expose the mismatch.
The `sanity_correct_aiger` column confirms the unmodified circuit still produces the expected result.
The `mismatch_detected` column shows that the corrupted circuit disagrees with the expected regex semantics, confirming the validation infrastructure can detect wrong behavior.

"""


def require_aigsim() -> str:
    aigsim = os.environ.get("AIGSIM")
    if not aigsim:
        raise AssertionError("AIGSIM is not set. Example: export AIGSIM=/path/to/aiger/aigsim")
    if not Path(aigsim).exists():
        raise AssertionError(f"AIGSIM does not exist: {aigsim}")
    return aigsim


def ensure_dirs() -> None:
    AIGER_DIR.mkdir(parents=True, exist_ok=True)
    WITNESS_DIR.mkdir(parents=True, exist_ok=True)


def parse_aiger_header(aag_text: str) -> tuple[int, int, int, int, int]:
    parts = aag_text.splitlines()[0].split()
    if len(parts) != 6 or parts[0] != "aag":
        raise AssertionError(f"Invalid AIGER header: {aag_text.splitlines()[0]}")
    return tuple(int(value) for value in parts[1:])  # type: ignore[return-value]


def parse_aiger_input_names(aag_text: str) -> list[str]:
    names_by_index: dict[int, str] = {}
    for line in aag_text.splitlines():
        line = line.strip()
        if not line.startswith("i"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        index_text, name = parts
        if index_text[1:].isdigit():
            names_by_index[int(index_text[1:])] = name
    return [names_by_index[index] for index in sorted(names_by_index)]


def compile_aiger(pattern: str, backend: str, bound: int | None) -> str:
    if backend == "bounded":
        if bound is None:
            raise AssertionError("Bounded backend requires a bound.")
        return compile_regex_to_aiger(pattern, bound)
    if backend == "sequential":
        circuit = compile_regex_to_sequential(pattern)
        return SequentialAigerWriter(circuit).write()
    raise AssertionError(f"Unsupported backend: {backend}")


def expected_unbounded(pattern: str, candidate: str) -> int:
    ast = parse_regex(pattern)
    nfa = build_product_aware_nfa(ast)
    return 1 if accepts(nfa, candidate) else 0


def expected_for_case(pattern: str, backend: str, bound: int | None, candidate: str) -> int:
    if backend == "bounded" and bound is not None and len(candidate) > bound:
        return 0
    return expected_unbounded(pattern, candidate)


def encode_bounded_candidate(candidate: str, input_names: list[str]) -> tuple[str, str]:
    bits: list[str] = []
    assignments: list[str] = []
    for name in input_names:
        if name.startswith("len_is_"):
            length = int(name.removeprefix("len_is_"))
            value = len(candidate) == length
            bits.append("1" if value else "0")
            assignments.append(f"{name}={1 if value else 0}")
            continue
        match = re.fullmatch(r"x_(\d+)_is_(.+)", name)
        if match:
            position = int(match.group(1))
            symbol = match.group(2)
            value = position < len(candidate) and candidate[position] == symbol
            bits.append("1" if value else "0")
            assignments.append(f"{name}={1 if value else 0}")
            continue
        raise ValueError(f"Unsupported bounded input name: {name}")
    return "".join(bits), ", ".join(assignments)


def encode_sequential_step(char: str | None, input_names: list[str]) -> tuple[str, str]:
    bits: list[str] = []
    assignments: list[str] = []
    for name in input_names:
        if name == "end":
            value = char is None
            bits.append("1" if value else "0")
            assignments.append(f"{name}={1 if value else 0}")
            continue
        if name.startswith("is_"):
            symbol = name.removeprefix("is_")
            value = char == symbol
            bits.append("1" if value else "0")
            assignments.append(f"{name}={1 if value else 0}")
            continue
        raise ValueError(f"Unsupported sequential input name: {name}")
    return "".join(bits), ", ".join(assignments)


def encode_sequential_trace(candidate: str, input_names: list[str]) -> tuple[list[str], str]:
    vectors: list[str] = []
    readable_steps: list[str] = []
    for index, char in enumerate(candidate):
        vector, assignments = encode_sequential_step(char, input_names)
        vectors.append(vector)
        readable_steps.append(f"step {index}: char={char!r}, vector={vector}, {assignments}")
    final_vector, final_assignments = encode_sequential_step(None, input_names)
    vectors.append(final_vector)
    readable_steps.append(f"step {len(candidate)}: end, vector={final_vector}, {final_assignments}")
    return vectors, " / ".join(readable_steps)


def write_stimulus_file(path: Path, vectors: list[str]) -> None:
    path.write_text("\n".join(vectors) + "\n.\n", encoding="utf-8")


def parse_bounded_aigsim_output(stdout: str) -> int:
    outputs: list[int] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("Trace is a witness"):
            continue
        parts = line.split()
        if len(parts) == 1 and parts[0] in {"0", "1"}:
            outputs.append(int(parts[0]))
        elif len(parts) == 2 and parts[1] in {"0", "1"}:
            outputs.append(int(parts[1]))
    if len(outputs) != 1:
        raise AssertionError(f"Expected exactly one bounded aigsim output:\n{stdout}")
    return outputs[0]


def parse_final_sequential_aigsim_output(stdout: str) -> int:
    final_output: int | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("Trace is a witness"):
            continue
        parts = line.split()
        if len(parts) == 4:
            _current_state, input_vector, output, _next_state = parts
            if set(input_vector) <= {"0", "1"} and output in {"0", "1"}:
                final_output = int(output)
        elif len(parts) == 2 and parts[1] in {"0", "1"}:
            final_output = int(parts[1])
        elif len(parts) == 1 and parts[0] in {"0", "1"}:
            final_output = int(parts[0])
    if final_output is None:
        raise AssertionError(f"Could not parse sequential aigsim output:\n{stdout}")
    return final_output


def run_aigsim(aag_path: Path, stim_path: Path, backend: str) -> int:
    result = subprocess.run(
        [require_aigsim(), str(aag_path), str(stim_path)],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "aigsim failed\n"
            f"AIGER: {aag_path}\n"
            f"stimulus: {stim_path}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    if backend == "bounded":
        return parse_bounded_aigsim_output(result.stdout)
    if backend == "sequential":
        return parse_final_sequential_aigsim_output(result.stdout)
    raise AssertionError(f"Unsupported backend: {backend}")


def corrupt_first_output(aag_text: str, corruption_type: str) -> str:
    lines = aag_text.splitlines()
    _max_var, num_inputs, num_latches, num_outputs, _num_ands = parse_aiger_header(aag_text)
    if num_outputs < 1:
        raise AssertionError("Cannot corrupt AIGER without outputs.")
    first_output_line_index = 1 + num_inputs + num_latches
    original_literal = int(lines[first_output_line_index])
    if corruption_type == "output_forced_false":
        lines[first_output_line_index] = "0"
    elif corruption_type == "output_forced_true":
        lines[first_output_line_index] = "1"
    elif corruption_type == "output_inverted":
        lines[first_output_line_index] = str(original_literal ^ 1)
    else:
        raise AssertionError(f"Unsupported corruption type: {corruption_type}")
    return "\n".join(lines) + "\n"


def safe_name(candidate: str) -> str:
    if candidate == "":
        return "epsilon"
    return re.sub(r"[^a-zA-Z0-9]+", "_", candidate)


def artifact_relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def clean_markdown(value: object) -> str:
    return str(value).replace("\n", "<br>").replace("|", "\\|")


def make_markdown_table(headers: list[str], rows: list[dict[str, object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(clean_markdown(row.get(header, "")) for header in headers) + " |")
    return "\n".join(lines) + "\n"


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def generate_validation_matrix() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case in VALIDATION_CASES:
        case_id = str(case["case_id"])
        pattern = str(case["pattern"])
        backend = str(case["backend"])
        strategy = str(case["intersection_strategy"])
        bound = case["bound"]
        candidates = list(case["candidates"])

        aag_text = compile_aiger(pattern, backend, bound)  # type: ignore[arg-type]
        aag_path = AIGER_DIR / f"{case_id}_{backend}.aag"
        aag_path.write_text(aag_text, encoding="utf-8")
        input_names = parse_aiger_input_names(aag_text)

        for index, candidate in enumerate(candidates):
            candidate_text = str(candidate)
            stim_path = WITNESS_DIR / f"{case_id}_{backend}_{index}_{safe_name(candidate_text)}.stim"

            if backend == "bounded":
                vector, readable = encode_bounded_candidate(candidate_text, input_names)
                write_stimulus_file(stim_path, [vector])
                encoded = vector
            else:
                vectors, readable = encode_sequential_trace(candidate_text, input_names)
                write_stimulus_file(stim_path, vectors)
                encoded = " / ".join(vectors)

            expected = expected_for_case(pattern, backend, bound, candidate_text)  # type: ignore[arg-type]
            observed = run_aigsim(aag_path, stim_path, backend)

            rows.append({
                "case_id": case_id,
                "pattern": pattern,
                "backend": backend,
                "intersection_strategy": strategy,
                "bound": "" if bound is None else bound,
                "candidate_string": repr(candidate_text),
                "encoded_input_or_trace": encoded,
                "readable_encoding": readable,
                "expected_regex_result": expected,
                "aigsim_output": observed,
                "verdict": "PASS" if expected == observed else "FAIL",
                "aiger_file": artifact_relative(aag_path),
                "stimulus_file": artifact_relative(stim_path),
            })
    return rows


def generate_negative_detection_matrix() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case in NEGATIVE_CASES:
        case_id = str(case["case_id"])
        pattern = str(case["pattern"])
        backend = str(case["backend"])
        bound = case["bound"]
        corruption_type = str(case["corruption_type"])
        witness = str(case["witness"])

        correct_aag = compile_aiger(pattern, backend, bound)  # type: ignore[arg-type]
        corrupted_aag = corrupt_first_output(correct_aag, corruption_type)

        correct_aag_path = AIGER_DIR / f"{case_id}_{backend}_correct.aag"
        corrupted_aag_path = AIGER_DIR / f"{case_id}_{backend}_{corruption_type}.aag"
        correct_aag_path.write_text(correct_aag, encoding="utf-8")
        corrupted_aag_path.write_text(corrupted_aag, encoding="utf-8")

        input_names = parse_aiger_input_names(corrupted_aag)
        stim_path = WITNESS_DIR / f"{case_id}_{backend}_{safe_name(witness)}.stim"

        if backend == "bounded":
            vector, readable = encode_bounded_candidate(witness, input_names)
            write_stimulus_file(stim_path, [vector])
            witness_trace = vector
        else:
            vectors, readable = encode_sequential_trace(witness, input_names)
            write_stimulus_file(stim_path, vectors)
            witness_trace = " / ".join(vectors)

        expected = expected_for_case(pattern, backend, bound, witness)  # type: ignore[arg-type]
        correct_output = run_aigsim(correct_aag_path, stim_path, backend)
        corrupted_output = run_aigsim(corrupted_aag_path, stim_path, backend)

        rows.append({
            "case_id": case_id,
            "pattern": pattern,
            "backend": backend,
            "bound": "" if bound is None else bound,
            "corruption_type": corruption_type,
            "witness_string": repr(witness),
            "witness_trace": witness_trace,
            "readable_witness_encoding": readable,
            "expected_regex_result": expected,
            "correct_aiger_output": correct_output,
            "corrupted_aiger_output": corrupted_output,
            "sanity_correct_aiger": "PASS" if correct_output == expected else "FAIL",
            "mismatch_detected": "YES" if corrupted_output != expected else "NO",
            "correct_aiger_file": artifact_relative(correct_aag_path),
            "corrupted_aiger_file": artifact_relative(corrupted_aag_path),
            "stimulus_file": artifact_relative(stim_path),
        })
    return rows


def write_encoding_table() -> None:
    content = """# Encoding Table

This document explains how candidate strings are represented as bit-level inputs for generated AIGER circuits.

# Bounded Encoding

The bounded backend uses one input vector per candidate word.

Typical bounded inputs:

```text
len_is_0
len_is_1
len_is_2
x_0_is_a
x_0_is_b
x_1_is_a
x_1_is_b
```

For candidate string `ab`, the bounded encoding sets:

```text
len_is_2 = 1
x_0_is_a = 1
x_1_is_b = 1
```

All incompatible length and character-position inputs are set to 0.

# Sequential Encoding

The sequential backend uses one input vector per time step.

Each normal step activates exactly one symbol input. The final step activates `end`.

If the input order is:

```text
end
is_a
is_b
```

then the encoding is:

```text
a   -> 010
b   -> 001
end -> 100
```

The word `ab` is represented as:

```text
010
001
100
.
```

The final dot terminates the aigsim stimulus file.

# Witness Meaning

A witness is an encoded input vector or trace that demonstrates a behavior of the generated AIGER circuit.

For ordinary validation, the witness shows agreement between the generated AIGER circuit and reference regex semantics.

For negative detection, the witness exposes a mismatch between expected regex semantics and a deliberately corrupted AIGER file.
"""
    (ARTIFACT_ROOT / "encoding_table.md").write_text(content, encoding="utf-8")


def write_readme() -> None:
    content = """# Validation Artifacts

This directory contains inspectable validation artifacts for the string-to-AIGER compiler.

The goal is to make external semantic validation visible as tables and witness files, not only as passing tests.

# Files

```text
validation_matrix.csv
validation_matrix.md
negative_detection_matrix.csv
negative_detection_matrix.md
encoding_table.md
aiger/
witnesses/
```

# Interpretation

These artifacts show that generated AIGER files are simulated externally with aigsim and compared against reference regex semantics.

This is testing-based external semantic validation, not a formal proof of compiler correctness.
"""
    (ARTIFACT_ROOT / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    require_aigsim()
    ensure_dirs()

    validation_headers = [
        "case_id", "pattern", "backend", "intersection_strategy", "bound",
        "candidate_string", "encoded_input_or_trace", "readable_encoding",
        "expected_regex_result", "aigsim_output", "verdict",
        "aiger_file", "stimulus_file",
    ]
    negative_headers = [
        "case_id", "pattern", "backend", "bound", "corruption_type",
        "witness_string", "witness_trace", "readable_witness_encoding",
        "expected_regex_result", "correct_aiger_output", "corrupted_aiger_output",
        "sanity_correct_aiger", "mismatch_detected", "correct_aiger_file",
        "corrupted_aiger_file", "stimulus_file",
    ]

    validation_rows = generate_validation_matrix()
    negative_rows = generate_negative_detection_matrix()

    write_csv(ARTIFACT_ROOT / "validation_matrix.csv", validation_headers, validation_rows)
    write_csv(ARTIFACT_ROOT / "negative_detection_matrix.csv", negative_headers, negative_rows)

    (ARTIFACT_ROOT / "validation_matrix.md").write_text(
        "# Validation Matrix\n\n" + make_markdown_table(validation_headers, validation_rows),
        encoding="utf-8",
    )
    (ARTIFACT_ROOT / "negative_detection_matrix.md").write_text(
        "# Negative Detection Matrix\n\n" + _NEGATIVE_DETECTION_PREAMBLE + make_markdown_table(negative_headers, negative_rows),
        encoding="utf-8",
    )

    write_encoding_table()
    write_readme()

    failed_rows = [row for row in validation_rows if row["verdict"] != "PASS"]
    undetected_rows = [row for row in negative_rows if row["mismatch_detected"] != "YES"]

    if failed_rows:
        raise AssertionError(f"Validation matrix contains failing rows: {failed_rows}")
    if undetected_rows:
        raise AssertionError(f"Negative detection matrix contains undetected mismatches: {undetected_rows}")

    print(f"Wrote validation artifacts to: {ARTIFACT_ROOT}")
    print(f"Validation rows: {len(validation_rows)}")
    print(f"Negative detection rows: {len(negative_rows)}")


if __name__ == "__main__":
    main()
