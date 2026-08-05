#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

if [[ -z "${AIGSIM:-}" ]]; then
  echo "AIGSIM is not set." >&2
  echo "Example: export AIGSIM=/path/to/aiger/aigsim" >&2
  exit 1
fi

if [[ ! -x "$AIGSIM" ]]; then
  echo "aigsim is not executable: $AIGSIM" >&2
  exit 1
fi

if ! TEMP_DIR="$(mktemp -d)" || [[ -z "$TEMP_DIR" || "$TEMP_DIR" != /* || ! -d "$TEMP_DIR" ]]; then
  echo "Failed to create a safe temporary directory." >&2
  exit 1
fi

cleanup() {
  if [[ -n "${TEMP_DIR:-}" && "$TEMP_DIR" == /* && -d "$TEMP_DIR" ]]; then
    rm -rf -- "$TEMP_DIR"
  fi
}

trap cleanup EXIT

failures=0

run_case() {
  local case_id="$1"
  local label="$2"
  local expected="$3"
  local should_match="$4"
  local aag="$5"
  local stim="$6"

  report_failure() {
    local reason="$1"
    printf "%-7s | %-45s | ERROR: %s\n" "$case_id" "$label" "$reason" >&2
    printf "  command: %q %q < %q\n" "$AIGSIM" "$aag" "$stim" >&2
    echo "  stdout:" >&2
    if [[ -s "$stdout_file" ]]; then
      sed 's/^/    /' "$stdout_file" >&2
    else
      echo "    <empty>" >&2
    fi
    echo "  stderr:" >&2
    if [[ -s "$stderr_file" ]]; then
      sed 's/^/    /' "$stderr_file" >&2
    else
      echo "    <empty>" >&2
    fi
  }

  local stdout_file="$TEMP_DIR/${case_id}.stdout"
  local stderr_file="$TEMP_DIR/${case_id}.stderr"
  : > "$stdout_file"
  : > "$stderr_file"

  local kind max_var num_inputs num_latches num_outputs num_ands
  if ! read -r kind max_var num_inputs num_latches num_outputs num_ands < "$aag"; then
    report_failure "cannot read AIGER header"
    return 1
  fi

  if [[ "$kind" != "aag" || ! "$num_inputs" =~ ^[0-9]+$ ||
        ! "$num_latches" =~ ^[0-9]+$ || "$num_outputs" != "1" ]]; then
    report_failure "invalid or unsupported AIGER header"
    return 1
  fi

  local stimulus_size last_byte vector_count
  stimulus_size="$(wc -c < "$stim")"
  if (( stimulus_size == 0 )); then
    report_failure "empty stimulus"
    return 1
  fi

  last_byte="$(tail -c 1 "$stim" | od -An -tuC | tr -d '[:space:]')"
  if [[ "$last_byte" != "10" ]] || LC_ALL=C grep -q $'\r' "$stim"; then
    report_failure "stimulus must use LF only and end with LF"
    return 1
  fi

  if ! vector_count="$(
    awk -v width="$num_inputs" '
      {
        lines[NR] = $0
        if ($0 == ".") {
          dots++
        } else if ($0 !~ /^[01]+$/ || length($0) != width) {
          invalid = 1
        }
      }
      END {
        if (NR < 2 || lines[NR] != "." || dots != 1 || invalid) {
          exit 1
        }
        print NR - 1
      }
    ' "$stim"
  )"; then
    report_failure "stimulus must contain Boolean vectors and one final '.' terminator"
    return 1
  fi

  "$AIGSIM" "$aag" < "$stim" > "$stdout_file" 2> "$stderr_file"
  local exit_code=$?

  if (( exit_code != 0 )); then
    report_failure "aigsim exited with status $exit_code"
    return 1
  fi

  if [[ -s "$stderr_file" ]]; then
    report_failure "aigsim produced unexpected stderr"
    return 1
  fi

  local actual
  if ! actual="$(
    awk \
      -v stimulus_path="$stim" \
      -v expected_count="$vector_count" \
      -v inputs="$num_inputs" \
      -v latches="$num_latches" '
      function is_bits(value, width) {
        return length(value) == width && value ~ /^[01]+$/
      }
      BEGIN {
        while ((getline stimulus_line < stimulus_path) > 0) {
          if (stimulus_line == ".") {
            break
          }
          expected[++stimulus_count] = stimulus_line
        }
        close(stimulus_path)
      }
      {
        line = $0
        sub(/^[[:space:]]+/, "", line)
        sub(/[[:space:]]+$/, "", line)

        if (line == "") {
          next
        }

        if (line ~ /^Trace is a witness for: \{[^}]*\}$/) {
          if (witness_seen || semantic_count != expected_count) {
            invalid = 1
          }
          witness_seen = 1
          next
        }

        if (witness_seen) {
          invalid = 1
        }

        semantic_count++
        field_count = split(line, fields, /[[:space:]]+/)

        if (latches > 0) {
          if (field_count != 4 || !is_bits(fields[1], latches) ||
              fields[2] != expected[semantic_count] ||
              fields[3] !~ /^[01]$/ || !is_bits(fields[4], latches)) {
            invalid = 1
          } else {
            actual = fields[3]
          }
        } else {
          if (field_count != 2 || fields[1] != expected[semantic_count] ||
              fields[2] !~ /^[01]$/) {
            invalid = 1
          } else {
            actual = fields[2]
          }
        }
      }
      END {
        if (invalid || semantic_count != expected_count ||
            stimulus_count != expected_count || actual !~ /^[01]$/) {
          exit 1
        }
        print actual
      }
    ' "$stdout_file"
  )"; then
    report_failure "missing, malformed, conflicting, or ambiguous aigsim output"
    return 1
  fi

  local verdict
  if [[ "$should_match" == "yes" ]]; then
    if [[ "$actual" == "$expected" ]]; then
      verdict="MATCH"
    else
      report_failure "unexpected semantic mismatch: expected=$expected actual=$actual"
      return 1
    fi
  else
    if [[ "$expected" != "1" ]]; then
      report_failure "negative control does not use an accepting reference witness"
      return 1
    fi
    if [[ "$actual" != "$expected" ]]; then
      verdict="MISMATCH DETECTED"
    else
      report_failure "negative control failed to produce its intended mismatch"
      return 1
    fi
  fi

  printf "%-7s | %-45s | expected=%s actual=%s | %s\n" \
    "$case_id" "$label" "$expected" "$actual" "$verdict"
}

run_required() {
  if ! run_case "$@"; then
    failures=$((failures + 1))
  fi
}

BOUNDED_CORRECT="artifacts/manual_aigsim_checks/aiger/bounded_ab_or_bc_correct.aag"
BOUNDED_FALSE="artifacts/manual_aigsim_checks/aiger/bounded_ab_or_bc_output_forced_false.aag"
SEQUENTIAL_CORRECT="artifacts/manual_aigsim_checks/aiger/sequential_bc_star_correct.aag"
SEQUENTIAL_FALSE="artifacts/manual_aigsim_checks/aiger/sequential_bc_star_output_forced_false.aag"

echo
echo "Manual aigsim checks"
echo "===================="
echo

run_required MAN001 "bounded ab|bc: accept ab" \
  1 yes "$BOUNDED_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/bounded_accept_ab.stim"

run_required MAN002 "bounded ab|bc: reject ac" \
  0 yes "$BOUNDED_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/bounded_reject_ac.stim"

run_required MAN003 "bounded negative control on ab" \
  1 no "$BOUNDED_FALSE" \
  "artifacts/manual_aigsim_checks/stimuli/bounded_accept_ab.stim"

echo
echo "Sequential trace family for (bc)*"
echo "---------------------------------"

run_required MAN004 "zero repetitions: <empty>, end" \
  1 yes "$SEQUENTIAL_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_accept_empty.stim"

run_required MAN005 "one repetition: b, c, end" \
  1 yes "$SEQUENTIAL_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_accept_bc.stim"

run_required MAN006 "two repetitions: b, c, b, c, end" \
  1 yes "$SEQUENTIAL_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_accept_bcbc.stim"

run_required MAN007 "incomplete repetition: b, end" \
  0 yes "$SEQUENTIAL_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_reject_b.stim"

run_required MAN008 "longer incomplete trace: b, c, b, end" \
  0 yes "$SEQUENTIAL_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_reject_bcb.stim"

run_required MAN009 "sequential negative control on bc" \
  1 no "$SEQUENTIAL_FALSE" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_accept_bc.stim"

echo
echo "Expected summary:"
echo "  correct AIGER cases        -> MATCH"
echo "  negative-control cases     -> MISMATCH DETECTED"

if (( failures > 0 )); then
  echo >&2
  echo "Manual aigsim checks failed: $failures required case(s)." >&2
  exit 1
fi

echo
echo "All 9 manual aigsim checks passed."
