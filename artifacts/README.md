# Validation and Model-Checking Artifacts

This is the authoritative index for committed validation evidence. The artifacts make generated AIGER circuits externally inspectable through concrete simulation, negative controls, constrained SAT checks, bounded sequential unrolling, and comparison with independent reference circuits.

## Provenance and Scope

The [committed artifact data](https://github.com/wh1tebrun/string-to-aiger/tree/presentation-release-2026-08-06/artifacts) indexed here is frozen by the annotated tag [`presentation-release-2026-08-06`](https://github.com/wh1tebrun/string-to-aiger/tree/presentation-release-2026-08-06), targeting commit [`f77c909cd8359a87bc81c0f89aaa813e89abf279`](https://github.com/wh1tebrun/string-to-aiger/commit/f77c909cd8359a87bc81c0f89aaa813e89abf279). That final release includes explicit LF output writing, fail-closed manual-simulation evidence, and test/CI infrastructure, and it passed the completed full release gate with 288 test functions in 29 scripts and the 245-function, 22-script internal profile. Subsequent changes do not alter this immutable tagged snapshot.

The earlier annotated tag [`presentation-validation-aa072d8`](https://github.com/wh1tebrun/string-to-aiger/tree/presentation-validation-aa072d8), targeting commit [`aa072d804572c128f4e905b052fb0c2184bd7b0e`](https://github.com/wh1tebrun/string-to-aiger/commit/aa072d804572c128f4e905b052fb0c2184bd7b0e), remains the historical pre-professionalization validated baseline.

The final-release artifact snapshot contains 45 semantic-simulation rows, six negative-detection rows, two bounded miter/Minisat rows, two fixed-depth sequential-unroll/Minisat rows, four generated-vs-reference rows, and nine manual rows. These are concrete or bounded checks. They do not establish universal correctness of the executable compiler.

## Evidence Index

| Directory | Generator | Artifact and question answered | Interpretation and limitation |
| --- | --- | --- | --- |
| [`validation/`](validation/) | [`generate_validation_artifacts.py`](../validation/generate_validation_artifacts.py) | AIGERs, stimuli, and matrices for 45 external `aigsim` comparisons plus six deliberately corrupted negative controls. Do generated artifacts agree with reference regex semantics on the recorded inputs, and can the harness detect wrong circuits? | External simulation/differential testing and negative-control evidence for selected cases; not exhaustive language equivalence. |
| [`manual_aigsim_checks/`](manual_aigsim_checks/) | [`generate_manual_aigsim_checks.py`](../validation/generate_manual_aigsim_checks.py) | Nine small AIGER/stimulus/output rows. Can a reviewer inspect representative bounded and sequential behavior, including two corrupted controls? | Fail-closed external simulation: all stimuli end with exactly one final `.` line and LF. Seven ordinary cases match expected semantics; two deliberately corrupted controls cleanly report `MISMATCH DETECTED`. Every case must exit 0 with empty stderr and well-formed output, and a negative control passes only after clean simulator execution. |
| [`model_checking/`](model_checking/) | [`generate_model_checking_artifacts.py`](../validation/generate_model_checking_artifacts.py) | Two bounded `aigmiter`/`aigtocnf`/Minisat cases with valid-input clauses. Does a correct circuit differ from itself, and can a corrupted circuit yield a decoded witness? | SAT-based bounded instance evidence: correct-vs-correct is UNSAT; correct-vs-corrupted is SAT with witness `ab`. It covers only the encoded bound and constraints. |
| [`sequential_model_checking/`](sequential_model_checking/) | [`generate_sequential_model_checking_artifacts.py`](../validation/generate_sequential_model_checking_artifacts.py) | Two depth-3 `aigmiter`/`aigunroll`/CNF/Minisat cases for `(bc)*`. Can a bounded trace expose a corrupted sequential output? | Bounded sequential counterexample extraction: the corrupted comparison is SAT with trace `b, c, end`. It is not unbounded sequential correctness. |
| [`reference_equivalence/`](reference_equivalence/) | [`generate_bounded_reference_equivalence_artifacts.py`](../validation/generate_bounded_reference_equivalence_artifacts.py) | Four generated-vs-independent-reference miters over valid bound-2 encodings. Is any valid bounded string a counterexample? | Constrained bounded equivalence evidence. Selected correct cases are UNSAT; a corrupted case is SAT with witness `ab`. The reference is an explicit accepted-word circuit, not the regex compiler. |

The canonical rIC3 workflow is separate from these committed directories. [`run_ric3_hwmcc.sh`](../validation/run_ric3_hwmcc.sh) generates four sequential models and raw/result files under ignored `outputs/`. At the tagged baseline it produced `SAT, UNSAT, SAT, UNSAT`; those results mean `accept` is reachable or unreachable in those four transition systems, not that the compiler is universally correct.

The separate [Isabelle/HOL project](https://gitlab.uni-freiburg.de/et130/regex-to-nfa-isabelle.git) supplies mathematical proof for the five-constructor Thompson core. It is not an artifact generator or a refinement proof of this Python implementation.

## Reproducing the Committed Artifact Families

After installing the package as shown in the root quickstart, run generators from the repository root under the documented Bash/WSL toolchain. `AIGER_TOOLS` must contain `aigmiter`, `aigtocnf`, and `aigunroll`; `minisat` must be on `PATH`; and `AIGSIM` must name the simulator executable.

```bash
export AIGER_TOOLS=/path/to/aiger
export AIGSIM=/path/to/aiger/aigsim
python3 validation/run_all_validation_artifacts.py
```

The aggregate runner executes these generators in order and rewrites the corresponding tracked artifact families:

```bash
python3 validation/generate_validation_artifacts.py
python3 validation/generate_model_checking_artifacts.py
python3 validation/generate_sequential_model_checking_artifacts.py
python3 validation/generate_bounded_reference_equivalence_artifacts.py
python3 validation/generate_manual_aigsim_checks.py
```

The optional canonical rIC3 workflow uses `RIC3_IMAGE` when set, otherwise `gipsyh/ric3:1.6`:

```bash
bash validation/run_ric3_hwmcc.sh
```

The CLI also supports the separate optional `STRING_TO_AIGER_EXTERNAL_AIGER_VALIDATOR` command. That hook checks whether a configured external command accepts a written file; it is not the semantic `AIGSIM` test suite.

## Validated Environment

These values are the environment recorded for the tagged validation baseline, not general minimum requirements except where stated.

| Component | Recorded identity | Qualification |
| --- | --- | --- |
| Python requirement | 3.10 or newer | Declared by `pyproject.toml`; the package has no declared runtime dependencies. |
| Windows Python | 3.14.2 | Recorded host interpreter; the full external gate was not claimed as native-Windows-only. |
| WSL Ubuntu Python | 3.10.12 | Interpreter used for the recorded external validation workflow. |
| `aigsim` | `/home/egetekin/tools/aiger/aigsim`; version not recorded | Machine-local validated executable path, not a portable pin. |
| AIGER tools | `/home/egetekin/tools/aiger/`; version not recorded | Recorded location for `aigmiter`, `aigtocnf`, and `aigunroll`. |
| Minisat | Ubuntu package `1:2.2.1-5build2` | Used for constrained CNF checks. |
| Docker | client/server 29.6.1; Docker Desktop 4.82.0 | Docker Desktop supplied the validated container runtime. |
| rIC3 image tag | `gipsyh/ric3:1.6` | A tag is mutable and is not itself a content digest. |
| rIC3 local image ID | `sha256:1c2418ef3f727592e7b3bf3c08fad5b56ef09a98c55fcc2631cc1a66b64ef532` | Recorded local image identity; a registry repository digest was not recorded. |
| rIC3 binary | `rIC3 1.5.2` | Version reported by the binary inside that validated image. |

The image tag, local image ID, registry digest, and contained binary version are different identifiers. Future reruns should record the actual tool versions, image ID, and repository digest used rather than assuming the tag still denotes the validated image.

## Platform Boundary and Interpretation

Core Python compilation and structural validation do not require the external toolchain. The runner's `--internal-only` profile excludes real `aigsim` tests, but its manual fake-simulator regression uses Bash; the CI environment supplies Bash on Ubuntu. The recorded real `aigsim`, AIGER-tool, Minisat, and rIC3 workflows ran from the repository root under WSL Ubuntu/Bash, with Docker Desktop exposed to WSL for rIC3. Ordinary per-push CI intentionally does not run those real external tools, and full native-Windows support for those external workflows has not been established.

The central AIGER writer explicitly emits LF, and the manual artifact generator explicitly emits LF for simulator stimuli and text captures; representative bounded and sequential runtime AIGER outputs were byte-identical across native Windows and WSL. In addition, `.gitattributes` forces tracked `.sh`, `.aag`, and `.stim` files to LF so Windows checkouts preserve line-oriented tool inputs. This does not prove that every unrelated direct file writer has identical bytes on every platform.

Simulation covers supplied traces. SAT/UNSAT results cover the encoded bounds and constraints, except the four separate rIC3 reachability instances, which are unbounded only for their generated transition systems. Structural AIGER validation proves well-formedness checks, not semantic equivalence. See the root [formal-verification scope](../README.md#formal-verification-scope) for the exact boundary between implementation evidence and mathematical proof.
