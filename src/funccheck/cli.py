from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from funccheck.formatting import render_output
from funccheck.scanner import collect_function_calls


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="funccheck",
        description="List called functions in Python and C files.",
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_paths: list[str] = list(args.paths)

    counts = collect_function_calls(
        [Path(path) for path in input_paths],
        include_user_defined=args.include_user_defined,
    )
    if not counts:
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
