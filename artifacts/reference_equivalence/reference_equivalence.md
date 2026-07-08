# Bounded reference equivalence checks

Detailed file paths and raw SAT assignments are in the CSV.

| case_id | description | pattern | bound | accepted_words | comparison | model_checker_result | expected_model_checker_result | verdict | decoded_counterexample |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REFEQ001 | generated bounded AIGER compared with independent exact-word reference | ab\|bc | 2 | ['ab', 'bc'] | generated_vs_reference | UNSAT | UNSAT | PASS |  |
| REFEQ002 | negative check: output-forced-false generated AIGER compared with independent reference | ab\|bc | 2 | ['ab', 'bc'] | corrupted_generated_vs_reference | SAT | SAT | PASS | 'ab' |
| REFEQ003 | character-class pattern compared with independent exact-word reference | a[bc] | 2 | ['ab', 'ac'] | generated_vs_reference | UNSAT | UNSAT | PASS |  |
| REFEQ004 | union and concatenation pattern compared with independent exact-word reference | (a\|b)(a\|b) | 2 | ['aa', 'ab', 'ba', 'bb'] | generated_vs_reference | UNSAT | UNSAT | PASS |  |
