from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
from itertools import combinations
from pathlib import Path
from string_to_aiger.regex.regex_to_aiger import compile_regex_to_aiger


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


AIGER_TOOLS = Path(os.environ.get("AIGER_TOOLS", "/home/egetekin/tools/aiger"))
AIGMITER = AIGER_TOOLS / "aigmiter"
AIGTOCNF = AIGER_TOOLS / "aigtocnf"
MINISAT = shutil.which("minisat")

ARTIFACT_ROOT = ROOT / "artifacts" / "reference_equivalence"
GENERATED_DIR = ARTIFACT_ROOT / "generated"
REFERENCE_DIR = ARTIFACT_ROOT / "reference"
CORRUPTED_DIR = ARTIFACT_ROOT / "corrupted"
MITER_DIR = ARTIFACT_ROOT / "miters"
CNF_DIR = ARTIFACT_ROOT / "cnf"
WITNESS_DIR = ARTIFACT_ROOT / "witnesses"

CASES = [
    {
        "case_id": "REFEQ001",
        "description": "generated bounded AIGER compared with independent exact-word reference",
        "pattern": "ab|bc",
        "bound": 2,
        "accepted_words": ["ab", "bc"],
        "comparison": "generated_vs_reference",
        "expected_result": "UNSAT",
        "use_corrupted_generated": False,
    },
    {
        "case_id": "REFEQ002",
        "description": "negative check: output-forced-false generated AIGER compared with independent reference",
        "pattern": "ab|bc",
        "bound": 2,
        "accepted_words": ["ab", "bc"],
        "comparison": "corrupted_generated_vs_reference",
        "expected_result": "SAT",
        "use_corrupted_generated": True,
    },
    {
        "case_id": "REFEQ003",
        "description": "character-class pattern compared with independent exact-word reference",
        "pattern": "a[bc]",
        "bound": 2,
        "accepted_words": ["ab", "ac"],
        "comparison": "generated_vs_reference",
        "expected_result": "UNSAT",
        "use_corrupted_generated": False,
    },
    {
        "case_id": "REFEQ004",
        "description": "union and concatenation pattern compared with independent exact-word reference",
        "pattern": "(a|b)(a|b)",
        "bound": 2,
        "accepted_words": ["aa", "ab", "ba", "bb"],
        "comparison": "generated_vs_reference",
        "expected_result": "UNSAT",
        "use_corrupted_generated": False,
    },
]


class AigerBuilder:
    def __init__(self, input_symbols: list[str]) -> None:
        self.input_symbols = input_symbols
        self.num_inputs = len(input_symbols)
        self.max_var = self.num_inputs
        self.ands: list[tuple[int, int, int]] = []

    def new_and(self, left: int, right: int) -> int:
        self.max_var += 1
        output = 2 * self.max_var
        self.ands.append((output, left, right))
        return output

    def and_all(self, literals: list[int]) -> int:
        if not literals:
            return 1

        result = literals[0]

        for literal in literals[1:]:
            result = self.new_and(result, literal)

        return result

    def or_two(self, left: int, right: int) -> int:
        # left OR right == NOT((NOT left) AND (NOT right))
        return self.new_and(left ^ 1, right ^ 1) ^ 1

    def or_all(self, literals: list[int]) -> int:
        if not literals:
            return 0

        result = literals[0]

        for literal in literals[1:]:
            result = self.or_two(result, literal)

        return result

    def render(self, output_literal: int, comment: str) -> str:
        lines: list[str] = []
        lines.append(f"aag {self.max_var} {self.num_inputs} 0 1 {len(self.ands)}")

        for index in range(self.num_inputs):
            lines.append(str(2 * (index + 1)))

        lines.append(str(output_literal))

        for output, left, right in self.ands:
            lines.append(f"{output} {left} {right}")

        for index, symbol in enumerate(self.input_symbols):
            lines.append(f"i{index} {symbol}")

        lines.append("o0 accept")
        lines.append("c")
        lines.append(comment)

        return "\n".join(lines) + "\n"


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


def require_tools() -> None:
    for tool in [AIGMITER, AIGTOCNF]:
        if not tool.exists():
            raise AssertionError(f"Required AIGER tool not found: {tool}")

    if MINISAT is None:
        raise AssertionError("minisat executable not found. Install it with: sudo apt install minisat")


def ensure_dirs() -> None:
    for directory in [
        GENERATED_DIR,
        REFERENCE_DIR,
        CORRUPTED_DIR,
        MITER_DIR,
        CNF_DIR,
        WITNESS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def artifact_relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def parse_aiger_header(aag_text: str) -> tuple[int, int, int, int, int]:
    first_line = aag_text.splitlines()[0]
    parts = first_line.split()

    if len(parts) != 6 or parts[0] != "aag":
        raise AssertionError(f"Invalid AIGER header: {first_line}")

    return tuple(int(value) for value in parts[1:])  # type: ignore[return-value]


def parse_aiger_input_literals(aag_text: str) -> list[int]:
    _max_var, num_inputs, _num_latches, _num_outputs, _num_ands = parse_aiger_header(aag_text)

    lines = aag_text.splitlines()
    input_literals: list[int] = []

    for index in range(num_inputs):
        input_literals.append(int(lines[1 + index].strip()))

    return input_literals


def parse_aiger_input_symbols(aag_text: str) -> list[str]:
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

        if not index_text[1:].isdigit():
            continue

        index = int(index_text[1:])

        if index < num_inputs:
            symbols[index] = symbol

    return symbols


def input_symbol_to_literal_map(input_symbols: list[str]) -> dict[str, int]:
    return {
        symbol: 2 * (index + 1)
        for index, symbol in enumerate(input_symbols)
    }


def parse_len_symbol(symbol: str) -> int | None:
    prefix = "len_is_"

    if symbol.startswith(prefix) and symbol[len(prefix):].isdigit():
        return int(symbol[len(prefix):])

    return None


def parse_char_symbol(symbol: str) -> tuple[int, str] | None:
    # Expected bounded encoding symbols:
    # x_0_is_a
    # x_1_is_b
    if not symbol.startswith("x_"):
        return None

    parts = symbol.split("_")

    if len(parts) < 4:
        return None

    if parts[2] != "is":
        return None

    if not parts[1].isdigit():
        return None

    position = int(parts[1])
    char = "_".join(parts[3:])

    return position, char


def make_reference_aiger(
    generated_aag_text: str,
    accepted_words: list[str],
    comment: str,
) -> str:
    input_symbols = parse_aiger_input_symbols(generated_aag_text)
    literal_by_symbol = input_symbol_to_literal_map(input_symbols)

    length_symbols: dict[int, str] = {}
    char_symbols: dict[tuple[int, str], str] = {}

    for symbol in input_symbols:
        length = parse_len_symbol(symbol)

        if length is not None:
            length_symbols[length] = symbol
            continue

        parsed_char = parse_char_symbol(symbol)

        if parsed_char is not None:
            char_symbols[parsed_char] = symbol

    builder = AigerBuilder(input_symbols)
    word_literals: list[int] = []

    for word in accepted_words:
        literals: list[int] = []

        if length_symbols:
            if len(word) not in length_symbols:
                # This word cannot be represented by the generated input interface.
                continue

            literals.append(literal_by_symbol[length_symbols[len(word)]])

            for length, symbol in sorted(length_symbols.items()):
                if length != len(word):
                    literals.append(literal_by_symbol[symbol] ^ 1)

        for position, char in enumerate(word):
            key = (position, char)

            if key not in char_symbols:
                raise AssertionError(
                    f"Accepted word {word!r} needs input symbol x_{position}_is_{char}, "
                    "but the generated AIGER interface does not contain it."
                )

            literals.append(literal_by_symbol[char_symbols[key]])

        word_literals.append(builder.and_all(literals))

    output_literal = builder.or_all(word_literals)

    return builder.render(output_literal, comment)


def force_first_output_false(aag_text: str) -> str:
    max_var, num_inputs, num_latches, num_outputs, _num_ands = parse_aiger_header(aag_text)

    if num_outputs < 1:
        raise AssertionError("Cannot corrupt AIGER without outputs")

    lines = aag_text.splitlines()
    first_output_index = 1 + num_inputs + num_latches
    lines[first_output_index] = "0"

    return "\n".join(lines) + "\n"


def parse_cnf_literal_mapping(cnf_text: str) -> dict[int, int]:
    mapping: dict[int, int] = {}

    for line in cnf_text.splitlines():
        parts = line.strip().split()

        if len(parts) == 4 and parts[0] == "c" and parts[2] == "->":
            mapping[int(parts[1])] = int(parts[3])

    return mapping


def build_input_variable_map(aag_text: str, cnf_text: str) -> dict[str, int]:
    input_literals = parse_aiger_input_literals(aag_text)
    input_symbols = parse_aiger_input_symbols(aag_text)
    literal_to_cnf_var = parse_cnf_literal_mapping(cnf_text)

    result: dict[str, int] = {}

    for literal, symbol in zip(input_literals, input_symbols):
        if literal in literal_to_cnf_var:
            result[symbol] = literal_to_cnf_var[literal]

    return result


def make_valid_input_clauses(input_var_by_symbol: dict[str, int]) -> tuple[list[str], str]:
    clauses: list[str] = []

    len_vars: list[int] = []
    char_vars_by_position: dict[int, list[int]] = {}

    for symbol, variable in input_var_by_symbol.items():
        length = parse_len_symbol(symbol)

        if length is not None:
            len_vars.append(variable)
            continue

        parsed_char = parse_char_symbol(symbol)

        if parsed_char is not None:
            position, _char = parsed_char
            char_vars_by_position.setdefault(position, []).append(variable)

    if len_vars:
        clauses.append(" ".join(str(variable) for variable in sorted(len_vars)) + " 0")

        for left, right in combinations(sorted(len_vars), 2):
            clauses.append(f"-{left} -{right} 0")

    for position in sorted(char_vars_by_position):
        variables = sorted(char_vars_by_position[position])

        if variables:
            clauses.append(" ".join(str(variable) for variable in variables) + " 0")

        for left, right in combinations(variables, 2):
            clauses.append(f"-{left} -{right} 0")

    description = (
        "valid bounded string encoding: exactly one length input if length inputs exist, "
        "and exactly one character input for each represented position"
    )

    return clauses, description


def add_clauses_to_cnf(src: Path, dst: Path, extra_clauses: list[str]) -> None:
    lines = src.read_text(encoding="utf-8").splitlines()
    out: list[str] = []

    saw_header = False

    for line in lines:
        if line.startswith("p cnf"):
            parts = line.split()
            num_vars = int(parts[2])
            num_clauses = int(parts[3])
            out.append(f"p cnf {num_vars} {num_clauses + len(extra_clauses)}")
            saw_header = True
        else:
            out.append(line)

    if not saw_header:
        raise AssertionError(f"CNF header not found in {src}")

    out.extend(extra_clauses)
    dst.write_text("\n".join(out) + "\n", encoding="utf-8")


def parse_sat_file(path: Path) -> tuple[str, list[int]]:
    text = path.read_text(encoding="utf-8").split()

    if not text:
        raise AssertionError(f"Empty SAT solver output: {path}")

    result = text[0]

    if result == "UNSAT":
        return "UNSAT", []

    if result != "SAT":
        raise AssertionError(f"Unexpected SAT solver output in {path}: {result}")

    assignment: list[int] = []

    for token in text[1:]:
        value = int(token)

        if value == 0:
            break

        assignment.append(value)

    return "SAT", assignment


def assignment_to_map(assignment: list[int]) -> dict[int, bool]:
    values: dict[int, bool] = {}

    for literal in assignment:
        values[abs(literal)] = literal > 0

    return values


def decode_bounded_assignment(
    input_var_by_symbol: dict[str, int],
    assignment: list[int],
) -> tuple[str, str]:
    if not assignment:
        return "", ""

    values = assignment_to_map(assignment)

    active_length: int | None = None
    active_chars: dict[int, str] = {}
    readable_parts: list[str] = []

    for symbol, variable in sorted(input_var_by_symbol.items()):
        value = values.get(variable, False)
        readable_parts.append(f"{symbol}={1 if value else 0}")

        if not value:
            continue

        length = parse_len_symbol(symbol)

        if length is not None:
            active_length = length
            continue

        parsed_char = parse_char_symbol(symbol)

        if parsed_char is not None:
            position, char = parsed_char
            active_chars[position] = char

    if active_length is None:
        if active_chars:
            active_length = max(active_chars) + 1
        else:
            active_length = 0

    decoded_chars = [
        active_chars.get(position, "?")
        for position in range(active_length)
    ]

    return repr("".join(decoded_chars)), ", ".join(readable_parts)


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
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")

    for row in rows:
        lines.append(
            "| "
            + " | ".join(clean_markdown(row.get(header, "")) for header in headers)
            + " |"
        )

    return "\n".join(lines) + "\n"


def generate_case(case: dict[str, object]) -> dict[str, object]:
    case_id = str(case["case_id"])
    description = str(case["description"])
    pattern = str(case["pattern"])
    comparison = str(case["comparison"])
    expected_result = str(case["expected_result"])

    bound_value = case["bound"]
    if not isinstance(bound_value, int):
        raise TypeError(f"Expected integer bound for {case_id}, got {bound_value!r}")
    bound = bound_value

    accepted_words_value = case["accepted_words"]
    if not isinstance(accepted_words_value, list):
        raise TypeError(f"Expected accepted_words list for {case_id}")
    accepted_words = [str(word) for word in accepted_words_value]

    use_corrupted_generated = bool(case["use_corrupted_generated"])

    generated_path = GENERATED_DIR / f"{case_id}_{comparison}_generated.aag"
    reference_path = REFERENCE_DIR / f"{case_id}_{comparison}_reference.aag"
    compared_generated_path = generated_path

    generated_aag = compile_regex_to_aiger(pattern, bound)
    generated_path.write_text(generated_aag, encoding="utf-8")

    reference_aag = make_reference_aiger(
        generated_aag,
        accepted_words,
        comment=(
            "independent exact-word reference circuit generated from explicit accepted_words; "
            f"pattern={pattern!r}, bound={bound}, accepted_words={accepted_words!r}"
        ),
    )
    reference_path.write_text(reference_aag, encoding="utf-8")

    if use_corrupted_generated:
        compared_generated_path = CORRUPTED_DIR / f"{case_id}_{comparison}_generated_output_forced_false.aag"
        compared_generated_path.write_text(force_first_output_false(generated_aag), encoding="utf-8")

    stem = f"{case_id}_{comparison}"

    miter_path = MITER_DIR / f"{stem}.aag"
    raw_cnf_path = CNF_DIR / f"{stem}.cnf"
    constrained_cnf_path = CNF_DIR / f"{stem}_valid_input.cnf"
    sat_path = WITNESS_DIR / f"{stem}.sat"

    run(
        [
            str(AIGMITER),
            "-o",
            str(miter_path),
            str(compared_generated_path),
            str(reference_path),
        ]
    )

    run(
        [
            str(AIGTOCNF),
            "-m",
            str(miter_path),
            str(raw_cnf_path),
        ]
    )

    miter_aag = miter_path.read_text(encoding="utf-8")
    raw_cnf = raw_cnf_path.read_text(encoding="utf-8")

    input_var_by_symbol = build_input_variable_map(miter_aag, raw_cnf)
    extra_clauses, constraint_description = make_valid_input_clauses(input_var_by_symbol)
    add_clauses_to_cnf(raw_cnf_path, constrained_cnf_path, extra_clauses)

    run(
        [
            str(MINISAT),
            str(constrained_cnf_path),
            str(sat_path),
        ],
        allowed_return_codes=(10, 20),
    )

    model_checker_result, assignment = parse_sat_file(sat_path)
    decoded_witness, readable_assignment = decode_bounded_assignment(
        input_var_by_symbol,
        assignment,
    )

    verdict = "PASS" if model_checker_result == expected_result else "FAIL"

    return {
        "case_id": case_id,
        "description": description,
        "pattern": pattern,
        "bound": bound,
        "accepted_words": repr(accepted_words),
        "comparison": comparison,
        "model_checker_result": model_checker_result,
        "expected_model_checker_result": expected_result,
        "verdict": verdict,
        "decoded_counterexample": decoded_witness,
        "readable_assignment": readable_assignment,
        "witness_assignment": " ".join(str(literal) for literal in assignment),
        "valid_input_constraints": constraint_description,
        "generated_aiger_file": artifact_relative(generated_path),
        "compared_generated_aiger_file": artifact_relative(compared_generated_path),
        "reference_aiger_file": artifact_relative(reference_path),
        "miter_file": artifact_relative(miter_path),
        "raw_cnf_file": artifact_relative(raw_cnf_path),
        "constrained_cnf_file": artifact_relative(constrained_cnf_path),
        "sat_witness_file": artifact_relative(sat_path),
    }


def write_readme() -> None:
    content = """# Bounded reference equivalence artifacts

This directory contains bounded equivalence-checking artifacts against an independent reference circuit.

The flow is:

```text
regex pattern
-> generated bounded AIGER from the compiler

explicit accepted_words list
-> independent exact-word reference AIGER

generated AIGER
reference AIGER
-> aigmiter
-> aigtocnf
-> valid input constraints
-> minisat
-> SAT/UNSAT
-> optional decoded counterexample string
```

## Why this is useful

Simulation checks selected example strings.

This artifact checks whether the generated bounded AIGER and the independent reference AIGER differ on any valid bounded string encoding. If the result is UNSAT, there is no counterexample within that bounded input space.

## Scope

This is a bounded equivalence artifact. It is not an unbounded formal proof of the whole compiler.

The reference circuit is intentionally simple: it is built directly from an explicit list of accepted words. It does not reuse the regex compiler pipeline.
"""

    (ARTIFACT_ROOT / "README.md").write_text(content, encoding="utf-8")


def main() -> None:
    require_tools()
    ensure_dirs()

    rows = [generate_case(case) for case in CASES]

    headers = [
        "case_id",
        "description",
        "pattern",
        "bound",
        "accepted_words",
        "comparison",
        "model_checker_result",
        "expected_model_checker_result",
        "verdict",
        "decoded_counterexample",
        "readable_assignment",
        "witness_assignment",
        "valid_input_constraints",
        "generated_aiger_file",
        "compared_generated_aiger_file",
        "reference_aiger_file",
        "miter_file",
        "raw_cnf_file",
        "constrained_cnf_file",
        "sat_witness_file",
    ]

    write_csv(ARTIFACT_ROOT / "reference_equivalence.csv", headers, rows)
    (ARTIFACT_ROOT / "reference_equivalence.md").write_text(
        "# Bounded reference equivalence checks\n\n"
        + make_markdown_table(headers, rows),
        encoding="utf-8",
    )

    write_readme()

    failing_rows = [row for row in rows if row["verdict"] != "PASS"]

    if failing_rows:
        raise AssertionError(f"Reference equivalence artifacts contain failing rows: {failing_rows}")

    print(f"Wrote reference equivalence artifacts to: {ARTIFACT_ROOT}")
    print(f"Rows: {len(rows)}")

    for row in rows:
        print(
            f"{row['case_id']}: {row['comparison']} -> "
            f"{row['model_checker_result']} decoded={row['decoded_counterexample']}"
        )


if __name__ == "__main__":
    main()
