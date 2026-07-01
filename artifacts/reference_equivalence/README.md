# Bounded reference equivalence artifacts

This directory contains bounded equivalence-checking artifacts against an independent reference circuit.

The flow is:

```text
regex pattern
-> generated bounded AIGER from the compiler

explicit accepted_words list
-> independent exact-word reference AIGER

generated AIGER
reference AIGER
-> aigmiter
-> aigtocnf
-> valid input constraints
-> minisat
-> SAT/UNSAT
-> optional decoded counterexample string
```

## Why this is useful

Simulation checks selected example strings.

This artifact checks whether the generated bounded AIGER and the independent reference AIGER differ on any valid bounded string encoding. If the result is UNSAT, there is no counterexample within that bounded input space.

## Scope

This is a bounded equivalence artifact. It is not an unbounded formal proof of the whole compiler.

The reference circuit is intentionally simple: it is built directly from an explicit list of accepted words. It does not reuse the regex compiler pipeline.
