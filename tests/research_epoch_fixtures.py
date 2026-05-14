#!/usr/bin/env python3
"""Epoch research workflow fixtures."""

from __future__ import annotations

import atexit
import shutil
import tempfile
from pathlib import Path

from research_workflow_common import *  # noqa: F403
from research_workflow_common import _get_plain_template  # noqa: F401


def approve_research_direction(research_dir: Path) -> None:
    path = research_dir / "RESEARCH_DIRECTION.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("- status: draft", "- status: human_approved")
    text = text.replace(
        "- `【待填写：允许探索方向 1，例如 MoE routing analysis】`\n"
        "- `【待填写：允许探索方向 2，例如 expert-DAG / expert-subgraph representation】`\n"
        "- `【待填写：允许探索方向 3，例如 routing trace / routing intervention】`",
        "- MoE routing analysis\n- expert-DAG / expert-subgraph representation\n- routing trace / routing intervention",
    )
    path.write_text(text, encoding="utf-8")

def make_epoch_closeout_complete(research_dir: Path, final_status: str = "closed_success") -> None:
    epoch = research_dir / "V0"
    wiki = epoch / "wiki"
    (wiki / "epoch_summary.md").write_text("# V0 Epoch Summary\n\n已完成最小验证并记录洞察。\n", encoding="utf-8")
    (wiki / "evidence_map.md").write_text(
        "# V0 Evidence Map\n\n- hypothesis_or_claim: C01\n  supported_by: [RUN_001]\n  challenged_by: []\n  falsified_by: []\n  unresolved: none\n  evidence_level: confirmatory\n",
        encoding="utf-8",
    )
    (wiki / "positive_signals.md").write_text(
        "# V0 Positive Signals\n\n- signal_id: SIG_001\n  source_task: TASK_001\n  source_run: RUN_001\n  source_artifact: artifacts/run_001.json\n  evidence_level: confirmatory\n  why_it_matters: 支持当前机制。\n  next_validation: 独立复跑。\n",
        encoding="utf-8",
    )
    (wiki / "negative_results.md").write_text(
        "# V0 Negative Results\n\n- result_id: NONE\n  category: unresolved\n  source_task: none\n  source_run: none\n  interpretation: 明确无负结果。\n",
        encoding="utf-8",
    )
    (wiki / "failed_paths.md").write_text(
        "# V0 Failed Paths\n\n- failed_path: NONE\n  why_failed: 明确无失败路径。\n  cost: none\n  future_avoidance_rule: none\n",
        encoding="utf-8",
    )
    (wiki / "baseline_landscape.md").write_text("# V0 Baseline Landscape\n\n- must_compare: [B01]\n- novelty_risk: low\n", encoding="utf-8")
    (wiki / "literature_notes.md").write_text(
        "# V0 Literature Notes\n\n- query: baseline\n  date: 2026-05-11\n  source: local note\n  relevance: high\n  must_compare: true\n  novelty_risk: low\n  action_required: compare B01\n",
        encoding="utf-8",
    )
    (wiki / "open_questions.md").write_text(
        "# V0 Open Questions\n\n- question_id: Q1\n  question: 是否可复现。\n  why_open: 需要复跑。\n  needed_evidence: RUN_002\n",
        encoding="utf-8",
    )
    (wiki / "next_version_seed.md").write_text(
        "# V0 Next Version Seed\n\n- should_create_next_version: false\n- why: 当前版本足够稳定。\n- keep: [C01]\n- drop: []\n- new_core_question: none\n- minimal_next_experiments: none\n- next_stop_conditions: none\n- out_of_scope_risk: none\n- required_human_review: false\n",
        encoding="utf-8",
    )
    (epoch / "closeout.md").write_text(
        f"""# V0 Closeout

## 1. Version Status

- version: V0
- final_status: {final_status}
- close_reason: evidence threshold reached
- closed_at: 2026-05-11

## 2. Original Hypothesis

H1 predicts a measurable signal.

## 3. What Was Executed

- actually_executed: RUN_001
- prompt_only_scaffold: none
- blocked: none
- not_started: none

## 4. What Failed or Blocked

- blocker_id: NONE
- category: execution_failure
- detail: none

## 5. What We Learned

- fact: RUN_001 completed
- artifact: artifacts/run_001.json
- interpretation: C01 is supported
- speculation: none

## 6. Positive Signals

- SIG_001

## 7. Negative Results

- none

## 8. Carry Forward

- artifact: [artifacts/run_001.json]
- baseline: [B01]
- code_module: []
- insight: [SIG_001]
- open_question: []
- dataset: [D01]
- metric: [M01]
- harness: [H01]

## 9. Drop

- hypothesis: []
- claim: []
- baseline: []
- experiment_path: []
- method_variant: []
- metric: []

## 10. Next Version Decision

- create_next_version: false
- next_version_type: stop
- next_core_question: none
- next_minimal_experiments: none
- next_stop_conditions: none
- must_stay_inside_research_corridor: true

## 11. Paper Binding Decision

- paper_binding_ready: false
- reason: not requested
- allowed_claims: []
- blocked_claims: []
""",
        encoding="utf-8",
    )

def make_paper_binding_decision(research_dir: Path, artifact_path: str = "docs/research/V0/artifacts/run_001.json") -> None:
    epoch = research_dir / "V0"
    status = read_yaml(epoch / "STATUS.yaml")
    status["status"] = "closed_stable"
    status["paper_binding"] = {"allowed": True, "reason": "V0 closed_stable"}
    write_yaml(epoch / "STATUS.yaml", status)
    (epoch / "PAPER_BINDING_DECISION.md").write_text(
        f"""# Paper Binding Decision

## Status

- paper_binding_ready: true
- source_version: V0
- decision_reason: V0 closed_stable with audited evidence.

## Allowed Claims

- claim_id: C01
  experiment_id: E01
  run_id: RUN_001
  artifact_path: {artifact_path}
  metric: M01
  baseline: B01
  seed_protocol: S01
  audit_status: passed
  real_data_check: real_dataset_provenance_verified
  real_model_check: real_model_provenance_verified
  non_smoke_full_run: full_run_not_smoke
  evidence_level: paper_admissible

## Blocked Claims

- none

## Evidence Requirements

Each allowed claim is bound above.

## Forbidden

- 不使用 exploratory-only insight 作为 main result。
- 不使用 prompt-only scaffold 作为 result。
- 不从 paper 反推实验。
- 不填入 plausible but unverified numbers。
""",
        encoding="utf-8",
    )


_closed_template: Path | None = None


def _get_closed_template() -> Path:
    global _closed_template
    if _closed_template is None:
        plain = _get_plain_template()
        tmp = Path(tempfile.mkdtemp(prefix="research_closed_template_"))
        shutil.copytree(plain, tmp, dirs_exist_ok=True)
        make_epoch_closeout_complete(tmp / "docs" / "research", final_status="closed_stable")
        _closed_template = tmp
        atexit.register(shutil.rmtree, str(tmp), ignore_errors=True)
    return _closed_template


def init_workspace_closed_fast(repo: Path) -> Path:
    template = _get_closed_template()
    shutil.copytree(template, repo, dirs_exist_ok=True)
    return repo / "docs" / "research"
