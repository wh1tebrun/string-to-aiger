# Encoding Table

This document explains how candidate strings are represented as bit-level inputs for generated AIGER circuits.

# Bounded Encoding

The bounded backend uses one input vector per candidate word.

Typical bounded inputs:

```text
len_is_0
len_is_1
len_is_2
x_0_is_a
x_0_is_b
x_1_is_a
x_1_is_b
```

For candidate string `ab`, the bounded encoding sets:

```text
len_is_2 = 1
x_0_is_a = 1
x_1_is_b = 1
```

All incompatible length and character-position inputs are set to 0.

# Sequential Encoding

The sequential backend uses one input vector per time step.

Each normal step activates exactly one symbol input. The final step activates `end`.

If the input order is:

```text
end
is_a
is_b
```

then the encoding is:

```text
a   -> 010
b   -> 001
end -> 100
```

The word `ab` is represented as:

```text
010
001
100
.
```

The final dot terminates the aigsim stimulus file.

# Witness Meaning

A witness is an encoded input vector or trace that demonstrates a behavior of the generated AIGER circuit.

For ordinary validation, the witness shows agreement between the generated AIGER circuit and reference regex semantics.

For negative detection, the witness exposes a mismatch between expected regex semantics and a deliberately corrupted AIGER file.
