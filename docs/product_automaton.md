# Product automaton construction

This document describes the explicit product automaton construction used by `string-to-aiger` for regular-expression intersection.

The project supports conjunction / intersection with the `&` operator.

For example:

```text
(a|b)*&a*
```

means that a word must be accepted by both sides at the same time.

The language of this expression is:

```text
L((a|b)*) ∩ L(a*)
```

This behaves like:

```text
a*
```

because `(a|b)*` accepts all words over `a` and `b`, while `a*` only accepts words consisting of `a`.

---

## Motivation

Intersection can be implemented in two different ways in this project.

The first strategy is structural compilation.

For the bounded backend, this means:

```text
compile(A & B) = compile(A) AND compile(B)
```

For the sequential backend, this means:

```text
run circuit(A) and circuit(B) in parallel
accept = accept_A AND accept_B
```

This is simple and works well, but it does not explicitly construct the automaton for the intersection language.

The second strategy is explicit product automaton construction.

This is more automata-theoretic:

```text
A & B
-> NFA(A)
-> NFA(B)
-> product NFA(A, B)
-> backend encoding
-> AIGER
```

This makes the implementation easier to explain in terms of formal language theory.

---

## Basic idea

Given two automata:

```text
A1 = (Q1, Σ, δ1, q01, F1)
A2 = (Q2, Σ, δ2, q02, F2)
```

their product automaton is:

```text
A = (Q1 × Q2, Σ, δ, (q01, q02), F1 × F2)
```

The state space is the Cartesian product of the two state spaces.

A product state has the form:

```text
(q1, q2)
```

where:

- `q1` is a state from the first automaton
- `q2` is a state from the second automaton

A product state is accepting iff both component states are accepting:

```text
(q1, q2) is accepting iff q1 ∈ F1 and q2 ∈ F2
```

Therefore, a word is accepted by the product automaton exactly when it is accepted by both original automata.

---

## Transition construction

For each symbol transition in the first automaton:

```text
q1 --a--> q1'
```

and each matching symbol transition in the second automaton:

```text
q2 --a--> q2'
```

the product automaton receives the transition:

```text
(q1, q2) --a--> (q1', q2')
```

This synchronizes both automata on the same input symbol.

For example, if both automata can read `a`, then the product automaton can also read `a`.

If one side cannot read the current symbol, then the product transition does not exist.

This is what enforces intersection behavior.

---

## Accepting condition

The product automaton accepts only when both sides accept.

Given:

```text
F1 = accepting states of A1
F2 = accepting states of A2
```

the accepting states of the product automaton are:

```text
F = F1 × F2
```

That means:

```text
(q1, q2) ∈ F
iff
q1 ∈ F1 and q2 ∈ F2
```

This corresponds directly to conjunction:

```text
accept = accept_A AND accept_B
```

---

## Example

Consider the expression:

```text
(a|b)*&a*
```

The left side accepts:

```text
""
"a"
"b"
"aa"
"ab"
"ba"
"bb"
...
```

The right side accepts:

```text
""
"a"
"aa"
"aaa"
...
```

The intersection accepts only words accepted by both sides:

```text
""
"a"
"aa"
"aaa"
...
```

So the product automaton accepts the same language as:

```text
a*
```

and rejects words such as:

```text
"b"
"ab"
"ba"
```

---

## Handling epsilon transitions

The project NFAs may contain epsilon transitions.

Epsilon transitions are represented internally with:

```text
None
```

Before product behavior is evaluated, epsilon reachability is taken into account by the NFA evaluation and compilation logic.

This allows expressions such as:

```text
a*
(ab)*
(a|b)*
```

to behave correctly even though their Thompson-style NFAs contain epsilon transitions.

---

## Relation to structural intersection

The project supports both intersection strategies:

```text
structural
product
```

The structural strategy keeps the two sides separate and combines their final results.

The product strategy constructs a single automaton representing the intersection language.

Conceptually:

```text
structural strategy:
A & B
-> compile(A)
-> compile(B)
-> AND results

product strategy:
A & B
-> product automaton for L(A) ∩ L(B)
-> compile product automaton
```

Both strategies should accept the same language.

The evaluation scripts compare these strategies on benchmark examples.

---

## Bounded backend

For the bounded backend, the product strategy follows this pipeline:

```text
regular expression with &
-> regex AST
-> product-aware NFA
-> bounded combinational encoding
-> netlist
-> ASCII AIGER
```

For example:

```text
python -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --intersection-strategy product --bound 4
```

This generates a combinational AIGER circuit.

The resulting AIGER header has:

```text
L = 0
```

because bounded encodings do not use latches.

---

## Sequential backend

For the sequential backend, the product strategy follows this pipeline:

```text
regular expression with &
-> regex AST
-> product-aware NFA
-> sequential circuit
-> latch-based ASCII AIGER
```

For example:

```text
python -m string_to_aiger --pattern "(a|b)*&a*" --backend sequential --intersection-strategy product
```

This generates a sequential AIGER circuit.

The resulting AIGER header has:

```text
L > 0
```

because the sequential backend uses latches to store active automaton states.

---

## CLI selection

The command-line interface exposes the strategy through:

```bash
--intersection-strategy structural
--intersection-strategy product
```

The default strategy is:

```text
structural
```

Example bounded structural compilation:

```bash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --intersection-strategy structural --bound 4
```

Example bounded product compilation:

```bash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend bounded --intersection-strategy product --bound 4
```

Example sequential structural compilation:

```bash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend sequential --intersection-strategy structural
```

Example sequential product compilation:

```bash
python -m string_to_aiger --pattern "(a|b)*&a*" --backend sequential --intersection-strategy product
```

---

## Evaluation

The evaluation scripts compare structural and product strategies.

The AIGER statistics evaluation compares:

```text
bounded + structural
bounded + product
sequential + structural
sequential + product
```

The language behavior evaluation checks selected positive and negative examples.

The exhaustive bounded evaluation generates all words up to the benchmark-specific bound over the extracted alphabet and compares:

```text
expected product-aware NFA result
bounded structural result
bounded product result
sequential structural result
sequential product result
```

A result is marked as `OK` only if all results agree.

---

## Correctness intuition

The correctness intuition is based on the standard automata-theoretic property:

```text
L(A1 × A2) = L(A1) ∩ L(A2)
```

A word is accepted by the product automaton iff:

```text
the first component reaches an accepting state
and
the second component reaches an accepting state
```

This is exactly the meaning of conjunction / intersection.

Therefore, product automata provide a direct automata-based implementation of the `&` operator.

---

## Limitations

The product automaton construction can increase the number of states.

If the first automaton has `n` states and the second automaton has `m` states, then the product automaton can have up to:

```text
n * m
```

states.

This is expected for explicit product constructions.

The project includes basic NFA cleanup utilities, but it does not yet implement full DFA minimization.

---

## Related files

The product automaton implementation is mainly connected to:

| File | Purpose |
|---|---|
| `string_to_aiger/regex/regex_to_product_nfa.py` | Builds product-aware NFAs for regexes with intersection. |
| `string_to_aiger/bounded/product_bounded_compiler.py` | Compiles product-aware NFAs with the bounded backend. |
| `string_to_aiger/sequential/product_sequential_compiler.py` | Compiles product-aware NFAs with the sequential backend. |
| `tests/tests_nfa_product.py` | Tests product automaton behavior. |
| `tests/tests_product_backend.py` | Tests product-based backend compilation. |
| `evaluation/evaluate_language_behavior.py` | Compares language behavior across strategies. |
| `evaluation/evaluate_exhaustive_behavior.py` | Performs exhaustive bounded comparison across strategies. |

---

## Summary

Product automata provide an explicit automata-theoretic implementation of regular-expression intersection.

The project supports both structural and product-based intersection strategies.

The product strategy is available for both bounded and sequential compilation.

The command-line interface exposes this strategy directly.

The evaluation scripts compare structural and product strategies to check that they agree on benchmark examples.