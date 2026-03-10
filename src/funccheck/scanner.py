from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
    "site-packages",
}

_SOURCE_SUFFIXES = {".py", ".c", ".h"}
_C_CONTROL_KEYWORDS = {
    "if",
    "for",
    "while",
    "switch",
    "return",
    "sizeof",
    "_Alignof",
}
_C_FUNC_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_C_FUNC_DEF_RE = re.compile(
    r"\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{", re.MULTILINE | re.DOTALL
)
_C_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_C_LINE_COMMENT_RE = re.compile(r"//.*?$", re.MULTILINE)
_C_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.DOTALL)


@dataclass(frozen=True)
class ScanIssue:
    file_label: str
    message: str
    line: int | None = None
    column: int | None = None


def _iter_source_files(paths: Iterable[Path]) -> Iterator[Path]:
    seen: set[Path] = set()
    for path in paths:
        if not path.exists():
            continue
        if path.is_file() and path.suffix.lower() in _SOURCE_SUFFIXES:
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield resolved
            continue
        if path.is_dir():
            for source_file in path.rglob("*"):
                if source_file.suffix.lower() not in _SOURCE_SUFFIXES:
                    continue
                if any(part in _SKIP_DIRS for part in source_file.parts):
                    continue
                if source_file.is_file():
                    resolved = source_file.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        yield resolved


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _defined_symbol_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def _called_function_names(tree: ast.AST) -> list[str]:
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name:
                calls.append(name)
    return calls


def _strip_c_comments_and_strings(source: str) -> str:
    source = _C_BLOCK_COMMENT_RE.sub(" ", source)
    source = _C_LINE_COMMENT_RE.sub(" ", source)
    source = _C_STRING_RE.sub(" ", source)
    return source


def _c_defined_symbol_names(source: str) -> set[str]:
    stripped = _strip_c_comments_and_strings(source)
    names: set[str] = set()
    for match in _C_FUNC_DEF_RE.finditer(stripped):
        name = match.group(1)
        if name not in _C_CONTROL_KEYWORDS:
            names.add(name)
    return names


def _c_called_function_names(source: str) -> list[str]:
    stripped = _strip_c_comments_and_strings(source)
    calls: list[str] = []
    for match in _C_FUNC_CALL_RE.finditer(stripped):
        name = match.group(1)
        if name not in _C_CONTROL_KEYWORDS:
            calls.append(name)
    return calls


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def collect_function_calls(
    paths: Iterable[Path], include_user_defined: bool = False
) -> tuple[Counter[tuple[str, str]], list[ScanIssue]]:
    user_defined: set[str] = set()
    python_calls_by_file: list[tuple[str, list[str]]] = []
    c_calls_by_file: list[tuple[str, list[str]]] = []
    issues: list[ScanIssue] = []

    for source_file in _iter_source_files(paths):
        file_label = _display_path(source_file)
        try:
            source = source_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        suffix = source_file.suffix.lower()
        if suffix == ".py":
            try:
                tree = ast.parse(source, filename=str(source_file))
            except SyntaxError as exc:
                issues.append(
                    ScanIssue(
                        file_label=file_label,
                        message=exc.msg,
                        line=exc.lineno,
                        column=exc.offset,
                    )
                )
                continue
            user_defined.update(_defined_symbol_names(tree))
            python_calls_by_file.append((file_label,
                                         _called_function_names(tree)))
            continue

        if suffix in {".c", ".h"}:
            user_defined.update(_c_defined_symbol_names(source))
            c_calls_by_file.append((file_label,
                                    _c_called_function_names(source)))

    counts: Counter[tuple[str, str]] = Counter()
    for file_label, call_names in python_calls_by_file:
        for name in call_names:
            if include_user_defined:
                counts[(file_label, name)] += 1
                continue
            bare_name = name.rsplit(".", 1)[-1]
            if name not in user_defined and bare_name not in user_defined:
                counts[(file_label, name)] += 1

    for file_label, call_names in c_calls_by_file:
        for name in call_names:
            if include_user_defined:
                counts[(file_label, name)] += 1
                continue
            if name not in user_defined:
                counts[(file_label, name)] += 1
    return counts, issues
