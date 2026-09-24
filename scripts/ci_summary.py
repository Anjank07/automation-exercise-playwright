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
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))

    total = failed = errored = skipped = 0
    seconds = 0.0
    failures: list[tuple[str, str]] = []
    for suite in suites:
        total += int(suite.get("tests", 0))
        failed += int(suite.get("failures", 0))
        errored += int(suite.get("errors", 0))
        skipped += int(suite.get("skipped", 0))
        seconds += float(suite.get("time", 0))
        for case in suite.iter("testcase"):
            problem = case.find("failure")
            if problem is None:
                problem = case.find("error")
            if problem is not None:
                name = f"{case.get('classname', '')}::{case.get('name', '')}"
                message = (problem.get("message") or "").strip().splitlines()
                failures.append((name, message[0][:200] if message else ""))

    passed = total - failed - errored - skipped
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
