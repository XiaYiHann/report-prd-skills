# Search and Reproduction Gates 实现计划

> Historical implementation plan. Superseded by the current RQ-driven pipeline:
> `RESEARCH_SPINE.yaml` is the version-level scheduling truth,
> `rqs/RQxx/TASKS.yaml` is the RQ-local execution truth,
> `TASK_QUEUE.yaml` is a compatibility aggregate view only,
> and version compounding flows through `wiki/` + `closeout.md` into `Vn+1`.

> **给执行者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐步实现此计划。步骤使用复选框（`- [ ]`）语法以便跟踪。

**目标：** 将 search lock 与 reproduction lock 升级为每个 epoch 的默认前置 Gate，阻止 proposed-method experiment 在 prior-work evidence substrate 尚未锁定前被激活。

**架构：** 保留现有 file-based gate-aware epoch protocol。先扩展 manifest 和 workspace 模板，生成 `search/` 与 `reproduction/` 元数据；再让 `NEXT_ACTION.md` 与 `update_state.py` 强制 search-required task 的 completion evidence；最后用 audit checks 和 README/skill 文档固化 reproduction claim boundary。不新增 backend、数据库、外部复现运行器或真实第三方下载流程。

**技术栈：** Python 3、PyYAML、pytest、现有 `skills/research-*` 脚本、Markdown/YAML 文件协议。

**Report 对齐：**
- **对应章节：** N/A，当前仓库没有 `docs/report` 工作区。
- **证据层：** 本计划产生的代码、模板和测试属于 `repo-observed fact`；spec 中的设计取舍属于 `design intent` / `report synthesis`。
- **状态追踪：** 当前不更新 report。若后续创建 report，应在“研究执行协议”“复现门禁”“证据链管理”“失败分诊”章节记录 commit SHA、测试证据和剩余风险。

**依赖关系图：**

```text
任务 1 ──→ 任务 2 ──→ 任务 4 ──→ 任务 5
   │          │
   └────────→ 任务 3 ────────────┘
```

---

## Report 对齐预检

- **Scope match:** spec 明确当前仓库无 report 工作区，本计划不新增 report 编辑任务。
- **Risk coverage:** spec 的主要风险是过度实现完整复现管理系统、search 无限扩张、reproduction failure 被误判为 hypothesis failure。本计划通过 P0 metadata-only、bounded search policy、failure/status enum 和 audit boundary 测试覆盖这些风险。
- **Evidence layer consistency:** 当前已有 gate-aware 协议按 `repo-observed fact` 处理；本计划新增行为在实现前属于 `design intent`，测试通过并提交后才可作为 `repo-observed fact`。
- **Report update completeness:** 当前无 progress/risk report 文件可更新；计划末尾保留未来 report 更新要求，不创建虚假 report。

## 文件结构

- 修改：`skills/research-init/_shared/schema/epoch_v1_manifest.yaml`
  - 职责：声明 search/reproduction metadata 文件、默认 gate、reproduction enum 和 SPEC 合同字段。
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
  - 职责：生成 `search/`、`reproduction/` 默认文件，渲染默认 `G0_SEARCH_LOCK` / `G1_REPRODUCTION_LOCK` task queue，并校验 reproduction/search 结构。
- 修改：`skills/research/scripts/update_state.py`
  - 职责：拒绝缺失 search logs 的 search-required task completion，保持 gate-aware transition。
- 修改：`skills/research-audit/scripts/audit_checks.py`
  - 职责：审计 reproduction evidence level、search evidence 和 paper claim boundary。
- 修改：`README.md`
  - 职责：将 Literature Policy 改为 Search and Evidence Acquisition Policy，说明 mandatory reproduction gate 和 carry-forward 边界。
- 修改：`skills/research/SKILL.md`
  - 职责：让 `/research` 默认执行 search/reproduction 前置门禁。
- 修改：`skills/research-audit/SKILL.md`
  - 职责：要求 audit 检查 search/reproduction gate 和 claim-support level。
- 创建：`docs/research/agent/SEARCH_POLICY.md`
  - 职责：定义 mandatory search、bounded search、absence evidence 和 repo search。
- 创建：`docs/research/agent/REPRODUCTION_POLICY.md`
  - 职责：定义 reproduction type、status、evidence level 和 failure boundary。
- 创建：`docs/research/agent/REPRODUCTION_AUDIT_POLICY.md`
  - 职责：定义 reproduction audit checklist 与 claim support level。
- 创建：`tests/test_search_reproduction_scaffold.py`
- 创建：`tests/test_search_precondition_enforcement.py`
- 创建：`tests/test_reproduction_index_validation.py`
- 创建：`tests/test_reproduction_audit_boundaries.py`
- 修改：`tests/test_epoch_manifest_contract.py`
- 修改：`tests/test_next_action_generation.py`
- 修改：`tests/test_update_state_gate_flow.py`
- 修改：`tests/test_installation_and_docs.py`

---

### 任务 1: Search/Reproduction Manifest 与默认 Scaffold

**Harness（测试框架）:**

- **范围：** 扩展 epoch manifest 和 init workspace，使新 epoch 默认包含 `search/`、`reproduction/` 元数据文件，以及 `G0_SEARCH_LOCK` 和 `G1_REPRODUCTION_LOCK`。不修改 `update_state.py` completion enforcement，不实现 audit 语义。
- **前置条件：** spec 文件 `docs/superpowers/specs/2026-05-13-search-reproduction-gates-design.md` 已存在；上一轮 gate-aware commit 已在当前分支。
- **测试入口：** `python3 -m pytest tests/test_search_reproduction_scaffold.py tests/test_epoch_manifest_contract.py -v`
- **通过标准：** 初始化 workspace 后存在 search/reproduction metadata 文件；`TASK_QUEUE.yaml` 首个 active gate 是 `G0_SEARCH_LOCK`；`G1_REPRODUCTION_LOCK` 存在但未 active；manifest contract 测试通过。
- **失败恢复：** `git reset --hard HEAD~1`
- **依赖：** 无。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`skills/research-init/_shared/schema/epoch_v1_manifest.yaml`
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 创建：`tests/test_search_reproduction_scaffold.py`
- 修改：`tests/test_epoch_manifest_contract.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: manifest 声明 `search/search_report.md`、`search/web_search_log.yaml`、`search/repo_search_log.yaml`、`search/candidate_baselines.yaml`、`search/candidate_reproductions.yaml`。
- [ ] 行为 2: manifest 声明 `reproduction/REPRODUCTION_INDEX.yaml`、`reproduction/REPRODUCTION_PLAN.md`、`reproduction/REPRODUCTION_DELTA.yaml`。
- [ ] 行为 3: `init_workspace()` 生成的 `TASK_QUEUE.yaml` 以 `G0_SEARCH_LOCK` 为 `current_gate`。
- [ ] 行为 4: `G0_SEARCH_LOCK` 包含 `T_G0_001` web search、`T_G0_002` repo search、`T_G0_003` reproduction set lock。
- [ ] 行为 5: `G1_REPRODUCTION_LOCK` 以 pending gate 存在，并且位于 proposed-method experiment gate 之前。
- [ ] 行为 6: `SPEC.yaml` 默认包含 `reproduction_contract` 与 `filesystem_contract` skeleton。

**接口合同（Interface Contract）:**

```python
from typing import Any

REPRODUCTION_TYPES: set[str]
REPRODUCTION_STATUSES: set[str]
REPRODUCTION_EVIDENCE_LEVELS: set[str]

def default_search_metadata(version: str) -> dict[str, dict[str, Any] | str]:
    """Return default payloads for Vn/search metadata files."""

def default_reproduction_metadata(version: str) -> dict[str, dict[str, Any] | str]:
    """Return default payloads for Vn/reproduction metadata files."""

def default_reproduction_contract(version: str) -> dict[str, Any]:
    """Return the default SPEC.yaml reproduction_contract block."""

def default_filesystem_contract(version: str) -> dict[str, Any]:
    """Return the default SPEC.yaml filesystem_contract block."""

def default_search_reproduction_gates(version: str) -> list[dict[str, Any]]:
    """Return default G0_SEARCH_LOCK and G1_REPRODUCTION_LOCK gate payloads."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_search_reproduction_scaffold.py`：

```python
#!/usr/bin/env python3
"""Search and reproduction epoch scaffold tests."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class SearchReproductionScaffoldTests(unittest.TestCase):  # noqa: F405
    def test_init_workspace_writes_search_and_reproduction_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch_dir = research_dir / "V0"

        expected = [
            epoch_dir / "search" / "search_report.md",
            epoch_dir / "search" / "web_search_log.yaml",
            epoch_dir / "search" / "repo_search_log.yaml",
            epoch_dir / "search" / "candidate_baselines.yaml",
            epoch_dir / "search" / "candidate_reproductions.yaml",
            epoch_dir / "reproduction" / "REPRODUCTION_INDEX.yaml",
            epoch_dir / "reproduction" / "REPRODUCTION_PLAN.md",
            epoch_dir / "reproduction" / "REPRODUCTION_DELTA.yaml",
        ]
        for path in expected:
            self.assertTrue(path.exists(), str(path))

    def test_default_task_queue_starts_with_search_lock_before_reproduction_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")

        self.assertEqual(queue["current_gate"], "G0_SEARCH_LOCK")
        self.assertEqual(queue["current_task"], "T_G0_001")
        gate_ids = [gate["gate_id"] for gate in queue["gates"]]
        self.assertLess(gate_ids.index("G0_SEARCH_LOCK"), gate_ids.index("G1_REPRODUCTION_LOCK"))
        self.assertEqual(queue["gates"][0]["status"], "active")
        self.assertEqual(queue["gates"][1]["status"], "pending")

    def test_default_spec_declares_reproduction_and_filesystem_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            spec = read_yaml(research_dir / "V0" / "SPEC.yaml")

        self.assertTrue(spec["reproduction_contract"]["required"])
        self.assertTrue(spec["reproduction_contract"]["search_required_before_reproduction"])
        self.assertEqual(spec["filesystem_contract"]["state_root"], "docs/research/V0")
        self.assertEqual(spec["filesystem_contract"]["reproduction_workspace_root"], "reproduction/V0")
```

运行：`python3 -m pytest tests/test_search_reproduction_scaffold.py -v`

预期：FAIL，失败原因是 search/reproduction scaffold 或默认 gate 尚不存在。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
python3 -m pytest tests/test_search_reproduction_scaffold.py -v
```

**必须确认：**
- 测试确实失败。
- 失败原因是缺少目标文件、字段或 gate，而不是 import typo。
- 测试没有依赖真实网络、真实外部仓库或当前机器私有状态。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- 在 manifest 中加入 search/reproduction metadata 文件声明。
- 在 `research_workspace.py` 中加入默认 metadata payload helper。
- 调整 `default_gate_aware_task_queue()`，使默认 active gate/task 从 `G0_SEARCH_LOCK` / `T_G0_001` 开始。
- 在默认 `SPEC.yaml` payload 中加入 `reproduction_contract` 与 `filesystem_contract`。
- 不创建根目录 `reproduction/V0/` 可执行 workspace。

运行：

```bash
python3 -m pytest tests/test_search_reproduction_scaffold.py tests/test_epoch_manifest_contract.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
python3 -m pytest tests/test_search_reproduction_scaffold.py tests/test_epoch_manifest_contract.py tests/test_research_init_scaffold.py -v
```

**必须确认：**
- 新 scaffold 测试通过。
- 既有 init scaffold 测试仍通过。
- 输出不包含新增 warning 或 schema regression。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research-init/_shared/schema/epoch_v1_manifest.yaml \
  skills/research-init/_shared/scripts/research_workspace.py \
  tests/test_search_reproduction_scaffold.py \
  tests/test_epoch_manifest_contract.py
git commit -m "feat(research): scaffold search and reproduction gates"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] 每个行为清单项都有测试覆盖。
- [ ] 接口签名与合同一致。
- [ ] 未生成完整可执行 reproduction workspace。
- [ ] 默认 gate 顺序没有绕过 `G0_SEARCH_LOCK` 或 `G1_REPRODUCTION_LOCK`。

---

### 任务 2: NEXT_ACTION Search Precondition 与 Completion Enforcement

**Harness（测试框架）:**

- **范围：** 当 active task 声明 `search.required=true` 时，`NEXT_ACTION.md` 必须渲染 Search Precondition；`update_state.py` 必须在缺少 required search evidence 时拒绝 completed。此任务不实现 reproduction audit。
- **前置条件：** 任务 1 已提交。
- **测试入口：** `python3 -m pytest tests/test_search_precondition_enforcement.py tests/test_next_action_generation.py tests/test_update_state_gate_flow.py -v`
- **通过标准：** search-required task 的 `NEXT_ACTION.md` 包含 Search Precondition；缺少 search logs 时 update_state 返回非零且不完成 task；存在 required logs 时允许进入既有 gate-aware transition。
- **失败恢复：** `git reset --hard HEAD~1`
- **依赖：** 任务 1。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 修改：`skills/research/scripts/update_state.py`
- 创建：`tests/test_search_precondition_enforcement.py`
- 修改：`tests/test_next_action_generation.py`
- 修改：`tests/test_update_state_gate_flow.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: `render_next_action()` 对 `search.required=true` task 渲染 `## Search Precondition`。
- [ ] 行为 2: Search Precondition 明确要求 web search log、repo search log、search report 或 absence evidence。
- [ ] 行为 3: `update_state.py --status completed` 对 search-required task 检查 required search outputs。
- [ ] 行为 4: 缺失 required search outputs 时，命令返回非零，task 保持 active。
- [ ] 行为 5: 存在 required search outputs 时，completion 继续走既有 gate-aware transition。
- [ ] 行为 6: 非 search-required task 不受该检查影响。

**接口合同（Interface Contract）:**

```python
from pathlib import Path
from typing import Any

def task_search_required(task: dict[str, Any]) -> bool:
    """Return True when a task declares search.required=true or search_required=true."""

def required_search_outputs(task: dict[str, Any]) -> list[str]:
    """Return required relative evidence paths for a search-required task."""

def missing_search_outputs(epoch_dir: Path, task: dict[str, Any]) -> list[str]:
    """Return missing required search evidence paths for the task."""

def assert_search_completion_allowed(epoch_dir: Path, task: dict[str, Any]) -> None:
    """Raise SystemExit or ValueError when a search-required task lacks evidence."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_search_precondition_enforcement.py`：

```python
#!/usr/bin/env python3
"""Search precondition rendering and completion enforcement tests."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class SearchPreconditionEnforcementTests(unittest.TestCase):  # noqa: F405
    def test_next_action_renders_search_precondition_for_search_required_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            text = (research_dir / "V0" / "NEXT_ACTION.md").read_text(encoding="utf-8")

        self.assertIn("## Search Precondition", text)
        self.assertIn("Search Required: yes", text)
        self.assertIn("web_search_log.yaml", text)
        self.assertIn("repo_search_log.yaml", text)

    def test_update_state_rejects_completed_search_task_without_search_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_workspace(repo)

            result = run_cmd([
                "python3", str(UPDATE_STATE_SCRIPT),
                "--repo", str(repo),
                "--task-id", "T_G0_001",
                "--gate-id", "G0_SEARCH_LOCK",
                "--status", "completed",
                "--harness-exit-code", "0",
            ], check=False)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing search evidence", result.stderr.lower() + result.stdout.lower())

    def test_update_state_allows_completed_search_task_with_required_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch_dir = research_dir / "V0"
            (epoch_dir / "search" / "web_search_log.yaml").write_text("queries: []\nabsence_claims: []\n", encoding="utf-8")
            (epoch_dir / "search" / "repo_search_log.yaml").write_text("commands: []\nfindings: {}\n", encoding="utf-8")
            (epoch_dir / "search" / "search_report.md").write_text("# Search Report\n\nNo findings yet.\n", encoding="utf-8")

            result = run_cmd([
                "python3", str(UPDATE_STATE_SCRIPT),
                "--repo", str(repo),
                "--task-id", "T_G0_001",
                "--gate-id", "G0_SEARCH_LOCK",
                "--status", "completed",
                "--harness-exit-code", "0",
            ])

            self.assertEqual(result.returncode, 0)
```

运行：`python3 -m pytest tests/test_search_precondition_enforcement.py -v`

预期：FAIL，失败原因是 Search Precondition 或 enforcement 尚未实现。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
python3 -m pytest tests/test_search_precondition_enforcement.py -v
```

**必须确认：**
- 测试失败点对应缺失 search precondition/enforcement。
- 失败不是因为 `UPDATE_STATE_SCRIPT` 路径或 fixture 问题。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- `render_next_action()` 在 task search required 时加入固定 `Search Precondition` 段落。
- task 支持两种兼容字段：`search: {required: true}` 与 legacy `search_required: true`。
- `update_state.py` 在 mark completed 前读取当前 task，并调用 search evidence 检查。
- 缺失 evidence 时输出明确错误，且不修改 `TASK_QUEUE.yaml`。

运行：

```bash
python3 -m pytest tests/test_search_precondition_enforcement.py tests/test_next_action_generation.py tests/test_update_state_gate_flow.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
python3 -m pytest tests/test_search_precondition_enforcement.py tests/test_next_action_generation.py tests/test_update_state_gate_flow.py tests/test_update_state_evidence.py -v
```

**必须确认：**
- search enforcement 测试通过。
- 既有 update_state evidence 测试仍通过。
- 非 search-required task completion 未被误阻断。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research-init/_shared/scripts/research_workspace.py \
  skills/research/scripts/update_state.py \
  tests/test_search_precondition_enforcement.py \
  tests/test_next_action_generation.py \
  tests/test_update_state_gate_flow.py
git commit -m "feat(research): enforce search preconditions"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] Search Precondition 只对 search-required task 出现。
- [ ] 缺失 search evidence 不会推进 gate。
- [ ] 该任务未实现 reproduction audit 或 claim boundary，避免越界。

---

### 任务 3: Reproduction Index Schema 与 Policy 文档

**Harness（测试框架）:**

- **范围：** 新增 reproduction/search policy 文档，并在 workspace helper 中校验 `REPRODUCTION_INDEX.yaml` 的 reproduction type、status、evidence level。此任务不实现 paper claim audit。
- **前置条件：** 任务 1 已提交。
- **测试入口：** `python3 -m pytest tests/test_reproduction_index_validation.py tests/test_installation_and_docs.py -v`
- **通过标准：** policy 文档存在且包含强制检索、bounded search、reproduction failure boundary；invalid reproduction type/status/evidence level 被 validation 拒绝。
- **失败恢复：** `git reset --hard HEAD~1`
- **依赖：** 任务 1。
- **证据层：** `repo-observed fact`

**文件:**

- 创建：`docs/research/agent/SEARCH_POLICY.md`
- 创建：`docs/research/agent/REPRODUCTION_POLICY.md`
- 创建：`docs/research/agent/REPRODUCTION_AUDIT_POLICY.md`
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 创建：`tests/test_reproduction_index_validation.py`
- 修改：`tests/test_installation_and_docs.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: `SEARCH_POLICY.md` 定义 mandatory search 场景、not required 场景、absence evidence、bounded search。
- [ ] 行为 2: `REPRODUCTION_POLICY.md` 定义 reproduction type、status、evidence level，并禁止 environment failure 作为 method failure。
- [ ] 行为 3: `REPRODUCTION_AUDIT_POLICY.md` 定义固定 audit checklist 与 `claim_support_level`。
- [ ] 行为 4: `validate_reproduction_index_shape()` 接受默认空 index。
- [ ] 行为 5: invalid `reproduction_type` 被拒绝。
- [ ] 行为 6: invalid `status` 或 `evidence_level` 被拒绝。

**接口合同（Interface Contract）:**

```python
from pathlib import Path
from typing import Any

def validate_reproduction_index_shape(index: dict[str, Any]) -> list[str]:
    """Return schema issues for reproduction/REPRODUCTION_INDEX.yaml."""

def validate_epoch_search_reproduction_shape(epoch_dir: Path) -> list[str]:
    """Return missing/invalid search and reproduction metadata issues for an epoch."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_reproduction_index_validation.py`：

```python
#!/usr/bin/env python3
"""Reproduction index schema validation tests."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class ReproductionIndexValidationTests(unittest.TestCase):  # noqa: F405
    def test_default_reproduction_index_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            issues = validate_epoch_schema(research_dir / "V0")

        self.assertEqual([], [issue for issue in issues if "reproduction" in issue.lower()])

    def test_invalid_reproduction_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            index_path = research_dir / "V0" / "reproduction" / "REPRODUCTION_INDEX.yaml"
            index = read_yaml(index_path)
            index["items"] = [{
                "repro_id": "R_BAD",
                "short_name": "Bad",
                "reproduction_type": "guessed_baseline",
                "status": "pending",
                "evidence_level": "literature_only",
            }]
            write_yaml(index_path, index)

            issues = validate_epoch_schema(research_dir / "V0")

        self.assertTrue(any("invalid reproduction_type" in issue for issue in issues))

    def test_invalid_reproduction_status_and_evidence_level_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            index_path = research_dir / "V0" / "reproduction" / "REPRODUCTION_INDEX.yaml"
            index = read_yaml(index_path)
            index["items"] = [{
                "repro_id": "R_BAD",
                "short_name": "Bad",
                "reproduction_type": "official_code",
                "status": "paper_disproved",
                "evidence_level": "claim_ready_without_audit",
            }]
            write_yaml(index_path, index)

            issues = validate_epoch_schema(research_dir / "V0")

        self.assertTrue(any("invalid reproduction status" in issue for issue in issues))
        self.assertTrue(any("invalid evidence_level" in issue for issue in issues))
```

运行：`python3 -m pytest tests/test_reproduction_index_validation.py -v`

预期：FAIL，失败原因是 validator 或 policy 文件尚不存在。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
python3 -m pytest tests/test_reproduction_index_validation.py -v
```

**必须确认：**
- 测试失败源于 schema validation 缺失。
- 默认 fixture 仍能初始化，不因任务 1 结构损坏失败。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- 新增 3 个 policy 文档，内容覆盖 spec 中列出的强制规则。
- 在 `research_workspace.py` 中加入 reproduction index validation helper。
- 将该 helper 接入既有 epoch schema validation。
- 文档不得声称当前系统已经执行真实 reproduction，只能定义协议。

运行：

```bash
python3 -m pytest tests/test_reproduction_index_validation.py tests/test_installation_and_docs.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
python3 -m pytest tests/test_reproduction_index_validation.py tests/test_installation_and_docs.py tests/test_epoch_schema_validation.py -v
```

**必须确认：**
- policy 文档测试通过。
- schema validation 没有误伤默认 workspace。
- 文档中没有 `TODO`、`TBD`、`PLACEHOLDER`。

- [ ] **步骤 5：提交代码**

```bash
git add docs/research/agent/SEARCH_POLICY.md \
  docs/research/agent/REPRODUCTION_POLICY.md \
  docs/research/agent/REPRODUCTION_AUDIT_POLICY.md \
  skills/research-init/_shared/scripts/research_workspace.py \
  tests/test_reproduction_index_validation.py \
  tests/test_installation_and_docs.py
git commit -m "feat(research): add reproduction policy contracts"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] Policy 文档覆盖 spec 的 mandatory search 与 reproduction failure boundary。
- [ ] Validator 不要求真实 reproduction 成功。
- [ ] Invalid enum 被拒绝，默认空 index 被接受。

---

### 任务 4: Reproduction Audit Boundary 与 Paper Claim 防线

**Harness（测试框架）:**

- **范围：** 扩展 audit checks，拒绝 `literature_only`、`official_smoke_only`、`failed_but_informative` 或未 audit pass 的 reproduction evidence 支撑 paper claim。此任务不执行真实 reproduction，也不创建 paper 内容。
- **前置条件：** 任务 2 和任务 3 已提交。
- **测试入口：** `python3 -m pytest tests/test_reproduction_audit_boundaries.py tests/test_audit_checks.py -v`
- **通过标准：** audit 能发现 unsupported reproduction evidence 被 paper claim ledger 使用；full/partial claim support 必须有 audit pass；failure classified reproduction 可以作为 discussion/sanity，但不能作为 allowed paper claim。
- **失败恢复：** `git reset --hard HEAD~1`
- **依赖：** 任务 2, 任务 3。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`skills/research-audit/scripts/audit_checks.py`
- 创建：`tests/test_reproduction_audit_boundaries.py`
- 修改：`tests/test_audit_checks.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: allowed paper claim 引用 `literature_only` reproduction evidence 时 audit 失败。
- [ ] 行为 2: allowed paper claim 引用 `official_smoke_only` evidence 时 audit 失败。
- [ ] 行为 3: allowed paper claim 引用 `failed_but_informative` evidence 时 audit 失败。
- [ ] 行为 4: allowed paper claim 引用 reproduction item 但 `audit_status != passed` 时 audit 失败。
- [ ] 行为 5: `claim_support_level: sanity_only` 或 `none` 不能支持 allowed paper claim。
- [ ] 行为 6: partial support 可以用于 claim draft，但必须被标记为 partial，audit 不得静默当作 full。

**接口合同（Interface Contract）:**

```python
from pathlib import Path
from typing import Any

def reproduction_items_by_id(epoch_dir: Path) -> dict[str, dict[str, Any]]:
    """Load reproduction index items keyed by repro_id."""

def check_reproduction_claim_boundaries(epoch_dir: Path) -> list[dict[str, Any]]:
    """Return audit findings for paper claims backed by unsupported reproduction evidence."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_reproduction_audit_boundaries.py`：

```python
#!/usr/bin/env python3
"""Reproduction audit boundary tests."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class ReproductionAuditBoundaryTests(unittest.TestCase):  # noqa: F405
    def test_literature_only_reproduction_cannot_support_allowed_paper_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch_dir = research_dir / "V0"
            index_path = epoch_dir / "reproduction" / "REPRODUCTION_INDEX.yaml"
            index = read_yaml(index_path)
            index["items"] = [{
                "repro_id": "R_LIT",
                "short_name": "LitOnly",
                "reproduction_type": "literature_only_not_executable",
                "status": "planned",
                "evidence_level": "literature_only",
                "audit_status": "passed",
                "claim_support_level": "none",
            }]
            write_yaml(index_path, index)
            ledger = {
                "claims": [{
                    "claim_id": "C1",
                    "status": "allowed",
                    "required_evidence": {"reproductions": ["R_LIT"]},
                    "current_evidence": {"reproductions": ["R_LIT"]},
                }]
            }
            write_yaml(epoch_dir / "PAPER_CLAIM_LEDGER.yaml", ledger)

            findings = run_epoch_audit_checks(research_dir, mode="evidence")

        self.assertTrue(any("unsupported_reproduction_claim_evidence" in str(item) for item in findings))

    def test_reproduction_without_passed_audit_cannot_support_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch_dir = research_dir / "V0"
            index_path = epoch_dir / "reproduction" / "REPRODUCTION_INDEX.yaml"
            index = read_yaml(index_path)
            index["items"] = [{
                "repro_id": "R_FULL",
                "short_name": "Full",
                "reproduction_type": "official_code",
                "status": "full_passed",
                "evidence_level": "official_full_reproduction",
                "audit_status": "pending",
                "claim_support_level": "full",
            }]
            write_yaml(index_path, index)
            write_yaml(epoch_dir / "PAPER_CLAIM_LEDGER.yaml", {
                "claims": [{
                    "claim_id": "C1",
                    "status": "allowed",
                    "current_evidence": {"reproductions": ["R_FULL"]},
                }]
            })

            findings = run_epoch_audit_checks(research_dir, mode="evidence")

        self.assertTrue(any("reproduction_audit_not_passed" in str(item) for item in findings))
```

运行：`python3 -m pytest tests/test_reproduction_audit_boundaries.py -v`

预期：FAIL，失败原因是 audit boundary 尚未实现。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
python3 -m pytest tests/test_reproduction_audit_boundaries.py -v
```

**必须确认：**
- 测试失败点是 audit 未发现 unsupported evidence。
- 失败不是因为 `PAPER_CLAIM_LEDGER.yaml` fixture 缺失或 YAML 写入错误。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- 从 `reproduction/REPRODUCTION_INDEX.yaml` 加载 reproduction items。
- 检查 `PAPER_CLAIM_LEDGER.yaml` 中 allowed claims 的 `current_evidence.reproductions`。
- 对 unsupported evidence level、未通过 audit、claim_support_level 不足生成结构化 finding。
- 不生成或修改 paper 正文。

运行：

```bash
python3 -m pytest tests/test_reproduction_audit_boundaries.py tests/test_audit_checks.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
python3 -m pytest tests/test_reproduction_audit_boundaries.py tests/test_audit_checks.py tests/test_reproduction_index_validation.py -v
```

**必须确认：**
- 新 audit boundary 测试通过。
- 既有 mock-evidence paper claim boundary 测试仍通过。
- audit finding 命名稳定，便于后续文档引用。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research-audit/scripts/audit_checks.py \
  tests/test_reproduction_audit_boundaries.py \
  tests/test_audit_checks.py
git commit -m "feat(research): audit reproduction claim boundaries"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] Literature-only 和 smoke-only reproduction 不支持 allowed claim。
- [ ] Audit 未通过的 reproduction 不支持 allowed claim。
- [ ] 没有把 failed reproduction 自动解释为 paper invalidity 或 hypothesis falsification。

---

### 任务 5: README / Skill 文档与全量回归

**Harness（测试框架）:**

- **范围：** 更新 README 与 research/research-audit skill 文档，说明 Search and Evidence Acquisition Policy、mandatory reproduction gate、carry-forward rule、subagent I/O boundary；运行全量测试。此任务不新增协议行为。
- **前置条件：** 任务 1-4 已提交。
- **测试入口：** `python3 -m pytest tests/test_installation_and_docs.py tests -v`
- **通过标准：** README 不再以 Literature Policy 作为唯一检索政策标题；文档明确 search/reproduction 是 early gate；全量测试通过。
- **失败恢复：** `git reset --hard HEAD~1`
- **依赖：** 任务 1, 任务 2, 任务 3, 任务 4。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`README.md`
- 修改：`skills/research/SKILL.md`
- 修改：`skills/research-audit/SKILL.md`
- 修改：`tests/test_installation_and_docs.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: README 将 `Literature Policy` 升级为 `Search and Evidence Acquisition Policy`。
- [ ] 行为 2: README 明确 `G0_SEARCH_LOCK` 和 `G1_REPRODUCTION_LOCK` 是默认 early gates。
- [ ] 行为 3: README 明确 reproduction failure 必须分类，不能静默忽略或当作 hypothesis falsification。
- [ ] 行为 4: README 说明 `docs/research/Vn/reproduction/` 是 metadata，`reproduction/Vn/` 是可执行 workspace。
- [ ] 行为 5: `skills/research/SKILL.md` 要求 `/research` 不能在 G0/G1 resolved 前激活 proposed-method experiment。
- [ ] 行为 6: `skills/research-audit/SKILL.md` 要求 audit 检查 reproduction claim support level。

**接口合同（Interface Contract）:**

```python
def test_readme_documents_search_and_reproduction_gates() -> None:
    """Docs test asserting policy names and mandatory gate language."""

def test_research_skills_reference_search_and_reproduction_policies() -> None:
    """Docs test asserting skill docs point to the new policy files and boundaries."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

在 `tests/test_installation_and_docs.py` 添加：

```python
def test_readme_documents_search_and_reproduction_gates(self) -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    self.assertIn("Search and Evidence Acquisition Policy", readme)
    self.assertIn("G0_SEARCH_LOCK", readme)
    self.assertIn("G1_REPRODUCTION_LOCK", readme)
    self.assertIn("reproduction failure", readme.lower())
    self.assertIn("docs/research/Vn/reproduction", readme)
    self.assertIn("reproduction/Vn", readme)

def test_research_skills_reference_search_and_reproduction_policies(self) -> None:
    research_skill = (REPO_ROOT / "skills" / "research" / "SKILL.md").read_text(encoding="utf-8")
    audit_skill = (REPO_ROOT / "skills" / "research-audit" / "SKILL.md").read_text(encoding="utf-8")
    self.assertIn("SEARCH_POLICY.md", research_skill)
    self.assertIn("REPRODUCTION_POLICY.md", research_skill)
    self.assertIn("G0_SEARCH_LOCK", research_skill)
    self.assertIn("REPRODUCTION_AUDIT_POLICY.md", audit_skill)
    self.assertIn("claim_support_level", audit_skill)
```

运行：`python3 -m pytest tests/test_installation_and_docs.py -v`

预期：FAIL，失败原因是 README/skill 文档尚未更新。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
python3 -m pytest tests/test_installation_and_docs.py -v
```

**必须确认：**
- 失败源于文档缺少新政策或 gate 名称。
- 没有破坏现有安装文档测试。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- README 用 `Search and Evidence Acquisition Policy` 替换或扩展旧 `Literature Policy`。
- README 只描述协议和边界，不声称已执行真实 reproduction。
- `skills/research/SKILL.md` 指向 `SEARCH_POLICY.md`、`REPRODUCTION_POLICY.md`，并说明 G0/G1 gate ordering。
- `skills/research-audit/SKILL.md` 指向 `REPRODUCTION_AUDIT_POLICY.md`，并说明 claim support level。

运行：

```bash
python3 -m pytest tests/test_installation_and_docs.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
python3 -m pytest tests -v
```

**必须确认：**
- 全量测试通过。
- 若存在环境 warning，只能记录，不得忽略 test failure。
- `rg -n "TODO|TBD|PLACEHOLDER|待填写" README.md skills docs/research/agent tests docs/superpowers/plans/2026-05-13-search-reproduction-gates.md` 不出现本计划新增的未决占位。

- [ ] **步骤 5：提交代码**

```bash
git add README.md \
  skills/research/SKILL.md \
  skills/research-audit/SKILL.md \
  tests/test_installation_and_docs.py
git commit -m "docs(research): document search and reproduction gates"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] README、skill docs 与代码行为一致。
- [ ] 文档没有把未执行的 reproduction 写成 repo fact。
- [ ] 全量测试已运行并记录结果。
- [ ] 当前 plan 的所有任务提交范围清晰可回滚。

---

## Report 进度更新

当前仓库没有 `docs/report/` 工作区，因此本计划完成后不更新 report 文件。若后续创建 report，应执行：

### 1. 更新进度章节

- [ ] 在进度章节记录本计划任务 commit SHA。
- [ ] 将 search/reproduction gates 标注为 `repo-observed fact`，前提是全量测试通过。
- [ ] 如实现与 spec 有偏离，在进度章节记录偏离原因。

### 2. 更新风险/下一步章节

- [ ] 记录剩余风险：未运行真实 reproduction、未下载外部数据、未验证具体领域 baseline。
- [ ] 记录后续 P1：具体 `research-literature` / `research-reproduce` subagent I/O 增强、真实 reproduction workspace task 模板。

### 3. 证据层标记

- [ ] 本计划产生的代码/测试 → `repo-observed fact`
- [ ] 本计划中的设计决策 → `design intent`（仅在 spec 中）
- [ ] 外部 reproducibility checklist → `source claim`（仅在报告引用时）

### 4. 交叉检查

- [ ] 进度章节未把真实 reproduction 结果写成已完成。
- [ ] 风险章节未遗漏 “protocol ready but domain-specific evidence not yet acquired”。
- [ ] 证据层未混淆 `design intent` 和 `repo-observed fact`。

## Task Completion Protocol

每个任务完成后：

1. 运行该任务 Harness 指定测试。
2. 运行相关回归测试。
3. 对照行为清单与接口合同做 spec 合规自检。
4. 提交独立 commit。
5. 更新本计划文件中的任务状态时，必须记录 commit SHA。

全部任务完成后：

1. 运行 `python3 -m pytest tests -v`。
2. 运行 placeholder scan。
3. 使用 `requesting-code-review` 做统一代码质量审查。
4. 处理 review feedback 后再考虑 merge 或后续提交。

## Self-Review

- **Spec coverage:** 任务 1 覆盖 manifest、scaffold、default gates、SPEC contract；任务 2 覆盖 NEXT_ACTION Search Precondition 与 completion enforcement；任务 3 覆盖 policy 文档和 reproduction index schema；任务 4 覆盖 reproduction audit claim boundary；任务 5 覆盖 README/skill docs 和全量回归。
- **Placeholder scan:** 本计划不包含未决 `TODO`、`TBD`、`PLACEHOLDER` 或“稍后实现”。
- **Type consistency:** 计划统一使用 `G0_SEARCH_LOCK`、`G1_REPRODUCTION_LOCK`、`reproduction_contract`、`filesystem_contract`、`claim_support_level`。
- **Harness completeness:** 每个任务包含范围、前置条件、测试入口、通过标准、失败恢复、依赖、证据层。
- **Atomicity check:** 每个任务只有一个主 concern，可独立提交和回滚。
- **TDD compliance:** 每个任务包含 Red、确认失败、Green、确认通过、提交、自检。
- **Report alignment:** 当前无 report 工作区，计划未创建虚假 report 更新。
