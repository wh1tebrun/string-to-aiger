#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

IMAGE="${RIC3_IMAGE:-gipsyh/ric3:1.6}"
mkdir -p outputs

check_case() {
    local name="$1"
    local pattern="$2"
    local expected="$3"
    local model="outputs/${name}.aag"

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
    output="$(
        docker run --rm \
            -v "$ROOT/$model:/model.aag:ro" \
            "$IMAGE" \
            check /model.aag ic3 2>&1
    )"
    ric3_status=$?
    set -e

    printf '%s\n' "$output"

    actual="$(
        printf '%s\n' "$output" |
        awk '/^(SAT|UNSAT)$/ { result=$0 } END { print result }'
    )"

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
