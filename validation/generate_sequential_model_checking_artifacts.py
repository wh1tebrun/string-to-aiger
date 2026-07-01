from __future__ import annotations

import csv
import shutil
import subprocess
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AIGER_TOOLS = Path('/home/egetekin/tools/aiger')
AIGMITER = AIGER_TOOLS / 'aigmiter'
AIGUNROLL = AIGER_TOOLS / 'aigunroll'
AIGTOCNF = AIGER_TOOLS / 'aigtocnf'
MINISAT = shutil.which('minisat')

ARTIFACT_ROOT = ROOT / 'artifacts' / 'sequential_model_checking'
MITER_DIR = ARTIFACT_ROOT / 'miters'
UNROLLED_DIR = ARTIFACT_ROOT / 'unrolled'
CNF_DIR = ARTIFACT_ROOT / 'cnf'
WITNESS_DIR = ARTIFACT_ROOT / 'witnesses'
VALIDATION_AIGER_DIR = ROOT / 'artifacts' / 'validation' / 'aiger'

CASES = [
    {
        'case_id': 'SQMC001',
        'description': 'sanity check: sequential correct AIGER compared with itself',
        'pattern': '(bc)*',
        'depth': 3,
        'comparison': 'correct_vs_correct',
        'left_aiger': VALIDATION_AIGER_DIR / 'N004_sequential_correct.aag',
        'right_aiger': VALIDATION_AIGER_DIR / 'N004_sequential_correct.aag',
        'expected_result': 'UNSAT',
    },
    {
        'case_id': 'SQMC002',
        'description': 'negative check: sequential correct AIGER compared with output-forced-false corrupted AIGER',
        'pattern': '(bc)*',
        'depth': 3,
        'comparison': 'correct_vs_corrupted_output_forced_false',
        'left_aiger': VALIDATION_AIGER_DIR / 'N004_sequential_correct.aag',
        'right_aiger': VALIDATION_AIGER_DIR / 'N004_sequential_output_forced_false.aag',
        'expected_result': 'SAT',
    },
]


def run(command: list[str], allowed_return_codes: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.returncode not in allowed_return_codes:
        raise AssertionError(
            'Command failed\n'
            f"command: {' '.join(command)}\n"
            f'return code: {result.returncode}\n'
            f'stdout:\n{result.stdout}\n'
            f'stderr:\n{result.stderr}'
        )
    return result


def require_tools() -> None:
    for tool in [AIGMITER, AIGUNROLL, AIGTOCNF]:
        if not tool.exists():
            raise AssertionError(f'Required AIGER tool not found: {tool}')
    if MINISAT is None:
        raise AssertionError('minisat executable not found. Install it with: sudo apt install minisat')


def ensure_dirs() -> None:
    for directory in [MITER_DIR, UNROLLED_DIR, CNF_DIR, WITNESS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def artifact_relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def parse_aiger_header(aag_text: str) -> tuple[int, int, int, int, int]:
    first_line = aag_text.splitlines()[0]
    parts = first_line.split()
    if len(parts) != 6 or parts[0] != 'aag':
        raise AssertionError(f'Invalid AIGER header: {first_line}')
    return tuple(int(value) for value in parts[1:])  # type: ignore[return-value]


def parse_aiger_input_literals(aag_text: str) -> list[int]:
    _max_var, num_inputs, _num_latches, _num_outputs, _num_ands = parse_aiger_header(aag_text)
    lines = aag_text.splitlines()
    return [int(lines[1 + index].strip()) for index in range(num_inputs)]


def parse_unrolled_input_symbols(aag_text: str) -> dict[int, str]:
    symbols: dict[int, str] = {}
    for line in aag_text.splitlines():
        line = line.strip()
        if not line.startswith('i'):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        index_text, name = parts
        if not index_text[1:].isdigit():
            continue
        symbols[int(index_text[1:])] = name
    return symbols


def parse_step_signal(symbol: str) -> tuple[int, str]:
    parts = symbol.split()
    if len(parts) < 2:
        raise AssertionError(f'Unsupported unrolled input symbol: {symbol}')
    return int(parts[0]), parts[1]


def parse_cnf_literal_mapping(cnf_text: str) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for line in cnf_text.splitlines():
        parts = line.strip().split()
        if len(parts) == 4 and parts[0] == 'c' and parts[2] == '->':
            mapping[int(parts[1])] = int(parts[3])
    return mapping


def build_input_variable_map(unrolled_aag: str, cnf_text: str) -> dict[tuple[int, str], int]:
    input_literals = parse_aiger_input_literals(unrolled_aag)
    input_symbols = parse_unrolled_input_symbols(unrolled_aag)
    literal_to_cnf_var = parse_cnf_literal_mapping(cnf_text)
    result: dict[tuple[int, str], int] = {}
    for input_index, literal in enumerate(input_literals):
        if input_index not in input_symbols:
            continue
        if literal not in literal_to_cnf_var:
            continue
        step, signal = parse_step_signal(input_symbols[input_index])
        result[(step, signal)] = literal_to_cnf_var[literal]
    return result


def make_valid_trace_clauses(input_var_by_step_signal: dict[tuple[int, str], int], depth: int) -> tuple[list[str], str]:
    clauses: list[str] = []
    signals_by_step: dict[int, list[tuple[str, int]]] = {}
    for (step, signal), variable in input_var_by_step_signal.items():
        signals_by_step.setdefault(step, []).append((signal, variable))

    for step in range(depth):
        entries = signals_by_step.get(step, [])
        end_vars = [variable for signal, variable in entries if signal == 'end']
        symbol_vars = [variable for signal, variable in entries if signal.startswith('is_')]
        is_final_step = step == depth - 1

        for variable in end_vars:
            clauses.append(f'{variable} 0' if is_final_step else f'-{variable} 0')

        if is_final_step:
            for variable in symbol_vars:
                clauses.append(f'-{variable} 0')
        elif symbol_vars:
            clauses.append(' '.join(str(variable) for variable in symbol_vars) + ' 0')
            for left, right in combinations(symbol_vars, 2):
                clauses.append(f'-{left} -{right} 0')

    description = 'normal steps: end false and exactly one present symbol input; final step: end true and present symbol inputs false'
    return clauses, description


def add_clauses_to_cnf(src: Path, dst: Path, extra_clauses: list[str]) -> None:
    lines = src.read_text(encoding='utf-8').splitlines()
    out: list[str] = []
    saw_header = False
    for line in lines:
        if line.startswith('p cnf'):
            parts = line.split()
            num_vars = int(parts[2])
            num_clauses = int(parts[3])
            out.append(f'p cnf {num_vars} {num_clauses + len(extra_clauses)}')
            saw_header = True
        else:
            out.append(line)
    if not saw_header:
        raise AssertionError(f'CNF header not found in {src}')
    out.extend(extra_clauses)
    dst.write_text('\n'.join(out) + '\n', encoding='utf-8')


def parse_sat_file(path: Path) -> tuple[str, list[int]]:
    text = path.read_text(encoding='utf-8').split()
    if not text:
        raise AssertionError(f'Empty SAT solver output: {path}')
    result = text[0]
    if result == 'UNSAT':
        return 'UNSAT', []
    if result != 'SAT':
        raise AssertionError(f'Unexpected SAT solver output in {path}: {result}')
    assignment: list[int] = []
    for token in text[1:]:
        value = int(token)
        if value == 0:
            break
        assignment.append(value)
    return 'SAT', assignment


def assignment_to_map(assignment: list[int]) -> dict[int, bool]:
    return {abs(literal): literal > 0 for literal in assignment}


def decode_trace(input_var_by_step_signal: dict[tuple[int, str], int], assignment: list[int], depth: int) -> tuple[str, str]:
    if not assignment:
        return '', ''
    values = assignment_to_map(assignment)
    decoded_chars: list[str] = []
    readable_steps: list[str] = []

    for step in range(depth):
        signals: list[str] = []
        end_value = False
        active_symbols: list[str] = []
        for (signal_step, signal), variable in sorted(input_var_by_step_signal.items()):
            if signal_step != step:
                continue
            value = values.get(variable, False)
            signals.append(f'{signal}={1 if value else 0}')
            if signal == 'end':
                end_value = value
            elif signal.startswith('is_') and value:
                active_symbols.append(signal.removeprefix('is_'))

        if end_value:
            readable_steps.append(f"step {step}: end, " + ', '.join(signals))
            break
        if len(active_symbols) == 1:
            decoded_chars.append(active_symbols[0])
            readable_steps.append(f"step {step}: char={active_symbols[0]!r}, " + ', '.join(signals))
        elif len(active_symbols) == 0:
            readable_steps.append(f"step {step}: no active symbol, " + ', '.join(signals))
        else:
            readable_steps.append(f"step {step}: multiple active symbols={active_symbols}, " + ', '.join(signals))

    return repr(''.join(decoded_chars)), ' / '.join(readable_steps)


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def clean_markdown(value: object) -> str:
    return str(value).replace('\n', '<br>').replace('|', '\\|')


def make_markdown_table(headers: list[str], rows: list[dict[str, object]]) -> str:
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |']
    for row in rows:
        lines.append('| ' + ' | '.join(clean_markdown(row.get(header, '')) for header in headers) + ' |')
    return '\n'.join(lines) + '\n'


def generate_case(case: dict[str, object]) -> dict[str, object]:
    case_id = str(case['case_id'])
    description = str(case['description'])
    pattern = str(case['pattern'])
    comparison = str(case['comparison'])
    expected_result = str(case['expected_result'])
    depth_value = case['depth']
    if not isinstance(depth_value, int):
        raise TypeError(f'Expected integer depth for {case_id}, got {depth_value!r}')
    depth = depth_value
    left_aiger = Path(str(case['left_aiger']))
    right_aiger = Path(str(case['right_aiger']))
    if not left_aiger.exists():
        raise AssertionError(f'Missing input AIGER file: {left_aiger}\nRun: python3 validation/generate_validation_artifacts.py')
    if not right_aiger.exists():
        raise AssertionError(f'Missing input AIGER file: {right_aiger}\nRun: python3 validation/generate_validation_artifacts.py')

    stem = f'{case_id}_{comparison}'
    miter_path = MITER_DIR / f'{stem}.aag'
    unrolled_path = UNROLLED_DIR / f'{stem}_k{depth}.aag'
    raw_cnf_path = CNF_DIR / f'{stem}_k{depth}.cnf'
    constrained_cnf_path = CNF_DIR / f'{stem}_k{depth}_valid_trace.cnf'
    sat_path = WITNESS_DIR / f'{stem}_k{depth}.sat'

    run([str(AIGMITER), '-o', str(miter_path), str(left_aiger), str(right_aiger)])
    unroll_result = run([str(AIGUNROLL), '-a', str(depth), str(miter_path)])
    unrolled_path.write_text(unroll_result.stdout, encoding='utf-8')
    run([str(AIGTOCNF), '-m', str(unrolled_path), str(raw_cnf_path)])

    unrolled_aag = unrolled_path.read_text(encoding='utf-8')
    raw_cnf = raw_cnf_path.read_text(encoding='utf-8')
    input_var_by_step_signal = build_input_variable_map(unrolled_aag, raw_cnf)
    extra_clauses, constraint_description = make_valid_trace_clauses(input_var_by_step_signal, depth)
    add_clauses_to_cnf(raw_cnf_path, constrained_cnf_path, extra_clauses)
    run([str(MINISAT), str(constrained_cnf_path), str(sat_path)], allowed_return_codes=(10, 20))

    model_checker_result, assignment = parse_sat_file(sat_path)
    decoded_witness, readable_trace = decode_trace(input_var_by_step_signal, assignment, depth)
    verdict = 'PASS' if model_checker_result == expected_result else 'FAIL'

    return {
        'case_id': case_id,
        'description': description,
        'pattern': pattern,
        'depth': depth,
        'comparison': comparison,
        'model_checker_result': model_checker_result,
        'expected_model_checker_result': expected_result,
        'verdict': verdict,
        'decoded_witness_string': decoded_witness,
        'readable_witness_trace': readable_trace,
        'witness_assignment': ' '.join(str(literal) for literal in assignment),
        'valid_trace_constraints': constraint_description,
        'miter_file': artifact_relative(miter_path),
        'unrolled_aiger_file': artifact_relative(unrolled_path),
        'raw_cnf_file': artifact_relative(raw_cnf_path),
        'constrained_cnf_file': artifact_relative(constrained_cnf_path),
        'sat_witness_file': artifact_relative(sat_path),
    }


def write_readme() -> None:
    content = '''# Sequential model-checking artifacts

This directory contains a small sequential model-checking style validation artifact.

The flow is:

```text
sequential AIGER 1
sequential AIGER 2
-> aigmiter
-> aigunroll for a fixed depth
-> aigtocnf
-> valid trace constraints
-> minisat
-> SAT/UNSAT result
-> decoded witness trace
```

## Cases

The artifact currently contains two cases for the sequential pattern `(bc)*`.

```text
SQMC001:
correct sequential AIGER compared with itself
expected result: UNSAT
meaning: no counterexample trace exists

SQMC002:
correct sequential AIGER compared with an output-forced-false corrupted AIGER
expected result: SAT
meaning: Minisat finds a counterexample trace
decoded witness: "bc"
```

## Interpretation

This is a bounded sequential counterexample extraction artifact.

It does not prove full unbounded correctness of the sequential compiler. It demonstrates that the model-checking style pipeline can extract a sequential witness trace automatically for a deliberately corrupted circuit.
'''
    (ARTIFACT_ROOT / 'README.md').write_text(content, encoding='utf-8')


def main() -> None:
    require_tools()
    ensure_dirs()
    rows = [generate_case(case) for case in CASES]
    headers = [
        'case_id', 'description', 'pattern', 'depth', 'comparison',
        'model_checker_result', 'expected_model_checker_result', 'verdict',
        'decoded_witness_string', 'readable_witness_trace', 'witness_assignment',
        'valid_trace_constraints', 'miter_file', 'unrolled_aiger_file',
        'raw_cnf_file', 'constrained_cnf_file', 'sat_witness_file',
    ]
    write_csv(ARTIFACT_ROOT / 'sequential_counterexamples.csv', headers, rows)
    (ARTIFACT_ROOT / 'sequential_counterexamples.md').write_text(
        '# Sequential model-checking counterexamples\n\n' + make_markdown_table(headers, rows),
        encoding='utf-8',
    )
    write_readme()
    failing_rows = [row for row in rows if row['verdict'] != 'PASS']
    if failing_rows:
        raise AssertionError(f'Sequential model-checking artifacts contain failing rows: {failing_rows}')
    print(f'Wrote sequential model-checking artifacts to: {ARTIFACT_ROOT}')
    print(f'Rows: {len(rows)}')
    for row in rows:
        print(f"{row['case_id']}: {row['comparison']} -> {row['model_checker_result']} decoded={row['decoded_witness_string']}")


if __name__ == '__main__':
    main()
