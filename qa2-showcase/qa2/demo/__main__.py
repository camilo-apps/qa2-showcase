"""
python -m qa2.demo

Generates the synthetic inputs, runs the QA, signs the one difference
that needs human judgement, and writes the Excel report.
"""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from qa2.demo.pipeline import (
    SignOff, read_export, read_traffic_sheet, run_rules, waiting_for_signature, write_report,
)
from qa2.demo.sample_data import CAMPAIGN, write_samples
from qa2.verdict import SCOPE_LABELS, VERDICT_LABELS, headline, overall, verdicts_by_scope

ROOT = Path.cwd()


def main() -> None:
    started = time.perf_counter()
    ts_path, export_path = write_samples(ROOT / "sample_data")
    requested, excluded = read_traffic_sheet(ts_path)
    implemented = read_export(export_path)
    findings = run_rules(requested, implemented, CAMPAIGN).findings

    print(f"\nQA2 demo · {CAMPAIGN}")
    print(f"{len({r.placement_id for r in requested})} placements in scope, "
          f"{excluded} rows out of scope (hold / not worked)\n")
    for f in sorted(findings, key=lambda f: ("FAIL", "REVIEW", "NOT_VERIFIED", "PASS").index(f.status.value)
                    if f.status.value in ("FAIL", "REVIEW", "NOT_VERIFIED", "PASS") else 9):
        print(f"  {f.status.value:<13} {f.rule_id:<8} {f.placement_id:<9} {f.message}")

    print(f"\nOverall: {VERDICT_LABELS[overall(findings)]}")
    for scope, value in sorted(verdicts_by_scope(findings).items()):
        print(f"  {SCOPE_LABELS[scope]:<15} {VERDICT_LABELS[value]}")
    if headline(findings):
        print(f"  -> {headline(findings)}")

    signoffs = {}
    for (rule, reason), items in waiting_for_signature(findings).items():
        print(f"\nWaiting for a signature: {rule} · {reason} ({len(items)})")
        for f in items:
            signoffs[f.finding_id] = SignOff(
                who="Laura Gómez", why="Client extended the flight by email",
                when=datetime.now().strftime("%Y-%m-%d %H:%M"),
            )
        print("  signed by Laura Gómez -- kept in the report as a callout, not a failure")

    report = write_report(findings, CAMPAIGN, ROOT / "out", signoffs, excluded)
    print(f"\nReport: {report.relative_to(ROOT)}")
    print(f"Done in {time.perf_counter() - started:.2f} s\n")


if __name__ == "__main__":
    main()
