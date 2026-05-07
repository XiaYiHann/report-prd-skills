#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def build_snippet(title: str, proposition: str) -> str:
    return f"""\\subsection{{争议与裁决：{title}}}

本小节用于记录围绕“{proposition}”展开的正反论证，并给出当前阶段更公允的裁决。这里的目的不是重复意见，而是把事实、前提假设、价值判断与最终结论明确分开，避免读者把尚未论证充分的判断误认为既定事实。

\\paragraph{{当前争议点}}
请用 1--2 段说明当前到底在争议什么，为什么这件事会影响后续设计、实现、资源投入或风险判断。

\\paragraph{{正方最强论据}}
请用学术论文风格的正式书面语总结支持当前写法或当前方案的最强论据，并说明这些论据分别属于 source claim、design intent、repo-observed fact 还是 report synthesis。

\\paragraph{{反方最强论据}}
请用学术论文风格的正式书面语总结反对当前写法或当前方案的最强论据，并说明这些论据分别属于 source claim、design intent、repo-observed fact 还是 report synthesis。

\\paragraph{{事实、价值判断与前提假设}}
请明确区分：哪些论点是事实判断，哪些论点是价值判断，哪些论点依赖尚未验证的前提假设。不要把尚未验证的假设伪装成结论。

\\paragraph{{当前裁决}}
请给出当前阶段更公允的结论，并说明为什么这个结论比原段落更稳健、更适合读者使用。

\\paragraph{{对正文的改写原则}}
请说明原正文应该保留什么、删掉什么、弱化什么、补充什么。必要时指出哪些措辞需要从“已经实现”改成“目标设计”。

\\paragraph{{剩余不确定项}}
请列出仍需后续验证的部分，并说明这些不确定项若被证明为真或假，会如何影响执行决策。

\\begin{{table}}[htbp]
\\centering
\\caption{{争议裁决摘要：{title}}}
\\begin{{tabularx}}{{\\textwidth}}{{>{{\\raggedright\\arraybackslash}}p{{0.16\\textwidth}} >{{\\raggedright\\arraybackslash}}X >{{\\raggedright\\arraybackslash}}p{{0.18\\textwidth}} >{{\\raggedright\\arraybackslash}}p{{0.18\\textwidth}} >{{\\raggedright\\arraybackslash}}p{{0.14\\textwidth}}}}
\\toprule
观点 & 最强依据 & 成立前提 & 主要风险 & 裁决 \\\\
\\midrule
正方 & 待补充 & 待补充 & 待补充 & 待补充 \\\\
反方 & 待补充 & 待补充 & 待补充 & 待补充 \\\\
\\bottomrule
\\end{{tabularx}}
\\end{{table}}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a LaTeX debate write-back snippet.")
    parser.add_argument("--title", required=True, help="Short title for the debate subsection.")
    parser.add_argument("--proposition", required=True, help="Claim or design proposition under debate.")
    parser.add_argument("--output", help="Optional output file path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snippet = build_snippet(args.title, args.proposition)
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(snippet)
        print(f"[OK] Wrote debate write-back snippet: {output_path}")
    else:
        print(snippet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
