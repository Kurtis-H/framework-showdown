"""Tests for the measuring scripts: the numbers in RESULTS.md are only as
good as these."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import measure  # noqa: E402
import report  # noqa: E402


def junit(*cases: tuple[str, str | None]) -> str:
    body = "".join(
        f'<testcase name="{name}">' + (f"<{outcome}/>" if outcome else "") + "</testcase>" for name, outcome in cases
    )
    return f'<testsuites><testsuite name="plan">{body}</testsuite></testsuites>'


class ParseJunit(unittest.TestCase):
    def files(self, *docs: str) -> list[Path]:
        tmp = Path(tempfile.mkdtemp())
        paths = []
        for i, doc in enumerate(docs):
            path = tmp / f"junit-{i}.xml"
            path.write_text(doc)
            paths.append(path)
        return paths

    def test_reads_each_framework_naming_style(self):
        doc = junit(("S1 Browse events", None), ("plan S2 Sign-in errors", None), ("plan.spec.ts > S3 Buy two seats", None),
                    ("S4 Ten-seat limit", "failure"), ("S5 Lose a seat to another buyer", "error"))
        self.assertEqual(measure.parse_junit(self.files(doc)),
                         {"S1": True, "S2": True, "S3": True, "S4": False, "S5": False})

    def test_missing_scenario_counts_as_failed(self):
        self.assertEqual(measure.parse_junit(self.files(junit(("S1 Browse events", None))))["S2"], False)

    def test_skipped_counts_as_failed(self):
        self.assertFalse(measure.parse_junit(self.files(junit(("S1 Browse events", "skipped"))))["S1"])

    def test_one_file_per_spec_is_combined(self):
        a = junit(("S1 Browse events", None), ("S2 Sign-in errors", None))
        b = junit(("S3 Buy two seats", None), ("S4 Ten-seat limit", None), ("S5 Lose a seat", None))
        self.assertTrue(all(measure.parse_junit(self.files(a, b)).values()))

    def test_a_retried_scenario_must_pass_every_attempt(self):
        doc = junit(("S1 Browse events", "failure"), ("S1 Browse events", None))
        self.assertFalse(measure.parse_junit(self.files(doc))["S1"])

    def test_ids_must_be_whole_words(self):
        # "S10" or "S1x" must not be read as S1.
        doc = junit(("S10 something", None), ("S1x other", None))
        self.assertFalse(measure.parse_junit(self.files(doc))["S1"])

    def test_broken_or_missing_files_mean_nothing_passed(self):
        broken = self.files("<testsuites><testcase name='S1'")
        self.assertFalse(any(measure.parse_junit(broken + [Path("/nope.xml")]).values()))


class Summarize(unittest.TestCase):
    def run_(self, seconds, ok=True, fail=()):
        return {"seconds": seconds, "scenarios": {s: (ok and s not in fail) for s in measure.SCENARIOS}}

    def test_median_max_and_pass_rates(self):
        s = measure.summarize([self.run_(10), self.run_(30, fail=("S5",)), self.run_(20)])
        self.assertEqual(s["run_seconds_median"], 20)
        self.assertEqual(s["run_seconds_max"], 30)
        self.assertAlmostEqual(s["pass_rate"]["S5"], 2 / 3)
        self.assertEqual(s["pass_rate"]["S1"], 1.0)
        self.assertEqual(s["all_green_runs"], 2)

    def test_even_number_of_runs_averages_the_middle_two(self):
        self.assertEqual(measure.summarize([self.run_(t) for t in (10, 20, 30, 40)])["run_seconds_median"], 25)


class RunPhase(unittest.TestCase):
    def test_times_runs_reads_junit_and_gates_on_pass_rate(self):
        out = Path(tempfile.mkdtemp())
        # A fake "framework" that writes a JUnit file where S5 fails.
        script = out / "fake.py"
        script.write_text(
            "import os\n"
            f"open(os.environ['JUNIT_FILE'],'w').write({junit(('S1 a',None),('S2 b',None),('S3 c',None),('S4 d',None),('S5 e','failure'))!r})\n"
        )
        code = measure.main(["run", "--framework", "fake", "--runs", "2", "--seed", "", "--out", str(out),
                             "--", sys.executable, str(script)])
        data = json.loads((out / "fake-run.json").read_text())
        self.assertEqual(len(data["runs"]), 2)
        self.assertEqual(data["pass_rate"]["S5"], 0.0)
        self.assertEqual(code, 1, "a scenario that never passes must fail the job")

    def test_setup_records_time_and_exit_code(self):
        out = Path(tempfile.mkdtemp())
        code = measure.main(["setup", "--framework", "fake", "--out", str(out), "--", sys.executable, "-c", "pass"])
        data = json.loads((out / "fake-setup.json").read_text())
        self.assertEqual((code, data["exit_code"]), (0, 0))
        self.assertGreaterEqual(data["setup_seconds"], 0)


class Report(unittest.TestCase):
    def test_code_lines_skip_blanks_and_comments(self):
        text = "// c\n\n# c\n/* a\n b */\nconst a = 1;\n  /* one line */\nb();\n"
        self.assertEqual(report.code_lines(text), 2)

    def test_missing_results_are_shown_not_dropped(self):
        md = report.build(Path(tempfile.mkdtemp()))
        for name in ("Playwright", "Cypress", "Appium", "Maestro"):
            self.assertIn(f"| {name} |", md)
        self.assertIn("no data", md)

    def test_numbers_from_results(self):
        results = Path(tempfile.mkdtemp())
        (results / "playwright-setup.json").write_text(json.dumps({"setup_seconds": 40.0}))
        (results / "playwright-run.json").write_text(json.dumps({
            "runs": [{}, {}], "run_seconds_median": 12.0, "run_seconds_max": 15.0, "all_green_runs": 1,
            "pass_rate": {"S1": 1, "S2": 1, "S3": 1, "S4": 1, "S5": 0.5},
        }))
        row = next(line for line in report.build(results).splitlines() if line.startswith("| Playwright | Web"))
        self.assertIn("| 40 s | 12 s | 15 s | 90% | 1 of 2 | 52 s |", row)


if __name__ == "__main__":
    unittest.main()
