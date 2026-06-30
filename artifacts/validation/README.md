# Validation Artifacts

This directory contains inspectable validation artifacts for the string-to-AIGER compiler.

The goal is to make external semantic validation visible as tables and witness files, not only as passing tests.

# Files

```text
validation_matrix.csv
validation_matrix.md
negative_detection_matrix.csv
negative_detection_matrix.md
encoding_table.md
aiger/
witnesses/
```

# Interpretation

These artifacts show that generated AIGER files are simulated externally with aigsim and compared against reference regex semantics.

This is testing-based external semantic validation, not a formal proof of compiler correctness.
