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
string or regex constraint
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

# Five-Minute Clean-Clone Quickstart

The package requires Python 3.10 or newer and declares no runtime dependencies. Start from a clean clone as follows:

```bash
git clone https://github.com/wh1tebrun/string-to-aiger.git
cd string-to-aiger
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
```

These commands use the validated WSL/POSIX executable name `python3`. If your Python 3.10+ installation is exposed as `python`, use `python -m venv .venv` instead. On Windows PowerShell, activate that environment with `.\.venv\Scripts\Activate.ps1`. After activation, the installed console command and module form are equivalent and should expose the same interface:

```bash
string-to-aiger --help
python -m string_to_aiger --help
```

Compile a small bounded example without writing into a tracked artifact directory:

```bash
string-to-aiger --pattern "ab|bc" --backend bounded --bound 2 --output ../string-to-aiger-smoke.aag
```

The command should exit successfully, report `AIGER validation: passed`, and write an ASCII AIGER file whose first line begins with `aag`. This validation is structural; the [bounded-input contract](#bounded-combinational-backend) and semantic evidence are described below.

The package CLI is the authoritative entry point. Root `main.py` is a legacy fixed-string demonstration that reads `examples/test1.txt`; it is not the general regex CLI.

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

The bounded backend compiles a regex into a combinational AIGER circuit for words up to a fixed bound.

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

These Boolean inputs have an external valid-word contract. A candidate word selects one `len_is_N` signal and encodes one symbol at each position within that length using `x_POSITION_is_SYMBOL` signals. Words longer than the chosen bound are outside this encoding, and inputs beyond the selected length do not extend the word. Arbitrary inconsistent Boolean valuations do not necessarily represent strings, so the bounded circuit is not claimed to be language-equivalent over the unrestricted Boolean input domain.

The CLI runs internal structural AIGER validation by default before writing the file. That check covers header fields and counts, basic body-line forms, literal bounds, and basic symbol/comment syntax; it is not a complete AIGER parser or a semantic correctness proof. Simulation helpers generate valid word encodings, while the bounded SAT/miter artifacts add the documented input-validity constraints before interpreting assignments as words.

This backend is useful for finite-word encodings, SAT-style checks, small examples, and debugging.

# Sequential Latch-Based Backend

The sequential backend compiles a regex into a latch-based AIGER circuit.

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

The project supports regex intersection using `&`.

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
string_to_aiger/regex/
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
validation/
artifacts/
outputs/
```

The `outputs/` directory is used for generated AIGER files and temporary simulator inputs.

New untracked `.aag` and `.stim` files directly under `outputs/` are ignored by Git. Curated, committed evidence is indexed in [`artifacts/README.md`](artifacts/README.md).

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

# Regex and Automata Layer

```text
string_to_aiger/regex/regex_ast.py
string_to_aiger/regex/regex_parser.py
string_to_aiger/regex/regex_bounded_compiler.py
string_to_aiger/regex/regex_to_aiger.py
string_to_aiger/regex/regex_to_product_nfa.py
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
string_to_aiger/sequential/sequential_regex_compiler.py
string_to_aiger/sequential/product_sequential_compiler.py
```

# Command-Line Interface

The authoritative package CLI is installed as `string-to-aiger`. The equivalent module form delegates to the same `string_to_aiger.cli:main` entry point:

```bash
string-to-aiger --help
python3 -m string_to_aiger --help
```

Root `main.py` remains a fixed-string teaching/demo program and is not the current general-purpose interface.

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
--external-validator-command 'some-checker --input "{path}"'
```

Keep the double quotes around `{path}` inside the command template so generated paths containing spaces remain one validator argument.

# External Semantic Validation with aigsim

A major part of the project is external semantic validation using Armin Biere's `aigsim`.

The validation pipeline is:

```text
regex
-> generated AIGER
-> aigsim simulation
-> observed accept/reject output
-> reference regex semantics
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

Run the internal CI profile without a real `aigsim` installation:

```bash
python3 run_all_tests.py --internal-only
```

The current manifest contains 31 scripts and 311 explicit `test_*` functions. The internal profile runs 24 scripts and 267 functions; it includes the Bash-based manual fake-simulator regression but excludes the seven real-`aigsim` scripts and their 44 functions. [`.github/workflows/internal-tests.yml`](.github/workflows/internal-tests.yml) installs the package and runs the internal profile on Ubuntu with Python 3.10 and 3.12.

Ordinary push and pull-request CI deliberately omits real external-tool validation. The provisioned full release gate remains authoritative for the real `aigsim` suite, AIGER-tool and Minisat artifacts, and the canonical Docker/rIC3 workflow.

The manual `aigsim` path is fail-closed: each stimulus must end with a final `.` line and LF, simulator execution must exit 0 with empty stderr and well-formed output, ordinary cases must match reference semantics, and deliberately corrupted controls count as successful detections only after clean simulator execution.

Important internal tests include:

```text
tests/tests.py
tests/tests_regex.py
tests/tests_regex_length.py
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
tests/tests_manual_aigsim_checks.py
tests/tests_external_aiger_validator.py
tests/tests_ric3_result.py
tests/tests_shell_line_endings.py
tests/tests_runner.py
```

Important external `aigsim` tests include:

```text
tests/tests_aigsim_bounded.py
tests/tests_aigsim_sequential.py
tests/tests_aigsim_product.py
tests/tests_aigsim_bounded_fuzzer.py
tests/tests_aigsim_sequential_fuzzer.py
tests/tests_aigsim_cross_backend.py
tests/tests_aigsim_negative_detection.py
```

The shared setup helper is:

```text
tests/aigsim_test_utils.py
```

# Bounded aigsim Tests

The bounded semantic tests compile regexes to combinational AIGER, simulate the generated AIGER files with `aigsim`, and compare the output against reference regex semantics.

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

The sequential semantic tests compile regexes to latch-based AIGER, encode candidate words as traces, simulate the traces with `aigsim`, and compare the final output on the `end` step against reference semantics.

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

The fuzzers generate many small regexes with a fixed random seed.

Because the seed is fixed, the tests are reproducible.

The fuzzing pipeline is:

```text
generated regex
-> AIGER generation
-> aigsim simulation
-> reference regex semantics
-> output comparison
```

During development, the fuzzer helped detect nested-intersection and constant-output edge cases.

# Cross-Backend Consistency

The project also checks whether different backends agree on the same regex and candidate words.

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
regex parser demo
NFA demo
NFA evaluator demo
bounded NFA demo
regex-to-AIGER demo
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
docs/regex_grammar.md
docs/product_automaton.md
docs/testing.md
```

`docs/testing.md` explains the external semantic validation approach in more detail.

# Hardware Model Checking with rIC3

The sequential AIGER backend can also be checked with the
[rIC3 hardware model checker](https://github.com/gipsyh/rIC3).

This is an optional external validation step and requires Docker.

```bash
docker pull gipsyh/ric3:1.6
bash validation/run_ric3_hwmcc.sh
```

The validation script generates sequential AIGER models and asks rIC3
whether the accepting output is reachable.

| Pattern | Expected result | Meaning |
| --- | --- | --- |
| `ab` | `SAT` | An accepting trace exists. |
| `b&c` | `UNSAT` | No valid trace can satisfy both expressions. |
| `(ab\|ba)*&(aa\|bb)*` | `SAT` | Both starred expressions accept the empty word. |
| `((ab\|ba)(ab\|ba)*)&((aa\|bb)(aa\|bb)*)` | `UNSAT` | Removing epsilon produces an empty intersection. |

For these checks:

```text
SAT
=
the accepting output is reachable

UNSAT
=
IC3 proved that the accepting output is unreachable
```

The expression `(ab|ba)*&(aa|bb)*` is not an empty language because both
sides contain a Kleene star and therefore accept epsilon. The final case
encodes one-or-more repetitions as `R R*`, removing the epsilon case.

# What Is Validated

For the tested cases, the project checks:

```text
generated AIGER circuit output
=
expected regex accept/reject result
```

Most behavioral checks run the generated AIGER files through an external simulator. Selected sequential models are additionally checked with the rIC3 hardware model checker.

Therefore, the tests do not only inspect Python objects internally.

They check the generated AIGER files as actual artifacts.

## Evidence Map

The detailed committed-evidence index is [`artifacts/README.md`](artifacts/README.md). Each category below has a deliberately limited interpretation.

| Category | Evidence strength | Authoritative location and scope |
| --- | --- | --- |
| Internal and focused tests | Unit/integration tests | The current [manifest](run_all_tests.py) contains 267 internal-profile functions in 24 scripts; the tagged baseline contained 220 such functions. The full current manifest also includes the seven-script, 44-function external `aigsim` profile. |
| External `aigsim` test suite | External simulation and differential validation | The [full runner](run_all_tests.py) invokes seven `tests/tests_aigsim_*.py` scripts whose 44 functions compare generated files with reference behavior. |
| Semantic artifact matrix | Committed external-simulation evidence | The [semantic matrix](artifacts/validation/validation_matrix.md) separately records 45 concrete `aigsim` rows; rows and test functions are different units. |
| Deterministic fuzzing | Reproducible differential testing | The [bounded](tests/tests_aigsim_bounded_fuzzer.py) and [sequential](tests/tests_aigsim_sequential_fuzzer.py) fuzz tests use fixed seeds; passing samples are not exhaustive proof. |
| Negative controls | Failure-sensitivity evidence | The [negative-detection matrix](artifacts/validation/negative_detection_matrix.md) records six deliberately corrupted circuits whose mismatches were detected. |
| Bounded miter/reference checks | SAT-based bounded instance evidence | [Miter counterexamples](artifacts/model_checking/model_checking_counterexamples.md) and [independent reference equivalence](artifacts/reference_equivalence/reference_equivalence.md) constrain inputs to valid bounded encodings. |
| Sequential checks | Bounded unrolling and protocol tests | [Sequential counterexamples](artifacts/sequential_model_checking/sequential_counterexamples.md) cover fixed-depth instances; [protocol tests](tests/tests_aigsim_sequential.py) exercise valid and invalid traces. |
| Canonical rIC3 workflow | Selected unbounded reachability instances | [`validation/run_ric3_hwmcc.sh`](validation/run_ric3_hwmcc.sh) checks four generated transition systems. SAT/UNSAT concerns reachability of `accept`, not universal compiler correctness. |
| Manual checks | Small inspectable external simulations | The [manual matrix](artifacts/manual_aigsim_checks/manual_aigsim_checks.md) records nine fail-closed checks: seven expected semantic matches and two detected corrupted-output mismatches. All nine current captures record exit 0, valid execution, and empty stderr. |
| Companion Isabelle/HOL project | Mathematical proof of a separate Thompson core | The [companion development](https://gitlab.uni-freiburg.de/et130/regex-to-nfa-isabelle.git) proves the five constructor results described below, not refinement of this Python pipeline. |
| Final presentation release | Immutable release/provenance marker | Tag [`presentation-release-2026-08-06`](https://github.com/wh1tebrun/string-to-aiger/tree/presentation-release-2026-08-06) freezes the final release at commit [`f77c909cd8359a87bc81c0f89aaa813e89abf279`](https://github.com/wh1tebrun/string-to-aiger/commit/f77c909cd8359a87bc81c0f89aaa813e89abf279). The earlier [`presentation-validation-aa072d8`](https://github.com/wh1tebrun/string-to-aiger/tree/presentation-validation-aa072d8) tag identifies historical pre-professionalization commit [`aa072d804572c128f4e905b052fb0c2184bd7b0e`](https://github.com/wh1tebrun/string-to-aiger/commit/aa072d804572c128f4e905b052fb0c2184bd7b0e). Subsequent changes do not alter either immutable tag. |

## Release Provenance and Environment Boundary

At the historical validation baseline, the recorded GO gate comprised 263 explicit test functions in 27 scripts, including 43 external `aigsim` tests; a separate 11-case sequential-protocol audit; the committed validation/SAT evidence; four canonical rIC3 cases with results `SAT, UNSAT, SAT, UNSAT`; and two clean-clone demo rehearsals. Its internal profile comprised 220 functions in 20 scripts. These facts describe only the historical `presentation-validation-aa072d8` tag.

The final post-professionalization gate and two clean-clone demo rehearsals completed successfully before `f77c909cd8359a87bc81c0f89aaa813e89abf279` was promoted to `main` and tagged `presentation-release-2026-08-06`. At that immutable release, the full profile passed with 288 explicit test functions in 29 scripts and the internal profile passed with 245 functions in 22 scripts. The released source includes explicit LF file writing, fail-closed manual `aigsim` validation, and internal test/packaging CI. Subsequent changes do not alter or become part of the immutable release tag.

The core package requires Python 3.10+ and uses only the standard library at runtime. The recorded external gate ran under WSL Ubuntu with Python 3.10.12 and additionally used Bash, AIGER tools/`aigsim`, Minisat, Docker Desktop, and rIC3. The central AIGER file-writing pipeline explicitly emits UTF-8 with LF newlines, and representative bounded and sequential outputs were byte-identical across native Windows and WSL. In addition, `.gitattributes` forces tracked `.sh`, `.aag`, and `.stim` files to LF after checkout. Full native-Windows support for the external toolchain is not claimed. Exact recorded versions and provenance limitations are in the [artifact index](artifacts/README.md#validated-environment).

# Formal Verification Scope

The companion [Isabelle/HOL development](https://gitlab.uni-freiburg.de/et130/regex-to-nfa-isabelle.git) proves language equivalence, within its mathematical model, between Thompson-style epsilon-NFA constructions and inductive regular-expression semantics for:

- epsilon;
- individual characters;
- concatenation;
- union;
- Kleene star.

These constructions closely correspond to the non-intersection Thompson core used by this Python prototype. The correspondence between the repositories is a manually audited structural correspondence, not a machine-checked refinement of the Python source.

The Isabelle development does not formally verify:

- Python parser correctness or surface-syntax desugaring;
- intersection or product automata;
- the bounded Boolean encoding;
- the sequential latch encoding or input-protocol guard;
- netlist lowering or AIGER serialization;
- external `aigsim` simulation, SAT, or rIC3 workflows;
- the complete executable regex-to-AIGER pipeline.

The executable pipeline is instead supported by empirical validation: testing, external simulation, and targeted unbounded reachability checks for selected sequential models.

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
the regex parser does not implement full PCRE/Python regex syntax
unsupported features include lookaround, anchors, lazy quantifiers, dot wildcard, predefined classes, and negated classes
the project does not perform unbounded language equivalence checking
rIC3 validation is optional, requires Docker, and is not part of the default test suite
the complete executable regex-to-AIGER pipeline is not formally verified
```

# Future Work

Possible extensions include:

```text
larger regex fragments
larger alphabets in fuzzing
more varied bounds in bounded fuzzing
additional cross-backend checks
broader SAT/model-checking integration and automated witness extraction
DFA construction and minimization
AIGER optimization
machine-checked refinement from the Isabelle model to the Python implementation
formal correctness proof for product automata
formal correctness proof for bounded Boolean encoding
formalization of an abstract AIG circuit semantics
eventual verified regex-to-AIGER compilation core
```

# Summary

`string-to-aiger` is a prototype compiler from fixed-string and regular-expression constraints to AIGER circuits.

The main implementation path is:

```text
fixed strings / regexes
-> ASTs and automata
-> bounded or sequential encodings
-> ASCII AIGER
```

The main validation path is:

```text
regex
-> generated AIGER
-> aigsim or rIC3
-> observed behavior or reachability proof
-> comparison with expected semantics
```

The project therefore aims not only to generate AIGER files, but also to validate that the generated circuits behave according to the intended regular-expression semantics.
