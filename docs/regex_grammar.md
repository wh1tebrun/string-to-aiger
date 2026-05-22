# Supported regular-expression grammar

This document describes the regular-expression fragment supported by `string-to-aiger`.

The parser is implemented as a small recursive-descent parser. It supports a deliberately limited but useful subset of regular expressions, designed for translation into automata and AIGER circuits.

---

## Supported operators

The currently supported operators are:

| Operator | Meaning | Example |
|---|---|---|
| concatenation | sequence of expressions | `ab` |
| `|` | union / alternation | `a|b` |
| `&` | conjunction / intersection | `a*&b*` |
| `*` | zero or more repetitions | `a*` |
| `+` | one or more repetitions | `a+` |
| `?` | optional expression | `a?` |
| `{n}` | exactly `n` repetitions | `a{3}` |
| `{m,n}` | between `m` and `n` repetitions | `a{1,3}` |
| `{m,}` | at least `m` repetitions | `a{2,}` |
| `(...)` | grouping | `(ab)*` |
| `[...]` | character class | `[ab]` |
| `[a-c]` | character range | `[a-c]` |
| `\` | escape next character | `a\*` |

---

## Grammar

The parser follows this precedence order:

```text
highest precedence

repetition operators: *, +, ?, {n}, {m,n}, {m,}
concatenation
&
|

lowest precedence
```

A simplified grammar is:

```text
regex        ::= union

union        ::= intersection ("|" intersection)*

intersection ::= concat ("&" concat)*

concat       ::= repeat+

repeat       ::= atom repetition_operator*

repetition_operator
             ::= "*"
              |  "+"
              |  "?"
              |  bounded_repetition

bounded_repetition
             ::= "{" number "}"
              |  "{" number "," number "}"
              |  "{" number "," "}"

atom         ::= literal
              |  escaped_literal
              |  group
              |  character_class

group        ::= "(" regex ")"

character_class
             ::= "[" class_item+ "]"

class_item   ::= class_literal
              |  class_literal "-" class_literal

number       ::= digit+
```

The parser rejects empty expressions and malformed bounded repetitions.

---

## Operator precedence examples

The expression:

```text
a|b&c
```

is parsed as:

```text
a | (b & c)
```

because `&` has higher precedence than `|`.

The expression:

```text
ab|c
```

is parsed as:

```text
(ab) | c
```

because concatenation has higher precedence than union.

The expression:

```text
a*&b*
```

is parsed as:

```text
(a*) & (b*)
```

because repetition operators have the highest precedence.

---

## Desugaring

Some parser-level operators are translated into the core regex AST.

The core AST nodes are:

```text
Empty
Char
Concat
UnionExpr
Star
Intersect
```

The parser keeps the AST small by desugaring higher-level operators.

## One-or-more repetition

The expression:

```text
a+
```

is desugared into:

```text
a a*
```

or structurally:

```text
Concat(Char("a"), Star(Char("a")))
```

## Optional expression

The expression:

```text
a?
```

is desugared into:

```text
ε | a
```

or structurally:

```text
UnionExpr(Empty(), Char("a"))
```

## Exact bounded repetition

The expression:

```text
a{3}
```

is desugared into:

```text
aaa
```

or structurally:

```text
Concat(Char("a"), Concat(Char("a"), Char("a")))
```

## Bounded repetition range

The expression:

```text
a{1,3}
```

is desugared into:

```text
a a? a?
```

This accepts:

```text
a
aa
aaa
```

## Open-ended bounded repetition

The expression:

```text
a{2,}
```

is desugared into:

```text
a a a*
```

This accepts all words with at least two `a` symbols.

## Character classes

The expression:

```text
[ab]
```

is desugared into:

```text
a | b
```

The expression:

```text
[a-c]
```

is desugared into:

```text
a | b | c
```

---

## Escaping

The parser supports basic escaping for literal operator characters.

For example:

```text
a\*
```

matches the concrete string:

```text
a*
```

instead of applying Kleene star to `a`.

Examples of escaped literals include:

```text
\*
\+
\?
\|
\&
\(
\)
\[
\]
\{
\}
\\
```

Escaping is also supported inside character classes.

For example:

```text
[a\-c]
```

matches one of:

```text
a
-
c
```

---

## Examples

The following expressions are supported:

```text
a*
(ab)*
(a|b)*
(a|ba)*
(a|b)*&a*
(ab)*&(a|b)*
a*&b*
a+
a?
a{3}
a{1,3}
a{2,}
[ab]*
[a-c]{2,4}
a\*
```

---

## Unsupported features

The parser intentionally does not implement full PCRE/Python-style regular expressions.

Unsupported features include:

```text
negated character classes, such as [^a]
dot wildcard, such as .
anchors, such as ^ and $
predefined classes, such as \d or \w
lookahead and lookbehind
lazy quantifiers, such as *? or +?
backreferences
capture groups
```

These features are outside the current project scope.

---

## Relation to the compiler pipeline

After parsing, the regex AST is translated into an NFA.

The main pipeline is:

```text
regular expression
-> regex AST
-> NFA
-> bounded or sequential circuit
-> ASCII AIGER
```

For conjunction / intersection expressions using `&`, the project supports two strategies:

```text
structural intersection
explicit product automaton construction
```

Both strategies are tested and can be selected through the command-line interface.