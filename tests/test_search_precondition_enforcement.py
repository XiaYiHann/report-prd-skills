#!/usr/bin/env python3
"""Search precondition rendering and completion enforcement tests."""

from __future__ import annotations

from research_workflow_helpers import *  # noqa: F403


def write_search_evidence(epoch_dir: Path) -> None:
    (epoch_dir / "search" / "web_search_log.yaml").write_text(
        "queries:\n  - query: baseline official code\n    results: []\nabsence_claims: []\n",
        encoding="utf-8",
    )
    (epoch_dir / "search" / "repo_search_log.yaml").write_text(
        "commands:\n  - command: rg baseline\n    purpose: local search\nfindings: {}\n",
        encoding="utf-8",
    )
    (epoch_dir / "search" / "search_report.md").write_text(
        "# Search Report\n\nSearch completed for baseline and reproduction candidates.\n",
        encoding="utf-8",
    )


class SearchPreconditionEnforcementTests(unittest.TestCase):  # noqa: F405
    def test_update_state_rejects_completed_search_task_without_search_logs(self) -> None:
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
                    "T_G0_001",
                    "--gate-id",
                    "G0_SEARCH_LOCK",
                    "--status",
                    "completed",
                    "--exit-code",
                    "0",
                ],
                cwd=repo,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing search evidence", result.stderr.lower() + result.stdout.lower())

    def test_update_state_allows_completed_search_task_with_required_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            research_dir = init_workspace(repo)
            epoch_dir = research_dir / "V0"
            write_search_evidence(epoch_dir)

            result = run_cmd(
                [
                    "python3",
                    str(UPDATE_STATE_SCRIPT),
                    "--repo",
                    str(repo),
                    "--task-id",
                    "T_G0_001",
                    "--gate-id",
                    "G0_SEARCH_LOCK",
                    "--status",
                    "completed",
                    "--executor",
                    "codex",
                    "--command",
                    "manual search",
                    "--exit-code",
                    "0",
                ],
                cwd=repo,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
