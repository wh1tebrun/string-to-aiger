#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

IMAGE="${RIC3_IMAGE:-gipsyh/ric3:1.6}"
RIC3_RUNNER="$ROOT/validation/ric3_result.py"
mkdir -p outputs

check_case() {
    local name="$1"
    local pattern="$2"
    local expected="$3"
    local model="outputs/${name}.aag"
    local stdout_log="outputs/${name}.ric3.stdout.log"
    local stderr_log="outputs/${name}.ric3.stderr.log"
    local result_file="outputs/${name}.ric3.result"
    local ric3_status
    local actual

    echo
    echo "============================================================"
    echo "Case:     $name"
    echo "Pattern:  $pattern"
    echo "Expected: $expected"
    echo "============================================================"

    python3 -m string_to_aiger \
        --pattern "$pattern" \
        --backend sequential \
        --output "$model"

    set +e
    python3 "$RIC3_RUNNER" \
        --stdout-log "$stdout_log" \
        --stderr-log "$stderr_log" \
        --result-file "$result_file" \
        -- \
        docker run --rm \
            -v "$ROOT/$model:/model.aag:ro" \
            "$IMAGE" \
            check --witness /model.aag ic3
    ric3_status=$?
    set -e

    if [[ "$ric3_status" -ne 0 ]]; then
        echo "FAIL: rIC3 command or result parsing exited with status $ric3_status"
        exit "$ric3_status"
    fi

    actual="$(<"$result_file")"

    if [[ "$actual" != "$expected" ]]; then
        echo "FAIL: expected $expected, received ${actual:-no result}"
        exit 1
    fi

    echo "PASS: $name -> $actual"
}

check_case \
    "ric3_ab_sat" \
    "ab" \
    "SAT"

check_case \
    "ric3_b_and_c_unsat" \
    "b&c" \
    "UNSAT"

check_case \
    "ric3_professor_exact_epsilon_sat" \
    "(ab|ba)*&(aa|bb)*" \
    "SAT"

check_case \
    "ric3_professor_nonempty_unsat" \
    "((ab|ba)(ab|ba)*)&((aa|bb)(aa|bb)*)" \
    "UNSAT"

echo
echo "All rIC3 hardware model-checking cases passed."
