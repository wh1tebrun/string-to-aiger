
# string-to-aiger

Prototype compiler from simple string and regular-expression fragments to ASCII AIGER.

The project started with fixed-string disjunctions such as `abba | abb`, was then extended with Kleene star support using automata-based encodings, and now also includes conjunction / intersection support using `&`.

---

## Current supported fragments

Milestone 1 supports disjunctions of concrete fixed strings:

```text
abba | abb | abbreviation
```

Milestone 2 extends this with a small regular-expression fragment including Kleene star:

```text
a*
(ab)*
(a|b)*
(a|ba)*
```

Milestone 3 adds conjunction / intersection support:

```text
(a|b)*&a*
(ab)*&(a|b)*
a*&b*
```

The project currently supports conjunction in two backends:

- bounded combinational encoding
- experimental sequential latch-based encoding

---

## High-level goal

The goal is to translate string and regular-expression constraints into AIGER circuits.

The long-term idea is:

```text
string / regex problem
-> logical or automata-based representation
-> circuit
-> AIGER
-> SAT / model checking tools
```

This makes it possible to represent string constraints in a hardware verification format.

---

## Project organization

The source code is organized as a Python package under:

```text
string_to_aiger/
```

The package is divided into submodules:

```text
string_to_aiger/
├── fixed/
├── logic/
├── netlist/
├── aiger/
├── regex/
├── nfa/
├── bounded/
└── sequential/
```

Demo scripts are stored under:

```text
demos/
```

Test scripts are stored under:

```text
tests/
```

Evaluation scripts and generated evaluation tables are stored under:

```text
evaluation/
```

Generated AIGER files are written to:

```text
outputs/
```

The project root contains the main entry point, runner scripts, documentation, examples, demos, tests, evaluation scripts, generated outputs, and the `string_to_aiger` package.

---

## Milestone 1 pipeline

For fixed-string disjunctions, the pipeline is:

```text
expression
-> parser
-> model
-> logical expression
-> netlist
-> ASCII AIGER
```

Example input:

```text
abba | abb
```

This expression represents the language:

```text
L = {"abba", "abb"}
```

---

## Milestone 1 encoding approach

For milestone 1, the input is a disjunction of fixed concrete strings.

The compiler translates each concrete string into a conjunction of constraints.

For example, `abba` becomes:

```text
len == 4
x[0] == 'a'
x[1] == 'b'
x[2] == 'b'
x[3] == 'a'
```

A disjunction of strings is then encoded as an OR of these conjunctions.

This is sufficient for black/white lists, because all accepted strings are known and have fixed length.

---

## Milestone 1 files

The milestone 1 implementation is mainly located in:

```text
string_to_aiger/fixed/
string_to_aiger/logic/
string_to_aiger/netlist/
string_to_aiger/aiger/
```

Important files:

| File | Purpose |
|---|---|
| `string_to_aiger/fixed/parser.py` | Parses a disjunction of concrete strings. |
| `string_to_aiger/fixed/model.py` | Defines the internal matcher representation. |
| `string_to_aiger/fixed/matcher.py` | Directly evaluates the matcher model on candidate strings. |
| `string_to_aiger/fixed/compiler.py` | Compiles matchers into logical expressions. |
| `string_to_aiger/logic/circuit.py` | Defines logical expression data structures. |
| `string_to_aiger/logic/pretty.py` | Provides readable printing of logical expressions. |
| `string_to_aiger/logic/evaluator.py` | Evaluates compiled expressions on candidate strings. |
| `string_to_aiger/netlist/netlist.py` | Defines gate-level netlist data structures. |
| `string_to_aiger/netlist/netlist_builder.py` | Converts logical expressions into a gate-level netlist. |
| `string_to_aiger/netlist/netlist_pretty.py` | Provides readable printing of netlists. |
| `string_to_aiger/aiger/aiger_writer.py` | Exports the netlist into ASCII AIGER. |
| `string_to_aiger/aiger/aiger.py` | High-level wrapper for compiling expressions to AIGER. |
| `main.py` | Milestone 1 demo entry point. |
| `tests/tests.py` | Milestone 1 regression tests. |

---

## Milestone 1 demo

To run the fixed-string disjunction demo:

```bash
python main.py
```

The current demo reads one selected example file:

```text
examples/test1.txt
```

and writes the generated AIGER circuit to:

```text
outputs/output.aag
```

---

## Milestone 1 tests

To run the milestone 1 tests:

```bash
python tests/tests.py
```

---

## Example expressions

Example expressions can be placed inside files under `examples/`.

```text
abba | abb
abc | ab
hello | world
```

At the current milestone 1 demo setup, `main.py` reads one selected example file at a time.

---

## Milestone 2: Kleene star support

Milestone 2 extends the project from fixed-string disjunctions toward regular expressions with Kleene star.

The implemented milestone 2 bounded pipeline is:

```text
regular expression
-> regex AST
-> NFA
-> bounded combinational logical expression
-> netlist
-> ASCII AIGER
```

The supported examples include:

```text
a*
(ab)*
(a|b)*
(a|ba)*
```

---

## Regex AST

For milestone 2 and milestone 3, a separate regex AST representation was introduced.

The main AST nodes are:

```text
Empty
Char
Concat
UnionExpr
Star
Intersect
```

For example, the expression:

```text
(a|ba)*
```

is represented as a tree containing:

```text
Star
└── UnionExpr
    ├── Char("a")
    └── Concat
        ├── Char("b")
        └── Char("a")
```

For intersection, the expression:

```text
(a|b)*&a*
```

is represented using:

```text
Intersect(left, right)
```

This separates the structure of the regular expression from the later compilation steps.

---

## NFA construction

After parsing, the regex AST is translated into an NFA.

The NFA representation contains:

- a start state
- a set of accepting states
- symbol transitions
- epsilon transitions

Epsilon transitions are represented internally with `None`.

For example, Kleene star introduces loops and epsilon transitions, allowing expressions such as:

```text
a*
(ab)*
```

to accept repeated occurrences, including the empty string.

---

## Bounded combinational encoding

The first milestone 2 backend uses bounded combinational encoding.

This means that a fixed bound is chosen, for example:

```text
bound = 3
```

The NFA is then unrolled up to this bound.

For example, the expression:

```text
a*
```

with bound 3 accepts:

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

because the word length exceeds the chosen bound.

This encoding is combinational and does not require AIGER latches.

---

## Sequential latch-based backend

In addition to the bounded combinational backend, an experimental sequential backend was added.

This backend translates an NFA into a sequential circuit with latches.

The pipeline is:

```text
regular expression
-> regex AST
-> NFA
-> sequential circuit
-> latch-based ASCII AIGER
```

The sequential circuit uses latches to store the current active NFA states.

The input protocol is stream-based:

- in each normal step, one symbol input such as `is_a` or `is_b` is true
- in the final step, `end` is true
- the output `accept` is true iff `end` is true and an accepting state is active

For example, the word `aaa` for the expression `a*` is represented as:

```text
step 1: is_a = true,  end = false
step 2: is_a = true,  end = false
step 3: is_a = true,  end = false
step 4: is_a = false, end = true
```

This backend produces AIGER files with `L > 0`, meaning that latches are present.

---

## Milestone 2 files

The following components have been implemented for milestone 2:

| File | Purpose |
|---|---|
| `string_to_aiger/regex/regex_ast.py` | Defines regex AST node types such as `Empty`, `Char`, `Concat`, `UnionExpr`, `Star`, and `Intersect`. |
| `string_to_aiger/regex/regex_pretty.py` | Provides readable printing of regex ASTs. |
| `string_to_aiger/regex/regex_parser.py` | Parses the supported regular-expression fragment. |
| `string_to_aiger/nfa/nfa.py` | Defines the NFA data structure. |
| `string_to_aiger/nfa/nfa_builder.py` | Constructs an NFA from a regex AST. |
| `string_to_aiger/nfa/nfa_evaluator.py` | Directly evaluates NFAs on candidate strings. |
| `string_to_aiger/bounded/bounded_nfa_encoding.py` | Encodes an NFA as a bounded combinational logical expression. |
| `string_to_aiger/regex/regex_to_aiger.py` | Provides a high-level wrapper from regex pattern and bound to ASCII AIGER. |
| `string_to_aiger/sequential/sequential_circuit.py` | Defines the intermediate representation for sequential circuits. |
| `string_to_aiger/sequential/sequential_aiger_writer.py` | Writes latch-based ASCII AIGER files. |
| `string_to_aiger/sequential/sequential_simulator.py` | Simulates sequential circuits in Python. |
| `string_to_aiger/sequential/nfa_to_sequential.py` | Translates a generic NFA into a sequential circuit. |
| `tests/tests_regex.py` | Tests regex parsing, NFA evaluation, bounded encoding, and AIGER output. |
| `tests/tests_sequential.py` | Tests the sequential backend. |

---

## Run milestone 2 demos

To run the regex parser demo:

```bash
python demos/regex_parser_demo.py
```

To inspect generated NFAs:

```bash
python demos/nfa_demo.py
```

To run the direct NFA evaluator demo:

```bash
python demos/nfa_evaluator_demo.py
```

To run the bounded NFA demo:

```bash
python demos/bounded_nfa_demo.py
```

To compile a regex directly to bounded AIGER:

```bash
python demos/regex_to_aiger_demo.py
```

To run the manual sequential `a*` demo:

```bash
python demos/sequential_astar_demo.py
```

To simulate the manual sequential `a*` circuit:

```bash
python demos/sequential_astar_sim_demo.py
```

To run the generic NFA-to-sequential demo:

```bash
python demos/nfa_to_sequential_demo.py
```

Generated AIGER files from these demos are written to:

```text
outputs/
```

---

## Milestone 3: Conjunction / intersection support

Milestone 3 adds support for conjunction, written as `&`.

The expression:

```text
((a|b)*) & (a*)
```

means that a candidate string must satisfy both regular expressions at the same time.

In this example, `(a|b)*` accepts all strings over `a` and `b`, while `a*` accepts only strings consisting of `a`.

Therefore, their intersection behaves like:

```text
a*
```

---

## Milestone 3 parser support

The regex parser now supports the `&` operator.

The precedence order is:

```text
1. Kleene star
2. concatenation
3. &
4. |
```

For example:

```text
a|b&c
```

is parsed as:

```text
a | (b & c)
```

The regex AST contains the node:

```text
Intersect(left, right)
```

---

## Bounded conjunction encoding

For the bounded backend, conjunction is compiled structurally.

The idea is:

```text
compile(A & B)
=
compile(A) AND compile(B)
```

This means that both sides are compiled separately into bounded logical expressions, and the final expression is the conjunction of both.

For example:

```text
(a|b)*&a*
```

is compiled by generating bounded encodings for both `(a|b)*` and `a*`, then combining them with `AND`.

This produces a combinational AIGER circuit.

---

## Sequential conjunction encoding

Sequential conjunction is implemented as an experimental parallel-composition backend.

The idea is:

```text
A & B
=
run A and B in parallel
accept = accept_A AND accept_B
```

For example, the expression:

```text
((a|b)*) & (a*)
```

is handled by compiling both sides into sequential circuits:

```text
left  = (a|b)*
right = a*
```

Both circuits read the same input stream.

Their internal latch names are renamed to avoid collisions:

```text
state_0 -> left_state_0
state_0 -> right_state_0
```

The final output is:

```text
accept = left_accept AND right_accept
```

This allows conjunction to be represented using latch-based AIGER without constructing an explicit product automaton.

---

## Milestone 3 files

The following components were added or extended for milestone 3:

| File | Purpose |
|---|---|
| `string_to_aiger/regex/regex_ast.py` | Adds the `Intersect` AST node for conjunction / intersection. |
| `string_to_aiger/regex/regex_pretty.py` | Adds readable printing support for `Intersect`. |
| `string_to_aiger/regex/regex_parser.py` | Adds parsing support for the `&` operator. |
| `string_to_aiger/regex/regex_bounded_compiler.py` | Compiles regex ASTs with bounded intersection support. |
| `string_to_aiger/sequential/sequential_intersection.py` | Provides helpers for merging sequential circuits for conjunction. |
| `string_to_aiger/sequential/sequential_regex_compiler.py` | Compiles regex ASTs into sequential circuits, including `Intersect`. |
| `tests/tests_intersection.py` | Tests bounded conjunction behavior and AIGER output. |
| `tests/tests_sequential_intersection.py` | Tests sequential conjunction behavior and latch-based AIGER output. |

---

## Run milestone 3 demos

To run the bounded intersection demo:

```bash
python demos/regex_intersection_demo.py
```

To run the sequential intersection demo:

```bash
python demos/sequential_intersection_demo.py
```

Generated AIGER files from these demos are written to:

```text
outputs/
```

---

## Milestone 3 current status

The bounded backend supports conjunction for examples such as:

```text
(a|b)*&a*
(ab)*&(a|b)*
a*&b*
```

The sequential backend also supports conjunction using parallel circuit composition.

The same examples are supported in the sequential backend:

```text
(a|b)*&a*
(ab)*&(a|b)*
a*&b*
```

The bounded backend produces combinational AIGER.

The sequential backend produces latch-based AIGER with `L > 0`.

---

## Milestone 4: Evaluation and validation

Milestone 4 evaluates the generated AIGER circuits on small example expressions.

The evaluation currently contains two parts:

- AIGER statistics comparison
- language behavior validation

The statistics comparison extracts information from the AIGER header:

```text
aag M I L O A
```

where:

- `M` is the maximum variable index
- `I` is the number of inputs
- `L` is the number of latches
- `O` is the number of outputs
- `A` is the number of AND gates

The language behavior validation checks whether the bounded and sequential backends agree with manually specified expected results for selected candidate strings.

---

## Milestone 4 files

The following evaluation files are currently used:

| File | Purpose |
|---|---|
| `evaluation/evaluate_aiger_stats.py` | Compares AIGER header statistics for bounded and sequential backends. |
| `evaluation/evaluate_language_behavior.py` | Validates language behavior on selected candidate strings. |
| `evaluation/aiger_stats.csv` | CSV output for AIGER statistics. |
| `evaluation/aiger_stats.md` | Markdown table output for AIGER statistics. |
| `evaluation/language_behavior.csv` | CSV output for language behavior validation. |
| `evaluation/language_behavior.md` | Markdown table output for language behavior validation. |
| `run_all_evaluations.py` | Runs all evaluation scripts. |

---

## Run evaluations

To run the AIGER statistics evaluation:

```bash
python evaluation/evaluate_aiger_stats.py
```

To run the language behavior validation:

```bash
python evaluation/evaluate_language_behavior.py
```

To run all evaluations:

```bash
python run_all_evaluations.py
```

The evaluation scripts generate:

```text
evaluation/aiger_stats.csv
evaluation/aiger_stats.md
evaluation/language_behavior.csv
evaluation/language_behavior.md
```

These files can be used directly in the project report or presentation.

---

## Tests

To run the milestone 1 tests:

```bash
python tests/tests.py
```

To run the regex and bounded encoding tests:

```bash
python tests/tests_regex.py
```

To run the sequential backend tests:

```bash
python tests/tests_sequential.py
```

To run the bounded intersection tests:

```bash
python tests/tests_intersection.py
```

To run the sequential intersection tests:

```bash
python tests/tests_sequential_intersection.py
```

A full local test run can be done with:

```bash
python run_all_tests.py
```

This is equivalent to running:

```bash
python tests/tests.py
python tests/tests_regex.py
python tests/tests_sequential.py
python tests/tests_intersection.py
python tests/tests_sequential_intersection.py
```

---

## Demo runner

All demos can be executed with:

```bash
python run_all_demos.py
```

This runs the milestone 1 demo, regex demos, NFA demos, bounded backend demos, sequential backend demos, and intersection demos.

---

## Output artifacts

Generated AIGER files are written to:

```text
outputs/
```

Examples include:

- `outputs/output.aag`
- `outputs/regex_output.aag`
- `outputs/bounded_output_astar.aag`
- `outputs/sequential_astar.aag`
- `outputs/sequential_generic_astar.aag`
- `outputs/intersection_output__aorb_staranda_star.aag`
- `outputs/sequential_intersection_output.aag`

The exact file names depend on the demo and the regex pattern being compiled.

Generated `.aag` files are ignored by Git because they can be regenerated from the demo scripts.

---

## Current status

The current implementation supports five compilation modes:

```text
Milestone 1:
fixed strings
-> logical constraints
-> netlist
-> combinational AIGER

Milestone 2A:
regular expressions with Kleene star
-> AST
-> NFA
-> bounded combinational AIGER

Milestone 2B:
regular expressions with Kleene star
-> AST
-> NFA
-> sequential circuit
-> latch-based AIGER

Milestone 3A:
regular expressions with conjunction
-> AST with Intersect
-> bounded logical conjunction
-> combinational AIGER

Milestone 3B:
regular expressions with conjunction
-> AST with Intersect
-> parallel sequential circuits
-> latch-based AIGER
```

Milestone 4 adds evaluation and validation scripts for the generated AIGER circuits.

---

## Current limitations

- The bounded backend only reasons about candidate strings up to a fixed maximum length.
- The sequential backend currently uses a simple stream-based input protocol.
- Sequential conjunction is implemented by parallel circuit composition rather than explicit product automaton construction.
- The language behavior validation is based on selected small examples, not exhaustive equivalence checking.
- External AIGER tool integration is not implemented yet.
- The project currently does not support full regular-expression syntax.
- The project currently does not support character classes.
- The project currently does not support escape handling.
- The project currently does not perform minimization or optimization of automata.
- The project currently does not include certified AIGER semantic checking with external tools.
- Product automata are not implemented as a separate construction.

---

## Future work

Possible future improvements include:

- product automaton construction for conjunction
- richer regular-expression parser
- better alphabet handling
- improved AIGER optimization
- external validation with AIGER tools
- comparison with external model checkers
- integration with hardware model checking workflows
- packaging improvements such as `pyproject.toml`
- optional CLI entry point
- more systematic benchmark generation

---

## Summary

The project implements a step-by-step compiler pipeline from string constraints to AIGER.

The conceptual progression is:

```text
Milestone 1:
fixed string disjunctions
-> logical constraints
-> AIGER

Milestone 2:
regular expressions with Kleene star
-> AST
-> NFA
-> bounded or sequential AIGER

Milestone 3:
regular expressions with conjunction
-> AST with Intersect
-> bounded or sequential AIGER

Milestone 4:
generated AIGER circuits
-> statistics comparison
-> language behavior validation
```

The bounded backend is useful as a simpler intermediate encoding.

The sequential backend introduces latches and moves the project closer to a hardware model checking representation of automata.

The conjunction support extends the regex fragment by allowing two expressions to be required simultaneously.

The evaluation scripts provide initial evidence that the generated circuits behave correctly on selected benchmark examples.
```
