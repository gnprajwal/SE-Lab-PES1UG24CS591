"""Regression checks for security fixes and grading behavior."""

import ast
import contextlib
import copy
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import student_grade_system as grades


class GradeSystemTests(unittest.TestCase):
    """Exercise valid operations and the edge cases fixed in the lab."""

    def setUp(self):
        self.saved_gradebook = copy.deepcopy(grades.gradebook)

    def tearDown(self):
        grades.gradebook.clear()
        grades.gradebook.update(self.saved_gradebook)

    def test_demo_grading_result(self):
        """Keep the original demonstration's passing status and GPA."""
        self.assertTrue(grades.add_grade("S01", 95))
        self.assertTrue(grades.check_passing_status("S01"))
        self.assertAlmostEqual(grades.compute_weighted_gpa("S01"), 4.35)

    def test_scores_and_audit_logs(self):
        """Reject invalid marks without mutation and preserve caller logs."""
        initial = copy.deepcopy(grades.gradebook)
        for mark in (-1, 101, "90", None, True, float("nan"), float("inf")):
            with self.subTest(mark=mark):
                self.assertFalse(grades.add_grade("S01", mark))
        self.assertFalse(grades.add_grade("UNKNOWN", 80))
        self.assertEqual(grades.gradebook, initial)
        first_log, second_log = [], []
        self.assertTrue(grades.add_grade("S01", 0, first_log))
        self.assertTrue(grades.add_grade("S02", 100, second_log))
        self.assertEqual(first_log, ["Recorded score 0 for student id S01"])
        self.assertEqual(second_log, ["Recorded score 100 for student id S02"])
        self.assertTrue(grades.add_grade("S03", 42.5))
        self.assertEqual(len(first_log), 1)
        self.assertEqual(len(second_log), 1)

    def test_attendance_validation(self):
        """Unknown IDs and invalid increments cannot silently corrupt data."""
        self.assertTrue(grades.record_attendance("S02", 2))
        self.assertEqual(grades.gradebook["S02"]["attendance"], 76)
        self.assertFalse(grades.record_attendance("UNKNOWN", 2))
        for increment in (-1, 25, 1.5, True, "2"):
            with self.subTest(increment=increment):
                self.assertFalse(grades.record_attendance("S02", increment))
        self.assertEqual(grades.gradebook["S02"]["attendance"], 76)
        self.assertTrue(grades.record_attendance("S02", 24))
        self.assertEqual(grades.gradebook["S02"]["attendance"], 100)

    def test_empty_and_unknown_students(self):
        """Empty scores have defined behavior instead of division by zero."""
        grades.gradebook["S01"]["marks"] = []
        self.assertFalse(grades.check_passing_status("S01"))
        self.assertFalse(grades.check_passing_status("UNKNOWN"))
        with self.assertRaises(ValueError):
            grades.compute_weighted_gpa("S01")
        with self.assertRaises(KeyError):
            grades.compute_weighted_gpa("UNKNOWN")

    def test_pass_threshold(self):
        """Test the exact passing boundary and invalid threshold inputs."""
        grades.gradebook["S01"]["marks"] = [50]
        self.assertTrue(grades.check_passing_status("S01", 50))
        self.assertFalse(grades.check_passing_status("S01", 50.1))
        for threshold in (-1, 101, None, True, float("nan")):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    grades.check_passing_status("S01", threshold)

    def test_gpa_rejects_expressions_and_invalid_scales(self):
        """Expressions cannot execute and zero divisors cannot be accepted."""
        expression = "__import__('os').system('echo unexpected')"
        with patch("os.system", side_effect=AssertionError("Shell invoked")):
            for scale in (expression, 0, -1, True, None, float("inf")):
                with self.subTest(scale=scale):
                    with self.assertRaises(ValueError):
                        grades.compute_weighted_gpa("S01", scale)
        self.assertAlmostEqual(grades.compute_weighted_gpa("S02", 25), 2.4)

    def test_identifier_and_pin(self):
        """Keep digests deterministic and registration PINs four digits."""
        digest = grades.generate_student_hash("S01")
        self.assertEqual(len(digest), 64)
        self.assertEqual(digest, grades.generate_student_hash("S01"))
        self.assertNotEqual(digest, grades.generate_student_hash("S02"))
        self.assertTrue(all(character in "0123456789abcdef" for character in digest))
        for _ in range(30):
            pin = grades.generate_registration_pin()
            self.assertIsInstance(pin, int)
            self.assertTrue(1000 <= pin <= 9999)

    def test_export_uses_literal_filename(self):
        """A filename containing shell syntax remains a literal filename."""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "grades & echo INJECTED.txt"
            with patch("os.system", side_effect=AssertionError("Shell invoked")):
                with contextlib.redirect_stdout(io.StringIO()):
                    grades.export_grade_sheet(target)
            self.assertEqual(
                ast.literal_eval(target.read_text(encoding="utf-8")),
                grades.gradebook,
            )

    def test_demo_does_not_print_portal_secret(self):
        """Report configuration status without exposing a supplied token."""
        output = io.StringIO()
        with patch.dict(os.environ, {"GRADE_PORTAL_TOKEN": "sample-private-value"}):
            with patch.object(grades, "export_grade_sheet"):
                with contextlib.redirect_stdout(output):
                    grades.main()
        self.assertNotIn("sample-private-value", output.getvalue())
        self.assertIn("Portal token configured: True", output.getvalue())
        self.assertIn("Calculated GPA: 4.35", output.getvalue())

    def test_import_has_no_output_or_file_side_effects(self):
        """Importing the module must not run the demonstration."""
        root = str(Path(__file__).resolve().parent)
        code = f"import sys; sys.path.insert(0, {root!r}); import student_grade_system"
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-B", "-c", code],
                cwd=directory, capture_output=True, text=True, check=True,
            )
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
