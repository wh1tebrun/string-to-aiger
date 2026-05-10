# string-to-aiger

Prototype compiler from simple string disjunctions to ASCII AIGER.

---

## Supported fragment

At the current milestone, the project supports:

* disjunction of concrete strings using `|`
* implicit concatenation inside concrete strings

Example input:

```text
abba | abb | abbreviation
```

---

## Current pipeline

```text
expression -> parser -> model -> logical expression -> netlist -> AIGER
```

---

## Files

* `parser.py`: parses a disjunction of concrete strings
* `model.py`: internal matcher representation
* `compiler.py`: compiles matchers into logical expressions
* `circuit.py`: logical expression data structures
* `evaluator.py`: evaluates compiled expressions on candidate strings
* `netlist_builder.py`: converts logical expressions into a gate-level netlist
* `aiger_writer.py`: exports the netlist into ASCII AIGER
* `aiger.py`: high-level wrapper for compiling expressions to AIGER
* `main.py`: demo entry point
* `tests.py`: basic regression tests

---

## Run

```bash
python main.py
```

---

## Tests

```bash
python tests.py
```

---

## Limitations

This is milestone 1 only. The implementation currently does not support:

* Kleene star `*`
* conjunction `&`
* parentheses
* full regular-expression parsing

---

## Example output

The tool generates an ASCII AIGER file:

```text
output.aag
```

---

## Example expressions

```text
abba | abb
abc | ab
hello | world
```

These examples can be placed inside files under `examples/`
and executed through `main.py`.

The current demo setup reads one example file at a time through:
`examples/test1.txt`

---

## Current encoding approach

For milestone 1, the supported input is a disjunction of fixed concrete strings.

Example:

```text
abba | abb
```

The compiler translates each concrete string into a conjunction of constraints:

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

## Current limitation

The current implementation is intentionally constraint-based and fixed-length.

It does not yet implement a full regular-expression AST or automaton construction. Therefore, expressions such as:

```text
a*
(a | ba)*
```

cannot be represented correctly with the current model.

Kleene star requires a state-based representation, such as an NFA/DFA with transitions and loops. This will be addressed in the next milestone.

---

## Plan for milestone 2

For Kleene star, the architecture will be extended as follows:

```text
regular expression
-> AST
-> NFA/DFA
-> transition system
-> AIGER
```

This means that milestone 2 will introduce a proper expression representation with nodes such as:

```text
Char
Concat
Union
Star
```

and then translate this representation into a state-based circuit.

---

## Future work

* support for Kleene star
* support for conjunction
* proper expression parser
* improved netlist sharing and optimization

## Milestone 2: Kleene star support

Milestone 2 extends the project from fixed-string disjunctions toward regular expressions with Kleene star.

The currently implemented Milestone 2 pipeline is:

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

For Milestone 2, a separate r```x AST representation was introduced.

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

For example, Kleene star introduces loop and epsilon transitions, allowing expressions such as:

```text
a*
(ab)*
```

to accept repeated occurrences, including the empty string.

## Bounded combinational encoding

For the current Milestone 2 implementation, the NFA is compiled using bounded combinational encoding.

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

This encoding is combinational and currently does not use AIGER latches.

## Current Milestone 2 status

The following components have been implemented:

r```x_ast.py: r```x AST node definitions
r```x_pretty.py: readable printing of r```x ASTs
r```x_parser.py: parser for a small r```x fragment
nfa.py: NFA data structure
nfa_builder.py: construction of an NFA from a r```x AST
nfa_evaluator.py: direct NFA evaluation on candidate strings
bounded_nfa_encoding.py: bounded combinational encoding of an NFA
r```x_to_aiger.py: high-level wrapper from r```x pattern and bound to ASCII AIGER
tests_r```x.py: tests for r```x parsing, NFA evaluation, bounded encoding, and AIGER output

## Milestone 2 limitations

The current Milestone 2 implementation is still bounded.

This means that the generated circuit only reasons about candidate strings up to a fixed maximum length.

The implementation currently does not yet use sequential AIGER with latches.

A future version can extend the backend as follows:

```text
r```x
-> AST
-> NFA
-> sequential transition system
-> latches
-> AIGER
```

This would allow the automaton state to be represented directly in the circuit instead of being unrolled up to a fixed bound.

## Run Milestone 2 demos

To run the bounded NFA demo:

```bash
python bounded_nfa_demo.py
```

To compile a r```x directly to AIGER:

```bash
python r```x_to_aiger_demo.py
```

To run the r```x-related tests:

```bash
python tests_r```x.py
```

## Milestone 2 summary

Milestone 2 introduces Kleene star support by moving from fixed-string constraints to an automata-based representation.

The important conceptual change is:

```text
Milestone 1:
fixed strings -> logical constraints -> AIGER

Milestone 2:
regular expressions -> AST -> NFA -> bounded logical encoding -> AIGER
```

The current implementation uses bounded combinational encoding as an intermediate step before moving to a possible sequential/latch-based AIGER encoding later.