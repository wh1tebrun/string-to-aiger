# Broken pipe-table regression fixture

The first table reproduces the original GFM defect class.

| pattern | result |
| --- | --- |
| `(ab|ba)*&(aa|bb)*` | `SAT` |

<!-- corrected companion -->

# Escaped pipe-table companion

| pattern | result |
| --- | --- |
| `(ab\|ba)*&(aa\|bb)*` | `SAT` |
