# Whiteboard-style validation summary

This file summarizes the validation artifacts in the simple style discussed on the whiteboard: input, expected match/not-match behavior, generated AIGER/model-checking output, witness/counterexample, and verdict.

The detailed machine-readable artifacts are stored in the referenced artifact directories.

## Simple artifact table

| Goal | Case | Pattern | Input / witness | Expected behavior | Tool / check | Result | Verdict | Detailed artifact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| External AIGER simulation | validation matrix | several bounded and sequential regex cases | explicit candidate strings and input vectors/traces | AIGER output should match regex semantics | `aigsim` | 45 validation rows | PASS | `artifacts/validation/validation_matrix.md` |
| Negative detection | negative detection matrix | deliberately corrupted bounded/sequential circuits | selected witness inputs | corrupted AIGER should disagree with expected semantics | `aigsim` | 6 mismatches detected | PASS | `artifacts/validation/negative_detection_matrix.md` |
| Bounded miter check | MC001 | `ab\|bc` | all valid bounded encodings under constraints | correct AIGER vs itself should have no counterexample | `aigmiter` + `aigtocnf` + `minisat` | UNSAT | PASS | `artifacts/model_checking/model_checking_counterexamples.md` |
| Bounded counterexample extraction | MC002 | `ab\|bc` | SAT witness decoded to `'ab'` | correct AIGER vs corrupted AIGER should differ | `aigmiter` + `aigtocnf` + `minisat` | SAT, witness `'ab'` | PASS | `artifacts/model_checking/model_checking_counterexamples.md` |
| Sequential trace extraction | SQMC001 | `(bc)*` | all valid traces up to depth 3 under constraints | correct sequential AIGER vs itself should have no counterexample | `aigmiter` + `aigunroll` + `aigtocnf` + `minisat` | UNSAT | PASS | `artifacts/sequential_model_checking/sequential_counterexamples.md` |
| Sequential counterexample trace | SQMC002 | `(bc)*` | trace `b, c, end`, decoded to `'bc'` | correct sequential AIGER vs corrupted sequential AIGER should differ | `aigmiter` + `aigunroll` + `aigtocnf` + `minisat` | SAT, witness trace `'bc'` | PASS | `artifacts/sequential_model_checking/sequential_counterexamples.md` |
| Independent reference equivalence | REFEQ001 | `ab\|bc` | all valid bounded encodings under constraints | generated AIGER should equal independent exact-word reference | `aigmiter` + `aigtocnf` + `minisat` | UNSAT | PASS | `artifacts/reference_equivalence/reference_equivalence.md` |
| Independent reference negative check | REFEQ002 | `ab\|bc` | SAT witness decoded to `'ab'` | corrupted generated AIGER should differ from independent reference | `aigmiter` + `aigtocnf` + `minisat` | SAT, witness `'ab'` | PASS | `artifacts/reference_equivalence/reference_equivalence.md` |
| Independent reference equivalence | REFEQ003 | `a[bc]` | all valid bounded encodings under constraints | generated AIGER should equal independent exact-word reference | `aigmiter` + `aigtocnf` + `minisat` | UNSAT | PASS | `artifacts/reference_equivalence/reference_equivalence.md` |
| Independent reference equivalence | REFEQ004 | `(a\|b)(a\|b)` | all valid bounded encodings under constraints | generated AIGER should equal independent exact-word reference | `aigmiter` + `aigtocnf` + `minisat` | UNSAT | PASS | `artifacts/reference_equivalence/reference_equivalence.md` |

## Mapping to the whiteboard goals

| Whiteboard goal | Where it is covered |
| --- | --- |
| Show generated AIGER is not just a file | `artifacts/validation/validation_matrix.md` and `artifacts/README.md` |
| Show input encoding | validation matrix, model-checking tables, reference-equivalence tables |
| Show expected match / not-match semantics | validation matrix and negative detection matrix |
| Show generated output / solver result | all artifact tables |
| Show mismatch detection | negative detection matrix, MC002, SQMC002, REFEQ002 |
| Build miter | `artifacts/model_checking/miters/`, `artifacts/sequential_model_checking/miters/`, `artifacts/reference_equivalence/miters/` |
| Convert to CNF | `artifacts/model_checking/cnf/`, `artifacts/sequential_model_checking/cnf/`, `artifacts/reference_equivalence/cnf/` |
| Run SAT solver | `.sat` files in the witness directories |
| Decode SAT witness to string | MC002 decodes to `'ab'`, REFEQ002 decodes to `'ab'` |
| Decode sequential trace | SQMC002 decodes to trace `b, c, end`, i.e. `'bc'` |
| Show valid-input constraints | model-checking, sequential model-checking, and reference-equivalence tables |

## Scope

These artifacts demonstrate bounded validation and model-checking style checking. They do not claim a full unbounded formal proof of the complete compiler.

The main added value is that the generated AIGER circuits are checked externally, counterexamples are represented as concrete witnesses, and selected generated circuits are compared against independent reference circuits over all valid bounded encodings.
