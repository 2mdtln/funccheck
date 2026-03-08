# funccheck

`funccheck` is a command-line tool to scan Python and C source files and report function calls.

Supported file types:
- Python: `.py`
- C/C headers: `.c`, `.h`

By default, user-defined symbols are excluded. Use `-d`/`--def` to include them.

## Installation

From PyPI:

```bash
pip install funccheck
```

From source:

```bash
pip install .
```

## Quick Start

Scan the current directory:

```bash
funccheck
```

Scan specific files/directories:

```bash
funccheck src tests some_file.py
```

## CLI Options

- `-d`, `--def`: include user-defined functions/classes in output.
- `-c`, `--count`: show counts like `func (3)`.
- `-n`: print one function per line.
- `-a`, `--all`: merge all scanned results under one combined title.
- `-h`, `--help`: show help.

## Output Examples

Default output (grouped by file):

```text
src/funccheck/scanner.py:
  set, int, print
```

With counts (`-c`):

```text
src/funccheck/scanner.py:
  set (4), int (2), print (1)
```

One-per-line (`-n`):

```text
src/funccheck/scanner.py:
  set
  int
  print
```

Merged output (`-a`):

```text
src, tests:
  set, int, print
```

## More Examples

```bash
# Default scan
funccheck

# Include user-defined symbols
funccheck -d src

# Show counts
funccheck -c src

# One function per line
funccheck -n src

# Merge all input paths and show counts
funccheck -a -c src tests
```

## Notes

- Files in common cache/venv/build directories are skipped automatically.
- If no calls are found, `funccheck` prints: `No function calls found.`

## License

MIT
