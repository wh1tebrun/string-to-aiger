# string-to-aiger

`string-to-aiger` is a prototype compiler that translates fixed-string and regular-expression constraints into ASCII AIGER circuits.

The project started with fixed-string disjunctions such as:

```text
abba | abb
```

and was later extended with regular expressions, intersection constraints, bounded and sequential AIGER backends, product automata, command-line compilation, and external semantic validation using `aigsim`.

The central goal is not merely to generate syntactically valid AIGER files.

The central goal is to check whether the generated AIGER circuits actually implement the intended string or regular-expression semantics.

# Overview

The high-level pipeline is:

```text
string or r```x constraint
-> parser
-> AST / internal representation
-> NFA or product automaton
-> bounded or sequential circuit encoding
-> ASCII AIGER
-> external simulation with aigsim
-> comparison against reference semantics
```

The project currently supports:

```text
fixed-string disjunctions
regular expressions
bounded combinational AIGER generation
sequential latch-based AIGER generation
intersection constraints with &
structural intersection encoding
product-automaton based intersection encoding
internal AIGER validation
external semantic validation with aigsim
deterministic fuzz testing
cross-backend consistency testing
```

# Supported Constraint Fragment

# Fixed-String Disjunctions

The first supported fragment consists of disjunctions of concrete strings:

```text
abba | abb | abbreviation
```

Each fixed string is compiled into a conjunction of length and character-position constraints.

For example, `abba` is represented by constraints of the form:

```text
len == 4
x[0] == a
x[1] == b
x[2] == b
x[3] == a
```

A disjunction of strings is then encoded as an OR of such exact matchers.

# Regular Expressions

The project supports a useful regular-expression fragment including:

```text
concatenation
union with |
intersection with &
Kleene star with *
one-or-more repetition with +
optional repetition with ?
exact bounded repetition with {n}
bounded repetition ranges with {m,n}
open-ended bounded repetition with {m,}
grouping with parentheses
character classes such as [ab]
character ranges such as [a-c]
basic escaping for literal operators
```

Example patterns:

```text
a*
(ab)*
(a|b)*
(a|ba)*
a?
a+
a{2}
a{1,3}
[ab]*
[a-c]{2,4}
(a|b)*&a*
a*&b*
(ab)*&(a|b)*
```

The parser builds a regular-expression AST. Several surface-level operators are desugared into a small core language.

The core AST contains:

```text
Empty
Char
Concat
UnionExpr
Star
Intersect
```

For example:

```text
a+
```

is represented as:

```text
Concat(Char("a"), Star(Char("a")))
```

and:

```text
a?
```

is represented as:

```text
UnionExpr(Empty(), Char("a"))
```

# Backends

# Bounded Combinational Backend

The bounded backend compiles a r```x into a combinational AIGER circuit for words up to a fixed bound.

For a bound such as:

```text
bound = 3
```

the expression:

```text
a*
```

accepts:

```text
""
"a"
"aa"
"aaa"
```

but rejects:

```text
"aaaa"
```

because the word length exceeds the configured bound.

The bounded backend uses input variables such as:

```text
len_is_0
len_is_1
x_0_is_a
x_0_is_b
x_1_is_a
x_1_is_b
```

This backend is useful for finite-word encodings, SAT-style checks, small examples, and debugging.

# Sequential Latch-Based Backend

The sequential backend compiles a r```x into a latch-based AIGER circuit.

The circuit reads one symbol per simulation step and uses an `end` input to mark the end of the word.

Typical input symbols are:

```text
end
is_a
is_b
```

For example, the word `aa` is encoded as:

```text
01
01
10
.
```

Here the final step sets `end = 1`.

The sequential backend stores active NFA states in latches. Therefore, generated sequential AIGER files have:

```text
L > 0
```

in the AIGER header.

# Intersection Support

The project supports r```x intersection using `&`.

Examples:

```text
(a|b)*&a*
a*&b*
(ab)*&(a|b)*
```

Two compilation strategies are implemented.

# Structural Intersection

Structural intersection compiles both sides separately and combines their accept conditions.

For the bounded backend:

```text
compile(A & B) = compile(A) AND compile(B)
```

For the sequential backend, two circuits are run in parallel and their accept outputs are combined:

```text
accept = accept_A AND accept_B
```

Latch names are renamed to avoid collisions.

# Product Automaton Intersection

The product strategy constructs an explicit product automaton for intersections.

The idea is:

```text
A & B
-> NFA(A)
-> NFA(B)
-> product NFA(A, B)
-> bounded or sequential AIGER
```

This strategy is available for both bounded and sequential AIGER generation.

The CLI exposes both strategies:

```bash
--intersection-strategy structural
--intersection-strategy product
```

# Project Structure

The main package is:

```text
string_to_aiger/
```

Important submodules:

```text
string_to_aiger/fixed/
string_to_aiger/logic/
string_to_aiger/netlist/
string_to_aiger/aiger/
string_to_aiger/r```x/
string_to_aiger/nfa/
string_to_aiger/bounded/
string_to_aiger/sequential/
```

Additional directories:

```text
docs/
demos/
tests/
evaluation/
outputs/
```

The `outputs/` directory is used for generated AIGER files and temporary simulator inputs.

Generated `.aag` and `.stim` files are ignored by Git.

# Important Components

# Fixed-String Layer

```text
string_to_aiger/fixed/parser.py
string_to_aiger/fixed/model.py
string_to_aiger/fixed/matcher.py
string_to_aiger/fixed/compiler.py
```

# Logic and AIGER Generation

```text
string_to_aiger/logic/circuit.py
string_to_aiger/logic/evaluator.py
string_to_aiger/netlist/netlist_builder.py
string_to_aiger/aiger/aiger_writer.py
string_to_aiger/aiger/aiger.py
```

# R```x and Automata Layer

```text
string_to_aiger/r```x/r```x_ast.py
string_to_aiger/r```x/r```x_parser.py
string_to_aiger/r```x/r```x_bounded_compiler.py
string_to_aiger/r```x/r```x_to_aiger.py
string_to_aiger/r```x/r```x_to_product_nfa.py
string_to_aiger/nfa/nfa.py
string_to_aiger/nfa/nfa_builder.py
string_to_aiger/nfa/nfa_evaluator.py
string_to_aiger/nfa/nfa_product.py
```

# Bounded Backend

```text
string_to_aiger/bounded/bounded_nfa_encoding.py
string_to_aiger/bounded/product_bounded_compiler.py
```

# Sequential Backend

```text
string_to_aiger/sequential/sequential_circuit.py
string_to_aiger/sequential/nfa_to_sequential.py
string_to_aiger/sequential/sequential_aiger_writer.py
string_to_aiger/sequential/sequential_simulator.py
string_to_aiger/sequential/sequential_trace.py
string_to_aiger/sequential/sequential_intersection.py
string_to_aiger/sequential/sequential_r```x_compiler.py
string_to_aiger/sequential/product_sequential_compiler.py
```

# Command-Line Interface

The project provides a CLI through:

```bash
python3 -m string_to_aiger
```

Generate a bounded AIGER circuit:

```bash
python3 -m string_to_aiger --pattern "a*" --backend bounded --bound 3 --output outputs/astar_bounded.aag
```

Generate a sequential AIGER circuit:

```bash
python3 -m string_to_aiger --pattern "a*" --backend sequential --output outputs/astar_sequential.aag
```

Generate a bounded AIGER circuit for an intersection:

```bash
python3 -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --bound 4 --output outputs/intersection_bounded.aag
```

Generate a bounded AIGER circuit using product automata:

```bash
python3 -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --intersection-strategy product --bound 4 --output outputs/intersection_product_bounded.aag
```

Generate a sequential AIGER circuit using product automata:

```bash
python3 -m string_to_aiger --pattern "(a|b)*&a*" --backend sequential --intersection-strategy product --output outputs/intersection_product_sequential.aag
```

Compile a pattern from a file:

```bash
python3 -m string_to_aiger --input-file examples/cli_pattern.txt --backend bounded --bound 4 --output outputs/from_file.aag
```

# AIGER Validation

The project includes internal structural validation for generated ASCII AIGER.

The validator checks:

```text
aag header shape
input count
latch count
output count
AND gate count
literal bounds
input literal format
latch line format
output line format
AND gate line format
symbol section structure
comment section structure
```

This catches malformed AIGER text before external tools are used.

The project also supports optional external AIGER validation through the CLI.

External validation can be requested with:

```bash
--external-validation
```

An external command can be provided with:

```bash
--external-validator-command "some-checker --input {path}"
```

# External Semantic Validation with aigsim

A major part of the project is external semantic validation using Armin Biere's `aigsim`.

The validation pipeline is:

```text
r```x
-> generated AIGER
-> aigsim simulation
-> observed accept/reject output
-> reference r```x semantics
-> comparison
```

This checks the generated `.aag` file as an external artifact.

It can detect bugs in:

```text
AIGER header generation
literal numbering
AND gate encoding
inverter handling
output wiring
latch encoding
input encoding
final newline compatibility
intersection handling
```

The external tests require the environment variable `AIGSIM`:

```bash
export AIGSIM=/path/to/aiger/aigsim
```

The tests intentionally fail if `AIGSIM` is not configured. This prevents external semantic validation from silently passing without actually running `aigsim`.

# Test Suite

Run the complete test suite:

```bash
export AIGSIM=/path/to/aiger/aigsim
python3 run_all_tests.py
```

Important internal tests include:

```text
tests/tests.py
tests/tests_r```x.py
tests/tests_r```x_length.py
tests/tests_sequential.py
tests/tests_sequential_trace.py
tests/tests_intersection.py
tests/tests_sequential_intersection.py
tests/tests_cli.py
tests/tests_evaluation.py
tests/tests_generated_benchmarks.py
tests/tests_nfa_product.py
tests/tests_product_backend.py
tests/tests_alphabet.py
tests/tests_nfa_prune.py
tests/tests_nfa_optimize.py
tests/tests_aiger_validator.py
tests/tests_aiger_pipeline.py
tests/tests_external_aiger_validator.py
```

Important external `aigsim` tests include:

```text
tests/tests_aigsim_bounded.py
tests/tests_aigsim_sequential.py
tests/tests_aigsim_product.py
tests/tests_aigsim_bounded_fuzzer.py
tests/tests_aigsim_sequential_fuzzer.py
tests/tests_aigsim_cross_backend.py
```

The shared setup helper is:

```text
tests/aigsim_test_utils.py
```

# Bounded aigsim Tests

The bounded semantic tests compile r```xes to combinational AIGER, simulate the generated AIGER files with `aigsim`, and compare the output against reference r```x semantics.

Covered examples include:

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

# Sequential aigsim Tests

The sequential semantic tests compile r```xes to latch-based AIGER, encode candidate words as traces, simulate the traces with `aigsim`, and compare the final output on the `end` step against reference semantics.

Covered examples include:

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

# Product Strategy Tests

The product strategy is externally validated for both bounded and sequential AIGER.

Example patterns include:

```text
(a|b)*&a*
a*&b*
(ab)*&(a|b)*
```

# Deterministic Fuzzing

The project includes deterministic fuzz tests for both bounded and sequential AIGER generation.

The fuzzers generate many small r```xes with a fixed random seed.

Because the seed is fixed, the tests are reproducible.

The fuzzing pipeline is:

```text
generated r```x
-> AIGER generation
-> aigsim simulation
-> reference r```x semantics
-> output comparison
```

During development, the fuzzer helped detect nested-intersection and constant-output edge cases.

# Cross-Backend Consistency

The project also checks whether different backends agree on the same r```x and candidate words.

The compared backends are:

```text
bounded structural backend
bounded product backend
sequential structural backend
sequential product backend
```

All generated AIGER files are simulated with `aigsim`.

The resulting outputs must agree.

This helps detect backend-specific errors.

# Evaluation

Evaluation scripts are stored under:

```text
evaluation/
```

Run all evaluations:

```bash
python3 run_all_evaluations.py
```

The evaluation includes:

```text
AIGER statistics comparison
selected language behavior validation
exhaustive bounded language validation
generated benchmark smoke tests
```

The main evaluation files are:

```text
evaluation/benchmark_cases.py
evaluation/evaluate_aiger_stats.py
evaluation/evaluate_language_behavior.py
evaluation/evaluate_exhaustive_behavior.py
evaluation/generated_benchmarks.py
```

Generated evaluation outputs include:

```text
evaluation/aiger_stats.csv
evaluation/aiger_stats.md
evaluation/language_behavior.csv
evaluation/language_behavior.md
evaluation/exhaustive_behavior.csv
evaluation/exhaustive_behavior_summary.csv
evaluation/exhaustive_behavior.md
evaluation/generated_benchmarks.csv
evaluation/generated_benchmarks_summary.csv
evaluation/generated_benchmarks.md
```

# Demos

Run all demos:

```bash
python3 run_all_demos.py
```

Individual demos are stored under:

```text
demos/
```

Examples include:

```text
r```x parser demo
NFA demo
NFA evaluator demo
bounded NFA demo
r```x-to-AIGER demo
sequential AIGER demo
intersection demo
product automaton demo
```

Generated AIGER files are written to:

```text
outputs/
```

# Documentation

Additional documentation is stored in:

```text
docs/
```

Important documents include:

```text
docs/r```x_grammar.md
docs/product_automaton.md
docs/testing.md
```

`docs/testing.md` explains the external semantic validation approach in more detail.

# What Is Validated

For the tested cases, the project checks:

```text
generated AIGER circuit output
=
expected r```x accept/reject result
```

This is done by running the generated AIGER files through an external simulator.

Therefore, the tests do not only inspect Python objects internally.

They check the generated AIGER files as actual artifacts.

# What Is Not Proved

The project does not provide a formal correctness proof.

It does not prove that the compiler is correct for every possible r```x and every possible input word.

The validation is testing-based and simulation-based.

However, it is end-to-end and external:

```text
generated AIGER
-> external simulator
-> observed behavior
-> comparison with expected semantics
```

This makes the generated circuits semantically checked on representative examples, product/intersection cases, deterministic fuzz-generated cases, and cross-backend consistency cases.

# Current Limitations

Current limitations include:

```text
the bounded backend requires a fixed maximum word length
the sequential backend uses a simple stream-based input protocol
the r```x parser does not implement full PCRE/Python r```x syntax
unsupported features include lookaround, anchors, lazy quantifiers, dot wildcard, predefined classes, and negated classes
the project does not perform unbounded language equivalence checking
the project does not yet integrate SAT solvers or hardware model checkers into the main pipeline
the project does not provide a formal proof of compiler correctness
```

# Future Work

Possible extensions include:

```text
larger r```x fragments
larger alphabets in fuzzing
more varied bounds in bounded fuzzing
additional cross-backend checks
integration with SAT or model checking tools
DFA construction and minimization
AIGER optimization
Isabelle/HOL formalization of r```x and NFA semantics
formal correctness proof for product automata
formal correctness proof for bounded Boolean encoding
formalization of an abstract AIG circuit semantics
eventual verified r```x-to-AIGER compilation core
```

# Summary

`string-to-aiger` is a prototype compiler from fixed-string and regular-expression constraints to AIGER circuits.

The main implementation path is:

```text
fixed strings / r```xes
-> ASTs and automata
-> bounded or sequential encodings
-> ASCII AIGER
```

The main validation path is:

```text
r```x
-> generated AIGER
-> aigsim
-> expected semantics
-> comparison
```

The project therefore aims not only to generate AIGER files, but also to validate that the generated circuits behave according to the intended regular-expression semantics.
