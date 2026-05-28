# Meeting speech

This document contains a short speech plan for presenting the current status of the project.

The focus is:

```text
Milestone 1:
fixed-string disjunctions -> AIGER

Milestone 2:
regular expressions with Kleene star -> AST -> NFA -> AIGER
```

The goal is to present the implemented work clearly and avoid getting lost in implementation details too early.

---

## Opening

Suggested wording:

```text
The goal of my project is to translate simple string and regular-expression constraints into ASCII AIGER circuits.

The motivation is that string constraints can then be represented in a hardware verification format, which makes it possible to connect them later to SAT solving or model checking workflows.

For the first meeting, I would like to focus on the first two milestones: fixed-string disjunctions and regular expressions with Kleene star.
```

---

## Milestone 1 overview

Suggested wording:

```text
For Milestone 1, I implemented a pipeline for fixed-string disjunctions.

An input expression can look like:

abba | abb | abbreviation

The parser reads this expression and converts it into an internal matcher representation.

Each concrete string is then translated into logical constraints over the candidate word.
```

Example explanation:

```text
For example, the string abba is encoded as:

len == 4
x[0] == 'a'
x[1] == 'b'
x[2] == 'b'
x[3] == 'a'

A disjunction such as abba | abb is then encoded as an OR over these string-specific constraints.
```

Transition sentence:

```text
After constructing this logical expression, the project translates it into a netlist and then writes the result as ASCII AIGER.
```

---

## Milestone 1 demo

Suggested live command:

```bash
python tests/tests.py
```

What to say:

```text
This runs the regression tests for the fixed-string pipeline.

It checks parsing, matcher behavior, logical expression evaluation, netlist construction, and AIGER generation.
```

Optional demo command:

```bash
python main.py
```

What to say:

```text
This runs the original fixed-string demo and writes the generated AIGER file to outputs/output.aag.
```

---

## Milestone 2 overview

Suggested wording:

```text
For Milestone 2, I extended the project from fixed strings to a regular-expression fragment.

The important examples are:

a*
(ab)*
(a|b)*
(a|ba)*

The implementation introduces a regex AST and then translates this AST into an NFA.
```

Pipeline:

```text
regular expression
-> regex AST
-> NFA
-> bounded combinational encoding
-> ASCII AIGER
```

Also mention:

```text
I also implemented a sequential backend where the NFA state is represented using latches, so the generated AIGER is latch-based.
```

---

## Regex AST explanation

Suggested wording:

```text
The regex parser produces an explicit AST.

The core AST nodes are:

Empty
Char
Concat
UnionExpr
Star
Intersect

For the first two milestones, the important nodes are Char, Concat, UnionExpr, and Star.
```

Example:

```text
The expression (a|ba)* is represented as a Star node around a UnionExpr.

One branch is Char("a"), and the other branch is a concatenation of Char("b") and Char("a").
```

What to emphasize:

```text
This separates parsing from later compilation steps.

The compiler does not directly work on raw strings, but on a structured regex representation.
```

---

## Regex parser demo

Suggested live command:

```bash
python demos/regex_parser_demo.py
```

What to say:

```text
This demo prints the parsed structure of selected regex examples.

It shows that expressions such as a*, (ab)*, and (a|b)* are parsed into an explicit AST.
```

---

## NFA construction explanation

Suggested wording:

```text
After parsing, the regex AST is translated into an NFA.

The NFA contains:

a start state
accepting states
symbol transitions
epsilon transitions

Kleene star is represented using epsilon transitions and loops.
```

Example:

```text
For a*, the automaton can either accept the empty string immediately or read another a and loop back.
```

What to emphasize:

```text
This is the automata-theoretic part of the second milestone.
The regular expression is not encoded directly into AIGER; it first becomes an automaton.
```

---

## NFA demo

Suggested live command:

```bash
python scripts/meeting_nfa_demo.py
```

What to say:

```text
This meeting-specific demo prints NFAs for the milestone 2 examples.

It is intentionally focused on a*, (ab)*, (a|b)*, and (a|ba)*.
```

---

## NFA evaluator explanation

Suggested wording:

```text
Before generating AIGER, I also implemented a direct NFA evaluator.

This is useful because it lets me test the language behavior of the automaton directly.

For example, a* should accept the empty string, a, aa, aaa, and reject b or ab.
```

Suggested live command:

```bash
python demos/nfa_evaluator_demo.py
```

---

## Bounded AIGER backend explanation

Suggested wording:

```text
The bounded backend turns the NFA into a combinational logical expression.

A fixed maximum word length is selected, for example bound = 3.

The NFA is then unrolled up to that bound.
```

Example:

```text
For a* with bound 3, the generated circuit accepts:

""
"a"
"aa"
"aaa"

but rejects "aaaa" because the length is outside the selected bound.
```

What to emphasize:

```text
This is a bounded encoding, so the bound is an explicit part of the backend.
The advantage is that the generated AIGER is combinational and simple to inspect.
```

Suggested live command:

```bash
python demos/regex_to_aiger_demo.py
```

---

## Sequential backend explanation

Suggested wording:

```text
In addition to the bounded combinational backend, I also implemented a sequential backend.

Here, the active NFA states are stored in latches.

The input is read as a stream of symbols, and a final end signal marks the end of the word.
```

Input protocol:

```text
normal step: one symbol input is true
final step: end is true
accept is true iff end is true and an accepting state is active
```

What to emphasize:

```text
The generated AIGER has latches, so its header has L > 0.
This moves the project closer to a hardware-style representation of automata.
```

---

## CLI explanation

Suggested wording:

```text
I also added a small command-line interface, so the compiler can be used directly from the terminal.

For example, I can compile a* with the bounded backend and write an AIGER file to outputs/.
```

Suggested live command:

```bash
python -m string_to_aiger --pattern "a*" --backend bounded --bound 3 --output outputs/demo_astar_bounded.aag
```

Then say:

```text
The CLI prints the selected pattern, backend, bound, validation status, and output path.
```

Sequential CLI command:

```bash
python -m string_to_aiger --pattern "a*" --backend sequential --output outputs/demo_astar_sequential.aag
```

Then say:

```text
This produces a latch-based AIGER file.
```

---

## Compact demo runner

Suggested wording:

```text
To make the demo reproducible, I also prepared a meeting demo runner.

It runs the main tests and demos for the first two milestones and writes a compact report.
```

Suggested live command:

```bash
python scripts/run_meeting_demo.py
```

Then open:

```text
outputs/meeting_demo_report.md
```

What to say:

```text
This report summarizes which demo steps passed and lists the generated AIGER files with their headers.

The detailed command logs are stored separately, so the terminal output stays compact.
```

---

## Validation explanation

Suggested wording:

```text
For the first two milestones, validation is mainly done through unit tests and direct behavior checks.

The tests cover parsing, NFA evaluation, bounded expression evaluation, AIGER generation, and sequential simulation.

The project also includes an internal structural AIGER validator that checks whether the generated ASCII AIGER text is well formed.
```

If asked about external validation:

```text
External model-checker based semantic validation is not part of the first two milestones.

However, I added optional support for configuring an external AIGER validator later.
```

---

## Scope clarification

Suggested wording:

```text
The implementation intentionally supports a useful regex fragment rather than a full PCRE/Python-style regex engine.

The first two milestones focus on fixed-string disjunctions and automata-based support for regular expressions with Kleene star.

More advanced features such as full regex syntax, DFA minimization, external semantic checking, and unbounded equivalence checking are treated as extensions or future work.
```

---

## Possible professor question: Is this full regex?

Answer:

```text
No, it is intentionally not a full regex engine.

The supported grammar is documented in docs/regex_grammar.md.

The goal is to support the fragment needed for the compiler pipeline and to keep the translation to automata and AIGER clear.
```

---

## Possible professor question: Why NFA and not DFA?

Answer:

```text
NFAs are a natural intermediate representation for regular expressions, especially with Kleene star and union.

They are easier to construct directly from the regex AST.

DFA construction and minimization would be useful future extensions, but they are not necessary for the first two milestones.
```

---

## Possible professor question: What is the main limitation of the bounded backend?

Answer:

```text
The bounded backend only reasons about words up to a fixed maximum length.

This is expected for a bounded combinational encoding.

The sequential backend addresses this differently by processing the input as a stream and storing active NFA states in latches.
```

---

## Possible professor question: How do you know the generated circuit is correct?

Answer:

```text
For the first two milestones, I validate the pipeline at multiple levels.

I test the parser, the NFA evaluator, the bounded logical encoding, the sequential simulator, and the generated AIGER structure.

The direct NFA evaluator gives a reference for the expected language behavior before AIGER generation.
```

---

## Closing summary

Suggested wording:

```text
To summarize, the first two milestones are implemented and runnable.

Milestone 1 translates fixed-string disjunctions into logical constraints, netlists, and ASCII AIGER.

Milestone 2 adds a regex AST, NFA construction, bounded AIGER generation, and a sequential latch-based backend for Kleene-star examples.

The implementation is tested, documented, and can be demonstrated through both individual demos and the meeting demo runner.
```

---

## Very short fallback version

If time is short, say:

```text
The project currently translates fixed-string disjunctions and a small regular-expression fragment into ASCII AIGER.

For Milestone 1, fixed strings are encoded as length and character-position constraints.

For Milestone 2, regexes are parsed into an AST, translated to NFAs, and then compiled either to bounded combinational AIGER or sequential latch-based AIGER.

I prepared tests, demos, and a small CLI to show the pipeline end to end.
```