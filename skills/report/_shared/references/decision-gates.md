# Report Decision Gates

这张表定义 `report` family 里哪些动作可以自动执行，哪些动作必须停下来问用户。默认原则很简单：

- 机械动作可以自动执行
- 方向性选择必须由用户拍板
- 一旦涉及结构、立场、边界、写法强度或写回范围，就不能代理替用户决定

## Decision Gate Table

| 决策点 | 触发条件 | 可以自动做的事 | 不得自动决定的事 | Skill |
| --- | --- | --- | --- | --- |
| 报告类型与使命 | 新报告同时像项目文档、研究说明、教学讲义或混合稿 | 生成候选结构、准备模板 | 最终报告类型、主叙事、文档使命 | `report-init` |
| 主要受众 | 同时可能面向执行者、学生、审阅者或混合读者 | 根据上下文给出受众建议 | 最终优先受众与解释深度 | `report-init`, `report-update` |
| 章节骨架 | 存在两套以上合法章节结构 | 给出 1--2 套候选目录 | 最终章节顺序与哪些章节被保留/压缩 | `report-init` |
| brainstorming 讨论目标 | 用户说“先讨论”，但问题仍然过宽或过散 | 归纳现有章节、列出候选问题 | 最终要讨论的核心问题、目标章节、讨论边界 | `report-brainstorming` |
| brainstorming 结论去向 | 讨论结束后可能进入普通改写、争议裁决或继续搁置 | 总结候选方向与推荐路线 | 是否立即进入 `report-update`、是否升级到 `report-debate` | `report-brainstorming` |
| repo 现状渗透范围 | 当前实现、里程碑或阻塞开始扩散到多个章节 | 提示这些内容应集中到 `项目进度` | 是否允许在其他章节展开 repo 现状 | `report-init`, `report-brainstorming`, `report-update`, `report-audit` |
| `项目进度` 更新范围 | 更新内容可能改动当前状态、里程碑或阻塞 | 草拟进度条目与状态摘要 | 哪些状态算“已完成”、哪些仍属于计划 | `report-update`, `report-audit` |
| 概念写回强度 | 某个概念可以轻改、重写、拆节或改 framing | 准备候选改法 | 是否大改结构、是否把某节改成另一种写法 | `report-update` |
| 证据层归类 | 事实、设计意图、外部资料、综合判断混在一起 | 标记冲突与候选归类 | 最终正文用哪一层来承载该判断 | `report-update`, `report-audit`, `report-debate` |
| 全局一致性扫面 | 某次改写会影响术语、缩写、摘要、图注或章节间引用 | 列出受影响位置与建议同步项 | 哪些概念需要全局改名、哪些旧表述保留 | `report-update` |
| 视觉策略 | 一节内容既可以画图，也可以拆成表或段落 | 建议图表类型与位置 | 最终采用哪种视觉表达及其信息重点 | `report-init`, `report-update` |
| 审计修复顺序 | 审计发现多类问题并存 | 生成 gap matrix 与修复顺序建议 | 先修结构、先修风格、先修证据，还是先修进度章节 | `report-audit` |
| 升级到 debate | 一段话的问题可能是“观点有争议”而非“写得不够清楚” | 标记 debate 候选点 | 是否进入 `report-debate` | `report-brainstorming`, `report-update`, `report-audit` |
| debate 命题 | 同一段可以按多种方式命题 | 准备候选命题和对比集 | 最终命题、不可变前提、比较对象 | `report-debate` |
| debate 回写范围 | 裁决结果可能只改一段、一个小节或全节 | 生成回写骨架和局部改写草案 | 最终改写范围与是否联动相邻章节 | `report-debate` |
| 编译问题修复策略 | 消除 warning 需要改变表格布局、删减内容或移动图表 | 列出 warning 与受影响文件 | 如何调整内容布局以清理 warning；是否把 warning 视为可发布状态（不允许） | `report-init`, `report-update`, `report-debate`, `report-audit` |
| 发布就绪判断 | 报告结构已成形，但风格、证据、进度、双产物同步或可执行性仍可能不足 | 给出 readiness judgment 和剩余阻塞 | 是否把当前 `report.pdf` / `report.md` 视为下游执行依据 | `report-audit` |

补充规则：warning 本身不是合法选项；如果清理 warning 需要改内容布局，必须问用户“怎么改”。

## Fast Rule Of Thumb

只要下一步会改变以下任一项，就应该停下来问用户：

1. 报告到底是什么
2. 报告主要给谁看
3. 报告正在主张什么
4. 报告要写得多强、多保守
5. 当前实现信息是否要扩散到正文
6. 哪条改写路线会变成最终写回结果

## 可以自动做的动作

以下动作默认不需要用户拍板：

- 生成 LaTeX 模板
- 重新渲染 `report.pdf` 与 `report.md`
- 生成 `compile-review.md`
- 生成 `self-check.md`
- 收集候选资料
- 读取目标章节
- 准备候选写法、候选命题、候选图表

## 触发 gate 时的输出模式

默认按这个结构停下来问：

1. 当前必须决定什么
2. 有哪 2--3 条合法路径
3. 每条路径的主要代价是什么
4. 建议走哪一条

不要只问一个空泛问题，也不要把重要分支藏在默认值里。
