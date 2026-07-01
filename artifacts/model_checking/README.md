# Model checking artifacts

This directory contains a small model-checking-style validation artifact.

The generated flow is:

```text
aigmiter
-> aigtocnf
-> minisat
-> SAT/UNSAT result
-> optional witness decoding
```

For the negative case, the script compares a correct generated AIGER file with a deliberately corrupted AIGER file.
The miter output is satisfiable exactly when the two circuits differ on some input assignment.

Because arbitrary Boolean assignments do not necessarily represent real candidate strings, the generated CNF is strengthened with bounded input-validity constraints:

```text
exactly one active length input
exactly one active symbol input per represented position
```

With these constraints, a SAT assignment can be decoded back into a real candidate string such as `ab`.

This is not yet a full formal proof of compiler correctness. It is a first artifact showing automatic counterexample extraction for bounded AIGER circuits using an external SAT/model-checking-style toolchain.
