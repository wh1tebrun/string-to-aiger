# Manual aigsim checks

This directory contains small, manually inspectable `aigsim` checks.

The main validation path is:

```text
AAG file + STIM file -> aigsim -> actual output
```

`aigsim` performs concrete simulation for the supplied stimulus trace. These
checks are intentionally small enough to inspect manually.

## Sequential trace family

The sequential example uses `(bc)*`, analogously to an `(ab)*` example. The
same generated sequential AIGER is simulated on traces of different lengths:

| word | stimulus meaning | expected output |
| --- | --- | --- |
| `<empty>` | `end` | 1 |
| `bc` | `b, c, end` | 1 |
| `bcbc` | `b, c, b, c, end` | 1 |
| `b` | `b, end` | 0 |
| `bcb` | `b, c, b, end` | 0 |

This demonstrates zero repetitions, one repetition, multiple repetitions, and
incomplete rejecting traces.

## Important terminology

`output_forced_false` means a deliberately modified AIGER used as a
negative-control example.

It is not a real compiler output. It is produced by taking a correct AIGER and
forcing its output literal to constant false. This should make accepting
witnesses fail, so the validation pipeline should detect a mismatch.

## How to read the table

For correct AIGER files:

```text
matches_expected_semantics = YES
```

For deliberately modified negative-control AIGER files:

```text
matches_expected_semantics = NO
mismatch_detected = YES
```

The useful result in a negative-control case is that the mismatch is visible
and detected.

## Re-run all manual examples

From the repository root:

```bash
export AIGSIM=/path/to/aiger/aigsim
bash scripts/demo_manual_aigsim_checks.sh
```

Individual examples can also be run directly:

```bash
$AIGSIM artifacts/manual_aigsim_checks/aiger/sequential_bc_star_correct.aag < artifacts/manual_aigsim_checks/stimuli/sequential_accept_bcbc.stim
$AIGSIM artifacts/manual_aigsim_checks/aiger/sequential_bc_star_output_forced_false.aag < artifacts/manual_aigsim_checks/stimuli/sequential_accept_bc.stim
```

The detailed file paths, commands, and captured stdout/stderr files are stored
in the CSV and in `artifacts/manual_aigsim_checks/outputs/`.
