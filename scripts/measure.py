#!/usr/bin/env python3
"""Measure one framework: how long it takes to install, and how it does when the
whole test plan runs several times in a row.

    measure.py setup --framework cypress --cwd web/cypress -- npm ci
    measure.py run --framework cypress --cwd web/cypress --runs 5 -- npx cypress run
    measure.py catch --framework cypress --expect-fail S3 -- npx cypress run

`setup` times one command. `run` reseeds the database, then runs the suite,
`--runs` times. `catch` runs it once against a deliberately broken app and
checks that exactly the expected scenarios fail: a suite that can't fail
proves nothing. Each run writes JUnit XML to the path in $JUNIT_FILE, which
every framework here can produce. Results go to results/<framework>-<phase>.json.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

SCENARIOS = ["S1", "S2", "S3", "S4", "S5"]
DEFAULT_SEED = "python -m app.seed --events 14 --seats 12 --users 60"
SCENARIO_ID = re.compile(r"\bS([1-5])\b")


def parse_junit(paths: list[Path]) -> dict[str, bool]:
    """Map each scenario id to passed/failed from one run's JUnit files.

    Frameworks name test cases differently ("S1 Browse events",
    "plan S1 Browse events") and some write one file per spec, so every
    test case in every file counts, matched by the scenario id in its name.
    A scenario that never appears counts as failed; if one appears more than
    once (a framework reporting a retry), every attempt must pass.
    """
    outcome: dict[str, bool | None] = {s: None for s in SCENARIOS}
    for path in paths:
        try:
            root = ET.parse(path).getroot()
        except (ET.ParseError, OSError):
            continue
        for case in root.iter("testcase"):
            match = SCENARIO_ID.search(case.get("name", ""))
            if not match:
                continue
            sid = "S" + match.group(1)
            passed = not any(child.tag in ("failure", "error", "skipped") for child in case)
            outcome[sid] = passed if outcome[sid] is None else (outcome[sid] and passed)
    return {s: bool(v) for s, v in outcome.items()}


def timed(cmd: list[str], cwd: Path, env: dict[str, str]) -> tuple[float, int]:
    start = time.monotonic()
    code = subprocess.call(cmd, cwd=cwd, env=env)
    return time.monotonic() - start, code


def write(out_dir: Path, framework: str, phase: str, data: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{framework}-{phase}.json"
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


def do_setup(args: argparse.Namespace) -> int:
    seconds, code = timed(args.cmd, Path(args.cwd), os.environ.copy())
    path = write(Path(args.out), args.framework, "setup", {
        "framework": args.framework, "setup_seconds": round(seconds, 1), "exit_code": code,
    })
    print(f"{args.framework} setup took {seconds:.1f}s (exit {code}) -> {path}")
    return code


def do_run(args: argparse.Namespace) -> int:
    out = Path(args.out).resolve()
    junit_root = out / f"{args.framework}-junit"
    junit_root.mkdir(parents=True, exist_ok=True)
    runs = []
    job_start = time.monotonic()
    for i in range(1, args.runs + 1):
        if args.seed:
            seed_code = subprocess.call(shlex.split(args.seed), cwd=args.seed_cwd or None)
            if seed_code != 0:
                print(f"reseeding failed before run {i}", file=sys.stderr)
                return seed_code
        run_dir = junit_root / f"run-{i}"
        run_dir.mkdir(exist_ok=True)
        env = os.environ.copy()
        env["JUNIT_FILE"] = str(run_dir / "junit.xml")
        cmd = [part.replace("{junit}", env["JUNIT_FILE"]) for part in args.cmd]
        print(f"--- {args.framework} run {i}/{args.runs}", flush=True)
        seconds, code = timed(cmd, Path(args.cwd), env)
        scenarios = parse_junit(sorted(run_dir.glob("*.xml")))
        runs.append({"run": i, "seconds": round(seconds, 1), "exit_code": code, "scenarios": scenarios})
        print(f"    {seconds:.1f}s, exit {code}, " + " ".join(f"{s}={'pass' if ok else 'FAIL'}" for s, ok in scenarios.items()))

    summary = summarize(runs)
    data = {"framework": args.framework, "runs": runs, "run_phase_seconds": round(time.monotonic() - job_start, 1),
            **summary}
    path = write(out, args.framework, "run", data)
    print(json.dumps(summary, indent=2))
    print(f"-> {path}")
    worst = min(summary["pass_rate"].values())
    if worst < args.min_pass_rate:
        print(f"::error::A scenario passed in only {worst:.0%} of runs (minimum {args.min_pass_rate:.0%}).")
        return 1
    return 0


def do_catch(args: argparse.Namespace) -> int:
    out = Path(args.out).resolve()
    run_dir = out / f"{args.framework}-junit" / "catch"
    run_dir.mkdir(parents=True, exist_ok=True)
    if args.seed:
        code = subprocess.call(shlex.split(args.seed), cwd=args.seed_cwd or None)
        if code != 0:
            print("reseeding failed", file=sys.stderr)
            return code
    env = os.environ.copy()
    env["JUNIT_FILE"] = str(run_dir / "junit.xml")
    cmd = [part.replace("{junit}", env["JUNIT_FILE"]) for part in args.cmd]
    print(f"--- {args.framework} against the planted bug", flush=True)
    seconds, code = timed(cmd, Path(args.cwd), env)
    scenarios = parse_junit(sorted(run_dir.glob("*.xml")))
    verdict = judge_catch(scenarios, args.expect_fail)
    data = {"framework": args.framework, "expected_failures": sorted(args.expect_fail), "scenarios": scenarios,
            "seconds": round(seconds, 1), **verdict}
    path = write(out, args.framework, "catch", data)
    print(f"    failed: {verdict['failed'] or 'none'}; expected: {sorted(args.expect_fail)} -> "
          f"{'caught it' if verdict['caught'] else 'DID NOT catch it'} ({path})")
    if not verdict["caught"]:
        print(f"::error::{args.framework} {verdict['problem']}")
        return 1
    return 0


def judge_catch(scenarios: dict[str, bool], expected: list[str]) -> dict:
    """Caught means the expected scenarios failed and nothing else did."""
    failed = sorted(s for s, ok in scenarios.items() if not ok)
    missed = sorted(set(expected) - set(failed))
    extra = sorted(set(failed) - set(expected))
    problem = ""
    if missed:
        problem = f"didn't fail {', '.join(missed)}, so the planted bug went unnoticed"
    elif extra:
        problem = f"also failed {', '.join(extra)}, which the planted bug doesn't affect"
    return {"failed": failed, "caught": not missed and not extra, "problem": problem}


def summarize(runs: list[dict]) -> dict:
    times = sorted(r["seconds"] for r in runs)
    mid = len(times) // 2
    median = times[mid] if len(times) % 2 else (times[mid - 1] + times[mid]) / 2
    pass_rate = {s: sum(r["scenarios"][s] for r in runs) / len(runs) for s in SCENARIOS}
    return {
        "run_seconds_median": round(median, 1),
        "run_seconds_max": round(times[-1], 1),
        "pass_rate": pass_rate,
        "all_green_runs": sum(all(r["scenarios"].values()) for r in runs),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="phase", required=True)
    for name in ("setup", "run", "catch"):
        p = sub.add_parser(name)
        p.add_argument("--framework", required=True)
        p.add_argument("--cwd", default=".")
        p.add_argument("--out", default="results")
        p.add_argument("cmd", nargs=argparse.REMAINDER)
    run = sub.choices["run"]
    run.add_argument("--runs", type=int, default=3)
    catch = sub.choices["catch"]
    catch.add_argument("--expect-fail", action="append", required=True, choices=SCENARIOS,
                       help="a scenario the broken app should fail (repeatable)")
    for p in (run, catch):
        p.add_argument("--seed", default=os.environ.get("SEED_CMD", DEFAULT_SEED),
                       help="command that resets the database first ('' to skip)")
        p.add_argument("--seed-cwd", default=os.environ.get("SEED_CWD", ""))
    run.add_argument("--min-pass-rate", type=float, default=float(os.environ.get("MIN_PASS_RATE", "0.8")),
                     help="fail the job if any scenario passes less often than this")
    args = parser.parse_args(argv)
    if args.cmd and args.cmd[0] == "--":
        args.cmd = args.cmd[1:]
    if not args.cmd:
        parser.error("give the command to time after --")
    return {"setup": do_setup, "run": do_run, "catch": do_catch}[args.phase](args)


if __name__ == "__main__":
    sys.exit(main())
