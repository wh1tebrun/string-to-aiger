ERKE string-to-aiger

Prototype compiler from simple string and regular-expression fragments to ASCII AIGER.

The project started with fixed-string disjunctions such as `abba | abb`, was then extended with regular-expression support using automata-based encodings, and now includes conjunction / intersection support using `&`, explicit product automata, bounded and sequential backends, validation scripts, and a command-line interface.

---

ERKEERKE Current supported fragments

Milestone 1 supports disjunctions of concrete fixed strings:

EGEtext
abba | abb | abbreviation
EGE

Milestone 2 extends this with regular-expression support based on regex ASTs and NFAs:

EGEtext
a*
(ab)*
(a|b)*
(a|ba)*
EGE

The supported regex fragment now includes:

- concatenation
- union / alternation with `|`
- conjunction / intersection with `&`
- Kleene star with `*`
- one-or-more repetition with `+`
- optional repetition with `?`
- exact bounded repetition with `{n}`
- bounded repetition ranges with `{m,n}`
- open-ended bounded repetition with `{m,}`
- grouping with parentheses
- character classes such as `[ab]`
- character ranges such as `[a-c]`
- basic escaping for literal operators

Examples:

EGEtext
a+
a?
a{3}
a{1,3}
a{2,}
[ab]*
[a-c]{2,4}
a\*
(a|b)*&a*
EGE

Milestone 3 adds conjunction / intersection support:

EGEtext
(a|b)*&a*
(ab)*&(a|b)*
a*&b*
EGE

The project currently supports conjunction in two backend families:

- bounded combinational encoding
- sequential latch-based encoding

Intersection can be compiled using two strategies:

- structural intersection encoding
- explicit product automaton construction

---

ERKEERKE High-level goal

The goal is to translate string and regular-expression constraints into AIGER circuits.

The long-term idea is:

EGEtext
string / regex problem
-> logical or automata-based representation
-> circuit
-> AIGER
-> SAT / model checking tools
EGE

This makes it possible to represent string constraints in a hardware verification format.

---

ERKEERKE Project organization

The source code is organized as a Python package under:

EGEtext
string_to_aiger/
EGE

The package is divided into submodules:

EGEtext
string_to_aiger/
├── fixed/
├── logic/
├── netlist/
├── aiger/
├── regex/
├── nfa/
├── bounded/
└── sequential/
EGE

Demo scripts are stored under:

EGEtext
demos/
EGE

Test scripts are stored under:

EGEtext
tests/
EGE

Evaluation scripts and generated evaluation tables are stored under:

EGEtext
evaluation/
EGE

Generated AIGER files are written to:

EGEtext
outputs/
EGE

The project root contains the main entry point, runner scripts, documentation, examples, demos, tests, evaluation scripts, generated outputs, packaging metadata, and the `string_to_aiger` package.

---

ERKEERKE Milestone 1 pipeline

For fixed-string disjunctions, the pipeline is:

EGEtext
expression
-> parser
-> model
-> logical expression
-> netlist
-> ASCII AIGER
EGE

Example input:

EGEtext
abba | abb
EGE

This expression represents the language:

EGEtext
L = {"abba", "abb"}
EGE

---

ERKEERKE Milestone 1 encoding approach

For milestone 1, the input is a disjunction of fixed concrete strings.

The compiler translates each concrete string into a conjunction of constraints.

For example, `abba` becomes:

EGEtext
len == 4
x[0] == 'a'
x[1] == 'b'
x[2] == 'b'
x[3] == 'a'
EGE

A disjunction of strings is then encoded as an OR of these conjunctions.

This is sufficient for black/white lists, because all accepted strings are known and have fixed length.

---

ERKEERKE Milestone 1 files

The milestone 1 implementation is mainly located in:

EGEtext
string_to_aiger/fixed/
string_to_aiger/logic/
string_to_aiger/netlist/
string_to_aiger/aiger/
EGE

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

ERKEERKE Milestone 1 demo

To run the fixed-string disjunction demo:

EGEbash
python main.py
EGE

The current demo reads one selected example file:

EGEtext
examples/test1.txt
EGE

and writes the generated AIGER circuit to:

EGEtext
outputs/output.aag
EGE

---

ERKEERKE Milestone 1 tests

To run the milestone 1 tests:

EGEbash
python tests/tests.py
EGE

---

ERKEERKE Example expressions

Example expressions can be placed inside files under `examples/`.

EGEtext
abba | abb
abc | ab
hello | world
(a|b)*&a*
a{1,3}
[ab]{2,}
EGE

At the current milestone 1 demo setup, `main.py` reads one selected example file at a time.

For the CLI, patterns can also be provided directly with `--pattern` or read from a file with `--input-file`.

---

ERKEERKE Milestone 2: Regular expressions and Kleene star support

Milestone 2 extends the project from fixed-string disjunctions toward regular expressions with Kleene star.

The implemented milestone 2 bounded pipeline is:

EGEtext
regular expression
-> regex AST
-> NFA
-> bounded combinational logical expression
-> netlist
-> ASCII AIGER
EGE

The supported examples include:

EGEtext
a*
(ab)*
(a|b)*
(a|ba)*
EGE

The parser has since been extended with additional operators such as `+`, `?`, `{n}`, `{m,n}`, `{m,}`, character classes, character ranges, and escaping.

---

ERKEERKE Regex AST

For milestone 2 and milestone 3, a separate regex AST representation was introduced.

The main AST nodes are:

EGEtext
Empty
Char
Concat
UnionExpr
Star
Intersect
EGE

Several parser-level operators are desugared into these core AST nodes.

For example:

EGEtext
a+
EGE

is represented using:

EGEtext
Concat(Char("a"), Star(Char("a")))
EGE

The expression:

EGEtext
a?
EGE

is represented using:

EGEtext
UnionExpr(Empty(), Char("a"))
EGE

The expression:

EGEtext
a{1,3}
EGE

is represented as a concatenation of the required part and optional repetitions.

For example, the expression:

EGEtext
(a|ba)*
EGE

is represented as a tree containing:

EGEtext
Star
└── UnionExpr
    ├── Char("a")
    └── Concat
        ├── Char("b")
        └── Char("a")
EGE

For intersection, the expression:

EGEtext
(a|b)*&a*
EGE

is represented using:

EGEtext
Intersect(left, right)
EGE

This separates the structure of the regular expression from the later compilation steps.

---

ERKEERKE NFA construction

After parsing, the regex AST is translated into an NFA.

The NFA representation contains:

- a start state
- a set of accepting states
- symbol transitions
- epsilon transitions

Epsilon transitions are represented internally with `None`.

For example, Kleene star introduces loops and epsilon transitions, allowing expressions such as:

EGEtext
a*
(ab)*
EGE

to accept repeated occurrences, including the empty string.

The project also includes NFA utility passes:

- explicit alphabet extraction
- unreachable-state pruning
- duplicate-transition elimination
- basic NFA cleanup through an optimization wrapper

These are not full automata minimization, but they provide basic cleanup and analysis support.

---

ERKEERKE Bounded combinational encoding

The bounded backend uses bounded combinational encoding.

This means that a fixed bound is chosen, for example:

EGEtext
bound = 3
EGE

The NFA is then unrolled up to this bound.

For example, the expression:

EGEtext
a*
EGE

with bound 3 accepts:

EGEtext
""
"a"
"aa"
"aaa"
EGE

but rejects:

EGEtext
"aaaa"
EGE

because the word length exceeds the chosen bound.

This encoding is combinational and does not require AIGER latches.

The project also includes regex length analysis. For a given regex AST, it computes:

- minimum accepted word length
- finite maximum accepted word length when available
- whether the analysis result is exact
- whether a chosen bound is complete for finite patterns

For example:

EGEtext
a{1,3} -> min length = 1, max length = 3
a*     -> min length = 0, max length = unbounded
EGE

The CLI reports this information for bounded compilation.

---

ERKEERKE Sequential latch-based backend

In addition to the bounded combinational backend, a sequential backend was added.

This backend translates an NFA into a sequential circuit with latches.

The pipeline is:

EGEtext
regular expression
-> regex AST
-> NFA
-> sequential circuit
-> latch-based ASCII AIGER
EGE

The sequential circuit uses latches to store the current active NFA states.

The input protocol is stream-based:

- in each normal step, exactly one symbol input such as `is_a` or `is_b` is true
- in the final step, `end` is true
- the final step must not activate a symbol input
- the output `accept` is true iff `end` is true and an accepting state is active

For example, the word `aaa` for the expression `a*` is represented as:

EGEtext
step 1: is_a = true, end = false
step 2: is_a = true, end = false
step 3: is_a = true, end = false
step 4: end = true
EGE

The simulator validates traces before simulation.

Invalid traces are rejected, for example:

- empty traces
- missing final `end`
- early `end`
- multiple active symbol inputs in a normal step
- symbol input active in the final step
- unknown non-symbol inputs
- non-boolean input values

This backend produces AIGER files with `L > 0`, meaning that latches are present.

---

ERKEERKE Milestone 2 files

The following components are used for milestone 2 and later regex support:

| File | Purpose |
|---|---|
| `string_to_aiger/regex/regex_ast.py` | Defines regex AST node types such as `Empty`, `Char`, `Concat`, `UnionExpr`, `Star`, and `Intersect`. |
| `string_to_aiger/regex/regex_pretty.py` | Provides readable printing of regex ASTs. |
| `string_to_aiger/regex/regex_parser.py` | Parses the supported regular-expression fragment. |
| `string_to_aiger/regex/regex_alphabet.py` | Extracts alphabets from regex ASTs. |
| `string_to_aiger/regex/regex_length.py` | Computes regex length information and bound completeness. |
| `string_to_aiger/nfa/nfa.py` | Defines the NFA data structure. |
| `string_to_aiger/nfa/nfa_builder.py` | Constructs an NFA from a regex AST. |
| `string_to_aiger/nfa/nfa_evaluator.py` | Directly evaluates NFAs on candidate strings. |
| `string_to_aiger/nfa/nfa_alphabet.py` | Extracts alphabets from NFAs. |
| `string_to_aiger/nfa/nfa_prune.py` | Removes unreachable states from NFAs. |
| `string_to_aiger/nfa/nfa_optimize.py` | Applies basic NFA cleanup passes. |
| `string_to_aiger/bounded/bounded_nfa_encoding.py` | Encodes an NFA as a bounded combinational logical expression. |
| `string_to_aiger/regex/regex_to_aiger.py` | Provides a high-level wrapper from regex pattern and bound to ASCII AIGER. |
| `string_to_aiger/sequential/sequential_circuit.py` | Defines the intermediate representation for sequential circuits. |
| `string_to_aiger/sequential/sequential_aiger_writer.py` | Writes latch-based ASCII AIGER files. |
| `string_to_aiger/sequential/sequential_simulator.py` | Simulates sequential circuits in Python. |
| `string_to_aiger/sequential/sequential_trace.py` | Validates stream-based sequential input traces. |
| `string_to_aiger/sequential/nfa_to_sequential.py` | Translates a generic NFA into a sequential circuit. |
| `tests/tests_regex.py` | Tests regex parsing, NFA evaluation, bounded encoding, and AIGER output. |
| `tests/tests_regex_length.py` | Tests regex length analysis. |
| `tests/tests_sequential.py` | Tests the sequential backend. |
| `tests/tests_sequential_trace.py` | Tests sequential trace validation. |

---

ERKEERKE Run milestone 2 demos

To run the regex parser demo:

EGEbash
python demos/regex_parser_demo.py
EGE

To inspect generated NFAs:

EGEbash
python demos/nfa_demo.py
EGE

To run the direct NFA evaluator demo:

EGEbash
python demos/nfa_evaluator_demo.py
EGE

To run the bounded NFA demo:

EGEbash
python demos/bounded_nfa_demo.py
EGE

To compile a regex directly to bounded AIGER:

EGEbash
python demos/regex_to_aiger_demo.py
EGE

To run the manual sequential `a*` demo:

EGEbash
python demos/sequential_astar_demo.py
EGE

To simulate the manual sequential `a*` circuit:

EGEbash
python demos/sequential_astar_sim_demo.py
EGE

To run the generic NFA-to-sequential demo:

EGEbash
python demos/nfa_to_sequential_demo.py
EGE

Generated AIGER files from these demos are written to:

EGEtext
outputs/
EGE

---

ERKEERKE Milestone 3: Conjunction / intersection support

Milestone 3 adds support for conjunction, written as `&`.

The expression:

EGEtext
((a|b)*) & (a*)
EGE

means that a candidate string must satisfy both regular expressions at the same time.

In this example, `(a|b)*` accepts all strings over `a` and `b`, while `a*` accepts only strings consisting of `a`.

Therefore, their intersection behaves like:

EGEtext
a*
EGE

---

ERKEERKE Milestone 3 parser support

The regex parser supports the `&` operator.

The precedence order is:

EGEtext
1. repetition operators: *, +, ?, {n}, {m,n}, {m,}
2. concatenation
3. &
4. |
EGE

For example:

EGEtext
a|b&c
EGE

is parsed as:

EGEtext
a | (b & c)
EGE

The regex AST contains the node:

EGEtext
Intersect(left, right)
EGE

---

ERKEERKE Structural bounded conjunction encoding

For the bounded backend, conjunction can be compiled structurally.

The idea is:

EGEtext
compile(A & B)
=
compile(A) AND compile(B)
EGE

This means that both sides are compiled separately into bounded logical expressions, and the final expression is the conjunction of both.

For example:

EGEtext
(a|b)*&a*
EGE

is compiled by generating bounded encodings for both `(a|b)*` and `a*`, then combining them with `AND`.

This produces a combinational AIGER circuit.

---

ERKEERKE Structural sequential conjunction encoding

Sequential conjunction can be implemented using parallel circuit composition.

The idea is:

EGEtext
A & B
=
run A and B in parallel
accept = accept_A AND accept_B
EGE

For example, the expression:

EGEtext
((a|b)*) & (a*)
EGE

is handled by compiling both sides into sequential circuits:

EGEtext
left  = (a|b)*
right = a*
EGE

Both circuits read the same input stream.

Their internal latch names are renamed to avoid collisions:

EGEtext
state_0 -> left_state_0
state_0 -> right_state_0
EGE

The final output is:

EGEtext
accept = left_accept AND right_accept
EGE

This allows conjunction to be represented using latch-based AIGER by parallel composition.

---

ERKEERKE Product automaton construction

The project also supports explicit product automata for intersection.

Instead of compiling `A & B` structurally, both sides can be converted into automata and combined into a product automaton.

The idea is:

EGEtext
A & B
-> NFA(A)
-> NFA(B)
-> product NFA(A, B)
-> backend encoding
EGE

The product construction is available for both:

- bounded combinational compilation
- sequential latch-based compilation

This gives two selectable intersection strategies:

EGEtext
structural
product
EGE

The CLI exposes this through:

EGEbash
--intersection-strategy structural
--intersection-strategy product
EGE

---

ERKEERKE Milestone 3 files

The following components were added or extended for conjunction and product automata:

| File | Purpose |
|---|---|
| `string_to_aiger/regex/regex_ast.py` | Adds the `Intersect` AST node for conjunction / intersection. |
| `string_to_aiger/regex/regex_pretty.py` | Adds readable printing support for `Intersect`. |
| `string_to_aiger/regex/regex_parser.py` | Adds parsing support for the `&` operator. |
| `string_to_aiger/regex/regex_bounded_compiler.py` | Compiles regex ASTs with bounded structural intersection support. |
| `string_to_aiger/regex/regex_to_product_nfa.py` | Builds product-aware NFAs for regexes with intersection. |
| `string_to_aiger/bounded/product_bounded_compiler.py` | Compiles regexes through explicit product automata for the bounded backend. |
| `string_to_aiger/sequential/sequential_intersection.py` | Provides helpers for merging sequential circuits for structural conjunction. |
| `string_to_aiger/sequential/sequential_regex_compiler.py` | Compiles regex ASTs into sequential circuits, including structural `Intersect`. |
| `string_to_aiger/sequential/product_sequential_compiler.py` | Compiles regexes through explicit product automata for the sequential backend. |
| `tests/tests_intersection.py` | Tests bounded conjunction behavior and AIGER output. |
| `tests/tests_sequential_intersection.py` | Tests sequential conjunction behavior and latch-based AIGER output. |
| `tests/tests_nfa_product.py` | Tests product automaton behavior. |
| `tests/tests_product_backend.py` | Tests product-based backend behavior. |

---

ERKEERKE Run milestone 3 demos

To run the bounded intersection demo:

EGEbash
python demos/regex_intersection_demo.py
EGE

To run the sequential intersection demo:

EGEbash
python demos/sequential_intersection_demo.py
EGE

Generated AIGER files from these demos are written to:

EGEtext
outputs/
EGE

---

ERKEERKE Milestone 3 current status

The bounded backend supports conjunction for examples such as:

EGEtext
(a|b)*&a*
(ab)*&(a|b)*
a*&b*
EGE

The sequential backend also supports conjunction.

The same examples are supported in the sequential backend:

EGEtext
(a|b)*&a*
(ab)*&(a|b)*
a*&b*
EGE

The bounded backend produces combinational AIGER.

The sequential backend produces latch-based AIGER with `L > 0`.

The project supports both structural and product-based intersection strategies.

---

ERKEERKE Milestone 4: Evaluation and validation

Milestone 4 evaluates the generated AIGER circuits on benchmark expressions.

The evaluation currently contains three main parts:

- AIGER statistics comparison
- selected language behavior validation
- exhaustive bounded language validation

The benchmark patterns, bounds, and expected positive/negative examples are centralized in:

EGEtext
evaluation/benchmark_cases.py
EGE

The statistics comparison extracts information from the AIGER header:

EGEtext
aag M I L O A
EGE

where:

- `M` is the maximum variable index
- `I` is the number of inputs
- `L` is the number of latches
- `O` is the number of outputs
- `A` is the number of AND gates

The AIGER statistics evaluation compares:

- bounded backend with structural intersection
- bounded backend with product automata
- sequential backend with structural intersection
- sequential backend with product automata

The selected language behavior validation checks whether all backend/strategy combinations agree with manually specified expected results for selected candidate strings.

The exhaustive bounded validation generates all words up to the benchmark-specific bound over the extracted alphabet and checks whether all backend/strategy combinations agree with the product-aware NFA result.

---

ERKEERKE Milestone 4 files

The following evaluation files are currently used:

| File | Purpose |
|---|---|
| `evaluation/benchmark_cases.py` | Defines shared benchmark patterns, bounds, and expected positive/negative examples. |
| `evaluation/evaluate_aiger_stats.py` | Compares AIGER header statistics for backend and intersection-strategy combinations. |
| `evaluation/evaluate_language_behavior.py` | Validates selected language behavior examples. |
| `evaluation/evaluate_exhaustive_behavior.py` | Performs exhaustive bounded validation over benchmark alphabets. |
| `evaluation/aiger_stats.csv` | CSV output for AIGER statistics. |
| `evaluation/aiger_stats.md` | Markdown table output for AIGER statistics. |
| `evaluation/language_behavior.csv` | CSV output for selected language behavior validation. |
| `evaluation/language_behavior.md` | Markdown table output for selected language behavior validation. |
| `evaluation/exhaustive_behavior.csv` | CSV output for exhaustive bounded behavior validation. |
| `evaluation/exhaustive_behavior_summary.csv` | Summary CSV output for exhaustive bounded behavior validation. |
| `evaluation/exhaustive_behavior.md` | Markdown output for exhaustive bounded behavior validation. |
| `run_all_evaluations.py` | Runs all evaluation scripts. |

---

ERKEERKE Run evaluations

To run the AIGER statistics evaluation:

EGEbash
python evaluation/evaluate_aiger_stats.py
EGE

To run the selected language behavior validation:

EGEbash
python evaluation/evaluate_language_behavior.py
EGE

To run the exhaustive bounded language behavior validation:

EGEbash
python evaluation/evaluate_exhaustive_behavior.py
EGE

To run all evaluations:

EGEbash
python run_all_evaluations.py
EGE

The evaluation scripts generate:

EGEtext
evaluation/aiger_stats.csv
evaluation/aiger_stats.md
evaluation/language_behavior.csv
evaluation/language_behavior.md
evaluation/exhaustive_behavior.csv
evaluation/exhaustive_behavior_summary.csv
evaluation/exhaustive_behavior.md
EGE

These files can be used directly in the project report or presentation.

---

ERKEERKE AIGER validation

The project includes an internal structural validator for ASCII AIGER text.

The validator checks basic structural properties such as:

- valid `aag M I L O A` header format
- header counts for inputs, latches, outputs, and AND gates
- literal bounds
- input literal shape
- latch line shape
- output line shape
- AND gate line shape
- symbol/comment section structure

This is not a certified external semantic checker, but it catches malformed generated AIGER text.

The project also includes a validated AIGER writing pipeline:

EGEtext
AIGER text
-> internal structural validation
-> output directory creation
-> file writing
EGE

The CLI uses this pipeline by default.

Validation can be skipped explicitly with:

EGEbash
--skip-validation
EGE

---

ERKEERKE Command-line interface

The project provides a command-line interface through the Python module entry point:

EGEbash
python -m string_to_aiger
EGE

The CLI supports two backends:

- bounded
- sequential

The input pattern can be provided directly with `--pattern` or read from a file with `--input-file`.

These two options are mutually exclusive, and one of them must be provided.

For the bounded backend, a maximum word length can be selected with `--bound`.

The CLI supports two intersection strategies:

- `structural`
- `product`

The default strategy is `structural`.

The selected strategy can be changed with:

EGEbash
--intersection-strategy product
EGE

For bounded compilation, the CLI reports regex length analysis:

- minimum accepted word length
- maximum accepted word length when finite
- whether the analysis is exact
- whether the selected bound is complete for finite patterns

The CLI also validates generated AIGER text by default.

Example bounded compilation with a direct pattern:

EGEbash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --bound 4 --output outputs/cli_bounded.aag
EGE

Example bounded compilation using product automata:

EGEbash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --intersection-strategy product --bound 4 --output outputs/cli_bounded_product.aag
EGE

Example sequential compilation with a direct pattern:

EGEbash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend sequential --output outputs/cli_sequential.aag
EGE

Example sequential compilation using product automata:

EGEbash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend sequential --intersection-strategy product --output outputs/cli_sequential_product.aag
EGE

Example bounded compilation from an input file:

EGEbash
python -m string_to_aiger --input-file examples/cli_pattern.txt --backend bounded --bound 4 --output outputs/from_file.aag
EGE

Example bounded compilation without internal validation:

EGEbash
python -m string_to_aiger --pattern "a{1,3}" --backend bounded --bound 3 --skip-validation --output outputs/no_validation.aag
EGE

The default output path is:

EGEtext
outputs/cli_output.aag
EGE

If neither `--pattern` nor `--input-file` is provided, the CLI prints a usage message.

---

ERKEERKE CLI files

The command-line interface is implemented by:

| File | Purpose |
|---|---|
| `string_to_aiger/cli.py` | Defines the CLI argument parser and compiler dispatch logic. |
| `string_to_aiger/__main__.py` | Enables `python -m string_to_aiger`. |
| `tests/tests_cli.py` | Tests bounded CLI compilation, sequential CLI compilation, product strategy selection, input-file compilation, validation behavior, and invalid argument handling. |

---

ERKEERKE Tests

To run the milestone 1 tests:

EGEbash
python tests/tests.py
EGE

To run the regex and bounded encoding tests:

EGEbash
python tests/tests_regex.py
EGE

To run the regex length analysis tests:

EGEbash
python tests/tests_regex_length.py
EGE

To run the sequential backend tests:

EGEbash
python tests/tests_sequential.py
EGE

To run the sequential trace validation tests:

EGEbash
python tests/tests_sequential_trace.py
EGE

To run the bounded intersection tests:

EGEbash
python tests/tests_intersection.py
EGE

To run the sequential intersection tests:

EGEbash
python tests/tests_sequential_intersection.py
EGE

To run the CLI tests:

EGEbash
python tests/tests_cli.py
EGE

To run the evaluation tests:

EGEbash
python tests/tests_evaluation.py
EGE

To run the product automaton tests:

EGEbash
python tests/tests_nfa_product.py
EGE

To run the product backend tests:

EGEbash
python tests/tests_product_backend.py
EGE

To run the alphabet extraction tests:

EGEbash
python tests/tests_alphabet.py
EGE

To run the NFA pruning tests:

EGEbash
python tests/tests_nfa_prune.py
EGE

To run the NFA optimization tests:

EGEbash
python tests/tests_nfa_optimize.py
EGE

To run the AIGER validator tests:

EGEbash
python tests/tests_aiger_validator.py
EGE

To run the AIGER pipeline tests:

EGEbash
python tests/tests_aiger_pipeline.py
EGE

A full local test run can be done with:

EGEbash
python run_all_tests.py
EGE

This runs the full project test suite.

---

ERKEERKE Demo runner

All demos can be executed with:

EGEbash
python run_all_demos.py
EGE

This runs the milestone 1 demo, regex demos, NFA demos, bounded backend demos, sequential backend demos, and intersection demos.

---

ERKEERKE Output artifacts

Generated AIGER files are written to:

EGEtext
outputs/
EGE

Examples include:

- `outputs/output.aag`
- `outputs/regex_output.aag`
- `outputs/bounded_output_astar.aag`
- `outputs/sequential_astar.aag`
- `outputs/sequential_generic_astar.aag`
- `outputs/intersection_output__aorb_staranda_star.aag`
- `outputs/sequential_intersection_output.aag`
- `outputs/cli_bounded.aag`
- `outputs/cli_sequential.aag`
- `outputs/from_file.aag`

The exact file names depend on the demo, CLI command, and the regex pattern being compiled.

Generated `.aag` files are ignored by Git because they can be regenerated from the demo scripts or CLI commands.

Evaluation output files are generated under:

EGEtext
evaluation/
EGE

Examples include:

- `evaluation/aiger_stats.csv`
- `evaluation/aiger_stats.md`
- `evaluation/language_behavior.csv`
- `evaluation/language_behavior.md`
- `evaluation/exhaustive_behavior.csv`
- `evaluation/exhaustive_behavior_summary.csv`
- `evaluation/exhaustive_behavior.md`

---

ERKEERKE Current status

The current implementation supports the following compilation modes:

EGEtext
Milestone 1:
fixed strings
-> logical constraints
-> netlist
-> combinational AIGER

Milestone 2A:
regular expressions
-> AST
-> NFA
-> bounded combinational AIGER

Milestone 2B:
regular expressions
-> AST
-> NFA
-> sequential circuit
-> latch-based AIGER

Milestone 3A:
regular expressions with conjunction
-> AST with Intersect
-> structural bounded conjunction
-> combinational AIGER

Milestone 3B:
regular expressions with conjunction
-> AST with Intersect
-> structural parallel sequential circuits
-> latch-based AIGER

Milestone 3C:
regular expressions with conjunction
-> explicit product automata
-> bounded or sequential AIGER

Milestone 4:
generated AIGER circuits
-> statistics comparison
-> selected language behavior validation
-> exhaustive bounded language validation
EGE

The CLI provides a direct compiler interface for bounded and sequential AIGER generation.

The project also includes internal structural AIGER validation, regex length analysis, sequential trace validation, NFA cleanup utilities, and strategy-aware evaluation.

---

ERKEERKE Current limitations

- The bounded backend still requires a fixed maximum word length.
- The project includes regex length analysis and bound-completeness reporting, but it does not remove the need for a bound in the bounded backend.
- The sequential backend uses a stream-based input protocol.
- The sequential protocol is validated before simulation, but it is still a simple symbol-stream interface.
- Exhaustive validation is bounded by the benchmark-specific bound.
- The project does not provide unbounded language equivalence checking.
- The project does not yet integrate external AIGER tools.
- The project includes an internal structural AIGER validator, but not certified external AIGER semantic checking.
- The project does not yet integrate external SAT solvers or hardware model checkers.
- The regex parser supports a useful fragment, but not full PCRE/Python-style regular-expression syntax.
- Unsupported regex features include negated character classes, dot wildcard, anchors, predefined classes, lookaround, and lazy quantifiers.
- The project includes basic NFA cleanup, but not full DFA conversion or automata minimization.

---

ERKEERKE Future work

Possible future improvements include:

- integration with external AIGER tools
- semantic validation using external model checkers
- integration with SAT / hardware model checking workflows
- unbounded equivalence checking for generated representations
- DFA construction and DFA minimization
- richer regular-expression parser features such as negated character classes and dot wildcard
- automatic benchmark generation
- larger benchmark suites
- comparison with external model checking tools
- batch CLI mode for compiling multiple patterns
- additional CLI reporting options
- improved AIGER optimization

---

ERKEERKE Summary

The project implements a step-by-step compiler pipeline from string constraints to AIGER.

The conceptual progression is:

EGEtext
Milestone 1:
fixed string disjunctions
-> logical constraints
-> AIGER

Milestone 2:
regular expressions
-> AST
-> NFA
-> bounded or sequential AIGER

Milestone 3:
regular expressions with conjunction
-> AST with Intersect
-> structural or product-based intersection
-> bounded or sequential AIGER

Milestone 4:
generated AIGER circuits
-> statistics comparison
-> selected behavior validation
-> exhaustive bounded behavior validation
-> command-line compilation interface
EGE

The bounded backend is useful as a simpler intermediate encoding.

The sequential backend introduces latches and moves the project closer to a hardware model checking representation of automata.

The conjunction support extends the regex fragment by allowing two expressions to be required simultaneously.

The product automaton backend provides an explicit automata-theoretic strategy for compiling intersections.

The evaluation scripts provide evidence that the generated circuits behave correctly on selected benchmark examples and exhaustive bounded benchmark languages.

The command-line interface makes the compiler easier to use as a small standalone tool.

The internal validator, trace checker, length analysis, product strategy selection, and evaluation infrastructure make the project easier to test, explain, and extend.