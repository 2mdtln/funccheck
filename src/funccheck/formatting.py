from __future__ import annotations

from collections import Counter

_COLOR_BLUE_BOLD = "\033[1;34m"
_COLOR_RESET = "\033[0m"


def render_output(
    counts: Counter[tuple[str, str]], show_count: bool, new_lines: bool
) -> list[str]:
    grouped: dict[str, list[tuple[str, int]]] = {}
    for (file_name, func_name), count in counts.items():
        grouped.setdefault(file_name, []).append((func_name, count))

    lines: list[str] = []
    for file_name in sorted(grouped):
        lines.append(f"{_COLOR_BLUE_BOLD}{file_name}:{_COLOR_RESET}")
        if show_count:
            entries = sorted(grouped[file_name],
                             key=lambda item: (-item[1], item[0]))
            if new_lines:
                lines.extend(f"  {func_name} "
                             f"({count})" for func_name, count in entries)
            else:
                rendered = ", ".join(
                    f"{func_name} ({count})" for func_name, count in entries
                )
                lines.append(f"  {rendered}")
            continue

        entries = sorted(grouped[file_name], key=lambda item: item[0])
        if new_lines:
            lines.extend(f"  {func_name}" for func_name, _ in entries)
        else:
            rendered = ", ".join(func_name for func_name, _ in entries)
            lines.append(f"  {rendered}")

    return lines
