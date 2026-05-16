# 测试重构计划

## 现状分析

| 指标 | 数值 |
|------|------|
| 总测试数 | 172 个 |
| 默认执行 | 21 passed, 151 skipped (0.24s) |
| 全量执行 | ~172 tests, 需要数分钟 |
| 核心 monolith | `research_workspace.py`: 9018 行, 213 个函数 |
| Subprocess 调用 | 113 次, 其中 72 次是 `validate_research.py` |

## 核心问题

### 1. 测试金字塔不存在
- **0 个单元测试** — 所有 172 个测试都是 integration（fork subprocess + filesystem）
- **166 个 integration tests** — 其中大部分只是验证"文件有没有被创建"或"YAML 有没有某字段"
- 唯一能跑的 6 个（`test_epoch_manifest_contract`）也是 integration，只是碰巧没被 mark

### 2. 测试内容不值得 integration 级别
166 个 integration test 中，大部分在做这些事：
- 检查某个目录/文件是否存在（50%+）
- 检查 YAML 里某个 key 是否存在
- 检查 markdown 里某句话是否存在
- 检查 script 的 exit code 是 0 还是 1

**这些都是静态验证，可以用 lint/schema 替代。**

### 3. `research_workspace.py` 是 9000 行的 monolith
- 42 个 validation 函数、11 个 write/scaffold 函数、5 个 init 函数、4 个 generate 函数
- 所有 validation mode（direction-ready, epoch-ready, loop-ready...）全部在这个文件
- 无法单独测试一个 validation 函数，只能通过 subprocess 调用整个 script

### 4. `init_workspace_fast` 是唯一的优化
- 通过 copy template 避免重复 fork `init_research.py`
- 但大部分测试还是会 fork `validate_research.py`（72 次）

---

## 重构方案：三阶段

### Phase 1：测试金字塔化（2-3 天）

**目标**：把有价值的测试变成快速单元测试，其余降级为 lint

#### 1.1 拆分 `research_workspace.py`（核心）

把 9018 行的 monolith 拆成模块：

```
skills/research-init/_shared/
├── scripts/
│   └── research_workspace.py      (CLI entry, 保持薄)
├── validation/
│   ├── __init__.py
│   ├── direction.py               # validate_direction_ready
│   ├── epoch.py                   # validate_epoch_ready, validate_loop_ready
│   ├── schema.py                  # validate_epoch_schema, validate_baseline_lock
│   ├── evidence.py                # validate_paper, validate_audit
│   └── hash.py                    # hash-based staleness detection
├── generation/
│   ├── __init__.py
│   ├── workspace.py               # scaffold functions
│   └── prompt.py                  # generate_plan, generate_goal
└── model/
    ├── __init__.py
    ├── validation.py              # Validation class, print_validation
    └── constants.py               # EPOCH_MANIFEST, required files, etc.
```

**为什么先拆**：拆完才能直接 import 单个 validation 函数做单元测试，不需要 fork subprocess。

#### 1.2 单元测试（目标：50 个快速测试）

从 172 个 integration 测试中提取 **纯逻辑** 部分：

| 测试文件 | 可提取的单元测试 | 数量 |
|----------|-----------------|------|
| `test_epoch_schema_validation.py` (32) | Schema 约束逻辑（YAML field 验证、link 校验） | ~20 |
| `test_stale_hash_detection.py` (4) | Hash drift 检测（纯字符串比较） | 4 |
| `test_reproduction_index_validation.py` (3) | Reproduction index 验证 | 3 |
| `test_update_state_gate_flow.py` (3) | Gate 状态机逻辑 | 3 |
| `test_update_state_evidence.py` (3) | Evidence hash 验证 | 3 |
| `test_reproduction_audit_boundaries.py` (2) | Claim 边界检查 | 2 |
| `test_epoch_manifest_contract.py` (6) | Manifest 声明校验 | 6 |
| `test_loop_prompt_validation.py` (5) | Prompt clause 验证 | 3 |
| **小计** | | **~44** |

**每个单元测试 < 5ms，总时间 < 1s。**

#### 1.3 降级文件/文档测试为 lint 脚本

以下内容不值得写 pytest test：

| 类型 | 当前测试数 | 替代方案 |
|------|-----------|----------|
| 目录/文件存在检查 | ~60 | `scripts/lint_workspace_structure.py` |
| 文档内容检查（README/SKILL.md 包含某句话） | ~19 | `scripts/lint_docs.py` |
| YAML schema 一致性 | ~20 | `scripts/validate_schemas.py`（已有部分逻辑） |
| Markdown 格式检查 | ~15 | pre-commit hook + markdownlint |
| **小计** | **~114** | **4 个 lint 脚本，在 CI 跑** |

---

### Phase 2：真正的 Integration 测试（1-2 天）

**目标**：保留 ~15-20 个端到端 integration test，用 `init_workspace_fast`

#### 保留的 integration tests（只测关键路径）

| 场景 | 测试 | 说明 |
|------|------|------|
| 完整 init 流程 | 1 | `init_research.py` 能创建完整 workspace |
| validate 每个 mode | 15 | 每个 mode 一个测试，验证 pass/fail |
| 完整 epoch 创建 | 1 | `create_epoch.py` 端到端 |
| update_state 状态机 | 3 | gate 逻辑端到端 |
| install.sh | 1 | 安装脚本完整性 |
| **总计** | **~21** | |

#### 运行策略

```bash
# Fast CI（每次 commit）
pytest tests/ --unit    # ~50 unit tests, <1s

# Full CI（PR merge / nightly）
pytest tests/ --run-integration --run-slow  # ~21 integration, ~2min
```

---

### Phase 3：基础设施优化（可选）

#### 3.1 去掉 `pytestmark = pytest.mark.integration` 的反模式

当前每个文件用 `pytestmark` 标记**全部** tests 为 integration。改为：

```python
# 只在需要 subprocess 的 test 上单独标记
@pytest.mark.integration
def test_full_validate_flow(self):
    ...

def test_hash_comparison_logic(self):  # 没有标记 = 默认跑
    ...
```

#### 3.2 优化 `init_workspace_fast`

当前 `_get_plain_template()` 会在第一次调用时 fork subprocess。改为：
- 在 CI 中 pre-generate template 并 commit
- 或者用 `pytest tmp_path_factory` 的 session-scoped fixture

#### 3.3 并行化

```python
# pytest.ini
[tool:pytest]
addopts = -n auto  # xdist parallel
```

---

## 重构后的效果对比

| 指标 | 现在 | 重构后 |
|------|------|--------|
| 测试总数 | 172 | ~50 unit + ~20 integration + lint 脚本 |
| 默认跑的时间 | 0.24s（21 passed, 151 skipped） | **<1s**（~50 unit tests） |
| 全量跑的时间 | 数分钟 | **~2min**（~20 integration） |
| 代码覆盖率 | 不可知（大部分 skip） | **可测**（50 unit tests 覆盖核心逻辑） |
| 维护成本 | 每次 template 变都要改 166 个 test | 只改 20 个 integration test |
| 测试价值 | 大部分测试"文件存在" | 测试**业务逻辑** |

---

## 执行计划

### Week 1: Phase 1（核心拆分 + 单元测试）

| Day | 任务 | 产出 |
|-----|------|------|
| Day 1 | 拆分 validation 模块（direction/epoch/schema） | `validation/` package, 可 import |
| Day 2 | 拆分 model/constants 模块 | `model/` package |
| Day 3 | 写 schema validation 的单元测试（20 个） | `tests/unit/test_schema.py` |
| Day 4 | 写 gate/hash/evidence 单元测试（15 个） | `tests/unit/test_gate.py`, `test_hash.py` |
| Day 5 | 写 lint 脚本替代文件/文档测试（~80 个 test 删除） | `scripts/lint_*` |

### Week 2: Phase 2（Integration 精简）

| Day | 任务 | 产出 |
|-----|------|------|
| Day 6 | 精简 integration tests 到 ~20 个 | 删除冗余，合并重复 |
| Day 7 | 优化 `init_workspace_fast` + 并行 | CI 提速 |

### Week 2+: Phase 3（可选优化）

- 按需进行

---

## 风险与注意事项

1. **`research_workspace.py` 拆分是核心风险** — 9000 行代码重构需要 careful refactoring，确保行为不变
2. **不要一次性删除所有 tests** — 先写单元测试覆盖逻辑，确认等价后再删 integration test
3. **lint 脚本要能给出清晰的错误信息** — 替代 pytest 时不能降低开发者体验
