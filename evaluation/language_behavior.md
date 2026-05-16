# Language behavior validation

| pattern | bound | word | expected | bounded | sequential | status |
| --- | --- | --- | --- | --- | --- | --- |
| a* | 3 | ε | True | True | True | OK |
| a* | 3 | a | True | True | True | OK |
| a* | 3 | aa | True | True | True | OK |
| a* | 3 | aaa | True | True | True | OK |
| a* | 3 | b | False | False | False | OK |
| a* | 3 | ab | False | False | False | OK |
| a* | 3 | ba | False | False | False | OK |
| (ab)* | 6 | ε | True | True | True | OK |
| (ab)* | 6 | ab | True | True | True | OK |
| (ab)* | 6 | abab | True | True | True | OK |
| (ab)* | 6 | ababab | True | True | True | OK |
| (ab)* | 6 | a | False | False | False | OK |
| (ab)* | 6 | b | False | False | False | OK |
| (ab)* | 6 | aba | False | False | False | OK |
| (ab)* | 6 | abb | False | False | False | OK |
| (a\|b)* | 4 | ε | True | True | True | OK |
| (a\|b)* | 4 | a | True | True | True | OK |
| (a\|b)* | 4 | b | True | True | True | OK |
| (a\|b)* | 4 | ab | True | True | True | OK |
| (a\|b)* | 4 | ba | True | True | True | OK |
| (a\|b)* | 4 | abba | True | True | True | OK |
| (a\|b)* | 4 | abc | False | False | False | OK |
| (a\|ba)* | 5 | ε | True | True | True | OK |
| (a\|ba)* | 5 | a | True | True | True | OK |
| (a\|ba)* | 5 | ba | True | True | True | OK |
| (a\|ba)* | 5 | aba | True | True | True | OK |
| (a\|ba)* | 5 | baa | True | True | True | OK |
| (a\|ba)* | 5 | ababa | True | True | True | OK |
| (a\|ba)* | 5 | b | False | False | False | OK |
| (a\|ba)* | 5 | bb | False | False | False | OK |
| (a\|b)*&a* | 4 | ε | True | True | True | OK |
| (a\|b)*&a* | 4 | a | True | True | True | OK |
| (a\|b)*&a* | 4 | aa | True | True | True | OK |
| (a\|b)*&a* | 4 | aaa | True | True | True | OK |
| (a\|b)*&a* | 4 | aaaa | True | True | True | OK |
| (a\|b)*&a* | 4 | b | False | False | False | OK |
| (a\|b)*&a* | 4 | ab | False | False | False | OK |
| (a\|b)*&a* | 4 | ba | False | False | False | OK |
| (ab)*&(a\|b)* | 6 | ε | True | True | True | OK |
| (ab)*&(a\|b)* | 6 | ab | True | True | True | OK |
| (ab)*&(a\|b)* | 6 | abab | True | True | True | OK |
| (ab)*&(a\|b)* | 6 | ababab | True | True | True | OK |
| (ab)*&(a\|b)* | 6 | a | False | False | False | OK |
| (ab)*&(a\|b)* | 6 | b | False | False | False | OK |
| (ab)*&(a\|b)* | 6 | aba | False | False | False | OK |
| (ab)*&(a\|b)* | 6 | abb | False | False | False | OK |
| a*&b* | 4 | ε | True | True | True | OK |
| a*&b* | 4 | a | False | False | False | OK |
| a*&b* | 4 | aa | False | False | False | OK |
| a*&b* | 4 | b | False | False | False | OK |
| a*&b* | 4 | bb | False | False | False | OK |
| a*&b* | 4 | ab | False | False | False | OK |
| a*&b* | 4 | ba | False | False | False | OK |

## Notes

- `expected` is the manually specified expected language result.
- `bounded` is the result of the bounded combinational encoding.
- `sequential` is the result of the sequential latch-based encoding.
- `OK` means that both backends agree with the expected result.
- The selected positive examples are within the configured bound.
