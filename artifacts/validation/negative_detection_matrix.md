# Negative Detection Matrix

These cases use deliberately corrupted AIGER circuits as negative controls.
Each corrupted circuit is derived from a correct generated AIGER by applying one of the following modifications:

| corruption_type | Meaning |
| --- | --- |
| `output_forced_false` | The output literal is replaced by constant 0. The circuit always rejects. |
| `output_forced_true` | The output literal is replaced by constant 1. The circuit always accepts. |
| `output_inverted` | The output literal is bit-flipped (XOR 1). Accept and reject are swapped. |

The `witness_string` column shows the input used to expose the mismatch.
The `sanity_correct_aiger` column confirms the unmodified circuit still produces the expected result.
The `mismatch_detected` column shows that the corrupted circuit disagrees with the expected regex semantics, confirming the validation infrastructure can detect wrong behavior.

| case_id | pattern | backend | bound | corruption_type | witness_string | witness_trace | readable_witness_encoding | expected_regex_result | correct_aiger_output | corrupted_aiger_output | sanity_correct_aiger | mismatch_detected | correct_aiger_file | corrupted_aiger_file | stimulus_file |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N001 | ab\|bc | bounded | 2 | output_forced_false | 'ab' | 11100 | len_is_2=1, x_0_is_a=1, x_1_is_b=1, x_0_is_b=0, x_1_is_c=0 | 1 | 1 | 0 | PASS | YES | artifacts/validation/aiger/N001_bounded_correct.aag | artifacts/validation/aiger/N001_bounded_output_forced_false.aag | artifacts/validation/witnesses/N001_bounded_ab.stim |
| N002 | ab\|bc | bounded | 2 | output_forced_true | 'aa' | 11000 | len_is_2=1, x_0_is_a=1, x_1_is_b=0, x_0_is_b=0, x_1_is_c=0 | 0 | 0 | 1 | PASS | YES | artifacts/validation/aiger/N002_bounded_correct.aag | artifacts/validation/aiger/N002_bounded_output_forced_true.aag | artifacts/validation/witnesses/N002_bounded_aa.stim |
| N003 | ab\|bc | bounded | 2 | output_inverted | 'bc' | 10011 | len_is_2=1, x_0_is_a=0, x_1_is_b=0, x_0_is_b=1, x_1_is_c=1 | 1 | 1 | 0 | PASS | YES | artifacts/validation/aiger/N003_bounded_correct.aag | artifacts/validation/aiger/N003_bounded_output_inverted.aag | artifacts/validation/witnesses/N003_bounded_bc.stim |
| N004 | (bc)* | sequential |  | output_forced_false | 'bc' | 010 / 001 / 100 | step 0: char='b', vector=010, end=0, is_b=1, is_c=0 / step 1: char='c', vector=001, end=0, is_b=0, is_c=1 / step 2: end, vector=100, end=1, is_b=0, is_c=0 | 1 | 1 | 0 | PASS | YES | artifacts/validation/aiger/N004_sequential_correct.aag | artifacts/validation/aiger/N004_sequential_output_forced_false.aag | artifacts/validation/witnesses/N004_sequential_bc.stim |
| N005 | (bc)* | sequential |  | output_forced_true | 'b' | 010 / 100 | step 0: char='b', vector=010, end=0, is_b=1, is_c=0 / step 1: end, vector=100, end=1, is_b=0, is_c=0 | 0 | 0 | 1 | PASS | YES | artifacts/validation/aiger/N005_sequential_correct.aag | artifacts/validation/aiger/N005_sequential_output_forced_true.aag | artifacts/validation/witnesses/N005_sequential_b.stim |
| N006 | (bc)* | sequential |  | output_inverted | 'bcbc' | 010 / 001 / 010 / 001 / 100 | step 0: char='b', vector=010, end=0, is_b=1, is_c=0 / step 1: char='c', vector=001, end=0, is_b=0, is_c=1 / step 2: char='b', vector=010, end=0, is_b=1, is_c=0 / step 3: char='c', vector=001, end=0, is_b=0, is_c=1 / step 4: end, vector=100, end=1, is_b=0, is_c=0 | 1 | 1 | 0 | PASS | YES | artifacts/validation/aiger/N006_sequential_correct.aag | artifacts/validation/aiger/N006_sequential_output_inverted.aag | artifacts/validation/witnesses/N006_sequential_bcbc.stim |
