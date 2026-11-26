#!/usr/bin/env python3
"""Turn the results/*.json files from measure.py into RESULTS.md.

    report.py --results results --out RESULTS.md

Frameworks with missing results are listed as "no data" rather than left out,
so a broken job can't quietly drop a framework from the comparison.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = {
    "S1": "Browse events",
    "S2": "Sign-in errors",
    "S3": "Buy two seats",
    "S4": "Ten-seat limit",
    "S5": "Lose a seat to another buyer",
}
FRAMEWORKS = {
    # name: (platform, test code globs relative to the repo root)
    "playwright": ("Web", ["web/playwright/tests/**/*.ts", "web/playwright/playwright.config.ts"]),
    "cypress": ("Web", ["web/cypress/cypress/**/*.ts", "web/cypress/cypress.config.ts"]),
    "appium": ("Android", ["mobile/appium/test/**/*.ts", "mobile/appium/wdio.conf.ts"]),
    "maestro": ("Android", ["mobile/maestro/**/*.yaml", "mobile/maestro/scripts/*.js"]),
}


def code_lines(text: str) -> int:
    """Lines that aren't blank or comments (//, #, and /* ... */ blocks)."""
    count, in_block = 0, False
    for raw in text.splitlines():
        line = raw.strip()
        if in_block:
            if "*/" in line:
                in_block = False
            continue
        if not line or line.startswith(("//", "#")):
            continue
        if line.startswith("/*"):
            in_block = "*/" not in line
            continue
        count += 1
    return count


def test_code_lines(root: Path, globs: list[str]) -> int:
    files = {p for pattern in globs for p in root.glob(pattern) if p.is_file()}
    return sum(code_lines(p.read_text()) for p in files)


def load(results: Path, framework: str, phase: str) -> dict | None:
    path = results / f"{framework}-{phase}.json"
    return json.loads(path.read_text()) if path.exists() else None


def fmt_seconds(s: float | None) -> str:
    if s is None:
        return "no data"
    return f"{s:.0f} s" if s < 90 else f"{s / 60:.1f} min"


def fmt_rate(r: float) -> str:
    return f"{r:.0%}"


def build(results: Path, root: Path = ROOT) -> str:
    rows, scenario_rows = [], []
    for name, (platform, globs) in FRAMEWORKS.items():
        setup = load(results, name, "setup")
        run = load(results, name, "run")
        lines = test_code_lines(root, globs)
        setup_s = setup["setup_seconds"] if setup else None
        if run:
            runs = len(run["runs"])
            overall = sum(run["pass_rate"].values()) / len(SCENARIOS)
            first_run = (setup_s or 0) + run["run_seconds_median"] if setup_s is not None else None
            rows.append(
                f"| {name.capitalize()} | {platform} | {fmt_seconds(setup_s)} | {fmt_seconds(run['run_seconds_median'])} "
                f"| {fmt_seconds(run['run_seconds_max'])} | {fmt_rate(overall)} | {run['all_green_runs']} of {runs} "
                f"| {fmt_seconds(first_run)} | {lines} |"
            )
            scenario_rows.append(
                f"| {name.capitalize()} | " + " | ".join(fmt_rate(run["pass_rate"][s]) for s in SCENARIOS) + " |"
            )
        else:
            rows.append(f"| {name.capitalize()} | {platform} | {fmt_seconds(setup_s)} | no data | no data | no data "
                        f"| no data | no data | {lines} |")
            scenario_rows.append(f"| {name.capitalize()} | " + " | ".join("no data" for _ in SCENARIOS) + " |")

    source = os.environ.get("RESULTS_SOURCE", "")
    return "\n".join([
        "# Results",
        "",
        "Measured in GitHub Actions on `ubuntu-latest` (4 cores). Each framework installs from scratch, then runs "
        "the whole [test plan](plan/test-plan.md) several times, reseeding the database before each run. "
        "Mobile suites run on an Android 14 emulator (API 34, x86_64, 4 cores, 4 GB).",
        *([f"", f"Source: {source}"] if source else []),
        "",
        "| Framework | Platform | Setup | Run (median) | Slowest run | Pass rate | All-green runs | Setup + one run | Test code (lines) |",
        "|---|---|---|---|---|---|---|---|---|",
        *rows,
        "",
        "## Pass rate by scenario",
        "",
        "| Framework | " + " | ".join(f"{sid} {title}" for sid, title in SCENARIOS.items()) + " |",
        "|---|" + "---|" * len(SCENARIOS),
        *scenario_rows,
        "",
        "**Setup** is installing the framework and its browser, driver or CLI on a fresh runner. Building the app "
        "and starting the API are shared by every framework on a platform, so they aren't counted. "
        "**Test code** counts non-blank, non-comment lines in each suite's tests, helpers and config.",
        "",
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results")
    parser.add_argument("--out", default="RESULTS.md")
    args = parser.parse_args(argv)
    text = build(Path(args.results))
    Path(args.out).write_text(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
