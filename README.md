# string-to-aiger

Prototype compiler from simple string and regular-expression fragments to ASCII AIGER.

The project started with fixed-string disjunctions such as abba | abb and was then extended with Kleene star support using automata-based encodings.

## Current supported fragments

Milestone 1 supports disjunctions of concrete fixed strings:

```text
abba | abb | abbreviation
```

Milestone 2 extends this with a small regular-expression fragment including:

```text
a*
(ab)*
(a|b)*
(a|ba)*
```

The project currently does not support conjunction &.

## High-level goal

The goal is to translate string and regular-expression constraints into AIGER circuits.

The long-term idea is:

```text
string / r```x problem
-> logical or automata-based representation
-> circuit
-> AIGER
-> SAT / model checking tools
```

This makes it possible to represent string constraints in a hardware verification format.

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

## Milestone 1 encoding approach

For milestone 1, the input is a disjunction of fixed concrete strings.

The compiler translates each concrete string into a conjunction of constraints.

For example, abba becomes:

```text
len == 4
x[0] == 'a'
x[1] == 'b'
x[2] == 'b'
x[3] == 'a'
```

A disjunction of strings is then encoded as an OR of these conjunctions.

This is sufficient for black/white lists, because all accepted strings are known and have fixed length.

## Milestone 1 files

parser.py: parses a disjunction of concrete strings
model.py: internal matcher representation
matcher.py: directly evaluates the matcher model on candidate strings
compiler.py: compiles matchers into logical expressions
circuit.py: logical expression data structures
pretty.py: readable printing of logical expressions
evaluator.py: evaluates compiled expressions on candidate strings
netlist.py: gate-level netlist data structures
netlist_builder.py: converts logical expressions into a gate-level netlist
netlist_pretty.py: readable printing of netlists
aiger_writer.py: exports the netlist into ASCII AIGER
aiger.py: high-level wrapper for compiling expressions to AIGER
main.py: demo entry point
tests.py: basic regression tests

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
output.aag
```

## Milestone 1 tests

To run the milestone 1 tests:

```bash
python tests.py
```

## Example expressions

Example expressions can be placed inside files under examples/.

```text
abba | abb
abc | ab
hello | world
```

At the current milestone 1 demo setup, main.py reads one selected example file at a time.

## Milestone 2: Kleene star support

Milestone 2 extends the project from fixed-string disjunctions toward regular expressions with Kleene star.

The implemented milestone 2 pipeline is:

```text
regular expression
-> r```x AST
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

## R```x AST

For milestone 2, a separate r```x AST representation was introduced.

The main AST nodes are:

```text
Empty
Char
Concat
UnionExpr
Star
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
└── Concat(Char("b"), Char("a"))
```

This separates the structure of the regular expression from the later compilation steps.

## NFA construction

After parsing, the r```x AST is translated into an NFA.

The NFA representation contains:

a start state
a set of accepting states
symbol transitions
epsilon transitions

Epsilon transitions are represented internally with None.

For example, Kleene star introduces loops and epsilon transitions, allowing expressions such as:

```text
a*
(ab)*
```

to accept repeated occurrences, including the empty string.

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

## Sequential latch-based backend

In addition to the bounded combinational backend, an experimental sequential backend was added.

This backend translates an NFA into a sequential circuit with latches.

The pipeline is:

```text
regular expression
-> r```x AST
-> NFA
-> sequential circuit
-> latch-based ASCII AIGER
```

The sequential circuit uses latches to store the current active NFA states.

The input protocol is stream-based:

in each normal step, one symbol input such as is_a or is_b is true
in the final step, end is true
the output accept is true iff end is true and an accepting state is active

For example, the word aaa for the expression a* is represented as:

```text
step 1: is_a = true, end = false
step 2: is_a = true, end = false
step 3: is_a = true, end = false
step 4: is_a = false, end = true
```

This backend produces AIGER files with L > 0, meaning that latches are present.

## Milestone 2 files

The following components have been implemented for milestone 2:

r```x_ast.py: r```x AST node definitions
r```x_pretty.py: readable printing of r```x ASTs
r```x_parser.py: parser for a small r```x fragment
nfa.py: NFA data structure
nfa_builder.py: construction of an NFA from a r```x AST
nfa_evaluator.py: direct NFA evaluation on candidate strings
bounded_nfa_encoding.py: bounded combinational encoding of an NFA
r```x_to_aiger.py: high-level wrapper from r```x pattern and bound to ASCII AIGER
tests_r```x.py: tests for r```x parsing, NFA evaluation, bounded encoding, and AIGER output
sequential_circuit.py: intermediate representation for sequential circuits
sequential_aiger_writer.py: ASCII AIGER writer with latch support
sequential_simulator.py: Python simulator for sequential circuits
sequential_astar_demo.py: manual sequential prototype for a*
sequential_astar_sim_demo.py: simulation demo for the manual a* circuit
nfa_to_sequential.py: generic NFA to sequential circuit translation
nfa_to_sequential_demo.py: demo for generic sequential NFA encoding
tests_sequential.py: tests for the sequential backend

## Run milestone 2 demos

To run the bounded NFA demo:

```bash
python bounded_nfa_demo.py
```

To compile a r```x directly to bounded AIGER:

```bash
python r```x_to_aiger_demo.py
```

To run the manual sequential a* demo:

```bash
python sequential_astar_demo.py
```

To simulate the manual sequential a* circuit:

```bash
python sequential_astar_sim_demo.py
```

To run the generic NFA-to-sequential demo:

```bash
python nfa_to_sequential_demo.py
```

## Tests

To run the milestone 1 tests:

```bash
python tests.py
```

To run the r```x and bounded encoding tests:

```bash
python tests_r```x.py
```

To run the sequential backend tests:

```bash
python tests_sequential.py
```

## Current status

The current implementation supports three levels:

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

Milestone 2B prototype:
regular expressions with Kleene star
-> AST
-> NFA
-> sequential circuit
-> latch-based AIGER
```

## Current limitations

The bounded backend only reasons about candidate strings up to a fixed maximum length.

The sequential backend is still experimental and currently uses a simple stream-based input protocol.

The project currently does not support:

conjunction &
full regular-expression syntax
character classes
escape handling
minimization or optimization of automata
certified AIGER semantic checking with external tools

## Future work

Possible future improvements include:

support for conjunction
richer regular-expression parser
better alphabet handling
improved AIGER optimization
external validation with AIGER tools
comparison between bounded and sequential encodings
integration with hardware model checkers

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
```

The bounded backend is useful as a simpler intermediate encoding.

The sequential backend introduces latches and moves the project closer to a hardware model checking representation of automata.