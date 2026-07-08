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

Detailed encoding vectors and file paths are in the CSV.

| case_id | pattern | backend | bound | corruption_type | witness_string | expected_regex_result | correct_aiger_output | corrupted_aiger_output | sanity_correct_aiger | mismatch_detected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N001 | ab\|bc | bounded | 2 | output_forced_false | 'ab' | 1 | 1 | 0 | PASS | YES |
| N002 | ab\|bc | bounded | 2 | output_forced_true | 'aa' | 0 | 0 | 1 | PASS | YES |
| N003 | ab\|bc | bounded | 2 | output_inverted | 'bc' | 1 | 1 | 0 | PASS | YES |
| N004 | (bc)* | sequential |  | output_forced_false | 'bc' | 1 | 1 | 0 | PASS | YES |
| N005 | (bc)* | sequential |  | output_forced_true | 'b' | 0 | 0 | 1 | PASS | YES |
| N006 | (bc)* | sequential |  | output_inverted | 'bcbc' | 1 | 1 | 0 | PASS | YES |
