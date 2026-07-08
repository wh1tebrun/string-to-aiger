# Sequential model-checking counterexamples

Detailed file paths and raw SAT assignments are in the CSV.

| case_id | description | pattern | depth | comparison | model_checker_result | expected_model_checker_result | verdict | decoded_witness_string | readable_witness_trace |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SQMC001 | sanity check: sequential correct AIGER compared with itself | (bc)* | 3 | correct_vs_correct | UNSAT | UNSAT | PASS |  |  |
| SQMC002 | negative check: sequential correct AIGER compared with output-forced-false corrupted AIGER | (bc)* | 3 | correct_vs_corrupted_output_forced_false | SAT | SAT | PASS | 'bc' | step 0: char='b', end=0, is_b=1 / step 1: char='c', is_c=1 / step 2: end, end=1 |
