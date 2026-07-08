# Model checking counterexamples

Detailed file paths and raw SAT assignments are in the CSV.

| case_id | description | pattern | bound | comparison | model_checker_result | expected_model_checker_result | verdict | decoded_witness_string |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MC001 | sanity check: correct AIGER compared with itself | ab\|bc | 2 | correct_vs_correct | UNSAT | UNSAT | PASS |  |
| MC002 | negative check: correct AIGER compared with output-forced-false corrupted AIGER | ab\|bc | 2 | correct_vs_corrupted_output_forced_false | SAT | SAT | PASS | 'ab' |
