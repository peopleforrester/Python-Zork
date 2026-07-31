#!/usr/bin/env python3
"""
ABOUTME: Tests the deploy verifier's parsing and match logic, plus the
ABOUTME: server's deployed-commit reporting that the verifier relies on.
"""

import importlib.util
import unittest
from pathlib import Path

import server

_SPEC = importlib.util.spec_from_file_location(
    "deploy_script", Path(__file__).parent.parent / "scripts" / "deploy.py"
)
deploy = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(deploy)


SAMPLE = """Recent Deployments
  0c82da3b-6340-4aae-81ec-e3098e99ad0c | BUILDING | 2026-07-31 13:30:45 +02:00
  b45c0046-cf07-41bf-b6e6-14325afb0202 | INITIALIZING | 2026-07-31 13:11:30 +02:00
  4db017e1-20b2-40ac-a676-016bc1dea393 | SUCCESS | 2026-07-29 17:39:45 +02:00
"""


class TestDeploymentParsing(unittest.TestCase):
    def test_parses_id_and_state_newest_first(self):
        rows = deploy.parse_deployments(SAMPLE)
        self.assertEqual(rows[0], ("0c82da3b-6340-4aae-81ec-e3098e99ad0c", "BUILDING"))
        self.assertEqual(rows[2][1], "SUCCESS")

    def test_header_line_is_not_a_deployment(self):
        self.assertTrue(all("Recent" not in r[0] for r in deploy.parse_deployments(SAMPLE)))

    def test_garbage_yields_no_rows(self):
        self.assertEqual(deploy.parse_deployments("Unauthorized. Please run login"), [])
        self.assertEqual(deploy.parse_deployments(""), [])


class TestStateClassification(unittest.TestCase):
    def test_success_is_ok(self):
        self.assertEqual(deploy.classify("SUCCESS"), "ok")

    def test_failures_are_bad(self):
        for state in ("FAILED", "CRASHED", "REMOVED"):
            self.assertEqual(deploy.classify(state), "bad", state)

    def test_in_flight_states_are_pending(self):
        # The two that stalled during the 2026-07-31 incident.
        for state in ("BUILDING", "INITIALIZING", "DEPLOYING", ""):
            self.assertEqual(deploy.classify(state), "pending", state)


class TestCommitMatching(unittest.TestCase):
    def test_identical_shas_match(self):
        self.assertTrue(deploy.commit_matches({"commit": "abc123def456"}, "abc123def456"))

    def test_short_sha_matches_full_sha(self):
        self.assertTrue(deploy.commit_matches({"commit": "abc123d"}, "abc123def456789"))

    def test_different_commit_does_not_match(self):
        self.assertFalse(deploy.commit_matches({"commit": "aaaaaaa"}, "bbbbbbb"))

    def test_unknown_never_matches(self):
        """The pre-stamp state must never read as a successful deploy."""
        self.assertFalse(deploy.commit_matches({"commit": "unknown"}, "abc123"))

    def test_missing_or_empty_never_matches(self):
        self.assertFalse(deploy.commit_matches({}, "abc123"))
        self.assertFalse(deploy.commit_matches({"commit": ""}, "abc123"))
        self.assertFalse(deploy.commit_matches({"status": "ok"}, "abc123"))


class TestServerReportsItsCommit(unittest.TestCase):
    def test_explicit_env_wins(self):
        self.assertEqual(server._deploy_commit(env={"DEPLOY_SHA": "cafe123"}), "cafe123")

    def test_platform_variable_is_used_when_present(self):
        self.assertEqual(
            server._deploy_commit(env={"RAILWAY_GIT_COMMIT_SHA": "beef456"}), "beef456"
        )

    def test_explicit_env_beats_platform_variable(self):
        self.assertEqual(
            server._deploy_commit(env={"DEPLOY_SHA": "aaa", "RAILWAY_GIT_COMMIT_SHA": "bbb"}),
            "aaa",
        )

    def test_no_variables_reports_unknown(self):
        """'unknown' is the honest answer, and never matches a real commit."""
        self.assertEqual(server._deploy_commit(env={}), "unknown")

    def test_blank_env_falls_through_rather_than_reporting_blank(self):
        self.assertEqual(server._deploy_commit(env={"DEPLOY_SHA": "   "}), "unknown")

    def test_health_endpoint_reports_status_and_commit(self):
        with server.app.test_client() as client:
            payload = client.get("/api/health").get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("commit", payload)


if __name__ == "__main__":
    unittest.main()
