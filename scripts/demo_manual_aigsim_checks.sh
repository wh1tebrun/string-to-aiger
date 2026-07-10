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

run_case() {
  local case_id="$1"
  local label="$2"
  local expected="$3"
  local should_match="$4"
  local aag="$5"
  local stim="$6"

  local kind max_var num_inputs num_latches num_outputs num_ands
  read -r kind max_var num_inputs num_latches num_outputs num_ands < <(head -n 1 "$aag")

  local raw_line
  raw_line="$(
    {
      awk 'NF' "$stim" | "$AIGSIM" "$aag" 2>/dev/null || true
    } | awk 'NF { last = $0 } END { print last }'
  )"

  if [[ -z "$raw_line" ]]; then
    printf "%-7s | %-45s | ERROR: no aigsim output\n" "$case_id" "$label"
    return 1
  fi

  local actual
  if (( num_latches > 0 )); then
    actual="$(awk '{ print $3 }' <<< "$raw_line")"
  else
    actual="$(awk '{ print $NF }' <<< "$raw_line")"
  fi

  local verdict
  if [[ "$should_match" == "yes" ]]; then
    if [[ "$actual" == "$expected" ]]; then
      verdict="MATCH"
    else
      verdict="UNEXPECTED"
    fi
  else
    if [[ "$actual" != "$expected" ]]; then
      verdict="MISMATCH DETECTED"
    else
      verdict="UNEXPECTED"
    fi
  fi

  printf "%-7s | %-45s | expected=%s actual=%s | %s\n" \
    "$case_id" "$label" "$expected" "$actual" "$verdict"
}

BOUNDED_CORRECT="artifacts/manual_aigsim_checks/aiger/bounded_ab_or_bc_correct.aag"
BOUNDED_FALSE="artifacts/manual_aigsim_checks/aiger/bounded_ab_or_bc_output_forced_false.aag"
SEQUENTIAL_CORRECT="artifacts/manual_aigsim_checks/aiger/sequential_bc_star_correct.aag"
SEQUENTIAL_FALSE="artifacts/manual_aigsim_checks/aiger/sequential_bc_star_output_forced_false.aag"

echo
echo "Manual aigsim checks"
echo "===================="
echo

run_case MAN001 "bounded ab|bc: accept ab" \
  1 yes "$BOUNDED_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/bounded_accept_ab.stim"

run_case MAN002 "bounded ab|bc: reject ac" \
  0 yes "$BOUNDED_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/bounded_reject_ac.stim"

run_case MAN003 "bounded negative control on ab" \
  1 no "$BOUNDED_FALSE" \
  "artifacts/manual_aigsim_checks/stimuli/bounded_accept_ab.stim"

echo
echo "Sequential trace family for (bc)*"
echo "---------------------------------"

run_case MAN004 "zero repetitions: <empty>, end" \
  1 yes "$SEQUENTIAL_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_accept_empty.stim"

run_case MAN005 "one repetition: b, c, end" \
  1 yes "$SEQUENTIAL_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_accept_bc.stim"

run_case MAN006 "two repetitions: b, c, b, c, end" \
  1 yes "$SEQUENTIAL_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_accept_bcbc.stim"

run_case MAN007 "incomplete repetition: b, end" \
  0 yes "$SEQUENTIAL_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_reject_b.stim"

run_case MAN008 "longer incomplete trace: b, c, b, end" \
  0 yes "$SEQUENTIAL_CORRECT" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_reject_bcb.stim"

run_case MAN009 "sequential negative control on bc" \
  1 no "$SEQUENTIAL_FALSE" \
  "artifacts/manual_aigsim_checks/stimuli/sequential_accept_bc.stim"

echo
echo "Expected summary:"
echo "  correct AIGER cases        -> MATCH"
echo "  negative-control cases     -> MISMATCH DETECTED"
