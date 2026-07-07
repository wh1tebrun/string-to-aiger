# Manual aigsim checks

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
