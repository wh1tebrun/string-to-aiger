# Testing and External Semantic Validation

This project does not only generate ASCII AIGER files syntactically.

It also performs end-to-end semantic validation of the generated AIGER circuits.

The main validation pipeline is:

```text
regular expression
-> parser / AST
-> NFA or product automaton
-> bounded or sequential AIGER generation
-> external simulation with aigsim
-> comparison against reference r```x semantics
```

# External AIGER Simulation with aigsim

The generated .aag files are simulated using Armin Biere's aigsim.

This is important because it checks the generated AIGER file as an external artifact.

A bug in literal numbering, AND gate encoding, header generation, latch encoding, or output wiring can be detected at the AIGER level.

The external tests require the environment variable AIGSIM to point to the aigsim binary:

```bash
export AIGSIM=/home/```tekin/tools/aiger/aigsim
```

Then the full test suite can be run with:

```bash
python3 run_all_tests.py
```

The external semantic tests intentionally fail if AIGSIM is not configured.

This avoids silently passing the test suite without actually validating generated AIGER files.

# What Is Tested?

# Bounded Combinational AIGER

The bounded backend compiles a r```x into a combinational AIGER circuit for words up to a fixed bound.

The tests check examples such as:

```text
a*
(ab)*
(a|b)*
(a|ba)*
a?
a+
a{2}
[ab]*
(a|b)*&a*
a*&b*
(ab)*&(a|b)*
```

For each candidate word, the test:

1. encodes the word as AIGER input bits,
2. runs the generated .aag file with aigsim,
3. parses the output bit,
4. compares it with the expected r```x semantics.

# Sequential Latch-Based AIGER

The sequential backend compiles a r```x into an AIGER circuit with latches.

Candidate words are encoded as traces.

Each character is one simulation step, followed by a final end step.

For example, for a sequential circuit with inputs:

```text
end
is_a
```

the word aa is encoded as:

```text
01
01
10
.
```

The final output on the end step is compared against the expected r```x result.

Sequential tests cover:

```text
a*
(ab)*
(a|b)*
a?
a+
a{2}
[ab]*
(a|ba)*
(a|b)*&a*
a*&b*
```

# Product Automaton Strategy

For r```x intersections, the project supports a product-automaton strategy.

The product strategy is externally validated for both:

```text
bounded product AIGER
sequential product AIGER
```

Example patterns include:

```text
(a|b)*&a*
a*&b*
(ab)*&(a|b)*
```

# Cross-Backend Consistency

The test suite also checks that different backends agree on the same r```x and candidate words.

For selected intersection patterns, the following backends are compared:

```text
bounded structural backend
bounded product backend
sequential structural backend
sequential product backend
```

All generated AIGER files are simulated with aigsim, and the resulting accept/reject outputs must match.

This helps detect backend-specific errors.

# Deterministic Fuzzing

The project also includes deterministic fuzz tests.

The fuzzers generate many small r```xes over a fixed alphabet using a fixed random seed.

Because the seed is fixed, the tests are reproducible.

The fuzzing pipeline is:

```text
generated r```x
-> AIGER generation
-> aigsim simulation
-> reference r```x semantics
-> output comparison
```

There are fuzz tests for:

```text
bounded AIGER
sequential AIGER
```

The fuzzer helped detect nested-intersection and constant-output edge cases during development.

# Reference Semantics

Expected results are computed using the r```x parser, NFA construction, product-aware NFA construction for intersections, and the NFA evaluator.

This means the tests validate the AIGER encoding pipeline against the project's reference r```x semantics.

The NFA and product-NFA components are also tested separately with hand-written unit tests.

# What This Does and Does Not Prove

These tests are not a formal correctness proof.

They do not prove that the compiler is correct for all possible r```xes and all possible inputs.

However, they provide practical end-to-end semantic validation:

```text
generated AIGER file
-> external simulator
-> observed circuit behavior
-> comparison with expected r```x behavior
```

This ensures that the generated AIGER circuits are not only syntactically valid, but are also semantically checked on representative, cross-backend, and deterministic fuzz-generated cases.