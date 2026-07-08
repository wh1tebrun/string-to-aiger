# Validation Matrix

Detailed encoding vectors and file paths are in the CSV.

| case_id | pattern | backend | intersection_strategy | bound | candidate_string | expected_regex_result | aigsim_output | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B001 | ab\|bc | bounded | structural | 2 | 'ab' | 1 | 1 | PASS |
| B001 | ab\|bc | bounded | structural | 2 | 'bc' | 1 | 1 | PASS |
| B001 | ab\|bc | bounded | structural | 2 | '' | 0 | 0 | PASS |
| B001 | ab\|bc | bounded | structural | 2 | 'a' | 0 | 0 | PASS |
| B001 | ab\|bc | bounded | structural | 2 | 'b' | 0 | 0 | PASS |
| B001 | ab\|bc | bounded | structural | 2 | 'aa' | 0 | 0 | PASS |
| B001 | ab\|bc | bounded | structural | 2 | 'ba' | 0 | 0 | PASS |
| B001 | ab\|bc | bounded | structural | 2 | 'abc' | 0 | 0 | PASS |
| B002 | (bc)* | bounded | structural | 4 | '' | 1 | 1 | PASS |
| B002 | (bc)* | bounded | structural | 4 | 'bc' | 1 | 1 | PASS |
| B002 | (bc)* | bounded | structural | 4 | 'bcbc' | 1 | 1 | PASS |
| B002 | (bc)* | bounded | structural | 4 | 'b' | 0 | 0 | PASS |
| B002 | (bc)* | bounded | structural | 4 | 'c' | 0 | 0 | PASS |
| B002 | (bc)* | bounded | structural | 4 | 'bcb' | 0 | 0 | PASS |
| B002 | (bc)* | bounded | structural | 4 | 'bcbcbc' | 0 | 0 | PASS |
| B003 | (a\|b)*&a* | bounded | structural | 4 | '' | 1 | 1 | PASS |
| B003 | (a\|b)*&a* | bounded | structural | 4 | 'a' | 1 | 1 | PASS |
| B003 | (a\|b)*&a* | bounded | structural | 4 | 'aa' | 1 | 1 | PASS |
| B003 | (a\|b)*&a* | bounded | structural | 4 | 'aaaa' | 1 | 1 | PASS |
| B003 | (a\|b)*&a* | bounded | structural | 4 | 'b' | 0 | 0 | PASS |
| B003 | (a\|b)*&a* | bounded | structural | 4 | 'ab' | 0 | 0 | PASS |
| B003 | (a\|b)*&a* | bounded | structural | 4 | 'ba' | 0 | 0 | PASS |
| B003 | (a\|b)*&a* | bounded | structural | 4 | 'aaaaa' | 0 | 0 | PASS |
| S001 | ab\|bc | sequential | structural |  | 'ab' | 1 | 1 | PASS |
| S001 | ab\|bc | sequential | structural |  | 'bc' | 1 | 1 | PASS |
| S001 | ab\|bc | sequential | structural |  | '' | 0 | 0 | PASS |
| S001 | ab\|bc | sequential | structural |  | 'a' | 0 | 0 | PASS |
| S001 | ab\|bc | sequential | structural |  | 'b' | 0 | 0 | PASS |
| S001 | ab\|bc | sequential | structural |  | 'aa' | 0 | 0 | PASS |
| S001 | ab\|bc | sequential | structural |  | 'ba' | 0 | 0 | PASS |
| S001 | ab\|bc | sequential | structural |  | 'abc' | 0 | 0 | PASS |
| S002 | (bc)* | sequential | structural |  | '' | 1 | 1 | PASS |
| S002 | (bc)* | sequential | structural |  | 'bc' | 1 | 1 | PASS |
| S002 | (bc)* | sequential | structural |  | 'bcbc' | 1 | 1 | PASS |
| S002 | (bc)* | sequential | structural |  | 'bcbcbc' | 1 | 1 | PASS |
| S002 | (bc)* | sequential | structural |  | 'b' | 0 | 0 | PASS |
| S002 | (bc)* | sequential | structural |  | 'c' | 0 | 0 | PASS |
| S002 | (bc)* | sequential | structural |  | 'bcb' | 0 | 0 | PASS |
| S003 | (a\|b)*&a* | sequential | structural |  | '' | 1 | 1 | PASS |
| S003 | (a\|b)*&a* | sequential | structural |  | 'a' | 1 | 1 | PASS |
| S003 | (a\|b)*&a* | sequential | structural |  | 'aa' | 1 | 1 | PASS |
| S003 | (a\|b)*&a* | sequential | structural |  | 'aaaaaa' | 1 | 1 | PASS |
| S003 | (a\|b)*&a* | sequential | structural |  | 'b' | 0 | 0 | PASS |
| S003 | (a\|b)*&a* | sequential | structural |  | 'ab' | 0 | 0 | PASS |
| S003 | (a\|b)*&a* | sequential | structural |  | 'ba' | 0 | 0 | PASS |
