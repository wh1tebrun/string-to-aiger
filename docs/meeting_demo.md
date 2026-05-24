# Meeting demo notes

This document is a short meeting-oriented demo plan for showing the current implementation status.

The main focus of this meeting is:

```text
Milestone 1:
fixed-string disjunctions -> AIGER

Milestone 2:
regular expressions with Kleene star -> AST -> NFA -> AIGER
```

Later milestones and additional features are available in the repository, but they do not need to be the main focus of this first meeting unless there is time or interest.

---

## Goal of the demo

The goal is to show that the first two milestones are implemented and runnable.

The demo should make clear that the project has:

- a working fixed-string pipeline
- a regex parser
- a regex AST representation
- an NFA construction
- bounded AIGER generation
- sequential AIGER generation
- tests and demos that can be run locally
- a small CLI for direct compilation

---

## Suggested meeting order

A good order for the meeting is:

```text
1. Briefly explain the project goal.
2. Show Milestone 1 fixed-string pipeline.
3. Show Milestone 2 regex / Kleene-star pipeline.
4. Show generated AIGER output.
5. Show tests.
6. Show CLI usage.
7. Discuss scope questions and next steps.
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

The pipeline is:

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
python demos/nfa_demo.py
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

What to point out:

```text
The CLI prints the selected pattern, backend, bound information for the bounded backend, AIGER validation status, and output path.
```

---

## Suggested commands to run live

A compact live demo can use the following commands:

```bash
python tests/tests.py
python tests/tests_regex.py
python demos/regex_parser_demo.py
python demos/nfa_demo.py
python demos/regex_to_aiger_demo.py
python -m string_to_aiger --pattern "a*" --backend bounded --bound 3 --output outputs/demo_astar_bounded.aag
python -m string_to_aiger --pattern "a*" --backend sequential --output outputs/demo_astar_sequential.aag
```

If there is enough time, also run:

```bash
python run_all_tests.py
```

---

## Files to mention for Milestone 1

Important Milestone 1 files:

| File | Purpose |
|---|---|
| `string_to_aiger/fixed/parser.py` | Parses fixed-string disjunctions. |
| `string_to_aiger/fixed/model.py` | Defines the matcher model. |
| `string_to_aiger/fixed/compiler.py` | Compiles matchers into logical expressions. |
| `string_to_aiger/logic/circuit.py` | Defines logical expression data structures. |
| `string_to_aiger/netlist/netlist_builder.py` | Converts logical expressions to netlists. |
| `string_to_aiger/aiger/aiger_writer.py` | Writes ASCII AIGER. |
| `tests/tests.py` | Tests the Milestone 1 pipeline. |

---

## Files to mention for Milestone 2

Important Milestone 2 files:

| File | Purpose |
|---|---|
| `string_to_aiger/regex/regex_parser.py` | Parses the supported regex fragment. |
| `string_to_aiger/regex/regex_ast.py` | Defines regex AST nodes. |
| `string_to_aiger/nfa/nfa_builder.py` | Builds NFAs from regex ASTs. |
| `string_to_aiger/nfa/nfa_evaluator.py` | Evaluates NFAs directly. |
| `string_to_aiger/bounded/bounded_nfa_encoding.py` | Builds bounded combinational encodings. |
| `string_to_aiger/sequential/nfa_to_sequential.py` | Builds sequential circuits from NFAs. |
| `string_to_aiger/sequential/sequential_aiger_writer.py` | Writes latch-based ASCII AIGER. |
| `tests/tests_regex.py` | Tests regex parsing, NFA evaluation, bounded encoding, and AIGER output. |
| `tests/tests_sequential.py` | Tests the sequential backend. |

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

## DFA minimization

Answer:

```text
DFA minimization is not part of the first two milestones.
The project currently uses NFAs and includes basic NFA cleanup utilities.
Full DFA construction and minimization are documented as future work.
```

## External model checker validation

Answer:

```text
The project includes internal structural AIGER validation.
External model-checker based semantic validation is not required for the first two milestones and is treated as an extension.
The project has optional support for configuring an external AIGER validator.
```

## Unbounded equivalence proof

Answer:

```text
The implementation currently validates behavior through direct automaton evaluation, tests, and bounded checks.
Unbounded equivalence checking is treated as future work.
```

---

## Things not to overemphasize in this first meeting

The repository already contains additional work beyond Milestone 1 and Milestone 2, but the first meeting should stay focused.

Do not lead with:

```text
Milestone 3 intersection support
Milestone 4 evaluation infrastructure
product automata
generated benchmarks
external validation wrapper
```

These can be mentioned briefly only if the discussion naturally moves toward later milestones.

---

## Good closing sentence for the meeting

A good closing summary is:

```text
The first two milestones are implemented and runnable.
The fixed-string pipeline generates AIGER from concrete string disjunctions.
The regex pipeline parses Kleene-star expressions, builds NFAs, and compiles them to bounded or sequential AIGER.
The current implementation is intentionally scoped to the requested fragment, while larger regex features and external semantic validation are treated as extensions.
```

---

## Final pre-meeting checklist

Before the meeting, run:

```bash
python run_all_tests.py
python run_all_demos.py
```

Optional:

```bash
python run_all_evaluations.py
```

Also check:

```bash
git status
```

The working tree should be clean before the meeting.