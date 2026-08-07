# Meeting demo notes

> **Historical snapshot — Milestone 3 meeting (June 2026).** This document was prepared for an earlier project meeting and is retained as project-process history.
> Commands, counts, results, limitations, and plans below reflect that point in time; they are not current release claims.
>
> For maintained information, see the current [README](../README.md), [testing guide](testing.md), [validation guide](validation_demo.md), [artifact index](../artifacts/README.md), [command-line interface](../README.md#command-line-interface), [validation scripts](../validation/), and [formal-verification scope](../README.md#formal-verification-scope). The immutable final release is [`presentation-release-2026-08-06`](https://github.com/wh1tebrun/string-to-aiger/tree/presentation-release-2026-08-06).

This document is a short meeting-oriented demo plan for showing the current implementation status.

The main focus of this meeting is:

```text
Milestone 1:
fixed-string disjunctions -> AIGER

Milestone 2:
regular expressions with Kleene star -> AST -> NFA -> bounded/sequential AIGER
 
Milestone 3:
regular-expression conjunction / intersection -> structural and product-based AIGER
```

Milestone 4 evaluation infrastructure also exists in the repository, but the main meeting focus should be Milestone 1, Milestone 2, and Milestone 3.

---

## Goal of the demo

The goal is to show that the first three milestones are implemented, runnable, and explainable.

The demo should make clear that the project has:

* a working fixed-string pipeline
* a regex parser
* a regex AST representation
* NFA construction
* bounded AIGER generation
* sequential AIGER generation
* conjunction / intersection support with `&`
* structural intersection compilation
* explicit product automaton construction
* bounded and sequential product backends
* tests and demos that can be run locally
* a small CLI for direct compilation

---

## Suggested meeting order

A good order for the meeting is:

```text

1. Briefly explain the project goal.
2. Show Milestone 1 fixed-string pipeline.
3. Show Milestone 2 regex / Kleene-star pipeline.
4. Show Milestone 3 conjunction / intersection support.
5. Show generated AIGER output.
6. Show tests.
7. Show CLI usage.
8. Discuss strategy choices and next steps.
   ```

---

## Short project summary

The project translates simple string and regular-expression constraints into ASCII AIGER circuits.

The conceptual pipeline is:

```text
string / regex expression
-> internal representation
-> logical or automata-based representation
-> circuit
-> ASCII AIGER
```

The motivation is to represent string constraints in a hardware verification format.

For the current meeting, the important progression is:

```text
Milestone 1:
fixed strings
-> logical constraints
-> AIGER

Milestone 2:
regular expressions
-> regex AST
-> NFA
-> bounded or sequential AIGER

Milestone 3:
regular expressions with conjunction
-> structural intersection or product automata
-> bounded or sequential AIGER
```

---

## Milestone 1: fixed-string disjunctions

Milestone 1 supports expressions such as:

```text
abba | abb | abbreviation
```

The pipeline is:

```text
fixed-string disjunction
-> parser
-> matcher model
-> logical expression
-> netlist
-> ASCII AIGER
```

Example interpretation:

```text
abba | abb
```

represents:

```text
L = {"abba", "abb"}
```

The compiler encodes each fixed string as a conjunction of length and character-position constraints.

For example:

```text
abba
```

becomes:

```text
len == 4
x[0] == 'a'
x[1] == 'b'
x[2] == 'b'
x[3] == 'a'
```

A disjunction of strings is then encoded as an OR of such conjunctions.

---

## Milestone 1 demo command

Run:

```bash
python main.py
```

Expected result:

```text
The demo reads an example fixed-string expression and writes an ASCII AIGER file to outputs/output.aag.
```

Useful file to open afterwards:

```text
outputs/output.aag
```

---

## Milestone 1 test command

Run:

```bash
python tests/tests.py
```

Expected result:

```text
All tests passed.
```

---

## Milestone 2: regex and Kleene star

Milestone 2 extends the project with regular-expression support.

Important examples are:

```text
a*
(ab)*
(a|b)*
(a|ba)*
```

The bounded pipeline is:

```text
regular expression
-> regex AST
-> NFA
-> bounded combinational encoding
-> ASCII AIGER
```

The project also includes a sequential backend:

```text
regular expression
-> regex AST
-> NFA
-> sequential circuit
-> latch-based ASCII AIGER
```

---

## Regex parser demo

Run:

```bash
python demos/regex_parser_demo.py
```

What to explain:

```text
This shows that regex expressions are parsed into an explicit AST.
The parser is a recursive-descent parser and is not hardcoded for only the demo examples.
```

Useful examples:

```text
a*
(ab)*
(a|b)*
(a|ba)*
```

---

## NFA construction demo

Run:

```bash
python scripts/meeting_nfa_demo.py
```

What to explain:

```text
The regex AST is translated into an NFA.
The NFA contains states, symbol transitions, epsilon transitions, a start state, and accepting states.
```

Important point:

```text
Kleene star is represented using epsilon transitions and loops.
```

The meeting-specific NFA demo is intentionally focused on Milestone 2 examples.

---

## NFA evaluator demo

Run:

```bash
python demos/nfa_evaluator_demo.py
```

What to explain:

```text
Before generating AIGER, the NFA can be evaluated directly on candidate strings.
This is useful for checking the language behavior of the automaton.
```

Example behavior:

```text
a* accepts "", "a", "aa", "aaa"
a* rejects "b", "ab"
```

---

## Bounded AIGER generation demo

Run:

```bash
python demos/regex_to_aiger_demo.py
```

What to explain:

```text
This compiles a regex into a bounded combinational AIGER circuit.
The bound limits the maximum candidate word length considered by the bounded backend.
```

Example:

```text
a* with bound 3 accepts "", "a", "aa", "aaa"
a* with bound 3 rejects "aaaa"
```

because the word length exceeds the selected bound.

---

## Sequential backend demo

Run:

```bash
python demos/nfa_to_sequential_demo.py
```

What to explain:

```text
The sequential backend stores active NFA states in latches.
The generated AIGER has L > 0 in the header.
```

The input protocol is stream-based:

```text
normal step: one symbol input is true
final step: end is true
accept is true iff end is true and an accepting state is active
```

---

## Milestone 3: conjunction / intersection

Milestone 3 adds conjunction / intersection support with the `&` operator.

Example expressions:

```text
(a|b)*&a*
(ab)*&(a|b)*
a*&b*
```

The expression:

```text
(a|b)*&a*
```

means that the candidate word must satisfy both sides at the same time.

In this case:

```text
(a|b)* accepts all words over a and b
a* accepts only words consisting of a
their intersection behaves like a*
```

---

## Milestone 3 parser support

The regex parser supports the `&` operator.

The precedence order is:

```text

1. repetition operators: *, +, ?, {n}, {m,n}, {m,}
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

## Milestone 3 strategy 1: structural intersection

The structural bounded strategy compiles:

```text
A & B
```

as:

```text
compile(A) AND compile(B)
```

This is simple and direct.

For example:

```text
(a|b)*&a*
```

is compiled by producing bounded encodings for `(a|b)*` and `a*`, and then combining them with logical AND.

The structural sequential strategy runs two sequential circuits in parallel on the same input stream.

The final accept output is:

```text
accept = accept_left AND accept_right
```

This works because a word is accepted by the conjunction exactly when both subcircuits accept it.

---

## Milestone 3 strategy 2: product automata

The project also implements an explicit product automaton construction.

The idea is:

```text
A & B
-> NFA(A)
-> NFA(B)
-> product NFA(A, B)
-> bounded or sequential AIGER
```

Product states are pairs of states:

```text
(q_left, q_right)
```

A product state is accepting iff both component states are accepting.

This is the automata-theoretic construction for language intersection.

Why both strategies exist:

```text
Structural strategy:
simple and practical

Product automaton strategy:
theoretically explicit and useful for cross-checking behavior
```

---

## Milestone 3 demo commands

Run the bounded intersection demo:

```bash
python demos/regex_intersection_demo.py
```

Run the sequential intersection demo:

```bash
python demos/sequential_intersection_demo.py
```

What to explain:

```text
These demos show that the project supports regex conjunction / intersection with &.
They also show that intersection can be compiled to bounded or sequential AIGER.
```

---

## Milestone 3 test commands

Run:

```bash
python tests/tests_intersection.py
python tests/tests_sequential_intersection.py
python tests/tests_nfa_product.py
python tests/tests_product_backend.py
```

Expected result:

```text
All Milestone 3 intersection and product backend tests pass.
```

---

## CLI demo

The project can also be used through:

```bash
python -m string_to_aiger
```

Bounded example:

```bash
python -m string_to_aiger --pattern "a*" --backend bounded --bound 3 --output outputs/demo_astar_bounded.aag
```

Sequential example:

```bash
python -m string_to_aiger --pattern "a*" --backend sequential --output outputs/demo_astar_sequential.aag
```

Another bounded example:

```bash
python -m string_to_aiger --pattern "(ab)*" --backend bounded --bound 6 --output outputs/demo_abstar_bounded.aag
```

Bounded structural intersection example:

```bash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --intersection-strategy structural --bound 4 --output outputs/demo_intersection_structural.aag
```

Bounded product intersection example:

```bash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --intersection-strategy product --bound 4 --output outputs/demo_intersection_product.aag
```

Sequential structural intersection example:

```bash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend sequential --intersection-strategy structural --output outputs/demo_intersection_seq_structural.aag
```

Sequential product intersection example:

```bash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend sequential --intersection-strategy product --output outputs/demo_intersection_seq_product.aag
```

What to point out:

```text
The CLI prints the selected pattern, backend, intersection strategy, bound information for the bounded backend, AIGER validation status, and output path.
```

---

## Compact meeting demo runner

For a compact live demo, use:

```bash
python scripts/run_meeting_demo.py
```

This runs selected tests, demos, and CLI examples for Milestone 1, Milestone 2, and Milestone 3.

It writes a compact report to:

```text
outputs/meeting_demo_report.md
```

What to show:

```text

1. Terminal PASS summary
2. outputs/meeting_demo_report.md
3. generated AIGER headers
4. one generated .aag file if requested
   ```

This avoids scrolling through large terminal output during the meeting.

---

## Suggested commands to run live

The safest live demo command is:

```bash
python scripts/run_meeting_demo.py
```

If individual commands are preferred, use:

```bash
python tests/tests.py
python tests/tests_regex.py
python tests/tests_intersection.py
python tests/tests_nfa_product.py
python demos/regex_parser_demo.py
python scripts/meeting_nfa_demo.py
python demos/regex_to_aiger_demo.py
python demos/regex_intersection_demo.py
python -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --intersection-strategy product --bound 4 --output outputs/demo_intersection_product.aag
```

If there is enough time, also run:

```bash
python run_all_tests.py
```

---

## Files to mention for Milestone 1

Important Milestone 1 files:

| File                                         | Purpose                                     |
| -------------------------------------------- | ------------------------------------------- |
| `string_to_aiger/fixed/parser.py`            | Parses fixed-string disjunctions.           |
| `string_to_aiger/fixed/model.py`             | Defines the matcher model.                  |
| `string_to_aiger/fixed/compiler.py`          | Compiles matchers into logical expressions. |
| `string_to_aiger/logic/circuit.py`           | Defines logical expression data structures. |
| `string_to_aiger/netlist/netlist_builder.py` | Converts logical expressions to netlists.   |
| `string_to_aiger/aiger/aiger_writer.py`      | Writes ASCII AIGER.                         |
| `tests/tests.py`                             | Tests the Milestone 1 pipeline.             |

---

## Files to mention for Milestone 2

Important Milestone 2 files:

| File                                                    | Purpose                                                                  |
| ------------------------------------------------------- | ------------------------------------------------------------------------ |
| `string_to_aiger/regex/regex_parser.py`                 | Parses the supported regex fragment.                                     |
| `string_to_aiger/regex/regex_ast.py`                    | Defines regex AST nodes.                                                 |
| `string_to_aiger/nfa/nfa_builder.py`                    | Builds NFAs from regex ASTs.                                             |
| `string_to_aiger/nfa/nfa_evaluator.py`                  | Evaluates NFAs directly.                                                 |
| `string_to_aiger/bounded/bounded_nfa_encoding.py`       | Builds bounded combinational encodings.                                  |
| `string_to_aiger/sequential/nfa_to_sequential.py`       | Builds sequential circuits from NFAs.                                    |
| `string_to_aiger/sequential/sequential_aiger_writer.py` | Writes latch-based ASCII AIGER.                                          |
| `tests/tests_regex.py`                                  | Tests regex parsing, NFA evaluation, bounded encoding, and AIGER output. |
| `tests/tests_sequential.py`                             | Tests the sequential backend.                                            |

---

## Files to mention for Milestone 3

Important Milestone 3 files:

| File                                                        | Purpose                                                                 |
| ----------------------------------------------------------- | ----------------------------------------------------------------------- |
| `string_to_aiger/regex/regex_ast.py`                        | Defines the `Intersect` AST node.                                       |
| `string_to_aiger/regex/regex_parser.py`                     | Parses the `&` operator with the correct precedence.                    |
| `string_to_aiger/regex/regex_bounded_compiler.py`           | Compiles regex ASTs with structural bounded intersection.               |
| `string_to_aiger/regex/regex_to_product_nfa.py`             | Builds product-aware NFAs for regexes with intersection.                |
| `string_to_aiger/nfa/nfa_product.py`                        | Implements explicit product automaton construction.                     |
| `string_to_aiger/bounded/product_bounded_compiler.py`       | Compiles regexes through product automata for the bounded backend.      |
| `string_to_aiger/sequential/sequential_intersection.py`     | Merges sequential circuits for structural intersection.                 |
| `string_to_aiger/sequential/sequential_regex_compiler.py`   | Compiles regexes into sequential circuits with structural intersection. |
| `string_to_aiger/sequential/product_sequential_compiler.py` | Compiles regexes through product automata for the sequential backend.   |
| `tests/tests_intersection.py`                               | Tests bounded structural intersection.                                  |
| `tests/tests_sequential_intersection.py`                    | Tests sequential structural intersection.                               |
| `tests/tests_nfa_product.py`                                | Tests product automaton behavior.                                       |
| `tests/tests_product_backend.py`                            | Tests product-based bounded and sequential backends.                    |
| `docs/product_automaton.md`                                 | Explains product automaton construction.                                |

---

## Scope clarification answers

These are useful short answers if scope questions come up.

## Full regex syntax

Answer:

```text
The implementation intentionally supports a useful limited regex fragment.
It is not intended to be a full PCRE/Python-style regex engine.
The supported fragment is documented in docs/regex_grammar.md.
```

---

## DFA minimization

Answer:

```text
DFA minimization is not part of the first three milestones.
The project currently uses NFAs and includes basic NFA cleanup utilities.
Full DFA construction and minimization are documented as future work.
```

---

## External model checker validation

Answer:

```text
The project includes internal structural AIGER validation.
External model-checker based semantic validation is not required for the first three milestones and is treated as an extension.
The project has optional support for configuring an external AIGER validator.
```

---

## Unbounded equivalence proof

Answer:

```text
The implementation currently validates behavior through direct automaton evaluation, tests, bounded checks, and sequential simulation.
Unbounded equivalence checking is treated as future work.
```

---

## Why two intersection strategies?

Answer:

```text
Both strategies are correct.

The structural strategy is simple and practical:
compile A and B separately, then combine their accept conditions with AND.

The product strategy is the explicit automata-theoretic construction:
build a product NFA whose states are pairs of states.

Having both strategies is useful because they provide independent ways to implement and cross-check intersection behavior.
```

---

## What not to overemphasize in this meeting

The repository also contains Milestone 4 evaluation infrastructure, but the main meeting focus should be Milestone 1, Milestone 2, and Milestone 3.

Do not lead with:

```text
Milestone 4 evaluation infrastructure
generated benchmarks
external validation wrapper
larger benchmark reports
```

These can be mentioned briefly only if the discussion naturally moves toward later milestones.

---

## Good closing sentence for the meeting

A good closing summary is:

```text
The first three milestones are implemented and runnable.

Milestone 1 generates AIGER from concrete fixed-string disjunctions.

Milestone 2 parses Kleene-star regular expressions, builds NFAs, and compiles them to bounded or sequential AIGER.

Milestone 3 adds conjunction / intersection with &, using both structural compilation and explicit product automata.

The current implementation is intentionally scoped to the requested regex fragment, while larger regex features, DFA minimization, external semantic validation, and unbounded equivalence checking are treated as extensions.
```

---

## Final pre-meeting checklist

Before the meeting, run:

```bash
python scripts/run_meeting_demo.py
python run_all_tests.py
```

Optional:

```bash
python run_all_demos.py
python run_all_evaluations.py
```

Also check:

```bash
git status
```

The working tree should be clean before the meeting.
