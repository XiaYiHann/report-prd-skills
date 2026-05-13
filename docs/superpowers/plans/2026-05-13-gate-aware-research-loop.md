# Gate-Aware Research Loop 实现计划

> **给执行者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐步实现此计划。步骤使用复选框（`- [ ]`）语法以便跟踪。

**目标：** 将现有 epoch research loop 升级为 gate-aware 执行协议，使 `TASK_QUEUE.yaml`、`NEXT_ACTION.md`、run report、`update_state.py`、audit/insight 与 stale hash 检查共同形成可验证的研究执行闭环。

**架构：** 保留现有 manifest-driven 架构，继续让 Codex / Claude Code 作为 executor。本计划先扩展 `epoch_v1_manifest.yaml` 和共享模板，再让 `update_state.py` 支持 gate-aware transition，随后补 controller stale hash、audit/insight 状态文件与 README/skill 文档。所有行为通过 pytest fixture 验证，不引入 backend、数据库或常驻服务。

**技术栈：** Python 3、PyYAML、pytest、git CLI、现有 `skills/research-*` 脚本。

**Report 对齐：**
- **对应章节：** N/A，当前仓库没有 `docs/report` 工作区。
- **证据层：** 本计划产生的代码、模板和测试属于 `repo-observed fact`；设计取舍仍以 spec 的 `design intent` / `report synthesis` 为准。
- **状态追踪：** 当前不更新 report。若后续创建 report，应在“执行协议”“审计门禁”“证据链管理”“失败分诊与负结果沉淀”章节记录本计划的 commit SHA、测试证据和剩余风险。

**依赖关系图：**

```text
任务 1 ──→ 任务 2 ──→ 任务 3 ──→ 任务 5
   │          │          │
   │          └────────→ 任务 4 ──┘
   └──────────────────→ 任务 6
```

---

## Report 对齐预检

- **Scope match:** spec 明确当前仓库无 report 工作区，本计划不新增 report 编辑任务。
- **Risk coverage:** spec 的主要风险是 schema 真源分裂、一次性改动过大、failed execution 被误判为 falsification。本计划通过 manifest-first、分任务提交、failure triage enum、gate transition 测试覆盖这些风险。
- **Evidence layer consistency:** 当前已有文件和测试按 `repo-observed fact` 处理；本计划新增行为在完成前属于 `design intent`，完成并测试通过后才可作为 `repo-observed fact`。
- **Report update completeness:** 当前无 progress/risk report 文件可更新；计划末尾保留未来 report 更新要求，不创建虚假 report。

## 文件结构

- 修改：`skills/research-init/_shared/schema/epoch_v1_manifest.yaml`
  - 职责：声明 gate-aware queue、run report、audit/insight/human review 文件和字段。
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
  - 职责：生成 gate-aware `TASK_QUEUE.yaml`、`NEXT_ACTION.md`、run report skeleton，并提供 schema helper。
- 修改：`skills/research/scripts/update_state.py`
  - 职责：支持 gate-aware task/gate 状态流转和 failure triage。
- 修改：`skills/research/scripts/research_loop.py`
  - 职责：增加 PRD/SPEC/PLAN/TASK_QUEUE/NEXT_ACTION hash stale 检查的 deterministic helper。
- 修改：`skills/research-audit/scripts/audit_checks.py`
  - 职责：校验 gate-aware evidence、audit queue、mock claim boundary。
- 修改：`README.md`、`skills/research/SKILL.md`、`skills/research-audit/SKILL.md`
  - 职责：记录 gate-aware 协议和失败分诊边界。
- 创建：`docs/research/agent/FAILURE_TRIAGE_POLICY.md`
  - 职责：定义失败分诊规则，供 executor 和 audit 引用。
- 创建：`tests/test_task_queue_gate_transitions.py`
- 创建：`tests/test_update_state_gate_flow.py`
- 创建：`tests/test_stale_hash_detection.py`
- 创建：`tests/test_next_action_generation.py`
- 修改：`tests/test_epoch_schema_validation.py`
- 修改：`tests/test_audit_checks.py`

---

### 任务 1: Gate-Aware Manifest 与模板合同

**Harness（测试框架）:**

- **范围：** 扩展 manifest 和 workspace 模板，使新 epoch 默认包含 gate-aware queue 字段、audit/insight/human-review 文件入口和 run report 必填字段。不修改 `update_state.py` 的状态流转逻辑。
- **前置条件：** spec 文件 `docs/superpowers/specs/2026-05-13-gate-aware-research-loop-design.md` 已存在。
- **测试入口：** `pytest tests/test_epoch_schema_validation.py tests/test_next_action_generation.py -v`
- **通过标准：** 新增和既有 schema/template 测试通过；`init_workspace()` 生成的 `V0/TASK_QUEUE.yaml` 含 `current_gate/current_task/gates/tasks`；`NEXT_ACTION.md` 含 Active Task、Forbidden Actions、Harness、Completion Contract、If Blocked。
- **失败恢复：** `git reset --hard HEAD~1`
- **依赖：** 无。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`skills/research-init/_shared/schema/epoch_v1_manifest.yaml`
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 创建：`tests/test_next_action_generation.py`
- 修改：`tests/test_epoch_schema_validation.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: manifest 声明 `TASK_QUEUE.yaml` 必填字段 `template_version`、`version`、`queue_status`、`current_gate`、`current_task`、`gates`、`tasks`。
- [ ] 行为 2: manifest 声明 gate status enum 为 `pending`、`active`、`audit_required`、`audit_failed`、`passed`、`blocked`、`falsified`。
- [ ] 行为 3: manifest 声明 task status enum 为 `pending`、`active`、`completed`、`blocked`、`failed_execution`、`failed_harness`、`skipped`。
- [ ] 行为 4: 初始化 workspace 时 `TASK_QUEUE.yaml` 默认包含一个 active gate 和一个 active PRD task。
- [ ] 行为 5: `NEXT_ACTION.md` 渲染 active gate/task、allowed files、forbidden actions、harness、completion contract、blocked protocol。
- [ ] 行为 6: `NEXT_ACTION.md` 在没有 active task 时生成 blocked 指令，而不是空白指令。

**接口合同（Interface Contract）:**

```python
from pathlib import Path
from typing import Any

TASK_STATUSES: set[str]
GATE_STATUSES: set[str]

def default_gate_aware_task_queue(version: str) -> dict[str, Any]:
    """Return the initial gate-aware TASK_QUEUE.yaml payload for a new epoch."""

def active_task_from_gate_queue(queue: dict[str, Any]) -> dict[str, Any] | None:
    """Return the current active task from a gate-aware task queue."""

def render_next_action(task: dict[str, Any] | None, queue: dict[str, Any], version: str) -> str:
    """Render NEXT_ACTION.md for the active task or a blocked no-active-task state."""

def validate_gate_queue_shape(queue: dict[str, Any]) -> list[str]:
    """Return human-readable schema issues for gate-aware TASK_QUEUE.yaml."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_next_action_generation.py`，并在 `tests/test_epoch_schema_validation.py` 中补充 gate-aware queue 校验测试。

```python
#!/usr/bin/env python3
"""Gate-aware NEXT_ACTION and TASK_QUEUE template tests."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class NextActionGenerationTests(unittest.TestCase):  # noqa: F405
    def test_init_workspace_writes_gate_aware_task_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")

        self.assertEqual(queue["current_gate"], "G0")
        self.assertEqual(queue["current_task"], "T_G0_001")
        self.assertEqual(queue["gates"][0]["gate_id"], "G0")
        self.assertEqual(queue["gates"][0]["status"], "active")
        self.assertEqual(queue["gates"][0]["audit"]["status"], "pending")
        self.assertEqual(queue["tasks"][0]["task_id"], "T_G0_001")
        self.assertEqual(queue["tasks"][0]["status"], "active")

    def test_next_action_contains_single_step_execution_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            next_action = (research_dir / "V0" / "NEXT_ACTION.md").read_text(encoding="utf-8")

        self.assertIn("## Active Task", next_action)
        self.assertIn("- Gate: G0", next_action)
        self.assertIn("- Task ID: T_G0_001", next_action)
        self.assertIn("## Forbidden Actions", next_action)
        self.assertIn("Do not modify Research Direction", next_action)
        self.assertIn("## Harness", next_action)
        self.assertIn("## Completion Contract", next_action)
        self.assertIn("## If Blocked", next_action)

    def test_next_action_blocks_when_no_active_task_exists(self) -> None:
        queue = {
            "template_version": "epoch_v1",
            "version": "V0",
            "queue_status": "blocked",
            "current_gate": None,
            "current_task": None,
            "gates": [],
            "tasks": [],
        }

        rendered = render_next_action(None, queue, "V0")

        self.assertIn("NO ACTIVE TASK", rendered)
        self.assertIn("Do not invent a task", rendered)
```

运行：`pytest tests/test_next_action_generation.py -v`

预期：FAIL，失败原因是 gate-aware helper 或字段尚不存在。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_next_action_generation.py -v
```

**必须确认：**
- 测试失败。
- 失败原因是缺少 gate-aware queue/NEXT_ACTION 行为，不是 import typo。
- 没有语法错误。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- 更新 manifest 的 TASK_QUEUE 和 run report required fields。
- 在 `research_workspace.py` 中新增 gate-aware helper。
- 初始化 `V0/TASK_QUEUE.yaml` 时使用 `default_gate_aware_task_queue("V0")`。
- `write_next_action_from_task_queue()` 或等价 helper 使用 `render_next_action()`。

运行：

```bash
pytest tests/test_next_action_generation.py tests/test_epoch_schema_validation.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_next_action_generation.py tests/test_epoch_schema_validation.py tests/test_research_init_scaffold.py -v
```

**必须确认：**
- 新增测试通过。
- 初始化 scaffold 测试仍通过。
- 输出无错误。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research-init/_shared/schema/epoch_v1_manifest.yaml \
  skills/research-init/_shared/scripts/research_workspace.py \
  tests/test_next_action_generation.py \
  tests/test_epoch_schema_validation.py
git commit -m "feat(research): add gate-aware epoch templates"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] 每个行为清单项都有测试覆盖。
- [ ] 接口签名与合同一致。
- [ ] 没有实现 update_state transition 或 stale hash，避免越界。
- [ ] 既有 scaffold 行为未被破坏。

---

### 任务 2: Gate-Aware update_state 状态流转

**Harness（测试框架）:**

- **范围：** 修改 `update_state.py`，让 task outcome 驱动 gate-aware queue transition；不实现 research_loop stale hash，也不实现 audit checker 的完整语义。
- **前置条件：** 任务 1 已提交，初始化 workspace 已生成 gate-aware `TASK_QUEUE.yaml`。
- **测试入口：** `pytest tests/test_update_state_gate_flow.py tests/test_update_state_evidence.py -v`
- **通过标准：** completed task 不直接 passed gate；同 gate 下一个 pending task 被激活；gate 全部 task completed 且 audit required 时进入 `audit_required`；`failed_execution`/`failed_harness` 不触发 falsification。
- **失败恢复：** `git reset --hard HEAD~1`
- **依赖：** 任务 1。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`skills/research/scripts/update_state.py`
- 创建：`tests/test_update_state_gate_flow.py`
- 修改：`tests/test_update_state_evidence.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: `--status completed` 支持 gate-aware queue，并兼容 legacy `done` alias。
- [ ] 行为 2: task completed 后，如果同 gate 仍有 pending task，只激活下一 task，gate 仍为 active。
- [ ] 行为 3: gate 内全部 task completed 且 audit.required=true 时，gate status 变为 `audit_required`，queue status 变为 `audit_required`。
- [ ] 行为 4: `failed_execution` 标记 task，gate status 变为 `blocked`，failure class 记录到 run report。
- [ ] 行为 5: `failed_harness` 标记 task，gate status 变为 `blocked` 或 `audit_required`，但不写 `falsified`。
- [ ] 行为 6: `research_falsification_candidate` 只能作为 failure class 记录，并触发 audit required；不能直接写 confirmed falsification。

**接口合同（Interface Contract）:**

```python
from pathlib import Path
from typing import Any

VALID_STATUSES: set[str]
VALID_FAILURE_CLASSES: set[str]

def normalize_task_status(status: str) -> str:
    """Map legacy aliases such as done to completed and validate task status."""

def update_gate_aware_task_queue(
    epoch_dir: Path,
    task_id: str,
    status: str,
    gate_id: str | None,
    failure_class: str | None,
) -> dict[str, Any] | None:
    """Update TASK_QUEUE.yaml and return the next active task, if any."""

def evaluate_gate_after_task(queue: dict[str, Any], gate_id: str) -> None:
    """Mutate queue gate status after a task outcome."""

def build_run_report_from_args(epoch_dir: Path, version: str, args: Any) -> dict[str, Any]:
    """Build schema_version 2 run report from CLI arguments."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_update_state_gate_flow.py`。

```python
#!/usr/bin/env python3
"""Gate-aware update_state transition tests."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class UpdateStateGateFlowTests(unittest.TestCase):  # noqa: F405
    def test_completed_task_activates_next_task_without_passing_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue_path = research_dir / "V0" / "TASK_QUEUE.yaml"
            queue = read_yaml(queue_path)
            queue["gates"][0]["tasks"].append({"task_id": "T_G0_002", "status": "pending"})
            queue["tasks"].append({"task_id": "T_G0_002", "gate_id": "G0", "status": "pending"})
            write_yaml(queue_path, queue)

            result = run_cmd([
                "python3", str(UPDATE_STATE_SCRIPT),
                "--repo", str(repo),
                "--task-id", "T_G0_001",
                "--gate-id", "G0",
                "--status", "completed",
                "--executor", "codex",
                "--command", "pytest tests/test_next_action_generation.py -v",
                "--exit-code", "0",
            ], cwd=repo)
            updated = read_yaml(queue_path)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(updated["current_task"], "T_G0_002")
        self.assertEqual(updated["gates"][0]["status"], "active")
        self.assertEqual(updated["tasks"][1]["status"], "active")

    def test_gate_enters_audit_required_after_all_tasks_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)

            result = run_cmd([
                "python3", str(UPDATE_STATE_SCRIPT),
                "--repo", str(repo),
                "--task-id", "T_G0_001",
                "--gate-id", "G0",
                "--status", "completed",
                "--executor", "codex",
                "--command", "pytest tests/test_next_action_generation.py -v",
                "--exit-code", "0",
            ], cwd=repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(queue["queue_status"], "audit_required")
        self.assertEqual(queue["gates"][0]["status"], "audit_required")
        self.assertIsNone(queue["current_task"])

    def test_failed_execution_does_not_falsify_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)

            result = run_cmd([
                "python3", str(UPDATE_STATE_SCRIPT),
                "--repo", str(repo),
                "--task-id", "T_G0_001",
                "--gate-id", "G0",
                "--status", "failed_execution",
                "--failure-class", "execution_failure",
                "--executor", "codex",
                "--command", "python missing.py",
                "--exit-code", "2",
            ], cwd=repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            report = read_yaml(research_dir / "V0" / "runs" / "T_G0_001_report.yaml")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(queue["gates"][0]["status"], "blocked")
        self.assertNotEqual(queue["gates"][0]["status"], "falsified")
        self.assertEqual(report["conclusion"]["failure_class"], "execution_failure")
        self.assertFalse(report["conclusion"]["research_interpretation_allowed"])
```

运行：`pytest tests/test_update_state_gate_flow.py -v`

预期：FAIL，失败原因是 status/failure-class/gate transition 尚未实现。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_update_state_gate_flow.py -v
```

**必须确认：**
- 测试失败。
- 失败原因是 `completed`、`failed_execution` 或 `--failure-class` 不被支持。
- 没有语法错误。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- 将 CLI status 扩展为新枚举，并保留 `done -> completed` 兼容。
- 新增 `--failure-class`。
- 对 gate-aware queue 使用 `task_id` 字段；必要时兼容 legacy `id`。
- run report 输出 `schema_version: 2` 和 `conclusion.failure_class`。
- 不创建 audit queue；只把 gate 标记为 `audit_required`。

运行：

```bash
pytest tests/test_update_state_gate_flow.py tests/test_update_state_evidence.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_update_state_gate_flow.py tests/test_update_state_evidence.py tests/test_next_action_generation.py -v
```

**必须确认：**
- gate transition 测试通过。
- 既有 evidence 测试仍通过。
- `done` legacy 用例仍可工作。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research/scripts/update_state.py \
  tests/test_update_state_gate_flow.py \
  tests/test_update_state_evidence.py
git commit -m "feat(research): make update_state gate-aware"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] `completed` 不直接通过 gate。
- [ ] `failed_execution` 和 `failed_harness` 不产生 falsification。
- [ ] run report 记录 failure class 和 interpretation boundary。
- [ ] 没有实现 controller stale hash 或 audit queue。

---

### 任务 3: Controller Stale Hash 检查

**Harness（测试框架）:**

- **范围：** 在 `research_loop.py` 或共享 helper 中加入 PRD/SPEC/PLAN/TASK_QUEUE/NEXT_ACTION 的 hash stale 检查；不实现完整 LLM/AI 编译器，只实现 deterministic stale detection 与 blocked response。
- **前置条件：** 任务 1 已提交；任务 2 可先行完成但不是本任务的直接前置。
- **测试入口：** `pytest tests/test_stale_hash_detection.py -v`
- **通过标准：** PRD drift 标记 SPEC stale；SPEC drift 标记 PLAN stale；PLAN drift 标记 TASK_QUEUE stale；TASK_QUEUE drift 标记 NEXT_ACTION stale。
- **失败恢复：** `git reset --hard HEAD~1`
- **依赖：** 任务 1。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`skills/research/scripts/research_loop.py`
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 创建：`tests/test_stale_hash_detection.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: `SPEC.yaml.source_prd_hash` 与 `PRD.md` 当前 hash 不一致时返回 `SPEC_STALE`。
- [ ] 行为 2: `PLAN.md` metadata 中的 `source_spec_hash` 与 `SPEC.yaml` 当前 hash 不一致时返回 `PLAN_STALE`。
- [ ] 行为 3: `TASK_QUEUE.yaml.source_plan_hash` 与 `PLAN.md` 当前 hash 不一致时返回 `TASK_QUEUE_STALE`。
- [ ] 行为 4: `NEXT_ACTION.md` metadata 中的 `source_task_queue_hash` 与 `TASK_QUEUE.yaml` 当前 hash 不一致时返回 `NEXT_ACTION_STALE`。
- [ ] 行为 5: stale 状态不会继续执行 active task，而是生成 blocked next action 或 controller blocked summary。

**接口合同（Interface Contract）:**

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(slots=True)
class StaleFinding:
    code: str
    source_path: str
    dependent_path: str
    expected_hash: str | None
    actual_hash: str

def sha256_file(path: Path) -> str:
    """Return sha256 digest for a file."""

def detect_epoch_stale_hashes(epoch_dir: Path) -> list[StaleFinding]:
    """Return stale findings for PRD/SPEC/PLAN/TASK_QUEUE/NEXT_ACTION hash links."""

def write_blocked_next_action_for_stale(epoch_dir: Path, findings: list[StaleFinding]) -> None:
    """Write NEXT_ACTION.md that blocks execution until stale downstream files are regenerated."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_stale_hash_detection.py`。

```python
#!/usr/bin/env python3
"""Stale hash detection tests for gate-aware research loop."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class StaleHashDetectionTests(unittest.TestCase):  # noqa: F405
    def test_prd_drift_marks_spec_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch = research_dir / "V0"
            spec = read_yaml(epoch / "SPEC.yaml")
            spec["source_prd_hash"] = "stale"
            write_yaml(epoch / "SPEC.yaml", spec)

            findings = detect_epoch_stale_hashes(epoch)

        self.assertIn("SPEC_STALE", [finding.code for finding in findings])

    def test_spec_drift_marks_plan_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch = research_dir / "V0"
            plan = epoch / "PLAN.md"
            plan.write_text("---\nsource_spec_hash: stale\n---\n# Plan\n", encoding="utf-8")

            findings = detect_epoch_stale_hashes(epoch)

        self.assertIn("PLAN_STALE", [finding.code for finding in findings])

    def test_blocked_next_action_is_written_for_stale_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch = research_dir / "V0"
            finding = StaleFinding(
                code="SPEC_STALE",
                source_path="PRD.md",
                dependent_path="SPEC.yaml",
                expected_hash="old",
                actual_hash="new",
            )

            write_blocked_next_action_for_stale(epoch, [finding])
            text = (epoch / "NEXT_ACTION.md").read_text(encoding="utf-8")

        self.assertIn("STALE HASH BLOCKER", text)
        self.assertIn("SPEC_STALE", text)
        self.assertIn("Do not execute active tasks", text)
```

运行：`pytest tests/test_stale_hash_detection.py -v`

预期：FAIL，失败原因是 stale helper 尚未实现。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_stale_hash_detection.py -v
```

**必须确认：**
- 测试失败。
- 失败原因是缺少 stale hash helper。
- 没有语法错误。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- 使用现有 `hash_path()` 或新增 `sha256_file()`，不要引入外部依赖。
- 支持 YAML 字段和 Markdown frontmatter 的最小解析。
- 只做 detection 和 blocked next action，不自动 regenerate。

运行：

```bash
pytest tests/test_stale_hash_detection.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_stale_hash_detection.py tests/test_research_loop_controller.py -v
```

**必须确认：**
- stale hash 测试通过。
- legacy controller 测试仍通过。
- 默认控制器没有误执行 stale task。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research/scripts/research_loop.py \
  skills/research-init/_shared/scripts/research_workspace.py \
  tests/test_stale_hash_detection.py
git commit -m "feat(research): detect stale epoch hashes"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] PRD/SPEC/PLAN/TASK_QUEUE/NEXT_ACTION hash 链均有测试。
- [ ] stale 只阻断执行，不自动创建 Vn+1。
- [ ] 没有引入 backend 或 daemon。

---

### 任务 4: Audit Queue、Insight Index 与 Human Review Schema

**Harness（测试框架）:**

- **范围：** 增加 audit queue、insight index、human review request 和 paper claim ledger 的文件模板与 audit checks；不实现 LLM 审稿，不实现 paper generation。
- **前置条件：** 任务 1 已提交；任务 2 完成后可额外验证 audit_required 状态。
- **测试入口：** `pytest tests/test_audit_checks.py tests/test_epoch_schema_validation.py -v`
- **通过标准：** 初始化 epoch 包含或能生成 schema-valid audit/insight/human-review 文件；audit checker 能拒绝 mock artifact 支持 paper claim、missing run report、missing exit code。
- **失败恢复：** `git reset --hard HEAD~1`
- **依赖：** 任务 1；建议在任务 2 后执行。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`skills/research-init/_shared/schema/epoch_v1_manifest.yaml`
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 修改：`skills/research-audit/scripts/audit_checks.py`
- 修改：`tests/test_audit_checks.py`
- 修改：`tests/test_epoch_schema_validation.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: epoch manifest 声明 `AUDIT_QUEUE.yaml`、`HUMAN_REVIEW_REQUESTS.yaml`、`PAPER_CLAIM_LEDGER.yaml`。
- [ ] 行为 2: wiki required files 包含 `insight_index.yaml`，且初始化时生成 machine-readable 空结构。
- [ ] 行为 3: audit checker 对 completed task 缺少 run report 返回 P0 FAIL。
- [ ] 行为 4: audit checker 对 run report 缺少 exit code 返回 P0 FAIL。
- [ ] 行为 5: audit checker 对 mock artifact 支持 paper claim 返回 P0 FAIL。
- [ ] 行为 6: audit result enum 只允许 `pass`、`repair_required`、`human_review_required`、`falsification_confirmed`。

**接口合同（Interface Contract）:**

```python
from pathlib import Path
from typing import Any

AUDIT_RESULT_STATUSES: set[str]

def default_audit_queue(version: str) -> dict[str, Any]:
    """Return empty AUDIT_QUEUE.yaml payload."""

def default_insight_index(version: str) -> dict[str, Any]:
    """Return empty wiki/insight_index.yaml payload."""

def default_human_review_requests(version: str) -> dict[str, Any]:
    """Return empty HUMAN_REVIEW_REQUESTS.yaml payload."""

def check_gate_evidence_completeness(epoch_dir: Path) -> list[Any]:
    """Return audit findings for missing run reports, exit codes, and artifacts."""

def check_paper_claim_ledger(epoch_dir: Path) -> list[Any]:
    """Return audit findings for unsupported or mock-backed paper claims."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

在 `tests/test_audit_checks.py` 添加 schema 和 audit behavior 测试。

```python
class GateAwareAuditChecksTests(unittest.TestCase):  # noqa: F405
    def test_init_workspace_writes_audit_and_review_state_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch = research_dir / "V0"

        self.assertTrue((epoch / "AUDIT_QUEUE.yaml").exists())
        self.assertTrue((epoch / "HUMAN_REVIEW_REQUESTS.yaml").exists())
        self.assertTrue((epoch / "PAPER_CLAIM_LEDGER.yaml").exists())
        self.assertTrue((epoch / "wiki" / "insight_index.yaml").exists())

    def test_audit_fails_completed_task_without_run_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch = research_dir / "V0"
            queue = read_yaml(epoch / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "completed"
            write_yaml(epoch / "TASK_QUEUE.yaml", queue)

            findings = check_gate_evidence_completeness(epoch)

        self.assertIn("missing_run_report", [finding.check_id for finding in findings])
        self.assertTrue(any(finding.severity == "P0" for finding in findings))

    def test_audit_fails_mock_backed_paper_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch = research_dir / "V0"
            write_yaml(epoch / "PAPER_CLAIM_LEDGER.yaml", {
                "schema_version": 1,
                "epoch": "V0",
                "claims": [{
                    "claim_id": "C1",
                    "status": "allowed",
                    "current_evidence": {
                        "run_reports": ["runs/T_G0_001_report.yaml"],
                    },
                }],
            })
            write_yaml(epoch / "runs" / "T_G0_001_report.yaml", {
                "schema_version": 2,
                "anti_mock": {"dataset_type": "mock"},
                "conclusion": {"research_interpretation_allowed": False},
                "command": {"exit_code": 0},
            })

            findings = check_paper_claim_ledger(epoch)

        self.assertIn("mock_evidence_supports_paper_claim", [finding.check_id for finding in findings])
```

运行：`pytest tests/test_audit_checks.py -v`

预期：FAIL，失败原因是文件模板和 audit helper 尚未实现。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_audit_checks.py -v
```

**必须确认：**
- 测试失败。
- 失败原因是 audit/insight/human review 文件或 checker 缺失。
- 没有语法错误。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- 初始化 epoch 时生成四个机器可读文件。
- audit checker 只读文件并返回结构化 findings。
- 不调用 LLM；不生成审稿长文。

运行：

```bash
pytest tests/test_audit_checks.py tests/test_epoch_schema_validation.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_audit_checks.py tests/test_epoch_schema_validation.py tests/test_create_epoch.py -v
```

**必须确认：**
- audit checks 通过。
- create_epoch 仍生成完整 epoch。
- strict schema 未被破坏。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research-init/_shared/schema/epoch_v1_manifest.yaml \
  skills/research-init/_shared/scripts/research_workspace.py \
  skills/research-audit/scripts/audit_checks.py \
  tests/test_audit_checks.py \
  tests/test_epoch_schema_validation.py
git commit -m "feat(research): add gate audit and insight state files"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] audit/insight/human review/paper ledger 均有 schema 测试。
- [ ] mock result 不支持 paper claim。
- [ ] audit helper 不依赖 LLM。
- [ ] 未实现 paper generation 或 Vn+1 自动创建。

---

### 任务 5: Failure Triage Policy 与文档收敛

**Harness（测试框架）:**

- **范围：** 更新 README、research skill 文档、audit skill 文档，并新增失败分诊 policy。只做文档和安装/文档测试，不改状态机代码。
- **前置条件：** 任务 2 和任务 4 已提交，实际行为已经存在。
- **测试入口：** `pytest tests/test_installation_and_docs.py -v`
- **通过标准：** 文档明确 Gate/Task/Harness/Audit/Insight 术语、failure triage、mock/paper boundary、no Vn+1 before closeout；安装与文档测试通过。
- **失败恢复：** `git reset --hard HEAD~1`
- **依赖：** 任务 2、任务 4。
- **证据层：** `repo-observed fact`

**文件:**

- 创建：`docs/research/agent/FAILURE_TRIAGE_POLICY.md`
- 修改：`README.md`
- 修改：`skills/research/SKILL.md`
- 修改：`skills/research-audit/SKILL.md`
- 修改：`tests/test_installation_and_docs.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: README 明确定义 Gate、Task、Harness、Audit、Insight。
- [ ] 行为 2: README 不再把 milestone 作为机器状态术语。
- [ ] 行为 3: FAILURE_TRIAGE_POLICY 定义七类失败并明确 falsification candidate/confirmed 的条件。
- [ ] 行为 4: research skill 指示 executor 每轮只执行 `NEXT_ACTION.md` 的 active task。
- [ ] 行为 5: audit skill 指示 failed_execution/failed_harness 不能视为 research falsification。
- [ ] 行为 6: docs tests 检查关键文件和关键短语存在。

**接口合同（Interface Contract）:**

```python
from pathlib import Path

def assert_doc_contains(path: Path, phrases: list[str]) -> None:
    """Test helper: assert a document contains all required phrases."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

在 `tests/test_installation_and_docs.py` 增加文档断言。

```python
class GateAwareDocsTests(unittest.TestCase):  # noqa: F405
    def test_failure_triage_policy_exists_and_defines_research_falsification_boundary(self) -> None:
        path = REPO_ROOT / "docs" / "research" / "agent" / "FAILURE_TRIAGE_POLICY.md"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        for phrase in [
            "Environment Failure",
            "Execution Failure",
            "Harness Failure",
            "Research Falsification Candidate",
            "Confirmed Research Falsification",
            "Allowed only after adversarial audit",
        ]:
            self.assertIn(phrase, text)

    def test_readme_documents_gate_aware_terms(self) -> None:
        text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in ["Gate", "Task", "Harness", "Audit", "Insight"]:
            self.assertIn(phrase, text)
        self.assertIn("failed_execution", text)
        self.assertIn("failed_harness", text)
```

运行：`pytest tests/test_installation_and_docs.py -v`

预期：FAIL，失败原因是 policy 或短语尚不存在。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_installation_and_docs.py -v
```

**必须确认：**
- 测试失败。
- 失败原因是文档内容缺失。
- 没有语法错误。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- 新增 `FAILURE_TRIAGE_POLICY.md`。
- README 增加术语和 failure triage 小节。
- skill 文档与实际行为一致，不承诺未实现 backend 或自动实验调度。

运行：

```bash
pytest tests/test_installation_and_docs.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_installation_and_docs.py tests/test_audit_checks.py tests/test_update_state_gate_flow.py -v
```

**必须确认：**
- 文档测试通过。
- 文档与 audit/update_state 行为一致。
- 没有把 design intent 写成已实现事实。

- [ ] **步骤 5：提交代码**

```bash
git add docs/research/agent/FAILURE_TRIAGE_POLICY.md \
  README.md \
  skills/research/SKILL.md \
  skills/research-audit/SKILL.md \
  tests/test_installation_and_docs.py
git commit -m "docs(research): document gate-aware failure triage"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] failure triage 七类边界完整。
- [ ] 文档没有承诺未实现的 P3 compiler full automation。
- [ ] mock/paper boundary 清楚。
- [ ] no Vn+1 before closeout 仍然明确。

---

### 任务 6: 全量回归与计划收尾

**Harness（测试框架）:**

- **范围：** 运行全量测试，修复因 gate-aware 升级引入的兼容性问题；不新增新功能。
- **前置条件：** 任务 1-5 已提交。
- **测试入口：** `pytest tests -v`
- **通过标准：** 全量测试通过；`git status --short` 只包含预期计划状态更新或为空；无 TODO/TBD/placeholders。
- **失败恢复：** 对失败修复做最小 patch；若无法修复，记录 blocker，不继续合并。
- **依赖：** 任务 1、任务 2、任务 3、任务 4、任务 5。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：仅允许修改测试失败直接相关文件。
- 修改：`docs/superpowers/plans/2026-05-13-gate-aware-research-loop.md`（标记任务完成状态时使用）。

**行为清单（Behavior List）:**

- [ ] 行为 1: 全量 pytest 通过。
- [ ] 行为 2: legacy controller 测试仍需显式 `--legacy-controller`，且不被 gate-aware 默认行为破坏。
- [ ] 行为 3: create_epoch 生成的新版本满足 manifest。
- [ ] 行为 4: audit checks 对旧 fixture 的期望仍稳定。
- [ ] 行为 5: 文档和 plan 不含 TODO/TBD/placeholders。

**接口合同（Interface Contract）:**

```python
def run_full_regression() -> int:
    """Equivalent verification command: pytest tests -v."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

本任务不新增行为测试；它以全量回归为 harness。若发现未覆盖的回归，先新增最小失败测试到对应测试文件。

运行：

```bash
pytest tests -v
```

预期：若前序任务遗漏兼容性处理，则 FAIL；若已完整，则 PASS。

- [ ] **步骤 2：运行测试确认失败或通过** (Red)

**必须确认：**
- 如果失败，失败原因对应真实回归。
- 如果通过，记录全量测试输出摘要。
- 不接受 flaky 或 skipped core tests 作为完成证据。

- [ ] **步骤 3：编写最小修复** (Green)

> **原则：Plan 不提供实现代码。** 执行者只修复全量回归暴露的问题，不新增 spec 外功能。

运行：

```bash
pytest tests -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests -v
rg -n "TODO|TBD|PLACEHOLDER|待填写" README.md skills docs/superpowers tests
git status --short
```

**必须确认：**
- 全量测试通过。
- placeholder scan 没有命中新增计划/实现中的未处理占位。
- git status 只包含本计划预期文件。

- [ ] **步骤 5：提交代码**

```bash
git add .
git commit -m "test(research): verify gate-aware research loop"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] spec 的 P0/P1/P2/P3 要求均有对应任务或明确保留为后续 open question。
- [ ] 所有新增接口都有测试。
- [ ] 无 backend、数据库、daemon、自动 Vn+1。
- [ ] 全量测试通过。

---

## Quality Gate

每个任务完成前必须满足：

- [ ] 当前任务测试通过。
- [ ] 相关既有回归测试通过。
- [ ] 没有 lint/type/import 错误。
- [ ] 没有 TODO、TBD、placeholder。
- [ ] Harness Pass Criteria 满足。
- [ ] Spec 合规自检通过。
- [ ] 提交信息清晰，且每个任务独立提交。

## Report 进度更新

当前仓库没有 `docs/report`，因此本计划不执行 report 更新。若后续创建 report，必须在完成后补充：

### 1. 更新进度章节

- [ ] 标记 gate-aware research loop 协议升级已完成。
- [ ] 引用任务 1-6 的 commit SHA。
- [ ] 说明与 spec 的偏离。

### 2. 更新风险/下一步章节

- [ ] 记录剩余风险：schema migration、LLM adversarial audit 是否作为补充、P3 compiler 是否设为默认。
- [ ] 记录已缓解风险：failed execution 不再误判为 falsification、mock claim 被 audit 阻断、stale hash 阻断执行。

### 3. 证据层标记

- [ ] 本计划产生的代码/测试 -> `repo-observed fact`。
- [ ] spec 中的设计取舍 -> `design intent` / `report synthesis`。

### 4. 交叉检查

- [ ] 不把 P3 后续增强写成已完成事实。
- [ ] 不把 mock 或未审计 artifact 写成实验结果。

## Task Completion Protocol

每个任务完成后：

1. 对照行为清单和接口合同做 spec 合规自检。
2. 运行任务 harness 和相关回归测试。
3. 提交当前任务。
4. 在本计划文件中标记任务完成状态、日期和 commit SHA。
5. 所有任务完成后，调用 `superpowers:requesting-code-review` 做统一代码质量审查。

## Plan-Level Self Review

- **Spec coverage:** 任务 1 覆盖 manifest/template/NEXT_ACTION；任务 2 覆盖 update_state gate flow；任务 3 覆盖 stale hash；任务 4 覆盖 audit/insight/human review/paper ledger；任务 5 覆盖 failure triage docs；任务 6 覆盖全量回归。
- **Placeholder scan:** 本计划不包含 TODO/TBD/待填写作为执行占位；出现这些词只在禁止项或扫描命令中。
- **Type consistency:** `current_gate/current_task/gates/tasks`、`completed/failed_execution/failed_harness`、`audit_required` 与 spec 一致。
- **Harness completeness:** 每个任务均包含范围、前置条件、测试入口、通过标准、失败恢复、依赖。
- **Atomicity:** 每个任务只有一个主关注点，可独立提交和回滚。
- **TDD compliance:** 每个实现任务均要求先写失败测试，再最小实现，再回归。
- **Report alignment:** 当前无 report 工作区，计划明确 N/A 且不伪造 report 更新。
