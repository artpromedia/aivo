#!/usr/bin/env python3
"""
Idempotently ensure `pyproject.toml` contains a Ruff config with:
  - [tool.ruff] line-length = 100, target-version = "py311"
  - [tool.ruff.lint] select = ["E","F","W","I","UP","N"]  (created if missing)

It preserves everything else and only edits/creates the [tool.ruff] tables.
Usage:
  python scripts/ensure_ruff_config.py --write     # modify file in place
  python scripts/ensure_ruff_config.py --check     # exit 1 if change needed
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PYPROJECT = Path("pyproject.toml")

RUFF_HDR_RE = re.compile(r"^\[tool\.ruff\]\s*$")
TABLE_HDR_RE = re.compile(r"^\[[^\]]+\]\s*$")


def _find_table(lines: list[str], header_re: re.Pattern[str]) -> tuple[int | None, int | None]:
    """Return (start_idx, end_idx_exclusive) for table header; end is next table or EOF."""
    start = None
    for i, ln in enumerate(lines):
        if header_re.match(ln):
            start = i
            break
    if start is None:
        return None, None
    # find next table or EOF
    for j in range(start + 1, len(lines)):
        if TABLE_HDR_RE.match(lines[j]):
            return start, j
    return start, len(lines)


def _ensure_kv(block_lines: list[str], key: str, value_line: str) -> list[str]:
    """Ensure 'key = ...' exists in block_lines; replace if present, append if not."""
    key_re = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for i, ln in enumerate(block_lines):
        if key_re.match(ln):
            block_lines[i] = value_line + "\n"
            return block_lines
    # append before possible trailing blank lines
    # trim trailing blanks, then add key, then re-add single blank
    while block_lines and block_lines[-1].strip() == "":
        block_lines.pop()
    block_lines.append(value_line + "\n")
    block_lines.append("\n")
    return block_lines


def _ensure_section(lines: list[str]) -> tuple[list[str], bool]:
    """
    Ensure [tool.ruff] and [tool.ruff.lint] sections exist and contain desired keys.
    Returns (new_lines, changed).
    """
    changed = False

    # 1) Ensure [tool.ruff] exists
    start, end = _find_table(lines, RUFF_HDR_RE)
    if start is None:
        # create a new [tool.ruff] table at EOF with desired defaults
        append = []
        if lines and lines[-1].strip() != "":
            append.append("\n")
        append.extend(
            [
                "[tool.ruff]\n",
                "line-length = 100\n",
                'target-version = "py311"\n',
                "\n",
            ]
        )
        lines = lines + append
        changed = True
        # refresh indices
        start, end = _find_table(lines, RUFF_HDR_RE)

    # 2) Ensure line-length and target-version inside [tool.ruff]
    block = lines[start:end]
    desired = block[:]
    desired = _ensure_kv(desired, "line-length", "line-length = 100")
    desired = _ensure_kv(desired, "target-version", 'target-version = "py311"')
    if desired != block:
        lines = lines[:start] + desired + lines[end:]
        changed = True
        # recompute indices in case sizes shifted
        start, end = _find_table(lines, RUFF_HDR_RE)

    # 3) Ensure [tool.ruff.lint] with select exists
    lint_hdr_re = re.compile(r"^\[tool\.ruff\.lint\]\s*$")
    lstart, lend = _find_table(lines, lint_hdr_re)
    if lstart is None:
        # create [tool.ruff.lint] after [tool.ruff]
        insert_at = end
        insert = [
            "[tool.ruff.lint]\n",
            'select = ["E","F","W","I","UP","N"]\n',
            "\n",
        ]
        lines = lines[:insert_at] + insert + lines[insert_at:]
        changed = True
    else:
        lint_block = lines[lstart:lend]
        desired_lint = _ensure_kv(lint_block[:], "select", 'select = ["E","F","W","I","UP","N"]')
        if desired_lint != lint_block:
            lines = lines[:lstart] + desired_lint + lines[lend:]
            changed = True

    return lines, changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write changes to pyproject.toml")
    ap.add_argument("--check", action="store_true", help="exit 1 if changes would be made")
    args = ap.parse_args()

    if not PYPROJECT.exists():
        print("pyproject.toml not found; nothing to do.")
        return 0

    original = PYPROJECT.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines, changed = _ensure_section(original)

    if args.check and changed:
        print("Ruff config changes needed (run with --write).")
        return 1

    if args.write and changed:
        PYPROJECT.write_text("".join(new_lines), encoding="utf-8", newline="\n")
        print("Updated pyproject.toml with Ruff config (line-length=100, target-version=py311).")
        return 0

    if changed:
        print("Changes required but --write not provided (use --write or --check).")
        return 1

    print("pyproject.toml already contains the desired Ruff configuration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
