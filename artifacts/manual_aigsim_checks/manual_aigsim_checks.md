# Manual aigsim checks

Detailed file paths, commands, and captured output files are in the CSV.

| case_id | backend | pattern | word_or_trace | aigsim_exit_code | execution_valid | stderr_empty | expected_semantic_output | aigsim_actual_output | matches_expected_semantics | mismatch_detected | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MAN001 | bounded | ab\|bc | ab | 0 | YES | YES | 1 | 1 | YES | NO | OK |
| MAN002 | bounded | ab\|bc | ac | 0 | YES | YES | 0 | 0 | YES | NO | OK |
| MAN003 | bounded negative control | ab\|bc | ab | 0 | YES | YES | 1 | 0 | NO | YES | MISMATCH DETECTED |
| MAN004 | sequential | (bc)* | &lt;empty&gt; -&gt; end | 0 | YES | YES | 1 | 1 | YES | NO | OK |
| MAN005 | sequential | (bc)* | b, c, end | 0 | YES | YES | 1 | 1 | YES | NO | OK |
| MAN006 | sequential | (bc)* | b, c, b, c, end | 0 | YES | YES | 1 | 1 | YES | NO | OK |
| MAN007 | sequential | (bc)* | b, end | 0 | YES | YES | 0 | 0 | YES | NO | OK |
| MAN008 | sequential | (bc)* | b, c, b, end | 0 | YES | YES | 0 | 0 | YES | NO | OK |
| MAN009 | sequential negative control | (bc)* | b, c, end | 0 | YES | YES | 1 | 0 | NO | YES | MISMATCH DETECTED |
