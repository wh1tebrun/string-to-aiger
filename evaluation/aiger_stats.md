# AIGER statistics comparison

| pattern | backend | bound | M | I | L | O | A | size(bytes) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a* | bounded | 3 | 16 | 7 | 0 | 1 | 9 | 234 |
| a* | sequential | - | 10 | 2 | 4 | 1 | 4 | 200 |
| (ab)* | bounded | 6 | 25 | 10 | 0 | 1 | 15 | 333 |
| (ab)* | sequential | - | 15 | 3 | 6 | 1 | 6 | 266 |
| (a|b)* | bounded | 4 | 69 | 13 | 0 | 1 | 56 | 766 |
| (a|b)* | sequential | - | 29 | 3 | 8 | 1 | 18 | 406 |
| (a|ba)* | bounded | 5 | 74 | 15 | 0 | 1 | 59 | 853 |
| (a|ba)* | sequential | - | 33 | 3 | 10 | 1 | 20 | 461 |
| (a|b)*&a* | bounded | 4 | 84 | 13 | 0 | 1 | 71 | 926 |
| (a|b)*&a* | sequential | - | 38 | 3 | 12 | 1 | 23 | 589 |
| (ab)*&(a|b)* | bounded | 6 | 281 | 19 | 0 | 1 | 262 | 3092 |
| (ab)*&(a|b)* | sequential | - | 42 | 3 | 14 | 1 | 25 | 659 |
| a*&b* | bounded | 4 | 42 | 13 | 0 | 1 | 29 | 506 |
| a*&b* | sequential | - | 20 | 3 | 8 | 1 | 9 | 372 |

## Notes

- `M` is the maximum variable index in the AIGER header.
- `I` is the number of inputs.
- `L` is the number of latches.
- `O` is the number of outputs.
- `A` is the number of AND gates.
- Bounded encodings are combinational and therefore have `L = 0`.
- Sequential encodings use latches and therefore have `L > 0`.
