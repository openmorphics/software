#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CoverageStats:
    covered_lines: int
    num_statements: int
    covered_branches: int
    num_branches: int

    @property
    def line_pct(self) -> float:
        if self.num_statements <= 0:
            return 100.0
        return (self.covered_lines / self.num_statements) * 100.0

    @property
    def branch_pct(self) -> float:
        if self.num_branches <= 0:
            return 100.0
        return (self.covered_branches / self.num_branches) * 100.0


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stats_from_summary(summary: dict[str, Any]) -> CoverageStats:
    statements = int(summary.get("num_statements", 0))
    missing_lines = int(summary.get("missing_lines", 0))
    covered_lines = statements - missing_lines
    covered_branches = int(summary.get("covered_branches", 0))
    num_branches = int(summary.get("num_branches", 0))
    return CoverageStats(
        covered_lines=covered_lines,
        num_statements=statements,
        covered_branches=covered_branches,
        num_branches=num_branches,
    )


def _aggregate_package_stats(files: dict[str, Any], prefix: str) -> CoverageStats:
    covered_lines = 0
    num_statements = 0
    covered_branches = 0
    num_branches = 0

    for path, payload in files.items():
        if not path.startswith(prefix):
            continue
        summary = payload.get("summary", {})
        stats = _stats_from_summary(summary)
        covered_lines += stats.covered_lines
        num_statements += stats.num_statements
        covered_branches += stats.covered_branches
        num_branches += stats.num_branches

    return CoverageStats(
        covered_lines=covered_lines,
        num_statements=num_statements,
        covered_branches=covered_branches,
        num_branches=num_branches,
    )


def _gate_line(name: str, stats: CoverageStats, line_min: float, branch_min: float) -> tuple[bool, str]:
    ok_line = stats.line_pct >= line_min
    ok_branch = stats.branch_pct >= branch_min
    ok = ok_line and ok_branch
    msg = (
        f"{name}: line={stats.line_pct:.1f}% ({stats.covered_lines}/{stats.num_statements}) "
        f"target>={line_min:.1f}% | "
        f"branch={stats.branch_pct:.1f}% ({stats.covered_branches}/{stats.num_branches}) "
        f"target>={branch_min:.1f}%"
    )
    return ok, msg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check package and overall coverage gates.")
    parser.add_argument(
        "--coverage-json",
        default="coverage.json",
        help="Path to coverage.py JSON report (from --cov-report=json:...).",
    )
    parser.add_argument(
        "--gates",
        default="tools/coverage_gates.json",
        help="Path to coverage gates config JSON.",
    )
    args = parser.parse_args(argv)

    coverage_path = Path(args.coverage_json)
    gates_path = Path(args.gates)
    if not coverage_path.is_file():
        print(f"coverage gates: missing coverage report: {coverage_path}", file=sys.stderr)
        return 2
    if not gates_path.is_file():
        print(f"coverage gates: missing gates config: {gates_path}", file=sys.stderr)
        return 2

    report = _load_json(coverage_path)
    gates = _load_json(gates_path)

    totals = report.get("totals", {})
    files = report.get("files", {})
    if not isinstance(files, dict):
        print("coverage gates: invalid coverage report format (files missing)", file=sys.stderr)
        return 2

    overall = _stats_from_summary(totals)
    overall_cfg = gates.get("overall", {})
    overall_line_min = float(overall_cfg.get("line_min", 0.0))
    overall_branch_min = float(overall_cfg.get("branch_min", 0.0))

    failures: list[str] = []

    ok, msg = _gate_line("overall", overall, overall_line_min, overall_branch_min)
    print(msg)
    if not ok:
        failures.append(msg)

    pkg_cfg = gates.get("packages", {})
    for name, cfg in pkg_cfg.items():
        prefix = str(cfg.get("prefix", ""))
        line_min = float(cfg.get("line_min", 0.0))
        branch_min = float(cfg.get("branch_min", 0.0))
        stats = _aggregate_package_stats(files, prefix)
        ok, msg = _gate_line(name, stats, line_min, branch_min)
        print(msg)
        if not ok:
            failures.append(msg)

    if failures:
        print("\ncoverage gates: FAILED")
        for f in failures:
            print(f" - {f}")
        return 1

    print("\ncoverage gates: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
