#!/usr/bin/env python3
"""Strict schema validation tests for every epoch version."""

from __future__ import annotations

import shutil

from research_workflow_helpers import *  # noqa: F403


class EpochSchemaValidationTests(unittest.TestCase):  # noqa: F405
    def test_epoch_ready_rejects_missing_spec_required_field_in_any_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_closed_fast(Path(tmp))
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
            research_dir = init_workspace_closed_fast(Path(tmp))
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
            research_dir = init_workspace_fast(Path(tmp))
            (research_dir / "V0" / "wiki" / "extra_protocol.md").write_text("# Extra\n", encoding="utf-8")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected epoch wiki file: V0/wiki/extra_protocol.md", result.stdout)

    def test_epoch_ready_still_rejects_v1_before_v0_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            shutil.copytree(research_dir / "V0", research_dir / "V1")

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot create next version before current epoch has closed_* status", result.stdout)

    def test_epoch_ready_rejects_missing_gate_aware_queue_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue.pop("current_gate", None)
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/TASK_QUEUE.yaml missing required field: current_gate", result.stdout)

    def test_epoch_ready_rejects_invalid_gate_and_task_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            queue = read_yaml(research_dir / "V0" / "TASK_QUEUE.yaml")
            queue["gates"][0]["status"] = "almost_done"
            queue["tasks"][0]["status"] = "working"
            write_yaml(research_dir / "V0" / "TASK_QUEUE.yaml", queue)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid gate status", result.stdout)
        self.assertIn("invalid task status", result.stdout)

    def test_epoch_ready_rejects_missing_spine_required_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine.pop("claims", None)
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/RESEARCH_SPINE.yaml missing required field: claims", result.stdout)

    def test_epoch_ready_rejects_spine_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["version"] = "V99"
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/RESEARCH_SPINE.yaml version V99 does not match epoch V0", result.stdout)

    def test_epoch_ready_rejects_missing_spine_direction_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine.pop("direction_ref", None)
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V0/RESEARCH_SPINE.yaml missing required field: direction_ref", result.stdout)

    def test_spine_ready_rejects_invalid_direction_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["direction_ref"] = "../NON_EXISTENT_DIRECTION.md"
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("direction_ref points to non-existent file", result.stdout)

    def test_spine_ready_validates_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_spine_ready_rejects_broken_rq_claim_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["research_questions"] = [{"id": "RQ1", "text": "q1"}]
            spine["claims"] = [{"id": "C1", "rq_id": "RQ_MISSING", "text": "c1"}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spine claim C1 references unknown rq_id: RQ_MISSING", result.stdout)

    def test_spine_ready_rejects_broken_claim_experiment_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["claims"] = [{"id": "C1", "rq_id": "RQ1", "text": "c1"}]
            spine["experiments"] = [{"id": "E1", "claim_ids": ["C_MISSING"], "purpose": "p1"}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spine experiment E1 references unknown claim_id: C_MISSING", result.stdout)

    def test_spine_ready_rejects_broken_experiment_evidence_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["experiments"] = [{"id": "E1", "claim_ids": ["C1"], "purpose": "p1"}]
            spine["evidence"] = [{"id": "EV1", "experiment_id": "E_MISSING", "artifact_path": None}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spine evidence EV1 references unknown experiment_id: E_MISSING", result.stdout)

    def test_spine_ready_rejects_broken_evidence_figure_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["evidence"] = [{"id": "EV1", "experiment_id": "E1", "artifact_path": None}]
            spine["figures_tables"] = [{"id": "FIG1", "evidence_ids": ["EV_MISSING"], "target_path": "f1.pdf"}]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spine figure/table FIG1 references unknown evidence_id: EV_MISSING", result.stdout)

    def test_spine_ready_rejects_broken_section_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            research_dir = init_workspace_fast(Path(tmp))
            spine = read_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml")
            spine["claims"] = [{"id": "C1", "rq_id": "RQ1", "text": "c1"}]
            spine["figures_tables"] = [{"id": "FIG1", "evidence_ids": ["EV1"], "target_path": "f1.pdf"}]
            spine["paper_sections"] = [
                {"id": "SEC1", "claims": ["C_MISSING"], "figures_tables": ["FIG_MISSING"]}
            ]
            write_yaml(research_dir / "V0" / "RESEARCH_SPINE.yaml", spine)

            result = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "spine-ready"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("spine paper_section SEC1 references unknown claim_id: C_MISSING", result.stdout)
        self.assertIn("spine paper_section SEC1 references unknown figure/table_id: FIG_MISSING", result.stdout)
