#!/usr/bin/env python3
"""Accept pending edit-preview markup in a report workspace.

When `report-update` writes back changes in preview mode, it wraps new content in
`\\reportadd{...}`, removed content in `\\reportdel{...}`, and in-place replacements
in `\\reportchg{old}{new}`. The rendered PDF shows a visual diff.

After the user confirms, run this script to strip the markup from
`sections/*.tex`, resulting in clean source files that render without diff
visualization.

Usage:

    python3 accept_edits.py /path/to/report [--dry-run] [--no-backup]
    python3 accept_edits.py /path/to/report --section 05-core-design.tex

Behaviour:

- `\\reportadd{X}` → `X`
- `\\reportdel{X}` → removed (empty)
- `\\reportchg{old}{new}` → `new`

Backups are written to `build/accept-edits-backup-<iso-timestamp>/sections/`
unless `--no-backup` is passed.
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


MACRO_NAMES = ("reportadd", "reportdel", "reportchg")


def _find_balanced_arg(source: str, start: int) -> tuple[str, int]:
    """Parse a brace-balanced LaTeX argument starting at `source[start]`.

    `source[start]` must be '{'. Returns (argument content without outer braces,
    index just past the closing '}').

    Handles nested `{...}` and skips `\\{` / `\\}` escaped braces.
    """
    if start >= len(source) or source[start] != "{":
        raise ValueError(f"expected '{{' at position {start}")
    depth = 1
    i = start + 1
    while i < len(source):
        ch = source[i]
        if ch == "\\" and i + 1 < len(source) and source[i + 1] in "{}":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1 : i], i + 1
        i += 1
    raise ValueError("unbalanced braces: missing closing '}'")


def accept_markup(source: str) -> str:
    """Strip diff-preview macros from a LaTeX source string."""
    out: list[str] = []
    i = 0
    length = len(source)
    while i < length:
        ch = source[i]
        if ch == "\\":
            matched = False
            for name in MACRO_NAMES:
                token = "\\" + name
                end = i + len(token)
                if (
                    source.startswith(token, i)
                    and end < length
                    and source[end] == "{"
                    and not (end - 1 > i and source[i + len(token) - 1].isalpha() and end < length and source[end].isalpha())
                ):
                    arg1, next_i = _find_balanced_arg(source, end)
                    if name == "reportadd":
                        out.append(accept_markup(arg1))
                        i = next_i
                    elif name == "reportdel":
                        i = next_i
                    elif name == "reportchg":
                        if next_i >= length or source[next_i] != "{":
                            raise ValueError(
                                f"\\reportchg at offset {i} is missing its second argument"
                            )
                        arg2, next_i2 = _find_balanced_arg(source, next_i)
                        out.append(accept_markup(arg2))
                        i = next_i2
                    matched = True
                    break
            if matched:
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def _has_markup(text: str) -> bool:
    return any("\\" + name + "{" in text for name in MACRO_NAMES)


def process_report(
    report_dir: Path,
    *,
    dry_run: bool = False,
    backup: bool = True,
    section: str | None = None,
) -> list[str]:
    """Apply accept_markup to every section file in the report workspace.

    Returns a list of section paths (relative to report_dir) that contained
    diff markup. In dry-run mode, the return value is the same but no files
    are written.
    """
    sections_dir = report_dir / "sections"
    if not sections_dir.is_dir():
        raise FileNotFoundError(f"sections directory not found under {report_dir}")

    selected_name = section.strip() if section else None

    def is_selected(path: Path) -> bool:
        if not selected_name:
            return True
        return selected_name in {
            path.name,
            path.stem,
            str(path.relative_to(report_dir)),
            str(path.relative_to(sections_dir)),
        }

    targets: list[tuple[Path, str, str]] = []
    for path in sorted(sections_dir.glob("*.tex")):
        if not is_selected(path):
            continue
        original = path.read_text()
        if not _has_markup(original):
            continue
        cleaned = accept_markup(original)
        if cleaned == original:
            continue
        targets.append((path, original, cleaned))

    changed = [str(path.relative_to(report_dir)) for path, _, _ in targets]
    if dry_run or not targets:
        return changed

    if backup:
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        backup_root = report_dir / "build" / f"accept-edits-backup-{stamp}" / "sections"
        backup_root.mkdir(parents=True, exist_ok=True)
        for path, original, _ in targets:
            (backup_root / path.name).write_text(original)

    for path, _, cleaned in targets:
        path.write_text(cleaned)

    return changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Accept report-update edit-preview markup and clean up .tex source."
    )
    parser.add_argument("report_dir", help="Path to the report workspace.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report which files would change; do not write.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip writing the backup copy under build/accept-edits-backup-<ts>/.",
    )
    parser.add_argument(
        "--section",
        help="Accept markup only in one section file. Accepts filename, stem, or sections/<file>.tex.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_dir = Path(args.report_dir).resolve()
    if not report_dir.exists():
        print(f"[ERROR] Report workspace not found: {report_dir}")
        return 1

    try:
        changed = process_report(
            report_dir,
            dry_run=args.dry_run,
            backup=not args.no_backup,
            section=args.section,
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1

    if not changed:
        print("[OK] No diff-preview markup found. Nothing to accept.")
        return 0

    mode = "dry-run" if args.dry_run else "accepted"
    print(f"[OK] {mode}: {len(changed)} file(s) with diff markup")
    for path in changed:
        print(f"  - {path}")
    if not args.dry_run and not args.no_backup:
        print("[OK] Backup written under build/accept-edits-backup-<timestamp>/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
