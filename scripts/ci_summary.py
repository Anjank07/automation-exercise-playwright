"""
Turn a pytest JUnit XML file into a Markdown summary for the GitHub Actions
run page.

Usage (in CI):  python scripts/ci_summary.py reports/junit.xml "UI smoke (chromium)"

GitHub renders whatever a step appends to the file named by the
GITHUB_STEP_SUMMARY environment variable at the top of the run page. That
puts pass/fail counts and the name + first line of every failure one click
from the green/red badge, without downloading an artifact. Outside CI (no
such variable) it prints to stdout, so it can be tried locally.

Standard library only on purpose: a reporting step must not be able to fail
because a third-party reporter changed its API.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def summarize(junit_path: Path, title: str) -> str:
    if not junit_path.exists():
        # The test step crashed before pytest wrote a report — say so rather
        # than failing this step too and hiding the real error.
        return f"### {title}\n\nNo JUnit report found at `{junit_path}`.\n"

    root = ET.parse(junit_path).getroot()

    # Count per TEST CASE, not per <failure>/<error> element. A test that
    # fails in its body AND errors in teardown carries both elements, so
    # totals taken from the suite attributes double-count it (an early
    # version of this script reported "-3 passed" on exactly that).
    rank = {"passed": 0, "skipped": 1, "error": 2, "failed": 3}
    outcome: dict[str, str] = {}
    reasons: dict[str, str] = {}
    seconds = 0.0
    for case in root.iter("testcase"):
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        seconds += float(case.get("time", 0))
        failure, error = case.find("failure"), case.find("error")
        if failure is not None:
            state = "failed"
        elif error is not None:
            state = "error"
        elif case.find("skipped") is not None:
            state = "skipped"
        else:
            state = "passed"
        if rank[state] >= rank[outcome.get(name, "passed")]:
            outcome[name] = state
        problem = failure if failure is not None else error
        if problem is not None and name not in reasons:
            lines = (problem.get("message") or "").strip().splitlines()
            reasons[name] = lines[0][:200] if lines else ""

    states = list(outcome.values())
    total = len(states)
    passed, failed = states.count("passed"), states.count("failed")
    errored, skipped = states.count("error"), states.count("skipped")
    failures = [(n, reasons.get(n, "")) for n, v in outcome.items() if v in ("failed", "error")]

    icon = "✅" if not (failed or errored) else "❌"
    lines = [
        f"### {icon} {title}",
        "",
        "| Passed | Failed | Errors | Skipped | Total | Duration |",
        "|---:|---:|---:|---:|---:|---:|",
        f"| {passed} | {failed} | {errored} | {skipped} | {total} | {seconds:.0f}s |",
        "",
    ]
    if failures:
        lines += ["| Failed test | Reason |", "|---|---|"]
        lines += [f"| `{name}` | {reason.replace('|', '/')} |" for name, reason in failures]
        lines += [
            "",
            "Full report and a Playwright trace per failure are in this run's artifacts.",
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: ci_summary.py <junit.xml> <title>")
    markdown = summarize(Path(sys.argv[1]), sys.argv[2])
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(markdown + "\n")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
