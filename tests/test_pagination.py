#!/usr/bin/env python3
"""
ABOUTME: Long output pages to the client's terminal height instead of dumping.
ABOUTME: With no reported height it must fall back to emitting everything.
"""

import unittest

import server


class TestPaginate(unittest.TestCase):
    """Pure splitting logic, so the interesting cases are cheap to pin."""

    def test_short_text_is_a_single_page(self):
        pages = server.paginate("a\nb\nc", rows=24)
        self.assertEqual(pages, ["a\nb\nc"])

    def test_long_text_splits(self):
        text = "\n".join(str(i) for i in range(100))
        pages = server.paginate(text, rows=24)
        self.assertGreater(len(pages), 1)

    def test_no_line_is_lost_or_duplicated(self):
        text = "\n".join(str(i) for i in range(100))
        rejoined = "\n".join(server.paginate(text, rows=24))
        self.assertEqual(rejoined.split("\n"), text.split("\n"))

    def test_every_page_fits_the_viewport(self):
        text = "\n".join(str(i) for i in range(100))
        for page in server.paginate(text, rows=24):
            # Leave room for the prompt and the --more-- line.
            self.assertLessEqual(len(page.split("\n")), 24 - 2)

    def test_unknown_height_returns_one_page(self):
        """Falling back to today's behaviour is always safe; stranding a player
        mid-page is not."""
        text = "\n".join(str(i) for i in range(100))
        self.assertEqual(server.paginate(text, rows=None), [text])

    def test_absurd_heights_do_not_produce_empty_pages(self):
        text = "\n".join(str(i) for i in range(20))
        for rows in (0, 1, 2, 3, -5):
            with self.subTest(rows=rows):
                pages = server.paginate(text, rows=rows)
                self.assertTrue(all(p for p in pages))
                self.assertEqual("\n".join(pages).split("\n"), text.split("\n"))

    def test_empty_text_is_handled(self):
        self.assertEqual(server.paginate("", rows=24), [""])


class TestTerminalSizeTracking(unittest.TestCase):
    def setUp(self):
        server._sessions.clear()
        server._input_buffers.clear()
        server._terminal_rows.clear()
        server._pending_pages.clear()
        self.client = server.socketio.test_client(server.app)

    def tearDown(self):
        self.client.disconnect()
        server._sessions.clear()
        server._terminal_rows.clear()
        server._pending_pages.clear()

    def test_client_can_report_its_height(self):
        self.client.emit("start_game")
        self.client.get_received()
        self.client.emit("terminal_size", {"rows": 30})
        self.assertIn(30, server._terminal_rows.values())

    def test_a_nonsense_height_is_ignored_rather_than_stored(self):
        self.client.emit("start_game")
        self.client.get_received()
        self.client.emit("terminal_size", {"rows": "tall"})
        self.client.emit("terminal_size", {"rows": -3})
        self.assertNotIn("tall", server._terminal_rows.values())
        self.assertNotIn(-3, server._terminal_rows.values())

    def test_long_output_pages_when_a_height_is_known(self):
        self.client.emit("start_game")
        self.client.emit("terminal_size", {"rows": 20})
        self.client.get_received()

        self.client.emit("terminal_input", {"input": "help\r"})
        text = " ".join(
            str(m["args"][0].get("output", ""))
            for m in self.client.get_received()
            if m["name"] == "terminal_output"
        )
        self.assertIn("--more--", text)

    def test_advancing_the_pager_does_not_run_a_command(self):
        self.client.emit("start_game")
        self.client.emit("terminal_size", {"rows": 20})
        self.client.get_received()
        self.client.emit("terminal_input", {"input": "help\r"})
        self.client.get_received()

        before = server._sessions[next(iter(server._sessions))].turns
        self.client.emit("terminal_input", {"input": "\r"})   # advance a page
        after = server._sessions[next(iter(server._sessions))].turns
        self.assertEqual(before, after)

    def test_narrative_output_is_never_paged(self):
        """Paging every command broke the flow of play: room descriptions split
        across pages and the end-to-end suite failed on all three tests. Only
        reference output the player asked for may page."""
        self.client.emit("start_game")
        self.client.emit("terminal_size", {"rows": 10})
        self.client.get_received()

        for command in ("look", "n", "solve"):
            self.client.emit("terminal_input", {"input": command + "\r"})
            text = " ".join(
                str(m["args"][0].get("output", ""))
                for m in self.client.get_received()
                if m["name"] == "terminal_output"
            )
            with self.subTest(command=command):
                self.assertNotIn("--more--", text)

    def test_reference_output_does_page(self):
        self.client.emit("start_game")
        self.client.emit("terminal_size", {"rows": 10})
        self.client.get_received()
        self.client.emit("terminal_input", {"input": "map\r"})
        text = " ".join(
            str(m["args"][0].get("output", ""))
            for m in self.client.get_received()
            if m["name"] == "terminal_output"
        )
        self.assertIn("--more--", text)

    def test_output_is_not_paged_without_a_reported_height(self):
        self.client.emit("start_game")
        self.client.get_received()
        self.client.emit("terminal_input", {"input": "help\r"})
        text = " ".join(
            str(m["args"][0].get("output", ""))
            for m in self.client.get_received()
            if m["name"] == "terminal_output"
        )
        self.assertNotIn("--more--", text)


if __name__ == "__main__":
    unittest.main()
