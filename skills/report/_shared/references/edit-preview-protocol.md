# 编辑预览协议（Edit Preview Protocol）

这份 reference 约束 `report-update` 在写回时的「可见 diff」流程。默认行为是：不直接覆盖原文，而是用三条宏把「新增」「删除」「替换」显式标记出来，让用户在 `report.pdf` 和派生的 `report.md` 里看清改了什么，再由用户主动说「接受修改」后由 `accept_edits.py` 一次性清理。

本协议只应用于 `report-update`。`report-init` 生成新骨架时不需要 diff 标记；`report-debate` 的裁决写回默认也直接覆盖，如果需要先预览再接受，可参考本文件同样使用三条宏。

## 三条宏

`style.tex` 已经在 `report-init` 生成的工作区里默认挂载以下三条宏，无需作者额外声明。

- `\reportadd{X}`：新增内容。渲染为蓝色正文。
- `\reportdel{X}`：删除内容。渲染为灰色删除线。
- `\reportchg{old}{new}`：替换。渲染为「灰色删除线 old 蓝色 new」。

三条宏都使用 `xcolor` + `ulem` 实现。颜色定义在 `style.tex` 中的 `ReportDiffAdd`（蓝）与 `ReportDiffDel`（灰），与正文字色体系一致。

## 使用规则

### 默认启用

`report-update` 做任何正文修改时，默认启用 diff 标记，不直接覆盖。这样保证了用户可以先在 PDF 和 Markdown 上检查再接受。

### 粒度建议

- 小范围替换（短句、术语、参数）优先使用 `\reportchg{旧}{新}`，读者能直接看到前后对比。
- 纯新增段落或句子使用 `\reportadd{...}`。
- 纯删除使用 `\reportdel{...}`，但要避免跨段落使用，因为 `\sout` 不能跨段工作。
- 大段替换（整段或多段）分解成「一段 `\reportdel` + 一段 `\reportadd`」，分别单独成段；不要尝试一条 `\reportchg` 包住大段。
- 复杂 LaTeX、长表格、数学公式或多层花括号内容只做小段 diff；如果一条宏会包住整张表或整组公式，改用章节级预览说明，避免让 accept 阶段承担语法修复。

### 不适用的场景

- 图表内部（TikZ、PGFPlots）：不用 diff 宏，直接改；图一般整体重绘。
- 表格单元格：允许使用，但注意 `\sout` 在窄列里可能折行异常，必要时改为段落说明。
- `brief.yaml`、`outline.md`、`sources.*` 等非 `.tex` 文件：不用宏，直接改。
- `项目进度` 章节：按 `progress-chapter-policy.md` 的规则更新，不使用 diff 宏（进度本身就是现状记录，不需要前后对照）。

### 与全局一致性扫面的关系

启用 diff 标记不影响 `report-update` 的「Mandatory Global Consistency Sweep」。扫面仍需覆盖首次定义、摘要、图注、术语漂移等，只是这些位置的改写同样应走 diff 宏，而不是直接覆盖。

## Workflow

`report-update` 的 diff 模式在原有 workflow 之上插入「预览-确认」两个步骤：

1. Resolve the active report and target section.（不变）
2. Confirm 写回方向已决定。
3. Update `brief.yaml` / `sources.*` / 图表等非 `.tex` 内容（如有，直接改）。
4. 按 diff 宏规则改 `sections/*.tex`：新增用 `\reportadd`，删除用 `\reportdel`，替换用 `\reportchg`。
5. Global consistency sweep：用同样的 diff 宏表达跨章节调整。
6. Re-render：
   ```bash
   python3 ~/.agents/skills/report/_shared/scripts/render_report.py /absolute/path/to/report-dir
   ```
7. 预览阶段：把「已经在 `report.pdf` / `report.md` 里可看到的 diff 摘要」告诉用户，等待用户回复「接受修改」或等价表达。不要在用户确认前就清理标记。
8. 用户确认后，清理 diff 标记：
   ```bash
   python3 ~/.agents/skills/report/_shared/scripts/accept_edits.py /absolute/path/to/report-dir --dry-run
   python3 ~/.agents/skills/report/_shared/scripts/accept_edits.py /absolute/path/to/report-dir
   ```
   `--dry-run` 给出将被改写的文件清单；正式执行会把 `sections/*.tex` 里的宏清掉并在 `build/accept-edits-backup-<timestamp>/sections/` 下写备份。如只接受单章，追加 `--section <section-file>.tex`。
9. 再次 re-render 并 self-check：
   ```bash
   python3 ~/.agents/skills/report/_shared/scripts/render_report.py /absolute/path/to/report-dir
   ```

## 用户确认信号

只有用户主动发出「接受修改 / 接受 / accept / 确认 / 同意」之类的信号，才能执行第 8 步。下列情形一律不视为确认：

- 用户只说「好的」「收到」「嗯」等模糊应答。
- 用户追问 diff 内容本身。
- 用户要求对某一处回退或继续改动：此时继续停留在 diff 模式，按新要求再加一轮 `\reportadd` / `\reportdel` / `\reportchg`，或直接修改尚未接受的宏参数。
- 用户要求对接受范围做裁剪（例如「只接受第 4 节的改动」）：使用 `accept_edits.py --section <section-file>.tex` 只接受目标章节；仍需确认该局部接受不会破坏 global consistency sweep。

## 接受范围与原子性

`accept_edits.py` 默认对整份报告做「全部接受」：扫描 `sections/*.tex`，把所有匹配到的 `\reportadd` / `\reportdel` / `\reportchg` 一次性消化。也可以通过 `--section <section-file>.tex` 只接受一个章节。默认全部接受的原因有二：

- 单次修改通常是一致的：写回时已经按讨论范围聚焦，部分接受容易打破 global consistency sweep 的前提。
- 宏级别的部分接受等价于二次编辑，直接继续在 diff 模式下调整比拆分工具更清晰。

执行前如需人工核对，先跑 `--dry-run`，它只列出文件名不动源。

## 失败与恢复

- 若 `accept_edits.py` 因为花括号不平衡而报错，检查目标 `.tex` 里 diff 宏的参数是否闭合；常见原因是手工编辑把 `\reportadd{...}` 的右括号误删。
- 若接受后渲染出现回归，从 `build/accept-edits-backup-<timestamp>/sections/` 复制回 `sections/` 即可恢复上一版。
- 备份目录按时间戳命名，重复执行不会覆盖旧备份。

## 与 `report-debate` / `report-audit` 的关系

- `report-debate` 的「争议与裁决」写回默认直接覆盖；若用户希望先预览，可显式要求进入 diff 模式，然后沿用本协议的三条宏与 `accept_edits.py`。
- `report-audit` 产生的修复建议本身不写回；若后续转给 `report-update`，仍按本协议执行。

## 自检

写回并渲染 `report.pdf` / `report.md` 后，执行 accept 之前至少扫一遍：

- 每处 `\reportadd` 是否真在加内容，而不是把本该删除的旧内容写回。
- 每处 `\reportdel` 是否真在删除，而不是误标本该保留的正文。
- 每处 `\reportchg{a}{b}` 的 `a` 确实是被替换的原文，`b` 是期望的新文；避免把两段不相关内容塞进同一条。
- diff 范围是否与本次讨论范围一致；范围外的 diff 应立即去掉或说明原因。

只有这一轮自检通过，才把 diff 结果呈给用户等待确认。
