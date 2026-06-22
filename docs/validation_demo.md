# Validation Demo

This document gives a short demo flow for explaining how generated AIGER circuits are semantically validated.

The main point is:

```text
The project does not only generate AIGER files.
It simulates the generated AIGER files with aigsim
and compares the observed circuit behavior against reference r```x semantics.
```

# 1. Motivation

Initially, generating an AIGER file only showed that the compiler could produce an output artifact.

However, this alone is not enough.

The important question is:

```text
Does the generated AIGER circuit actually implement the intended r```x language?
```

Therefore, external semantic validation was added.

# 2. Validation Pipeline

The validation pipeline is:

```text
r```x pattern
-> compiler
-> generated ASCII AIGER
-> aigsim external simulation
-> observed accept/reject output
-> reference r```x semantics
-> comparison
```

This checks the generated `.aag` file as an external artifact.

It can detect errors in:

```text
AIGER header generation
literal numbering
AND gate encoding
output wiring
latch encoding
input encoding
intersection handling
```

# 3. Required Setup

The external semantic tests require `aigsim`.

In my WSL setup:

```bash
export AIGSIM=/home/```tekin/tools/aiger/aigsim
```

The tests intentionally fail if `AIGSIM` is not configured.

This prevents the external validation tests from silently passing without actually running `aigsim`.

# 4. Bounded AIGER Example

Generate a bounded AIGER circuit:

```bash
python3 -m string_to_aiger --pattern "a*" --backend bounded --bound 3 --output outputs/demo_astar_bounded.aag
```

For `a*` with bound 3, the expected behavior is:

```text
""     accepted
"a"    accepted
"aa"   accepted
"aaa"  accepted
"b"    rejected
"ab"   rejected
"aaaa" rejected because it exceeds the bound
```

Run the bounded aigsim validation tests:

```bash
python3 tests/tests_aigsim_bounded.py
```

# 5. Sequential AIGER Example

Generate a sequential AIGER circuit:

```bash
python3 -m string_to_aiger --pattern "a*" --backend sequential --output outputs/demo_astar_sequential.aag
```

The sequential backend uses latches and reads one symbol per step.

For example, the word `aa` is encoded as:

```text
01
01
10
.
```

The final step sets `end = 1`.

Run the sequential aigsim validation tests:

```bash
python3 tests/tests_aigsim_sequential.py
```

# 6. Product Automaton Validation

Intersection patterns can be compiled using an explicit product automaton.

Example:

```bash
python3 -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --intersection-strategy product --bound 4 --output outputs/demo_product_bounded.aag
```

Run product strategy validation:

```bash
python3 tests/tests_aigsim_product.py
```

This validates both bounded and sequential product-based AIGER generation.

# 7. Fuzzing

The project includes deterministic fuzzing.

The bounded fuzzer uses multiple bounds and a three-symbol alphabet.

The sequential fuzzer generates small random r```xes and checks the resulting latch-based AIGER circuits.

Run the fuzzers:

```bash
python3 tests/tests_aigsim_bounded_fuzzer.py
python3 tests/tests_aigsim_sequential_fuzzer.py
```

The fuzzers are deterministic because they use fixed random seeds.

During development, fuzzing helped detect edge cases such as:

```text
nested intersections
constant-output AIGER behavior
zero-input output parsing
```

# 8. Cross-Backend Consistency

The project also checks whether different backend strategies agree.

The compared backends are:

```text
bounded structural backend
bounded product backend
sequential structural backend
sequential product backend
```

Run cross-backend validation:

```bash
python3 tests/tests_aigsim_cross_backend.py
```

This helps detect backend-specific errors.

# 9. Negative Detection Test

The project includes a negative validation test.

It deliberately corrupts a generated AIGER file by replacing the output literal with constant false.

Then it checks whether the semantic validation infrastructure observes the mismatch.

Run it with:

```bash
python3 tests/tests_aigsim_negative_detection.py
```

This shows that the validation infrastructure can actually detect wrong circuit behavior.

# 10. Full Test Suite

Run all tests:

```bash
export AIGSIM=/home/```tekin/tools/aiger/aigsim
python3 run_all_tests.py
```

Expected result:

```text
All tests passed.
```

# 11. What This Validates

For the tested cases, the project checks:

```text
generated AIGER circuit output
=
expected r```x accept/reject result
```

This is done by simulating the generated AIGER file externally with `aigsim`.

Therefore, the validation does not only inspect internal Python objects.

It checks the generated AIGER artifact itself.

# 12. What This Does Not Prove

This is not a formal correctness proof.

It does not prove correctness for all possible r```xes and all possible inputs.

The current validation is testing-based and simulation-based.

However, it is end-to-end and external:

```text
r```x
-> generated AIGER
-> aigsim
-> observed behavior
-> expected semantics
-> comparison
```

# 13. Short Explanation for the Meeting

The concise explanation is:

```text
After generating AIGER files, I added external semantic validation with aigsim.
The tests compile r```xes to AIGER, simulate the generated AIGER files, and compare the outputs against reference r```x semantics.

This is done for bounded circuits, sequential latch-based circuits, product automata, deterministic fuzz-generated cases, cross-backend consistency cases, and deliberately corrupted AIGER files.

So the generated AIGER files are not only syntactically valid; their behavior is checked externally.
```
