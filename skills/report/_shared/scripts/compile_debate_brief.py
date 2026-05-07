#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def resolve_section(report_dir: Path, section: str) -> Path:
    direct = Path(section)
    if direct.is_absolute() and direct.exists():
        return direct

    candidate = (report_dir / section).resolve()
    if candidate.exists():
        return candidate

    section_dir = report_dir / "sections"
    matches = list(section_dir.glob(section))
    if len(matches) == 1:
        return matches[0].resolve()

    by_name = [path for path in section_dir.glob("*.tex") if path.name == section]
    if len(by_name) == 1:
        return by_name[0].resolve()

    raise FileNotFoundError(f"Cannot resolve section '{section}' under {report_dir}")


def build_brief(
    report_dir: Path,
    section_path: Path,
    proposition: str,
    audience: str,
    immutable_assumptions: list[str],
    candidate_options: list[str],
    allowed_sources: list[str],
) -> str:
    section_text = section_path.read_text()
    relative = section_path.relative_to(report_dir)

    lines = [
        "# Debate Brief",
        "",
        f"- 报告工作区: `{report_dir}`",
        f"- 目标章节: `{relative.as_posix()}`",
        f"- 目标受众: `{audience}`",
        f"- 被辩论命题: {proposition}",
        "",
        "## 原始章节内容",
        "",
        "```tex",
        section_text.rstrip(),
        "```",
        "",
        "## 不可更改前提",
        "",
    ]

    if immutable_assumptions:
        lines.extend(f"- {item}" for item in immutable_assumptions)
    else:
        lines.append("- 无显式不可变前提。")

    lines.extend(["", "## 必须比较的候选方案", ""])
    if candidate_options:
        lines.extend(f"- {item}" for item in candidate_options)
    else:
        lines.append("- 无显式候选方案。")

    lines.extend(["", "## 允许优先引用的资料范围", ""])
    if allowed_sources:
        lines.extend(f"- {item}" for item in allowed_sources)
    else:
        lines.append("- 官方文档、标准、论文、项目主页等一手资料。")

    lines.extend(
        [
            "",
            "## 双代理约束",
            "",
            "- 正方代理只能论证当前写法或当前方案为什么值得保留或成立。",
            "- 反方代理只能论证当前写法或当前方案为什么不足、错误或应改。",
            "- 两方都可以读取本简报、目标章节、允许的资料范围，并检索外部资料。",
            "- 两方都不得直接编辑正文。",
            "- 两方都不得仅因“尚未实现”就否决设计意图。",
            "- 两方都必须区分 source claim、design intent、repo-observed fact、report synthesis。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile a debate brief for report-debate.")
    parser.add_argument("--report-dir", required=True, help="Path to the report workspace.")
    parser.add_argument("--section", required=True, help="Section file, relative path, or glob under sections/.")
    parser.add_argument("--proposition", required=True, help="Claim or design proposition to debate.")
    parser.add_argument("--audience", default="mixed", help="Audience label for the rewritten section.")
    parser.add_argument(
        "--immutable-assumption",
        action="append",
        default=[],
        help="Assumption that the debate must not change. Repeatable.",
    )
    parser.add_argument(
        "--candidate-option",
        action="append",
        default=[],
        help="Candidate option that must be considered. Repeatable.",
    )
    parser.add_argument(
        "--allowed-source",
        action="append",
        default=[],
        help="Preferred source scope. Repeatable.",
    )
    parser.add_argument("--output", help="Optional output file path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_dir = Path(args.report_dir).resolve()
    if not report_dir.exists():
        print(f"[ERROR] Report workspace not found: {report_dir}")
        return 1

    try:
        section_path = resolve_section(report_dir, args.section)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}")
        return 1

    brief = build_brief(
        report_dir=report_dir,
        section_path=section_path,
        proposition=args.proposition,
        audience=args.audience,
        immutable_assumptions=args.immutable_assumption,
        candidate_options=args.candidate_option,
        allowed_sources=args.allowed_source,
    )

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(brief)
        print(f"[OK] Wrote debate brief: {output_path}")
    else:
        print(brief)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
