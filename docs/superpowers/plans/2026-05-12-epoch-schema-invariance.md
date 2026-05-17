# Epoch Schema Invariance 实现计划

> Historical implementation plan. Superseded by the current RQ-driven pipeline:
> `RESEARCH_SPINE.yaml` is the version-level scheduling truth,
> `rqs/RQxx/TASKS.yaml` is the RQ-local execution truth,
> `TASK_QUEUE.yaml` is a compatibility aggregate view only,
> and version compounding flows through `wiki/` + `closeout.md` into `Vn+1`.

> **给执行者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐步实现此计划。步骤使用复选框（`- [ ]`）语法以便跟踪。

**目标：** 实现严格一致的 epoch schema、结构化执行证据、可失败 audit hard gate，并把 legacy 路径降级为 migration-only。

**架构：** 新增 `epoch_v1_manifest.yaml` 作为 epoch 结构唯一声明源，`research_workspace.py` 通过 manifest 创建和校验 `Vn/`。Codex / Claude Code 继续作为 agent executor，`update_state.py` 负责把执行证据提交为结构化 run report。audit 检查器只读研究工作区并输出 PASS/WARN/FAIL，P0 失败阻断 closeout promotion 和 paper binding。

**技术栈：** Python 3、PyYAML、unittest、git CLI、现有 `skills/research-*` 脚本。

**Report 对齐：**
- **对应章节：** 当前仓库没有 `docs/report` 工作区；本计划对应未来报告中的“架构设计”“执行协议”“审计机制”“证据链管理”章节。
- **证据层：** 本计划完成后的代码与测试属于 `repo-observed fact`；本计划本身和其设计取舍属于 `design intent` / `report synthesis`。
- **状态追踪：** 当前无 report 文件可更新；完成后应在后续报告的进度章节和风险/下一步章节记录实现 commits、剩余风险和证据边界。

**依赖关系图：**

```text
任务 1 ──→ 任务 2 ──→ 任务 3
   │          │
   │          └──────────────→ 任务 5 ──→ 任务 6
   └────────→ 任务 4 ────────┘
```

---

## Report 对齐预检

- **Scope match:** Spec 明确当前仓库没有 `docs/report`，因此本计划不引入 report 编辑任务，只保留完成后的 report 更新指引。
- **Risk coverage:** Spec 已明确不新增独立 backend、不做 Docker/GPU 调度、不做私钥签名；计划通过结构化 run report、artifact hash、git commit 和 audit hard gate 覆盖当前阶段风险。
- **Evidence layer consistency:** 已有脚本和测试按 `repo-observed fact` 处理；新增 manifest、validator、audit、CLI 设计按 `design intent` 逐步实现，任务完成后由测试转为 `repo-observed fact`。
- **Report update completeness:** 当前无 report 工作区，计划末尾保留进度章节与风险/下一步章节的未来更新清单，不在本计划中创建 report。

## 文件结构

- 创建：`skills/research-init/_shared/schema/epoch_v1_manifest.yaml`
  - 职责：声明 epoch schema version、required files、required dirs、wiki files、required YAML fields、allowed extra patterns。
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
  - 职责：加载 manifest；从 manifest 派生 epoch 常量；提供 strict epoch validation helper；保留现有模板生成函数。
- 创建：`skills/research/scripts/create_epoch.py`
  - 职责：在当前版本 closeout 后，从 manifest 和模板工厂创建 `Vn+1/`。
- 修改：`skills/research/scripts/update_state.py`
  - 职责：接收 executor、commands、stdout/stderr、exit code、test output、artifact hash、files changed、dirty tree 等结构化证据。
- 创建：`skills/research-audit/scripts/audit_checks.py`
  - 职责：执行 evidence、paper-binding、carry_forward、epoch schema 等 hard gate 检查。
- 修改：`skills/research-audit/scripts/generate_research_audit.py`
  - 职责：在生成审计文件时调用 audit checks 并输出机器可读结果。
- 修改：`skills/research-spec/scripts/validate_research.py`
  - 职责：继续作为 CLI 包装；实际 validator 仍来自 `research_workspace.py`。
- 修改：`skills/research/scripts/research_loop.py`
  - 职责：epoch workspace 默认只做 epoch contract 检查和 NEXT_ACTION 指引；legacy deterministic controller 需要显式 `--legacy-controller`。
- 修改：`README.md`、`skills/research/SKILL.md`、`skills/research-audit/SKILL.md`
  - 职责：声明 Codex / Claude Code 是 agent executor；系统不新增独立 backend；legacy 仅为 migration 输入。
- 创建：`tests/test_epoch_manifest_contract.py`
- 创建：`tests/test_epoch_schema_validation.py`
- 创建：`tests/test_create_epoch.py`
- 创建：`tests/test_update_state_evidence.py`
- 创建：`tests/test_audit_checks.py`
- 创建：`tests/test_epoch_legacy_boundary.py`
- 修改：`tests/research_workflow_common.py`
  - 职责：新增 `CREATE_EPOCH_SCRIPT`、`UPDATE_STATE_SCRIPT`、`AUDIT_CHECKS_SCRIPT` 常量。
- 修改：`tests/test_research_loop_controller.py`
  - 职责：legacy controller 测试改为显式传入 `--legacy-controller`。

---

### 任务 1: Epoch Manifest 合同与加载器

**Harness（测试框架）:**

- **范围：** 创建 `epoch_v1_manifest.yaml`，并在 `research_workspace.py` 中提供 manifest 加载与派生常量接口。不改 validator 行为，不改 epoch 创建逻辑。
- **前置条件：** 当前 spec 已存在于 `docs/superpowers/specs/2026-05-12-epoch-schema-invariance-design.md`。
- **测试入口：** `pytest tests/test_epoch_manifest_contract.py -v`
- **通过标准：** 3 个测试通过，0 失败；manifest 文件存在；`EPOCH_REQUIRED_FILES` 和 `EPOCH_WIKI_FILES` 从 manifest 派生且包含当前模板要求。
- **失败恢复：** 停止执行，保留 `git diff`；若已提交，使用 `git revert <commit-sha>` 回滚本任务提交。
- **依赖：** 无。
- **证据层：** `repo-observed fact`

**文件:**

- 创建：`skills/research-init/_shared/schema/epoch_v1_manifest.yaml`
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 创建：`tests/test_epoch_manifest_contract.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: manifest 文件声明 `schema_version: epoch_v1`。
- [ ] 行为 2: manifest 声明的 required files 包含 `PRD.md`、`SPEC.yaml`、`PLAN.md`、`STATUS.yaml`、`TASK_QUEUE.yaml`、`NEXT_ACTION.md`、`LOOP_LOG.md`、`GIT_STATE.yaml`、`git_log.md`、`closeout.md`、`PAPER_BINDING_DECISION.md`。
- [ ] 行为 3: manifest 声明的 wiki files 与当前 `EPOCH_WIKI_FILES` 完全一致。
- [ ] 行为 4: `load_epoch_manifest()` 返回可解析字典，且缺失 manifest 时抛出清晰异常。

**接口合同（Interface Contract）:**

```python
from pathlib import Path
from typing import Any

EPOCH_SCHEMA_DIR: Path
EPOCH_MANIFEST_PATH: Path

def load_epoch_manifest(path: Path | None = None) -> dict[str, Any]:
    """Load and validate the epoch manifest file."""

def epoch_manifest_list(key: str, manifest: dict[str, Any] | None = None) -> list[str]:
    """Return a string list from the manifest and reject missing or non-list keys."""

def epoch_required_files(manifest: dict[str, Any] | None = None) -> list[str]:
    """Return required files for every Vn epoch."""

def epoch_wiki_files(manifest: dict[str, Any] | None = None) -> list[str]:
    """Return required wiki files for every Vn epoch."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_epoch_manifest_contract.py`：

```python
#!/usr/bin/env python3
"""Manifest contract tests for strict epoch schema invariance."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SHARED_SCRIPT_DIR = REPO_ROOT / "skills" / "research-init" / "_shared" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPT_DIR))

from research_workspace import (  # noqa: E402
    EPOCH_MANIFEST_PATH,
    EPOCH_REQUIRED_FILES,
    EPOCH_WIKI_FILES,
    epoch_required_files,
    epoch_wiki_files,
    load_epoch_manifest,
)


class EpochManifestContractTests(unittest.TestCase):
    def test_manifest_exists_and_declares_epoch_v1_schema(self) -> None:
        self.assertTrue(EPOCH_MANIFEST_PATH.exists())

        manifest = load_epoch_manifest()

        self.assertEqual(manifest["schema_version"], "epoch_v1")
        self.assertEqual(manifest["epoch_dir_pattern"], r"V\\d+")

    def test_manifest_required_files_match_runtime_constants(self) -> None:
        required = epoch_required_files()

        self.assertEqual(required, EPOCH_REQUIRED_FILES)
        self.assertEqual(
            required,
            [
                "PRD.md",
                "SPEC.yaml",
                "PLAN.md",
                "STATUS.yaml",
                "TASK_QUEUE.yaml",
                "NEXT_ACTION.md",
                "LOOP_LOG.md",
                "GIT_STATE.yaml",
                "git_log.md",
                "closeout.md",
                "PAPER_BINDING_DECISION.md",
            ],
        )

    def test_manifest_wiki_files_match_runtime_constants(self) -> None:
        wiki_files = epoch_wiki_files()

        self.assertEqual(wiki_files, EPOCH_WIKI_FILES)
        self.assertEqual(
            wiki_files,
            [
                "epoch_summary.md",
                "evidence_map.md",
                "positive_signals.md",
                "negative_results.md",
                "failed_paths.md",
                "baseline_landscape.md",
                "literature_notes.md",
                "open_questions.md",
                "next_version_seed.md",
            ],
        )

    def test_missing_manifest_fails_with_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing_manifest.yaml"

            with self.assertRaises(FileNotFoundError) as raised:
                load_epoch_manifest(missing)

        self.assertIn("epoch manifest not found", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
```

运行：`pytest tests/test_epoch_manifest_contract.py -v`

预期：FAIL，失败原因是 `research_workspace` 尚未定义 `EPOCH_MANIFEST_PATH`、`load_epoch_manifest`、`epoch_required_files` 或 `epoch_wiki_files`。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_epoch_manifest_contract.py -v
```

**必须确认：**
- 测试失败。
- 失败原因是 manifest 加载接口不存在或 manifest 文件不存在。
- 没有语法错误。

- [ ] **步骤 3：编写最小实现** (Green)

> **原则：Plan 不提供实现代码。** 执行者根据接口合同和行为清单，从零写最小实现。

实现要求：
- 新增 `skills/research-init/_shared/schema/epoch_v1_manifest.yaml`。
- 在 `research_workspace.py` 中新增 manifest 路径常量和加载函数。
- 将 `EPOCH_REQUIRED_FILES`、`EPOCH_WIKI_FILES` 从 manifest 派生。
- 不改变 `init_research_workspace()` 的输出行为。

运行：`pytest tests/test_epoch_manifest_contract.py -v`

预期：PASS，3 个测试通过。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_epoch_manifest_contract.py -v
pytest tests/test_epoch_research_loop.py -v
```

**必须确认：**
- 新增 manifest 测试通过。
- 现有 epoch scaffold 测试仍通过。
- 输出无错误。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research-init/_shared/schema/epoch_v1_manifest.yaml \
  skills/research-init/_shared/scripts/research_workspace.py \
  tests/test_epoch_manifest_contract.py
git commit -m "feat(research): add epoch v1 manifest contract"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] manifest 是唯一 required epoch 文件列表来源。
- [ ] `Vn/` 必需文件包含 `closeout.md` 和 `PAPER_BINDING_DECISION.md`。
- [ ] 没有改变 legacy scaffold 行为。
- [ ] 没有引入独立 backend 或 runner。

---

### 任务 2: Strict Epoch Schema Validator

**Harness（测试框架）:**

- **范围：** 升级 `validate_epoch_ready()`，使其校验所有 `Vn/` 都符合 manifest，并检查 YAML 必需字段与 wiki 文件集合。不创建新版本，不修改状态文件。
- **前置条件：** 任务 1 已提交。
- **测试入口：** `pytest tests/test_epoch_schema_validation.py -v`
- **通过标准：** 4 个测试通过，0 失败；缺字段、额外 wiki 文件、版本字段不一致、未 closeout 创建下一版本均返回非零状态。
- **失败恢复：** 停止执行，保留 `git diff`；若已提交，使用 `git revert <commit-sha>` 回滚本任务提交。
- **依赖：** 任务 1。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 创建：`tests/test_epoch_schema_validation.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: `epoch-ready` 校验所有 `Vn/`，不只校验 `CURRENT`。
- [ ] 行为 2: `SPEC.yaml` 缺少 manifest 声明的必需字段时失败。
- [ ] 行为 3: `STATUS.yaml.version`、`SPEC.yaml.version`、`TASK_QUEUE.yaml.version` 与目录名不一致时失败。
- [ ] 行为 4: `wiki/` 出现 manifest 未声明的 `.md` 文件时 strict fail。
- [ ] 行为 5: 当前版本未 closeout 时存在更高版本目录，继续失败。

**接口合同（Interface Contract）:**

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass(slots=True)
class EpochSchemaIssue:
    path: str
    message: str
    severity: str = "FAIL"

def validate_epoch_schema(research_dir: Path, strict: bool = True) -> list[EpochSchemaIssue]:
    """Validate every Vn directory against epoch_v1_manifest.yaml."""

def validate_epoch_yaml_fields(epoch_dir: Path, manifest: dict[str, Any]) -> list[EpochSchemaIssue]:
    """Validate required YAML fields for STATUS.yaml, SPEC.yaml, TASK_QUEUE.yaml and run reports."""

def validate_epoch_wiki_set(epoch_dir: Path, manifest: dict[str, Any], strict: bool = True) -> list[EpochSchemaIssue]:
    """Validate required and unexpected wiki markdown files."""
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_epoch_schema_validation.py`：

```python
#!/usr/bin/env python3
"""Strict schema validation tests for every epoch version."""

from __future__ import annotations

import shutil

from research_workflow_helpers import *  # noqa: F403


class EpochSchemaValidationTests(unittest.TestCase):  # noqa: F405
    def test_epoch_ready_rejects_missing_spec_required_field_in_any_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_epoch_closeout_complete(research_dir)
            shutil.copytree(research_dir / "V0", research_dir / "V1")
            (research_dir / "CURRENT").write_text("V1\n", encoding="utf-8")
            spec = read_yaml(research_dir / "V1" / "SPEC.yaml")
            spec["version"] = "V1"
            spec.pop("anti_mock_policy", None)
            write_yaml(research_dir / "V1" / "SPEC.yaml", spec)
            status = read_yaml(research_dir / "V1" / "STATUS.yaml")
            status["version"] = "V1"
            write_yaml(research_dir / "V1" / "STATUS.yaml", status)
            queue = read_yaml(research_dir / "V1" / "TASK_QUEUE.yaml")
            queue["version"] = "V1"
            write_yaml(research_dir / "V1" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V1/SPEC.yaml missing required field: anti_mock_policy", result.stdout)

    def test_epoch_ready_rejects_version_field_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            make_epoch_closeout_complete(research_dir)
            shutil.copytree(research_dir / "V0", research_dir / "V1")
            (research_dir / "CURRENT").write_text("V1\n", encoding="utf-8")
            status = read_yaml(research_dir / "V1" / "STATUS.yaml")
            status["version"] = "V0"
            write_yaml(research_dir / "V1" / "STATUS.yaml", status)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V1/STATUS.yaml version V0 does not match epoch V1", result.stdout)

    def test_epoch_ready_rejects_unexpected_wiki_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            (research_dir / "V0" / "wiki" / "extra_protocol.md").write_text("# Extra\n", encoding="utf-8")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected epoch wiki file: V0/wiki/extra_protocol.md", result.stdout)

    def test_epoch_ready_still_rejects_v1_before_v0_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace(Path(tmp))
            shutil.copytree(research_dir / "V0", research_dir / "V1")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot create next version before current epoch has closed_* status", result.stdout)
```

运行：`pytest tests/test_epoch_schema_validation.py -v`

预期：FAIL，失败原因是 validator 只校验当前版本的部分文件，尚未使用 manifest 校验所有版本和 wiki strict set。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_epoch_schema_validation.py -v
```

**必须确认：**
- 测试失败。
- 失败原因是 strict schema validation 尚未实现。
- 现有 helper import 没有错误。

- [ ] **步骤 3：编写最小实现** (Green)

实现要求：
- 在 manifest 中声明 `yaml_required_fields`。
- `validate_epoch_ready()` 调用 `validate_epoch_schema()`。
- 对所有 `epoch_versions(research_dir)` 执行结构检查。
- `.md` wiki 文件集合必须等于 manifest 声明集合。
- 错误消息必须包含测试断言中的路径和字段名。

运行：`pytest tests/test_epoch_schema_validation.py -v`

预期：PASS，4 个测试通过。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_epoch_manifest_contract.py tests/test_epoch_schema_validation.py tests/test_epoch_research_loop.py -v
```

**必须确认：**
- manifest 测试通过。
- strict schema 测试通过。
- 现有 epoch workflow 测试仍通过。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research-init/_shared/schema/epoch_v1_manifest.yaml \
  skills/research-init/_shared/scripts/research_workspace.py \
  tests/test_epoch_schema_validation.py
git commit -m "feat(research): validate strict epoch schema"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] `epoch-ready` 覆盖所有 `Vn/`。
- [ ] 缺字段、不一致版本、wiki 漂移都 hard fail。
- [ ] 没有创建或修改任何 epoch 状态文件。
- [ ] legacy 路径没有被纳入 epoch 真源校验。

---

### 任务 3: 新版本模板工厂 create_epoch.py

**Harness（测试框架）:**

- **范围：** 新增 `create_epoch.py`，只在当前版本 closeout 后创建 `Vn+1/`，并保证新版本来自统一模板而不是复制旧 task/run 状态。不实现自动 pivot 决策。
- **前置条件：** 任务 1、任务 2 已提交。
- **测试入口：** `pytest tests/test_create_epoch.py -v`
- **通过标准：** 3 个测试通过，0 失败；未 closeout 时创建失败；closeout 后创建的 `V1` 通过 `epoch-ready`；`V1` 不继承 `V0` completed task 状态和 run reports。
- **失败恢复：** 停止执行，保留 `git diff`；若已提交，使用 `git revert <commit-sha>` 回滚本任务提交。
- **依赖：** 任务 1、任务 2。
- **证据层：** `repo-observed fact`

**文件:**

- 创建：`skills/research/scripts/create_epoch.py`
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 修改：`tests/research_workflow_common.py`
- 创建：`tests/test_create_epoch.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: 当前版本不是 `closed_*` 或 `paper_binding_ready` 时，创建 `Vn+1` 返回非零状态。
- [ ] 行为 2: `create_epoch.py --version V1 --from-version V0` 创建 manifest 要求的全部文件和 wiki 文件。
- [ ] 行为 3: 新版本 `STATUS.yaml.version`、`SPEC.yaml.version`、`TASK_QUEUE.yaml.version` 都等于 `V1`。
- [ ] 行为 4: 新版本不复制旧版本 `runs/*.yaml`、completed task queue、paper binding ready 决策。
- [ ] 行为 5: 创建成功后 `CURRENT` 更新为新版本。

**接口合同（Interface Contract）:**

```python
from pathlib import Path

def create_epoch(
    research_dir: Path,
    version: str,
    from_version: str | None = None,
    force: bool = False,
) -> Path:
    """Create a new epoch from templates and approved closeout context."""

def assert_can_create_epoch(research_dir: Path, from_version: str, target_version: str) -> None:
    """Raise ValueError when source epoch is not closed or target version is invalid."""
```

CLI 合同：

```bash
python3 skills/research/scripts/create_epoch.py \
  --repo . \
  --version V1 \
  --from-version V0
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_create_epoch.py`：

```python
#!/usr/bin/env python3
"""Tests for creating same-schema research epochs."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


CREATE_EPOCH_SCRIPT = REPO_ROOT / "skills" / "research" / "scripts" / "create_epoch.py"  # noqa: F405


class CreateEpochTests(unittest.TestCase):  # noqa: F405
    def test_create_epoch_rejects_next_version_before_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)

            result = run_cmd(
                [
                    "python3",
                    str(CREATE_EPOCH_SCRIPT),
                    "--repo",
                    str(repo),
                    "--version",
                    "V1",
                    "--from-version",
                    "V0",
                ],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source epoch V0 is not closed", result.stderr + result.stdout)

    def test_create_epoch_from_closed_v0_creates_manifest_complete_v1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            make_epoch_closeout_complete(research_dir, final_status="closed_stable")

            result = run_cmd(
                [
                    "python3",
                    str(CREATE_EPOCH_SCRIPT),
                    "--repo",
                    str(repo),
                    "--version",
                    "V1",
                    "--from-version",
                    "V0",
                ],
                cwd=repo,
            )
            check = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual((research_dir / "CURRENT").read_text(encoding="utf-8").strip(), "V1")
        self.assertTrue((research_dir / "V1" / "PRD.md").exists())
        self.assertTrue((research_dir / "V1" / "PAPER_BINDING_DECISION.md").exists())

    def test_create_epoch_does_not_copy_completed_queue_runs_or_binding_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            make_epoch_closeout_complete(research_dir, final_status="closed_stable")
            write_yaml(
                research_dir / "V0" / "runs" / "TASK_999_report.yaml",
                {"task": {"version": "V0", "task_id": "TASK_999", "status": "done"}},
            )
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "done"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)
            make_paper_binding_decision(research_dir)

            result = run_cmd(
                [
                    "python3",
                    str(CREATE_EPOCH_SCRIPT),
                    "--repo",
                    str(repo),
                    "--version",
                    "V1",
                    "--from-version",
                    "V0",
                ],
                cwd=repo,
            )
            v1_queue = read_yaml(research_dir / "V1" / "TASK_QUEUE.yaml")
            v1_status = read_yaml(research_dir / "V1" / "STATUS.yaml")
            v1_binding = (research_dir / "V1" / "PAPER_BINDING_DECISION.md").read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(list((research_dir / "V1" / "runs").glob("*_report.yaml")))
        self.assertEqual(v1_queue["version"], "V1")
        self.assertEqual(v1_queue["tasks"][0]["status"], "active")
        self.assertEqual(v1_status["status"], "initialized")
        self.assertIn("paper_binding_ready: false", v1_binding)
```

运行：`pytest tests/test_create_epoch.py -v`

预期：FAIL，失败原因是 `create_epoch.py` 不存在。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_create_epoch.py -v
```

**必须确认：**
- 测试失败。
- 失败原因是 `create_epoch.py` 缺失或 `create_epoch()` 未实现。
- 没有 fixture 或 import 层面的误失败。

- [ ] **步骤 3：编写最小实现** (Green)

实现要求：
- 新增 `create_epoch.py` CLI。
- 在 `research_workspace.py` 复用现有 `epoch_*_template()`、`epoch_*_payload()` 函数创建新版本。
- 新版本 `runs/`、`artifacts/`、`audits/` 为空目录。
- 从旧版本 closeout/wiki 写入新 `PRD.md` 的上下文摘要可以保留，但不能复制旧任务状态。
- 创建成功后写入 `CURRENT`。

运行：`pytest tests/test_create_epoch.py -v`

预期：PASS，3 个测试通过。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_epoch_manifest_contract.py tests/test_epoch_schema_validation.py tests/test_create_epoch.py -v
pytest tests/test_epoch_research_loop.py -v
```

**必须确认：**
- create epoch 测试通过。
- schema validation 测试仍通过。
- 初始化产生的 `V0` 未被破坏。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research/scripts/create_epoch.py \
  skills/research-init/_shared/scripts/research_workspace.py \
  tests/research_workflow_common.py \
  tests/test_create_epoch.py
git commit -m "feat(research): create epochs from invariant templates"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] 新版本只通过模板工厂创建。
- [ ] 新版本结构与 `V0` 同构。
- [ ] 不复制旧版本 run reports 或 paper binding decision。
- [ ] 未 closeout 时不能创建下一版本。

---

### 任务 4: update_state.py 结构化执行证据

**Harness（测试框架）:**

- **范围：** 扩展 `update_state.py` 参数和 run report schema，使 Codex / Claude Code 能提交真实命令、测试、artifact hash、executor 和 git 状态。不实现实验 runner，不自动执行命令。
- **前置条件：** 任务 1 已提交。
- **测试入口：** `pytest tests/test_update_state_evidence.py -v`
- **通过标准：** 3 个测试通过，0 失败；`status=done` 能写入 executor、exit code、commands、test output、artifact hash；缺证据时可被 audit 使用。
- **失败恢复：** 停止执行，保留 `git diff`；若已提交，使用 `git revert <commit-sha>` 回滚本任务提交。
- **依赖：** 任务 1。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`skills/research/scripts/update_state.py`
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 修改：`tests/research_workflow_common.py`
- 创建：`tests/test_update_state_evidence.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: `update_state.py` 接收 `--executor codex|claude-code|manual` 并写入 run report。
- [ ] 行为 2: `--command` 可重复传入并写入 `execution.commands_run`。
- [ ] 行为 3: `--stdout-path`、`--stderr-path`、`--exit-code` 写入 `execution`。
- [ ] 行为 4: `--test-command`、`--test-output-path`、`--tests-passed` 写入 `evidence.tests`。
- [ ] 行为 5: `--artifact path:sha256=<hash>` 写入 `evidence.artifacts`。
- [ ] 行为 6: `--file-changed`、`--dirty-tree-after-task` 写入 git / execution 证据。

**接口合同（Interface Contract）:**

```python
from pathlib import Path
from typing import Any

def parse_artifact_arg(raw: str) -> dict[str, str]:
    """Parse 'path:sha256=<digest>' into {'path': path, 'sha256': digest}."""

def build_run_report_from_args(
    epoch_dir: Path,
    version: str,
    args: Any,
) -> dict[str, Any]:
    """Build the machine-readable run report submitted by an agent executor."""
```

CLI 合同：

```bash
python3 skills/research/scripts/update_state.py \
  --repo . \
  --task-id TASK_001 \
  --status done \
  --executor codex \
  --command "python3 -m pytest tests/test_epoch_manifest_contract.py -v" \
  --stdout-path docs/research/V0/runs/TASK_001.stdout.txt \
  --stderr-path docs/research/V0/runs/TASK_001.stderr.txt \
  --exit-code 0 \
  --test-command "python3 -m pytest tests/test_epoch_manifest_contract.py -v" \
  --test-output-path docs/research/V0/runs/TASK_001.pytest.txt \
  --tests-passed true \
  --artifact docs/research/V0/artifacts/result.json:sha256=abc123 \
  --file-changed skills/research-init/_shared/scripts/research_workspace.py \
  --dirty-tree-after-task false
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_update_state_evidence.py`：

```python
#!/usr/bin/env python3
"""Structured evidence submission tests for update_state.py."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


UPDATE_STATE_SCRIPT = REPO_ROOT / "skills" / "research" / "scripts" / "update_state.py"  # noqa: F405


class UpdateStateEvidenceTests(unittest.TestCase):  # noqa: F405
    def test_update_state_records_executor_commands_exit_code_and_artifact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            runs = research_dir / "V0" / "runs"
            artifacts = research_dir / "V0" / "artifacts"
            runs.mkdir(parents=True, exist_ok=True)
            artifacts.mkdir(parents=True, exist_ok=True)
            stdout_path = runs / "TASK_001.stdout.txt"
            stderr_path = runs / "TASK_001.stderr.txt"
            test_output = runs / "TASK_001.pytest.txt"
            artifact = artifacts / "result.json"
            stdout_path.write_text("pytest passed\n", encoding="utf-8")
            stderr_path.write_text("", encoding="utf-8")
            test_output.write_text("1 passed\n", encoding="utf-8")
            artifact.write_text('{"metric": 1.0}\n', encoding="utf-8")

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "TASK_001",
                    "--status",
                    "done",
                    "--executor",
                    "codex",
                    "--command",
                    "python3 -m pytest tests/test_epoch_manifest_contract.py -v",
                    "--stdout-path",
                    "docs/research/V0/runs/TASK_001.stdout.txt",
                    "--stderr-path",
                    "docs/research/V0/runs/TASK_001.stderr.txt",
                    "--exit-code",
                    "0",
                    "--test-command",
                    "python3 -m pytest tests/test_epoch_manifest_contract.py -v",
                    "--test-output-path",
                    "docs/research/V0/runs/TASK_001.pytest.txt",
                    "--tests-passed",
                    "true",
                    "--artifact",
                    "docs/research/V0/artifacts/result.json:sha256=abc123",
                    "--file-changed",
                    "skills/research-init/_shared/scripts/research_workspace.py",
                    "--dirty-tree-after-task",
                    "false",
                ],
                cwd=repo,
            )
            report = read_yaml(research_dir / "V0" / "runs" / "TASK_001_report.yaml")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["execution"]["executor"], "codex")
        self.assertEqual(report["execution"]["exit_code"], 0)
        self.assertEqual(report["execution"]["commands_run"], ["python3 -m pytest tests/test_epoch_manifest_contract.py -v"])
        self.assertEqual(report["execution"]["stdout_path"], "docs/research/V0/runs/TASK_001.stdout.txt")
        self.assertEqual(report["execution"]["stderr_path"], "docs/research/V0/runs/TASK_001.stderr.txt")
        self.assertTrue(report["evidence"]["tests"]["passed"])
        self.assertEqual(report["evidence"]["tests"]["commands"], ["python3 -m pytest tests/test_epoch_manifest_contract.py -v"])
        self.assertEqual(report["evidence"]["tests"]["output_path"], "docs/research/V0/runs/TASK_001.pytest.txt")
        self.assertEqual(report["evidence"]["artifacts"][0]["path"], "docs/research/V0/artifacts/result.json")
        self.assertEqual(report["evidence"]["artifacts"][0]["sha256"], "abc123")
        self.assertEqual(report["execution"]["files_changed"], ["skills/research-init/_shared/scripts/research_workspace.py"])
        self.assertFalse(report["git"]["dirty_tree_after_task"])

    def test_update_state_rejects_unknown_executor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_workspace(repo)

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "TASK_001",
                    "--status",
                    "done",
                    "--executor",
                    "local-shell",
                ],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_update_state_rejects_malformed_artifact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_workspace(repo)

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "TASK_001",
                    "--status",
                    "done",
                    "--executor",
                    "codex",
                    "--artifact",
                    "docs/research/V0/artifacts/result.json",
                ],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("artifact must use path:sha256=<digest>", result.stderr + result.stdout)
```

运行：`pytest tests/test_update_state_evidence.py -v`

预期：FAIL，失败原因是 `update_state.py` 尚未支持新增证据参数。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_update_state_evidence.py -v
```

**必须确认：**
- 测试失败。
- 失败原因是 CLI 参数未定义或 run report 字段缺失。
- 不是 fixture 初始化错误。

- [ ] **步骤 3：编写最小实现** (Green)

实现要求：
- 扩展 argparse。
- 新增 artifact 参数解析。
- `write_run_report_from_args()` 改为委托 `build_run_report_from_args()`。
- 保持旧参数兼容；未传新证据时仍能写旧格式，但 `done` 的完整性由任务 5 audit 检查。

运行：`pytest tests/test_update_state_evidence.py -v`

预期：PASS，3 个测试通过。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_update_state_evidence.py tests/test_epoch_research_loop.py -v
```

**必须确认：**
- 新证据字段测试通过。
- 现有 epoch workflow 测试仍通过。
- `update_state.py` 未执行任何外部实验命令。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research/scripts/update_state.py \
  skills/research-init/_shared/scripts/research_workspace.py \
  tests/research_workflow_common.py \
  tests/test_update_state_evidence.py
git commit -m "feat(research): record structured task evidence"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] Codex / Claude Code 被记录为 executor。
- [ ] 系统没有新增 local-shell backend。
- [ ] run report 能记录命令、测试、artifact hash、dirty tree。
- [ ] prompt-only scaffold 仍不能自动成为 paper result。

---

### 任务 5: Audit Checks Hard Gate

**Harness（测试框架）:**

- **范围：** 新增 `audit_checks.py` 并接入 `audit-ready` / `paper-binding-ready` 必要路径，使证据缺失、prompt-only 结果、旧 artifact 未 carry_forward 等情况返回 FAIL。不修改研究内容。
- **前置条件：** 任务 2、任务 4 已提交。
- **测试入口：** `pytest tests/test_audit_checks.py -v`
- **通过标准：** 4 个测试通过，0 失败；audit checks CLI 对 P0 FAIL 返回非零；`validate_research --mode audit-ready` 可复用检查结果。
- **失败恢复：** 停止执行，保留 `git diff`；若已提交，使用 `git revert <commit-sha>` 回滚本任务提交。
- **依赖：** 任务 2、任务 4。
- **证据层：** `repo-observed fact`

**文件:**

- 创建：`skills/research-audit/scripts/audit_checks.py`
- 修改：`skills/research-audit/scripts/generate_research_audit.py`
- 修改：`skills/research-init/_shared/scripts/research_workspace.py`
- 创建：`tests/test_audit_checks.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: audit check 返回 `check_id`、`status`、`severity`、`message`、`paths`。
- [ ] 行为 2: completed task 缺少 run report 时 FAIL。
- [ ] 行为 3: run report `status=done` 但缺少 exit code、commands、artifact hash 或 tests evidence 时 FAIL。
- [ ] 行为 4: paper binding 引用 prompt-only scaffold 时 FAIL。
- [ ] 行为 5: paper binding 引用旧版本 artifact 但当前 PRD/SPEC 未声明 carry_forward 时 FAIL。
- [ ] 行为 6: `generate_research_audit.py` 写出 `audit_results.yaml`。

**接口合同（Interface Contract）:**

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(slots=True)
class AuditCheckResult:
    check_id: str
    status: str
    severity: str
    message: str
    paths: list[str] = field(default_factory=list)

def run_audit_checks(research_dir: Path, mode: str = "full") -> list[AuditCheckResult]:
    """Run read-only audit checks for the requested mode."""

def has_blocking_failures(results: list[AuditCheckResult]) -> bool:
    """Return True when a P0 or P1 FAIL should block promotion."""

def write_audit_results_yaml(path: Path, results: list[AuditCheckResult]) -> None:
    """Write machine-readable audit results."""
```

CLI 合同：

```bash
python3 skills/research-audit/scripts/audit_checks.py \
  --research-dir docs/research \
  --mode full \
  --format yaml
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_audit_checks.py`：

```python
#!/usr/bin/env python3
"""Hard-gate audit checks for epoch research workspaces."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


AUDIT_CHECKS_SCRIPT = REPO_ROOT / "skills" / "research-audit" / "scripts" / "audit_checks.py"  # noqa: F405


class AuditChecksTests(unittest.TestCase):  # noqa: F405
    def test_evidence_audit_rejects_done_task_without_run_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "done"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(
                ["python3", str(AUDIT_CHECKS_SCRIPT), "--research-dir", str(research_dir), "--mode", "evidence"],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence.done_task_has_run_report", result.stdout)

    def test_evidence_audit_rejects_done_report_without_exit_code_and_artifact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "done"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)
            write_yaml(
                research_dir / "V0" / "runs" / "TASK_001_report.yaml",
                {
                    "task": {"version": "V0", "task_id": "TASK_001", "status": "done"},
                    "execution": {"executor": "codex", "commands_run": [], "exit_code": None},
                    "evidence": {"tests": {"passed": False, "output_path": None}, "artifacts": []},
                },
            )

            result = run_cmd(
                ["python3", str(AUDIT_CHECKS_SCRIPT), "--research-dir", str(research_dir), "--mode", "evidence"],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence.done_task_has_exit_code", result.stdout)
        self.assertIn("evidence.done_task_has_artifact_hash", result.stdout)

    def test_generate_research_audit_writes_machine_readable_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)

            result = run_cmd(
                [
                    "python3",
                    str(AUDIT_SCRIPT),
                    "--research-dir",
                    str(research_dir),
                    "--date",
                    "2026-05-12",
                    "--mode",
                    "full",
                    "--force",
                ],
                cwd=repo,
            )
            audit_results = research_dir / "V0" / "audits" / "2026-05-12-audit" / "audit_results.yaml"

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(audit_results.exists())
        payload = read_yaml(audit_results)
        self.assertIn("checks", payload)

    def test_audit_ready_fails_when_evidence_hard_gate_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["tasks"][0]["status"] = "done"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "audit-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence.done_task_has_run_report", result.stdout)
```

运行：`pytest tests/test_audit_checks.py -v`

预期：FAIL，失败原因是 `audit_checks.py` 不存在或 `audit-ready` 未接入 hard gate。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_audit_checks.py -v
```

**必须确认：**
- 测试失败。
- 失败原因是 audit checks 功能缺失。
- paper-binding 既有测试仍未被改坏。

- [ ] **步骤 3：编写最小实现** (Green)

实现要求：
- 新增只读 audit checks 引擎。
- `mode=evidence` 至少覆盖 completed task run report 完整性。
- `mode=paper-binding` 可复用现有 `validate_paper_binding_ready()` 的关键规则。
- `generate_research_audit.py` 为 epoch workspace 写入 `Vn/audits/<date>-audit/audit_results.yaml`。
- `validate_audit()` 调用 audit checks 并把 blocking failure 转成 validation error。

运行：`pytest tests/test_audit_checks.py -v`

预期：PASS，4 个测试通过。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_update_state_evidence.py tests/test_audit_checks.py tests/test_epoch_research_loop.py -v
```

**必须确认：**
- evidence 提交测试通过。
- audit hard gate 测试通过。
- paper binding 相关既有规则未退化。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research-audit/scripts/audit_checks.py \
  skills/research-audit/scripts/generate_research_audit.py \
  skills/research-init/_shared/scripts/research_workspace.py \
  tests/test_audit_checks.py
git commit -m "feat(research): add hard-gate audit checks"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] audit checks 对 hard failure 返回非零状态。
- [ ] audit 只读研究工作区，不修改 PRD/SPEC/PLAN。
- [ ] completed task 证据缺失会失败。
- [ ] paper binding 仍拒绝 prompt-only scaffold 和未授权旧 artifact。

---

### 任务 6: Legacy 降级为 migration-only 并修正文档定位

**Harness（测试框架）:**

- **范围：** 将 `research_loop.py` 默认行为改为 epoch contract 模式；legacy deterministic controller 只在显式 `--legacy-controller` 时运行。更新 README 和 skill 文档，明确 Codex / Claude Code 是 agent executor，不新增独立 backend。
- **前置条件：** 任务 2、任务 5 已提交。
- **测试入口：** `pytest tests/test_epoch_legacy_boundary.py tests/test_research_loop_controller.py tests/test_installation_and_docs.py -v`
- **通过标准：** 新增 boundary 测试通过；旧 legacy controller 测试在显式 `--legacy-controller` 下继续通过；文档测试通过。
- **失败恢复：** 停止执行，保留 `git diff`；若已提交，使用 `git revert <commit-sha>` 回滚本任务提交。
- **依赖：** 任务 2、任务 5。
- **证据层：** `repo-observed fact`

**文件:**

- 修改：`skills/research/scripts/research_loop.py`
- 修改：`README.md`
- 修改：`skills/research/SKILL.md`
- 修改：`skills/research-audit/SKILL.md`
- 修改：`tests/test_research_loop_controller.py`
- 创建：`tests/test_epoch_legacy_boundary.py`

**行为清单（Behavior List）:**

- [ ] 行为 1: epoch workspace 默认运行 `research_loop.py` 时不再创建或推进 legacy `state.yaml` / `plans/plan_queue.yaml`。
- [ ] 行为 2: 默认 JSON 输出包含 `controller_mode: epoch_contract`。
- [ ] 行为 3: legacy deterministic controller 必须显式传入 `--legacy-controller`。
- [ ] 行为 4: README 不再把系统描述为脱离 Agent runtime 的独立 backend。
- [ ] 行为 5: skill 文档明确 prompt-only scaffold 不是实验结果，Codex / Claude Code 是执行后端。

**接口合同（Interface Contract）:**

```python
def is_epoch_workspace(research_dir: Path) -> bool:
    """Return True when RESEARCH_DIRECTION.md, CURRENT, and at least one Vn directory exist."""

def epoch_contract_summary(research_dir: Path) -> dict[str, Any]:
    """Return read-only controller summary for Codex / Claude Code executor."""
```

CLI 合同：

```bash
python3 skills/research/scripts/research_loop.py --repo . --json
python3 skills/research/scripts/research_loop.py --repo . --json --legacy-controller
```

- [ ] **步骤 1：编写失败的测试** (Red)

创建 `tests/test_epoch_legacy_boundary.py`：

```python
#!/usr/bin/env python3
"""Boundary tests between epoch contract mode and legacy controller mode."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


class EpochLegacyBoundaryTests(unittest.TestCase):  # noqa: F405
    def test_research_loop_defaults_to_epoch_contract_when_epoch_workspace_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            legacy_state = research_dir / "state.yaml"
            if legacy_state.exists():
                legacy_state.unlink()

            result = run_cmd(
                ["python3", str(RESEARCH_SCRIPT), "--repo", str(repo), "--max-steps", "1", "--json"],
                cwd=repo,
            )
            summary = yaml.safe_load(result.stdout)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(summary["controller_mode"], "epoch_contract")
        self.assertEqual(summary["current_version"], "V0")
        self.assertEqual(summary["execution_backend"]["mode"], "codex_or_claude_code_agent")
        self.assertFalse(legacy_state.exists())

    def test_legacy_controller_requires_explicit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            result = run_cmd(
                [
                    "python3",
                    str(RESEARCH_SCRIPT),
                    "--repo",
                    str(repo),
                    "--max-steps",
                    "1",
                    "--json",
                    "--legacy-controller",
                ],
                cwd=repo,
            )
            summary = yaml.safe_load(result.stdout)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(summary["controller_mode"], "legacy_controller")
        self.assertEqual(summary["execution_backend"]["mode"], "prompt-only")

    def test_readme_names_codex_claude_as_agent_executors_not_backend(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")  # noqa: F405

        self.assertIn("Codex / Claude Code", readme)
        self.assertIn("agent executor", readme)
        self.assertIn("不提供独立常驻 backend", readme)
        self.assertNotIn("backend 空壳", readme)
```

同时修改 `tests/test_research_loop_controller.py` 中所有 legacy controller 调用，统一追加 `--legacy-controller`，因为这些测试验证的是 legacy deterministic controller 的历史行为。

运行：

```bash
pytest tests/test_epoch_legacy_boundary.py tests/test_research_loop_controller.py -v
```

预期：FAIL，失败原因是默认 `research_loop.py` 仍走 legacy controller，且文档尚未更新。

- [ ] **步骤 2：运行测试确认失败** (Red)

运行：

```bash
pytest tests/test_epoch_legacy_boundary.py tests/test_research_loop_controller.py -v
```

**必须确认：**
- 新 boundary 测试失败。
- legacy controller 测试失败原因仅是缺少显式 flag 或输出模式未调整。
- 没有破坏 fixture 初始化。

- [ ] **步骤 3：编写最小实现** (Green)

实现要求：
- `research_loop.py` 新增 `--legacy-controller`。
- 检测到 epoch workspace 且未传 `--legacy-controller` 时，只输出 epoch contract summary。
- legacy controller 旧逻辑保留在显式 flag 后。
- README 和 skill 文档修正项目定位。
- 不删除 legacy 文件生成函数；迁移路径后续仍可能需要。

运行：

```bash
pytest tests/test_epoch_legacy_boundary.py tests/test_research_loop_controller.py -v
```

预期：PASS。

- [ ] **步骤 4：运行测试确认通过** (Green)

运行：

```bash
pytest tests/test_epoch_legacy_boundary.py tests/test_research_loop_controller.py tests/test_installation_and_docs.py -v
pytest tests/ -q
```

**必须确认：**
- boundary 测试通过。
- legacy controller 测试在显式 flag 下通过。
- 全量测试通过。

- [ ] **步骤 5：提交代码**

```bash
git add skills/research/scripts/research_loop.py \
  README.md \
  skills/research/SKILL.md \
  skills/research-audit/SKILL.md \
  tests/test_research_loop_controller.py \
  tests/test_epoch_legacy_boundary.py
git commit -m "feat(research): make epoch contract the default controller mode"
```

- [ ] **步骤 6：验证 spec 合规（自检）**

- [ ] epoch 是默认执行协议。
- [ ] legacy controller 只能显式启用。
- [ ] 文档没有声称存在独立 backend。
- [ ] Codex / Claude Code executor 边界清楚。
- [ ] prompt-only scaffold 不是实验结果。

---

## 统一质量门禁

每个任务完成前必须满足：

- [ ] 当前任务测试通过。
- [ ] 之前任务测试仍通过。
- [ ] 没有 lint/type/import 错误。
- [ ] 没有未完成标记、延期标记或未解释占位内容。
- [ ] Harness 通过标准全部满足。
- [ ] 行为清单均有测试覆盖。
- [ ] 接口合同与实现签名一致。
- [ ] 没有实现 spec 未要求的功能。
- [ ] 已使用描述性 commit message 提交。

## Report 进度更新

当前仓库没有 `docs/report`，因此本计划完成时不修改 report 文件。若后续新增 report，应执行以下更新：

### 1. 更新进度章节

- [ ] 将 “Epoch Schema Invariance” 标记为已实现。
- [ ] 引用任务 1 到任务 6 的 commit SHA。
- [ ] 记录 legacy controller 仍保留为 migration-only 的边界。

### 2. 更新风险/下一步章节

- [ ] 风险矩阵记录“多文件状态更新仍非事务化”。
- [ ] 风险矩阵记录“无 Docker/GPU 调度，真实实验仍由 Agent runtime 执行”。
- [ ] 后续动作清单记录“事务日志或 SQLite 状态提交”。
- [ ] 后续动作清单记录“更强 PRD/SPEC/PAPER 语义一致性检查”。

### 3. 证据层标记

- [ ] 本计划产生的代码/测试标记为 `repo-observed fact`。
- [ ] 本计划中的设计决策标记为 `design intent`。
- [ ] 关于不新增 backend 的取舍标记为 `report synthesis`。

### 4. 交叉检查

- [ ] 进度章节不把未实现的 Docker/GPU 调度写成已实现事实。
- [ ] 风险章节不遗漏状态事务化仍未实现。
- [ ] 证据层不混淆 `design intent` 和 `repo-observed fact`。

## Task Completion Protocol

每个任务完成后：

1. 运行该任务测试入口。
2. 运行所有已完成任务的测试入口。
3. 运行 `pytest tests/ -q`，除非当前任务说明只允许局部验证；若无法全量运行，必须在提交说明中写明原因。
4. 对照行为清单和接口合同自检。
5. 提交代码。
6. 在本计划文档中把该任务标记为完成，并记录 commit SHA。

所有任务完成后：

1. 运行 `pytest tests/ -q`。
2. 使用 `superpowers:requesting-code-review` 做统一代码质量审查。
3. 根据审查意见修复。
4. 再次运行相关测试。
5. 准备合并或交付总结。

## 自检结果

- **Spec coverage:** 任务 1 覆盖 manifest；任务 2 覆盖 strict epoch validation；任务 3 覆盖模板工厂；任务 4 覆盖结构化证据；任务 5 覆盖 audit hard gate；任务 6 覆盖 legacy migration-only 与文档定位。
- **占位风险扫描:** 本计划不包含未完成标记、延期标记或未解释占位内容。
- **Type consistency:** `load_epoch_manifest()`、`validate_epoch_schema()`、`create_epoch()`、`build_run_report_from_args()`、`run_audit_checks()` 的签名在任务间一致。
- **Harness completeness:** 每个任务包含范围、前置条件、测试入口、通过标准、失败恢复、依赖和证据层。
- **Atomicity check:** 每个任务只处理一个主要职责，并以独立 commit 结束。
- **TDD compliance:** 每个任务均要求先写失败测试，再实现最小代码，再运行回归测试。
- **Spec compliance verification:** 每个任务包含步骤 6 自检。
- **Report alignment check:** 当前无 report 工作区，因此只保留未来更新清单，不新增 report 文件。

## 执行完成记录

- 任务 1 已完成：`792c294 feat(research): add epoch v1 manifest contract`
- 任务 2 已完成：`f176754 feat(research): validate strict epoch schema`
- 任务 3 已完成：`5915533 feat(research): create epochs from invariant templates`
- 任务 4 已完成：`a14cab7 feat(research): record structured task evidence`
- 任务 5 已完成：`d5991db feat(research): add hard-gate audit checks`
- 任务 6 已完成：`0af6d58 feat(research): make epoch contract the default controller mode`
