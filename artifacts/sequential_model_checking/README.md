# Sequential model-checking artifacts

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
