# Meeting Q&A notes

This document contains possible questions and short answers for the project meeting.

The focus of the meeting is mainly:

```text
Milestone 1:
fixed-string disjunctions -> AIGER

Milestone 2:
regular expressions with Kleene star -> AST -> NFA -> AIGER
```

The goal is to answer questions clearly without overclaiming.

---

## General project questions

## What is the main goal of the project?

Answer:

```text
The main goal is to translate simple string and regular-expression constraints into ASCII AIGER circuits.

The idea is to represent string constraints in a hardware verification format, so that they can later be connected to SAT or model checking workflows.
```

---

## Why AIGER?

Answer:

```text
AIGER is a compact and standard format for And-Inverter Graphs.

It is commonly used in hardware verification and model checking contexts.

By translating string constraints into AIGER, the project creates a bridge between string/regex constraints and hardware verification representations.
```

---

## What exactly is compiled to AIGER?

Answer:

```text
The compiler currently generates a circuit whose output represents whether a candidate word satisfies the input expression.

For fixed strings, the circuit checks length and character-position constraints.

For regexes, the expression is first translated into an NFA, and then the NFA is encoded either as a bounded combinational circuit or as a sequential latch-based circuit.
```

---

## Milestone 1 questions

## How does the fixed-string encoding work?

Answer:

```text
Each concrete string is encoded as a conjunction of constraints.

For example, abba becomes:

len == 4
x[0] == 'a'
x[1] == 'b'
x[2] == 'b'
x[3] == 'a'

A disjunction such as abba | abb is encoded as an OR over the encodings of the individual strings.
```

---

## Is Milestone 1 separate from the regex pipeline?

Answer:

```text
Milestone 1 was implemented first as a direct fixed-string pipeline.

Later, the regex pipeline generalizes the idea using regex ASTs and NFAs.

So the fixed-string implementation is still useful as the initial milestone and as a simple reference pipeline.
```

---

## Why not represent fixed strings directly as regexes from the beginning?

Answer:

```text
The project was developed milestone by milestone.

The first milestone intentionally used a simpler direct representation for fixed-string disjunctions.

This made the parser, logical encoding, netlist generation, and AIGER writer easier to build and test before adding automata.
```

---

## How do you test Milestone 1?

Answer:

```text
The Milestone 1 tests check parsing, matcher behavior, logical expression evaluation, netlist construction, and ASCII AIGER generation.

They can be run with:

python tests/tests.py
```

---

## Milestone 2 questions

## How does the Kleene-star implementation work?

Answer:

```text
The regex is parsed into an AST.

Then the AST is translated into an NFA.

Kleene star is represented in the NFA using epsilon transitions and loops.

The resulting NFA can then be encoded as a bounded combinational circuit or as a sequential circuit with latches.
```

---

## Why use an NFA?

Answer:

```text
NFAs are a natural intermediate representation for regular expressions.

They are easy to construct from regex ASTs, especially for union, concatenation, and Kleene star.

The NFA also gives a clear automata-theoretic layer between parsing and AIGER generation.
```

---

## Why not use a DFA directly?

Answer:

```text
DFA construction is not necessary for the first two milestones.

The current goal is to support regex-to-automaton translation and AIGER generation.

Using NFAs keeps the construction simple and close to the structure of the regex.

DFA conversion and minimization are useful future extensions.
```

---

## Is DFA minimization implemented?

Answer:

```text
No, full DFA minimization is not implemented.

The project includes basic NFA cleanup utilities, but not full DFA construction or minimization.

I treat DFA minimization as future work because it is an optimization step, not required for the first two milestones.
```

---

## What regex syntax is supported?

Answer:

```text
The project supports a deliberately limited but useful regex fragment.

The important Milestone 2 examples are:

a*
(ab)*
(a|b)*
(a|ba)*

The parser has also been extended with operators such as +, ?, bounded repetitions, character classes, character ranges, and escaping.

The supported grammar is documented in docs/regex_grammar.md.
```

---

## Is this a full PCRE or Python-style regex parser?

Answer:

```text
No.

The parser is intentionally not a full PCRE/Python-style regex engine.

It supports the fragment needed for the compiler pipeline.

Unsupported features include negated character classes, dot wildcard, anchors, predefined classes, lookaround, lazy quantifiers, and backreferences.
```

---

## Why add features beyond Kleene star?

Answer:

```text
The core Milestone 2 requirement is Kleene-star support.

The additional parser features are small extensions that make the fragment more useful and demonstrate that the parser is structured rather than hardcoded for only a few examples.

They are still translated into the same core AST representation.
```

---

## What is the bounded backend?

Answer:

```text
The bounded backend unrolls the NFA up to a fixed maximum word length.

For example, with bound 3, a* accepts "", "a", "aa", and "aaa", but not "aaaa".

The result is a combinational AIGER circuit.
```

---

## Why is a bound needed?

Answer:

```text
The bounded backend is combinational.

To represent regex behavior over a finite circuit without latches, the maximum word length must be fixed.

This is why the bound is an explicit parameter.
```

---

## Is the bounded backend complete?

Answer:

```text
It is complete only up to the selected bound.

For finite regexes, the project includes length analysis to report whether the selected bound covers all possible accepted words.

For unbounded regexes such as a*, no finite bound is complete.
```

---

## What does the sequential backend add?

Answer:

```text
The sequential backend represents active NFA states using latches.

Instead of fixing a word length in a purely combinational circuit, it reads the input as a stream of symbols and uses an end signal to mark the end of the word.

The generated AIGER has latches, so the AIGER header has L > 0.
```

---

## How does the sequential input protocol work?

Answer:

```text
In each normal step, exactly one symbol input is active.

In the final step, the end input is active.

The accept output is true iff end is true and an accepting NFA state is active.
```

---

## Validation questions

## How do you know the parser is correct?

Answer:

```text
The parser is tested on representative expressions for characters, concatenation, union, Kleene star, bounded repetitions, character classes, escaping, and intersections.

The supported grammar is also documented explicitly in docs/regex_grammar.md.
```

---

## How do you know the NFA construction is correct?

Answer:

```text
The NFA construction is tested through direct NFA evaluation.

For example, for a*, the evaluator checks that "", "a", "aa", and "aaa" are accepted, while "b" and "ab" are rejected.

This validates the automaton behavior before AIGER generation.
```

---

## How do you know the generated AIGER is correct?

Answer:

```text
For the first two milestones, the project validates the pipeline at several levels.

It tests the parser, NFA evaluator, bounded logical expression evaluator, sequential simulator, and generated AIGER structure.

The project also includes an internal structural AIGER validator that checks the generated ASCII AIGER format.
```

---

## Did you use an external model checker?

Answer:

```text
External model-checker based semantic validation is not part of the first two milestones.

The project currently has internal structural AIGER validation and optional support for configuring an external AIGER validator.

Deeper integration with external model checkers is treated as future work.
```

---

## Do you have an unbounded equivalence proof?

Answer:

```text
No.

The implementation uses tests, direct NFA evaluation, bounded checks, and structural validation.

Unbounded language-equivalence checking is not part of the first two milestones and is documented as future work.
```

---

## What is validated internally?

Answer:

```text
The internal AIGER validator checks the structure of the generated ASCII AIGER text.

It checks the header, counts, literal bounds, input lines, latch lines, output lines, AND gate lines, symbols, and comments.

This catches malformed AIGER output, but it is not a certified semantic proof.
```

---

## Demo questions

## What should I look at first in the demo?

Answer:

```text
A good first file is docs/meeting_demo.md.

It explains the demo order.

Then scripts/run_meeting_demo.py can be run to generate outputs/meeting_demo_report.md.
```

---

## Why do you have a meeting demo runner?

Answer:

```text
The meeting demo runner makes the demo reproducible.

It runs the key Milestone 1 and Milestone 2 tests and demos, writes compact logs, and generates a short report.

This avoids relying on manual terminal scrolling during the meeting.
```

---

## What does the meeting report show?

Answer:

```text
The report lists the demo steps, whether they passed, the commands that were run, the log files, and the generated AIGER files with their headers.
```

---

## Scope and limitation questions

## What are the main limitations right now?

Answer:

```text
The bounded backend requires a fixed bound.

The sequential backend uses a simple stream-based input protocol.

The parser supports a useful regex fragment, but not full PCRE/Python-style regex syntax.

External semantic checking and unbounded equivalence checking are treated as future work.
```

---

## Which parts are future work?

Answer:

```text
Possible future work includes:

external semantic validation with model checkers
unbounded language-equivalence checking
DFA construction and minimization
richer regex syntax
larger or randomized benchmark suites
deeper integration with SAT or hardware model checking workflows
```

---

## If asked about Milestone 3 or later work

Answer carefully:

```text
I have also started exploring later extensions in the repository, but for this meeting I wanted to focus on the first two milestones and make sure their scope and implementation are correct before presenting the later parts in detail.
```

This is useful because it does not hide that the repository may contain later work, but it keeps the meeting focused.

---

## If asked why the repository has more than Milestone 1 and 2

Answer:

```text
I continued implementing later extensions while preparing the first two milestones.

However, the demo is intentionally focused on Milestone 1 and Milestone 2, because those are the parts I wanted to clarify and show first.
```

---

## Short answers for very direct questions

## Is full regex syntax required for Milestone 2?

Answer:

```text
My understanding is no.

Milestone 2 focuses on a regex fragment with Kleene star, not a full regex engine.
```

---

## Is DFA minimization required for Milestone 2?

Answer:

```text
My understanding is no.

It would be an optimization/future-work item.
```

---

## Is external model checking required for Milestone 2?

Answer:

```text
My understanding is no.

For the first two milestones, internal tests and structural validation are sufficient, while external semantic checking is a later extension.
```

---

## Is unbounded equivalence checking required?

Answer:

```text
My understanding is no.

The current implementation focuses on compilation and bounded/direct validation.
```

---

## Good closing answer

Answer:

```text
My current goal is to keep the implementation milestone-oriented.

The first milestone establishes the fixed-string-to-AIGER pipeline.

The second milestone generalizes this using regex ASTs and NFAs.

The current implementation is runnable, tested, and documented, while heavier features such as full regex syntax, DFA minimization, external semantic validation, and unbounded equivalence checking are treated as extensions.
```