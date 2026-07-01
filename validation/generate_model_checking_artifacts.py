from __future__ import annotations

import csv
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "model_checking"
MITER_DIR = ARTIFACT_ROOT / "miters"
CNF_DIR = ARTIFACT_ROOT / "cnf"
WITNESS_DIR = ARTIFACT_ROOT / "witnesses"

AIGER_TOOL_DIR = Path("/home/egetekin/tools/aiger")
AIGMITER = AIGER_TOOL_DIR / "aigmiter"
AIGTOCNF = AIGER_TOOL_DIR / "aigtocnf"
MINISAT = shutil.which("minisat") or "minisat"


CASES = [
    {
        "case_id": "MC001",
        "description": "sanity check: correct AIGER compared with itself",
        "pattern": "ab|bc",
        "bound": 2,
        "left_aiger": ROOT / "artifacts" / "validation" / "aiger" / "N001_bounded_correct.aag",
        "right_aiger": ROOT / "artifacts" / "validation" / "aiger" / "N001_bounded_correct.aag",
        "comparison": "correct_vs_correct",
        "expected_model_checker_result": "UNSAT",
    },
    {
        "case_id": "MC002",
        "description": "negative check: correct AIGER compared with output-forced-false corrupted AIGER",
        "pattern": "ab|bc",
        "bound": 2,
        "left_aiger": ROOT / "artifacts" / "validation" / "aiger" / "N001_bounded_correct.aag",
        "right_aiger": ROOT / "artifacts" / "validation" / "aiger" / "N001_bounded_output_forced_false.aag",
        "comparison": "correct_vs_corrupted_output_forced_false",
        "expected_model_checker_result": "SAT",
    },
]


def run(
    command: list[str],
    allowed_return_codes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
    )

    if result.returncode not in allowed_return_codes:
        raise AssertionError(
            "Command failed\n"
            f"command: {' '.join(command)}\n"
            f"return code: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    return result


def ensure_tools() -> None:
    for tool in [AIGMITER, AIGTOCNF]:
        if not tool.exists():
            raise AssertionError(f"Required AIGER tool does not exist: {tool}")

    if shutil.which(str(MINISAT)) is None and not Path(str(MINISAT)).exists():
        raise AssertionError(
            "minisat was not found. Install it with: sudo apt install -y minisat"
        )


def ensure_input_files() -> None:
    for case in CASES:
        for key in ["left_aiger", "right_aiger"]:
            path = Path(case[key])
            if not path.exists():
                raise AssertionError(
                    f"Missing input AIGER file: {path}\n"
                    "Run first: python3 validation/generate_validation_artifacts.py"
                )


def ensure_dirs() -> None:
    MITER_DIR.mkdir(parents=True, exist_ok=True)
    CNF_DIR.mkdir(parents=True, exist_ok=True)
    WITNESS_DIR.mkdir(parents=True, exist_ok=True)


def parse_aiger_input_names(aag_path: Path) -> list[str]:
    names_by_index: dict[int, str] = {}

    for raw_line in aag_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line.startswith("i"):
            continue

        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue

        index_text, name = parts

        if not index_text[1:].isdigit():
            continue

        names_by_index[int(index_text[1:])] = name

    return [names_by_index[index] for index in sorted(names_by_index)]


def parse_cnf_aiger_literal_map(cnf_path: Path) -> dict[int, int]:
    """Parse comments of the form 'c <aiger-lit> -> <cnf-var>'."""
    mapping: dict[int, int] = {}

    for raw_line in cnf_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        match = re.fullmatch(r"c\s+(\d+)\s+->\s+(\d+)", line)
        if match:
            aiger_lit = int(match.group(1))
            cnf_var = int(match.group(2))
            mapping[aiger_lit] = cnf_var

    return mapping


def input_name_to_aiger_literal(input_index: int) -> int:
    """ASCII AIGER input i0 has literal 2, i1 literal 4, etc."""
    return 2 * (input_index + 1)


def input_name_to_cnf_var(
    input_names: list[str],
    cnf_mapping: dict[int, int],
) -> dict[str, int]:
    result: dict[str, int] = {}

    for index, name in enumerate(input_names):
        aiger_lit = input_name_to_aiger_literal(index)

        if aiger_lit not in cnf_mapping:
            raise AssertionError(
                f"No CNF variable found for input {name!r} with AIGER literal {aiger_lit}"
            )

        result[name] = cnf_mapping[aiger_lit]

    return result


def exactly_one_clauses(vars_: list[int]) -> list[list[int]]:
    if not vars_:
        return []

    clauses: list[list[int]] = []

    clauses.append(vars_[:])

    for i in range(len(vars_)):
        for j in range(i + 1, len(vars_)):
            clauses.append([-vars_[i], -vars_[j]])

    return clauses


def build_valid_bounded_input_clauses(name_to_var: dict[str, int]) -> tuple[list[list[int]], str]:
    """Build validity constraints for the bounded string encoding.

    This demonstration uses the currently visible bounded input vocabulary.
    It enforces exactly one active length input and exactly one active symbol per
    represented position. For the MC002 example this turns Minisat's raw Boolean
    assignment into a real candidate string such as 'ab'.
    """
    len_vars: list[tuple[int, int]] = []
    position_vars: dict[int, list[tuple[str, int]]] = {}

    for name, cnf_var in name_to_var.items():
        len_match = re.fullmatch(r"len_is_(\d+)", name)
        if len_match:
            length = int(len_match.group(1))
            len_vars.append((length, cnf_var))
            continue

        char_match = re.fullmatch(r"x_(\d+)_is_(.+)", name)
        if char_match:
            position = int(char_match.group(1))
            symbol = char_match.group(2)
            position_vars.setdefault(position, []).append((symbol, cnf_var))
            continue

    clauses: list[list[int]] = []

    len_vars_sorted = [var for _length, var in sorted(len_vars)]
    clauses.extend(exactly_one_clauses(len_vars_sorted))

    for position in sorted(position_vars):
        vars_for_position = [var for _symbol, var in sorted(position_vars[position])]
        clauses.extend(exactly_one_clauses(vars_for_position))

    description_parts = []
    if len_vars_sorted:
        description_parts.append("exactly one length input")
    if position_vars:
        description_parts.append("exactly one symbol input per represented position")

    return clauses, "; ".join(description_parts)


def rewrite_cnf_with_extra_clauses(
    src: Path,
    dst: Path,
    extra_clauses: list[list[int]],
) -> None:
    lines = src.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    header_rewritten = False

    for line in lines:
        if line.startswith("p cnf"):
            parts = line.split()
            num_vars = int(parts[2])
            num_clauses = int(parts[3])
            out.append(f"p cnf {num_vars} {num_clauses + len(extra_clauses)}")
            header_rewritten = True
        else:
            out.append(line)

    if not header_rewritten:
        raise AssertionError(f"CNF header not found in {src}")

    for clause in extra_clauses:
        out.append(" ".join(str(lit) for lit in clause) + " 0")

    dst.write_text("\n".join(out) + "\n", encoding="utf-8")


def minisat_result(stdout: str, sat_file: Path) -> str:
    if "UNSATISFIABLE" in stdout:
        return "UNSAT"

    if "SATISFIABLE" in stdout:
        return "SAT"

    if sat_file.exists():
        first = sat_file.read_text(encoding="utf-8").splitlines()[0].strip()
        if first == "SAT":
            return "SAT"
        if first == "UNSAT":
            return "UNSAT"

    raise AssertionError(f"Could not determine Minisat result:\n{stdout}")


def parse_sat_assignment(sat_file: Path) -> dict[int, bool]:
    if not sat_file.exists():
        return {}

    lines = sat_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "SAT":
        return {}

    assignment: dict[int, bool] = {}

    for token in " ".join(lines[1:]).split():
        lit = int(token)
        if lit == 0:
            continue
        assignment[abs(lit)] = lit > 0

    return assignment


def decode_bounded_witness(
    input_names: list[str],
    name_to_var: dict[str, int],
    assignment: dict[int, bool],
) -> tuple[str, str]:
    active_lengths: list[int] = []
    active_symbols: dict[int, str] = {}
    readable_assignments: list[str] = []

    for name in input_names:
        cnf_var = name_to_var[name]
        value = assignment.get(cnf_var, False)
        readable_assignments.append(f"{name}={1 if value else 0}")

        len_match = re.fullmatch(r"len_is_(\d+)", name)
        if len_match and value:
            active_lengths.append(int(len_match.group(1)))
            continue

        char_match = re.fullmatch(r"x_(\d+)_is_(.+)", name)
        if char_match and value:
            position = int(char_match.group(1))
            symbol = char_match.group(2)
            active_symbols[position] = symbol

    if not active_lengths:
        decoded = "<no active length>"
    else:
        length = active_lengths[0]
        chars = []
        for position in range(length):
            chars.append(active_symbols.get(position, "?"))
        decoded = "".join(chars)

    return decoded, ", ".join(readable_assignments)


def make_markdown_table(headers: list[str], rows: list[dict[str, object]]) -> str:
    def clean(value: object) -> str:
        text = str(value)
        text = text.replace("\n", "<br>")
        text = text.replace("|", "\\|")
        return text

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")

    for row in rows:
        lines.append("| " + " | ".join(clean(row.get(header, "")) for header in headers) + " |")

    return "\n".join(lines) + "\n"


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def generate_case(case: dict[str, object]) -> dict[str, object]:
    case_id = str(case["case_id"])
    pattern = str(case["pattern"])
    comparison = str(case["comparison"])

    bound_value = case["bound"]
    if not isinstance(bound_value, int):
        raise TypeError(f"Expected integer bound for {case_id}, got {bound_value!r}")
    bound = bound_value

    left_aiger = Path(str(case["left_aiger"]))
    right_aiger = Path(str(case["right_aiger"]))

    miter_path = MITER_DIR / f"{case_id}_{comparison}.aag"
    raw_cnf_path = CNF_DIR / f"{case_id}_{comparison}.cnf"
    constrained_cnf_path = CNF_DIR / f"{case_id}_{comparison}_valid_input.cnf"
    sat_path = WITNESS_DIR / f"{case_id}_{comparison}.sat"

    run([str(AIGMITER), "-o", str(miter_path), str(left_aiger), str(right_aiger)])
    run([str(AIGTOCNF), "-m", str(miter_path), str(raw_cnf_path)])

    input_names = parse_aiger_input_names(miter_path)
    cnf_mapping = parse_cnf_aiger_literal_map(raw_cnf_path)
    name_to_var = input_name_to_cnf_var(input_names, cnf_mapping)
    validity_clauses, validity_description = build_valid_bounded_input_clauses(name_to_var)

    rewrite_cnf_with_extra_clauses(raw_cnf_path, constrained_cnf_path, validity_clauses)

    minisat_run = run(
        [str(MINISAT), str(constrained_cnf_path), str(sat_path)],
        allowed_return_codes=(10, 20),
    )

    result = minisat_result(minisat_run.stdout, sat_path)
    assignment = parse_sat_assignment(sat_path)

    if result == "SAT":
        decoded_witness, readable_assignment = decode_bounded_witness(
            input_names,
            name_to_var,
            assignment,
        )
        witness_assignment = " ".join(
            str(var if value else -var) for var, value in sorted(assignment.items())
        )
    else:
        decoded_witness = ""
        readable_assignment = ""
        witness_assignment = ""

    expected = str(case["expected_model_checker_result"])
    verdict = "PASS" if result == expected else "FAIL"

    return {
        "case_id": case_id,
        "description": str(case["description"]),
        "pattern": pattern,
        "bound": bound,
        "comparison": comparison,
        "model_checker_result": result,
        "expected_model_checker_result": expected,
        "verdict": verdict,
        "decoded_witness_string": repr(decoded_witness) if decoded_witness else "",
        "witness_assignment": witness_assignment,
        "readable_input_assignment": readable_assignment,
        "valid_input_constraints": validity_description,
        "miter_file": rel(miter_path),
        "raw_cnf_file": rel(raw_cnf_path),
        "constrained_cnf_file": rel(constrained_cnf_path),
        "sat_witness_file": rel(sat_path),
    }


def write_readme() -> None:
    content = """# Model checking artifacts

This directory contains a small model-checking-style validation artifact.

The generated flow is:

```text
aigmiter
-> aigtocnf
-> minisat
-> SAT/UNSAT result
-> optional witness decoding
```

For the negative case, the script compares a correct generated AIGER file with a deliberately corrupted AIGER file.
The miter output is satisfiable exactly when the two circuits differ on some input assignment.

Because arbitrary Boolean assignments do not necessarily represent real candidate strings, the generated CNF is strengthened with bounded input-validity constraints:

```text
exactly one active length input
exactly one active symbol input per represented position
```

With these constraints, a SAT assignment can be decoded back into a real candidate string such as `ab`.

This is not yet a full formal proof of compiler correctness. It is a first artifact showing automatic counterexample extraction for bounded AIGER circuits using an external SAT/model-checking-style toolchain.
"""
    (ARTIFACT_ROOT / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    ensure_tools()
    ensure_input_files()
    ensure_dirs()

    rows = [generate_case(case) for case in CASES]

    headers = [
        "case_id",
        "description",
        "pattern",
        "bound",
        "comparison",
        "model_checker_result",
        "expected_model_checker_result",
        "verdict",
        "decoded_witness_string",
        "witness_assignment",
        "readable_input_assignment",
        "valid_input_constraints",
        "miter_file",
        "raw_cnf_file",
        "constrained_cnf_file",
        "sat_witness_file",
    ]

    write_csv(ARTIFACT_ROOT / "model_checking_counterexamples.csv", headers, rows)
    (ARTIFACT_ROOT / "model_checking_counterexamples.md").write_text(
        "# Model checking counterexamples\n\n" + make_markdown_table(headers, rows),
        encoding="utf-8",
    )
    write_readme()

    failing_rows = [row for row in rows if row["verdict"] != "PASS"]
    if failing_rows:
        raise AssertionError(f"Unexpected model-checking results: {failing_rows}")

    print(f"Wrote model-checking artifacts to: {ARTIFACT_ROOT}")
    print(f"Rows: {len(rows)}")
    for row in rows:
        print(
            f"{row['case_id']}: {row['comparison']} -> "
            f"{row['model_checker_result']} "
            f"decoded={row['decoded_witness_string']}"
        )


if __name__ == "__main__":
    main()
