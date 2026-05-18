# Language behavior validation

This evaluation compares manually specified expected results against bounded and sequential backends using both structural and product intersection strategies.

| pattern | bound | word | expected | bounded_structural | bounded_product | sequential_structural | sequential_product | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a* | 3 | ε | True | True | True | True | True | OK |
| a* | 3 | a | True | True | True | True | True | OK |
| a* | 3 | aa | True | True | True | True | True | OK |
| a* | 3 | aaa | True | True | True | True | True | OK |
| a* | 3 | b | False | False | False | False | False | OK |
| a* | 3 | ab | False | False | False | False | False | OK |
| a* | 3 | ba | False | False | False | False | False | OK |
| (ab)* | 6 | ε | True | True | True | True | True | OK |
| (ab)* | 6 | ab | True | True | True | True | True | OK |
| (ab)* | 6 | abab | True | True | True | True | True | OK |
| (ab)* | 6 | ababab | True | True | True | True | True | OK |
| (ab)* | 6 | a | False | False | False | False | False | OK |
| (ab)* | 6 | b | False | False | False | False | False | OK |
| (ab)* | 6 | aba | False | False | False | False | False | OK |
| (ab)* | 6 | abb | False | False | False | False | False | OK |
| (a\|b)* | 4 | ε | True | True | True | True | True | OK |
| (a\|b)* | 4 | a | True | True | True | True | True | OK |
| (a\|b)* | 4 | b | True | True | True | True | True | OK |
| (a\|b)* | 4 | ab | True | True | True | True | True | OK |
| (a\|b)* | 4 | ba | True | True | True | True | True | OK |
| (a\|b)* | 4 | abba | True | True | True | True | True | OK |
| (a\|b)* | 4 | abc | False | False | False | False | False | OK |
| (a\|ba)* | 5 | ε | True | True | True | True | True | OK |
| (a\|ba)* | 5 | a | True | True | True | True | True | OK |
| (a\|ba)* | 5 | ba | True | True | True | True | True | OK |
| (a\|ba)* | 5 | aba | True | True | True | True | True | OK |
| (a\|ba)* | 5 | baa | True | True | True | True | True | OK |
| (a\|ba)* | 5 | ababa | True | True | True | True | True | OK |
| (a\|ba)* | 5 | b | False | False | False | False | False | OK |
| (a\|ba)* | 5 | bb | False | False | False | False | False | OK |
| (a\|b)*&a* | 4 | ε | True | True | True | True | True | OK |
| (a\|b)*&a* | 4 | a | True | True | True | True | True | OK |
| (a\|b)*&a* | 4 | aa | True | True | True | True | True | OK |
| (a\|b)*&a* | 4 | aaa | True | True | True | True | True | OK |
| (a\|b)*&a* | 4 | aaaa | True | True | True | True | True | OK |
| (a\|b)*&a* | 4 | b | False | False | False | False | False | OK |
| (a\|b)*&a* | 4 | ab | False | False | False | False | False | OK |
| (a\|b)*&a* | 4 | ba | False | False | False | False | False | OK |
| (ab)*&(a\|b)* | 6 | ε | True | True | True | True | True | OK |
| (ab)*&(a\|b)* | 6 | ab | True | True | True | True | True | OK |
| (ab)*&(a\|b)* | 6 | abab | True | True | True | True | True | OK |
| (ab)*&(a\|b)* | 6 | ababab | True | True | True | True | True | OK |
| (ab)*&(a\|b)* | 6 | a | False | False | False | False | False | OK |
| (ab)*&(a\|b)* | 6 | b | False | False | False | False | False | OK |
| (ab)*&(a\|b)* | 6 | aba | False | False | False | False | False | OK |
| (ab)*&(a\|b)* | 6 | abb | False | False | False | False | False | OK |
| a*&b* | 4 | ε | True | True | True | True | True | OK |
| a*&b* | 4 | a | False | False | False | False | False | OK |
| a*&b* | 4 | aa | False | False | False | False | False | OK |
| a*&b* | 4 | b | False | False | False | False | False | OK |
| a*&b* | 4 | bb | False | False | False | False | False | OK |
| a*&b* | 4 | ab | False | False | False | False | False | OK |
| a*&b* | 4 | ba | False | False | False | False | False | OK |
| a{1,3} | 3 | a | True | True | True | True | True | OK |
| a{1,3} | 3 | aa | True | True | True | True | True | OK |
| a{1,3} | 3 | aaa | True | True | True | True | True | OK |
| a{1,3} | 3 | ε | False | False | False | False | False | OK |
| a{1,3} | 3 | aaaa | False | False | False | False | False | OK |
| a{1,3} | 3 | b | False | False | False | False | False | OK |
| [ab]{2,} | 4 | aa | True | True | True | True | True | OK |
| [ab]{2,} | 4 | ab | True | True | True | True | True | OK |
| [ab]{2,} | 4 | ba | True | True | True | True | True | OK |
| [ab]{2,} | 4 | bb | True | True | True | True | True | OK |
| [ab]{2,} | 4 | abba | True | True | True | True | True | OK |
| [ab]{2,} | 4 | ε | False | False | False | False | False | OK |
| [ab]{2,} | 4 | a | False | False | False | False | False | OK |
| [ab]{2,} | 4 | ac | False | False | False | False | False | OK |

## Notes

- `expected` is the manually specified expected language result.
- `bounded_structural` uses the bounded backend with structural intersection encoding.
- `bounded_product` uses the bounded backend with explicit product automata for intersection.
- `sequential_structural` uses the sequential backend with parallel circuit composition.
- `sequential_product` uses the sequential backend with explicit product automata for intersection.
- `OK` means that all evaluated backend/strategy combinations agree with the expected result.
- The selected positive examples are within the configured bound.
