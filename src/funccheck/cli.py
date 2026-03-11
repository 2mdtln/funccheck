from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from funccheck import __version__
from funccheck.formatting import render_output
from funccheck.scanner import ScanIssue, collect_function_calls_with_issues


def _format_issue(issue: ScanIssue) -> str:
    location = ""
    if issue.line is not None:
        location = f":{issue.line}"
        if issue.column is not None:
            location += f":{issue.column}"
    return f"{issue.file_label}{location}: {issue.message}"


def _version_parts(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version))


def _is_newer_version(candidate: str, current: str) -> bool:
    candidate_parts = _version_parts(candidate)
    current_parts = _version_parts(current)
    max_len = max(len(candidate_parts), len(current_parts))
    padded_candidate = candidate_parts + (0,) * (max_len - len(candidate_parts))
    padded_current = current_parts + (0,) * (max_len - len(current_parts))
    return padded_candidate > padded_current


def _get_latest_pypi_version(timeout: float = 1.5) -> str | None:
    url = "https://pypi.org/pypi/funccheck/json"
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.load(response)
    except (URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None
    latest = payload.get("info", {}).get("version")
    return latest if isinstance(latest, str) and latest else None


def _maybe_print_update_notice() -> None:
    latest = _get_latest_pypi_version()
    if latest and _is_newer_version(latest, __version__):
        print(
            f"✨ A new version of funccheck is available: {latest} "
            f"(installed: {__version__}).",
            file=sys.stderr,
        )
        print("Update with: pip install --upgrade funccheck\n", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="funccheck",
        description="List called functions in Python and C files.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the installed version and exit.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories to scan. Defaults to current directory.",
    )
    parser.add_argument(
        "-d",
        "--def",
        dest="include_user_defined",
        action="store_true",
        help="Include user-defined functions and classes in output.",
    )
    parser.add_argument(
        "-c",
        "--count",
        action="store_true",
        help="Show occurrence counts per file/function pair.",
    )
    parser.add_argument(
        "-n",
        dest="new_lines",
        action="store_true",
        help="Print one function per line under each file.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Group all functions under one combined title.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 if any files are skipped due to parse errors.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _maybe_print_update_notice()
    input_paths: list[str] = list(args.paths)

    counts, issues = collect_function_calls_with_issues(
        [Path(path) for path in input_paths],
        include_user_defined=args.include_user_defined,
    )
    if issues:
        print("Skipped files with parse errors:", file=sys.stderr)
        for issue in issues:
            print(f"  {_format_issue(issue)}", file=sys.stderr)
        runtime = sys.version.split()[0]
        print(
            f"funccheck is running on Python {runtime}. "
            "These errors can be caused by invalid syntax or syntax that "
            "requires a newer interpreter.",
            file=sys.stderr,
        )
        if args.strict:
            return 1
    if not counts:
        if issues:
            print("No function calls found in successfully scanned files.")
        else:
            print("No function calls found.")
        return 0

    if args.all:
        title = ", ".join(input_paths) if input_paths else "."
        merged: Counter[tuple[str, str]] = Counter()
        for (_, func_name), count in counts.items():
            merged[(title, func_name)] += count
        counts = merged

    for line in render_output(counts, show_count=args.count,
                              new_lines=args.new_lines):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
