#!/usr/bin/env python3
"""Tests for the minimal scientific judgment compiler."""

from __future__ import annotations

import pytest

from research_workflow_helpers import *  # noqa: F403

pytestmark = pytest.mark.integration


class MinimalScientificJudgmentCompilerTests(unittest.TestCase):  # noqa: F405
    def test_init_from_minimal_scientific_judgment_compiles_epoch_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            judgment_path = repo / "judgment.yaml"
            write_yaml(
                judgment_path,
                {
                    "title": "Judgment Driven Research",
                    "big_rq": "Can explicit evidence gates reduce unsupported claims in agent research workflows?",
                    "core_hypothesis": "Explicit evidence gates reduce unsupported claims by forcing every claim through observed artifacts and audit.",
                    "falsification_condition": "If unsupported claim rate is unchanged after gate enforcement under the declared evaluation protocol.",
                    "closest_baseline": "Ad-hoc prompting without a claim-to-evidence gate.",
                    "dataset_or_environment": "A controlled repository fixture with scripted research tasks.",
                    "metric_or_judgment_rule": "Unsupported claim rate after audit.",
                    "stop_rule": "Stop if G0 search cannot define a fair baseline or if G1 reproduction remains blocked after human review.",
                },
            )

            result = run_cmd(
                [
                    "python3",
                    str(INIT_SCRIPT),
                    "--repo",
                    str(repo),
                    "--judgment-file",
                    str(judgment_path),
                    "--force",
                ]
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            research_dir = repo / "docs" / "research"
            epoch = research_dir / "V0"
            self.assertTrue((epoch / "SCIENTIFIC_JUDGMENT.yaml").exists())
            self.assertTrue((epoch / "EVIDENCE_GATE.yaml").exists())

            direction = (research_dir / "RESEARCH_DIRECTION.md").read_text(encoding="utf-8")
            self.assertIn("status: `human_approved`", direction)
            self.assertIn("Can explicit evidence gates reduce unsupported claims", direction)
            self.assertIn("Ad-hoc prompting without a claim-to-evidence gate", direction)

            prd = (epoch / "PRD.tex").read_text(encoding="utf-8")
            self.assertIn("PRD_STATUS: HUMAN_APPROVED", prd)
            self.assertIn("Minimal Scientific Judgment Binding", prd)
            self.assertIn("Unsupported claim rate after audit", prd)

            spine = read_yaml(epoch / "RESEARCH_SPINE.yaml")
            self.assertEqual(spine["research_questions"][0]["id"], "RQ01")
            self.assertEqual(spine["claims"][0]["id"], "C01")
            self.assertEqual(spine["experiments"][0]["id"], "E01")
            self.assertEqual(spine["evidence"][0]["id"], "EV01")

            self.assertFalse((epoch / "SPEC.yaml").exists())
            self.assertFalse((epoch / "PLAN.md").exists())

            rq_spec = read_yaml(epoch / "rqs" / "RQ01" / "SPEC.yaml")
            self.assertEqual(rq_spec["human_approval"]["status"], "approved")
            self.assertIn("Explicit evidence gates reduce unsupported claims", rq_spec["research_question"]["alternative_hypothesis"])
            self.assertEqual(rq_spec["candidate_inputs"]["baseline"]["id"], "B_USER_BASELINE")
            self.assertEqual(rq_spec["candidate_inputs"]["metric_or_judgment_rule"]["id"], "M_PRIMARY")

            queue = read_yaml(epoch / "TASK_QUEUE.yaml")
            self.assertEqual(queue["current_gate"], "G0_SEARCH_LOCK")
            self.assertEqual(queue["tasks"][0]["status"], "active")
            self.assertIn("Can explicit evidence gates reduce unsupported claims", queue["tasks"][0]["success_criteria"][0])

            gate = read_yaml(epoch / "EVIDENCE_GATE.yaml")
            self.assertEqual(gate["next_required_gate"], "G0_SEARCH_LOCK")
            self.assertEqual(gate["claim_states"]["draft_claim"][0]["claim_id"], "C01")
            self.assertEqual(gate["claim_states"]["allowed_claim"], [])

            direction_ready = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "direction-ready"])
            self.assertEqual(direction_ready.returncode, 0, direction_ready.stdout + direction_ready.stderr)
            epoch_ready = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "epoch-ready"])
            self.assertEqual(epoch_ready.returncode, 0, epoch_ready.stdout + epoch_ready.stderr)
            baseline_ready = run_cmd(["python3", str(VALIDATE_SCRIPT), "--research-dir", str(research_dir), "--mode", "baseline-lock-ready"])
            self.assertNotEqual(baseline_ready.returncode, 0)
            self.assertIn("BASELINE_LOCK.yaml must be locked", baseline_ready.stdout)

    def test_minimal_scientific_judgment_requires_core_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            judgment_path = repo / "judgment.yaml"
            write_yaml(judgment_path, {"big_rq": "Can gates help?"})

            result = run_cmd(
                [
                    "python3",
                    str(INIT_SCRIPT),
                    "--repo",
                    str(repo),
                    "--judgment-file",
                    str(judgment_path),
                ]
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("minimal scientific judgment missing required field", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
