# Validation and model-checking artifacts

This directory contains the generated validation artifacts for the string-to-AIGER compiler.

The artifacts are intended to make the generated AIGER circuits inspectable and externally checkable. They include simulation-based validation, negative detection, SAT/model-checking style counterexample extraction, sequential trace extraction, and bounded reference equivalence checks.

## Artifact overview

| Validation goal | Artifact | Main result |
| --- | --- | --- |
| External semantic simulation with `aigsim` | `artifacts/validation/validation_matrix.md` | 45 validation rows comparing expected regex semantics with AIGER simulation output |
| Negative detection on deliberately corrupted AIGERs | `artifacts/validation/negative_detection_matrix.md` | 6 negative rows where corrupted AIGERs are detected by mismatching witnesses |
| Bounded miter/CNF/SAT counterexample extraction | `artifacts/model_checking/model_checking_counterexamples.md` | correct-vs-correct is UNSAT; correct-vs-corrupted is SAT and decodes to the witness string `'ab'` |
| Sequential model-checking style trace extraction | `artifacts/sequential_model_checking/sequential_counterexamples.md` | sequential correct-vs-corrupted is SAT and decodes to the trace `b, c, end`, i.e. the string `'bc'` |
| Bounded generated-vs-reference equivalence checking | `artifacts/reference_equivalence/reference_equivalence.md` | generated AIGERs are UNSAT against independent reference AIGERs for selected bounded cases; corrupted generated AIGER is SAT with decoded counterexample `'ab'` |

## Reproducing the artifacts

From the repository root:

```bash
export AIGER_TOOLS=/path/to/aiger
export AIGSIM=/path/to/aiger/aigsim

python3 validation/generate_validation_artifacts.py
python3 validation/generate_model_checking_artifacts.py
python3 validation/generate_sequential_model_checking_artifacts.py
python3 validation/generate_bounded_reference_equivalence_artifacts.py
python3 run_all_tests.py
```

## Scope

These artifacts are bounded validation and model-checking style checks. They are not a full unbounded formal proof of the entire compiler.

The goal is to make the generated AIGER circuits externally inspectable and to show concrete SAT/UNSAT results, witnesses, decoded counterexamples, and trace artifacts.
