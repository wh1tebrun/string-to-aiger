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
