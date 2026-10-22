# Lab 5 Static Code Analysis - Student Grade System

## Repository links

Forked repository URL: [https://github.com/gnprajwal/L5_42_student_grade_system](https://github.com/gnprajwal/L5_42_student_grade_system)

Original course repository: [https://github.com/SETAPESU26/L5_42_student_grade_system](https://github.com/SETAPESU26/L5_42_student_grade_system)

The fork URL above was supplied for this submission. This package contains local
deliverables; it does not confirm that they have been committed or pushed to GitHub.

## Submission files

1. [Issues document](output/pdf/issues_report.pdf), with an editable copy in [issues.md](issues.md).
2. Before reports in [reports/before](reports/before) and after reports in [reports/after](reports/after).
   Each folder contains `pylint_report.txt`, `bandit_report.txt`, and `flake8_report.txt`.
3. This README, containing the forked repository URL.

Supporting files are the cleaned [student_grade_system.py](student_grade_system.py),
the unmodified [original source](original/student_grade_system.py), and the
[regression tests](test_student_grade_system.py).

## Verified results

Analysis date: 22 October 2026. Python 3.13.5 on Windows.

| Tool | Before | After |
| --- | --- | --- |
| Pylint 4.1.3 | 5.51/10; 22 messages | 10.00/10; 0 messages |
| Bandit 1.9.4 | 6 findings (2 high, 1 medium, 3 low) | 0 findings |
| Flake8 7.4.1 | 8 findings | 0 findings |

All 10 regression tests passed. All three final analyzer commands exited with code 0.
The reports are captured tool output, with no suppression comments or disabled checks.

## Reproduce the analysis

Create a virtual environment and install the recorded analyzer versions:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Capture reports from the preserved original and the cleaned source:

```powershell
.venv\Scripts\python.exe tools/collect_reports.py before
.venv\Scripts\python.exe tools/collect_reports.py after
```

The report collector runs these commands for each source path:

```text
python -m pylint --persistent=n <source>
python -m bandit -r <source> -f txt
python -m flake8 --isolated --statistics --count <source>
```

Pylint persistence is disabled to avoid cached-score comparisons. Flake8 ignores
external configuration so its standard checks are used. Its clean report contains
`0` because `--count` is enabled. `--statistics` provides the before counts by code.

Each stage includes a `manifest.json` recording commands, versions, timestamp,
source SHA-256 hash, and exit status. Tool stderr is preserved separately. Nonzero
before exit codes indicate findings: Pylint 28, Bandit 1, and Flake8 1.

Run the program and checks:

```powershell
.venv\Scripts\python.exe student_grade_system.py
.venv\Scripts\python.exe -m unittest -v test_student_grade_system
```

The program prints a passing result and GPA `4.35`, then exports `grade_sheet.txt`.
The PIN varies on each run. Set `GRADE_PORTAL_TOKEN` externally if needed; the
program displays only whether it is configured.

## Changes to the interface

- `addGrade` is renamed to `add_grade`.
- `compute_weighted_gpa(student_id, scale=20.0)` accepts a positive finite numeric
  divisor. Arbitrary Python expression strings are no longer accepted. All marks
  retain equal weights, matching the original demo calculation.
- Empty-score GPA calculations raise `ValueError`; unknown student GPA lookups
  raise `KeyError`. Boolean operations return `False` for missing students.
- Marks must be numeric values from 0 to 100. Attendance additions must be whole,
  nonnegative points and cannot take the recorded attendance above 100.
- Identifier digests use SHA-256. Importing the module no longer runs the demo.

## Evidence scope

The required tool reports cover `student_grade_system.py`, not the support scripts
or regression suite. Clean reports are evidence of these checks, not a guarantee
of complete application security. The source snapshot and its hash make each
before/after result traceable.

This directory arrived without Git history. No commits or pushes were made as
part of preparing these three local submission deliverables.
