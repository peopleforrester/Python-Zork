#!/usr/bin/env python3
"""
ABOUTME: Unit tests for server.py helpers — env-var parsing and config.
ABOUTME: Imports server module without starting Flask.
"""

import unittest

import server


class TestParseOrigins(unittest.TestCase):
    """server._parse_origins must turn an env string into a clean list."""

    def test_default_when_unset(self):
        self.assertEqual(server._parse_origins(None), ["http://localhost:5173"])

    def test_default_when_empty(self):
        self.assertEqual(server._parse_origins(""), ["http://localhost:5173"])

    def test_single_origin(self):
        self.assertEqual(
            server._parse_origins("https://example.com"),
            ["https://example.com"],
        )

    def test_comma_separated(self):
        self.assertEqual(
            server._parse_origins("https://a.com,https://b.com"),
            ["https://a.com", "https://b.com"],
        )

    def test_strips_whitespace_and_drops_blanks(self):
        self.assertEqual(
            server._parse_origins("  https://a.com ,, https://b.com  ,"),
            ["https://a.com", "https://b.com"],
        )


class TestEnvFlags(unittest.TestCase):
    """Boolean env helpers default safe (debug off, localhost host)."""

    def test_debug_default_off(self):
        self.assertFalse(server._env_bool(None))
        self.assertFalse(server._env_bool(""))
        self.assertFalse(server._env_bool("0"))
        self.assertFalse(server._env_bool("false"))

    def test_debug_on_when_truthy(self):
        self.assertTrue(server._env_bool("1"))
        self.assertTrue(server._env_bool("true"))
        self.assertTrue(server._env_bool("yes"))


if __name__ == "__main__":
    unittest.main()
