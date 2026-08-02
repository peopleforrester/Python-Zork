#!/usr/bin/env python3
"""
ABOUTME: Regressions for the targeted review of 2026-08-02.
ABOUTME: Each test pins one confirmed defect in code added since the last review.
"""

import threading
import time
import unittest
import unittest.mock

import server
from computerquest.config import is_virus_name
from computerquest.mechanics.puzzles import HintMode
from tests._helpers import build_real_game


class TestObjectivesDoesNotFakeCompletion(unittest.TestCase):
    """Viruses are ordinary items and `take` accepts them without a scan, so the
    player's pack is a hiding place the room sweep never looked in."""

    def _carry_one_virus_and_finish_everything_else(self):
        game = build_real_game()
        for room in game.game_map.rooms.values():
            for item in list(room.items):
                if not is_virus_name(item):
                    continue
                if item == "boot_sector_virus":
                    game.player.items[item] = room.items.pop(item)  # carried, never found
                else:
                    game.player.found_viruses.append(item)
                    game.player.quarantined_viruses.append(item)
            room.mark_visited()
        for puzzle_id in game.puzzle_registry.by_id:
            game.player.solved_puzzles.add(puzzle_id)
        game._recompute_knowledge()
        return game

    def test_a_carried_virus_is_not_reported_as_a_clean_system(self):
        game = self._carry_one_virus_and_finish_everything_else()
        out = game.feed("objectives")
        self.assertNotIn("system is clean", out.lower())

    def test_the_carried_virus_is_surfaced_as_work_remaining(self):
        game = self._carry_one_virus_and_finish_everything_else()
        self.assertIn("boot_sector_virus", game.feed("objectives"))

    def test_the_closing_line_requires_real_completion(self):
        """'Nothing left to do' must mean the game is actually won."""
        game = build_real_game()
        for room in game.game_map.rooms.values():
            for item in list(room.items):
                if is_virus_name(item):
                    game.player.found_viruses.append(item)
                    game.player.quarantined_viruses.append(item)
            room.mark_visited()
        for puzzle_id in game.puzzle_registry.by_id:
            game.player.solved_puzzles.add(puzzle_id)
        game._recompute_knowledge()
        self.assertIn("clean", game.feed("objectives").lower())


class TestObjectivesRegionRanking(unittest.TestCase):
    def test_regions_are_ranked_by_unexplored_ground_not_alphabetically(self):
        """Sorting by name meant three uppercase region names always won the
        slice, so the region holding the most unexplored rooms could be hidden."""
        game = build_real_game()
        storage = {"ssd", "hdd", "sata_ports", "storage_controller"}
        for room_id, room in game.game_map.rooms.items():
            if room_id not in storage:
                room.mark_visited()
        self.assertIn("storage", game.feed("objectives").lower())


class TestObjectivesWeakestAreaWording(unittest.TestCase):
    def test_a_maxed_area_is_not_called_weakest(self):
        game = build_real_game()
        for area in game.player.knowledge:
            game.player.knowledge[area] = 5
        self.assertNotIn("weakest", game.feed("objectives").lower())


class TestPagerDoesNotSwallowCommands(unittest.TestCase):
    """The pager consumed the newline, so a real command typed at --more-- was
    echoed and then thrown away."""

    def setUp(self):
        for store in (server._sessions, server._input_buffers,
                      server._terminal_rows, server._pending_pages):
            store.clear()
        self.client = server.socketio.test_client(server.app)
        self.client.emit("start_game")
        self.client.emit("terminal_size", {"rows": 20})
        self.client.get_received()

    def tearDown(self):
        self.client.disconnect()
        for store in (server._sessions, server._pending_pages):
            store.clear()

    def _text(self):
        return " ".join(
            str(m["args"][0].get("output", ""))
            for m in self.client.get_received()
            if m["name"] == "terminal_output"
        )

    def _sid(self):
        return next(iter(server._sessions))

    def test_a_command_typed_while_paging_runs(self):
        self.client.emit("terminal_input", {"input": "help\r"})
        self.client.get_received()
        self.client.emit("terminal_input", {"input": "look\r"})
        self.assertIn("LOCATION", self._text())

    def test_a_command_typed_while_paging_cancels_the_pager(self):
        self.client.emit("terminal_input", {"input": "help\r"})
        self.client.get_received()
        self.client.emit("terminal_input", {"input": "look\r"})
        self.client.get_received()
        self.assertFalse(server._pending_pages.get(self._sid()))

    def test_a_bare_enter_still_advances_the_pager(self):
        self.client.emit("terminal_input", {"input": "help\r"})
        self.client.get_received()
        self.client.emit("terminal_input", {"input": "\r"})
        self.assertIn("--more--", self._text() + "|")

    def test_ctrl_c_cancels_the_pager(self):
        self.client.emit("terminal_input", {"input": "help\r"})
        self.client.get_received()
        self.client.emit("terminal_input", {"input": "\x03"})
        self.client.get_received()
        self.assertFalse(server._pending_pages.get(self._sid()))

    def test_restarting_the_game_clears_held_pages(self):
        self.client.emit("terminal_input", {"input": "help\r"})
        self.client.get_received()
        self.client.emit("start_game")
        self.client.get_received()
        self.assertFalse(server._pending_pages.get(self._sid()))

    def test_a_typo_corrected_verb_still_pages(self):
        """`hlp` is corrected to `help` by the game, so it must page like one."""
        self.client.emit("terminal_input", {"input": "hlp\r"})
        self.assertIn("--more--", self._text())

    def test_an_absurd_terminal_height_is_rejected(self):
        self.client.emit("terminal_size", {"rows": 10 ** 12})
        self.assertNotIn(10 ** 12, server._terminal_rows.values())


class TestEscapeSequencesAreDropped(unittest.TestCase):
    """The server dropped the ESC byte but kept the CSI tail, so an arrow key
    typed `[A` into the command line."""

    def setUp(self):
        for store in (server._sessions, server._input_buffers):
            store.clear()
        self.client = server.socketio.test_client(server.app)
        self.client.emit("start_game")
        self.client.get_received()

    def tearDown(self):
        self.client.disconnect()
        server._sessions.clear()

    def test_an_arrow_key_leaves_the_buffer_untouched(self):
        sid = next(iter(server._sessions))
        for ch in "kn":
            self.client.emit("terminal_input", {"input": ch})
        self.client.emit("terminal_input", {"input": "\x1b[A"})
        self.assertEqual(server._input_buffers[sid], "kn")

    def test_a_split_escape_sequence_is_also_dropped(self):
        """xterm may deliver the sequence one byte per event."""
        sid = next(iter(server._sessions))
        for ch in ("k", "\x1b", "[", "B", "n"):
            self.client.emit("terminal_input", {"input": ch})
        self.assertEqual(server._input_buffers[sid], "kn")


class TestAutoPromptRespectsTheGate(unittest.TestCase):
    """gated_room_puzzles applied decision 2; maybe_auto_prompt did not, so the
    two paths disagreed about the same puzzle in the same room."""

    def test_a_locked_puzzle_is_not_auto_presented(self):
        game = build_real_game()
        game.player.location = game.game_map.rooms["core1_registers"]  # difficulty 3
        self.assertEqual(game._gated_room_puzzles(), [])
        self.assertEqual(game.puzzles.maybe_auto_prompt(), "")

    def test_an_unlocked_puzzle_is_still_auto_presented(self):
        game = build_real_game()
        game.player.location = game.game_map.rooms["core1_l1"]
        self.assertIn("PUZZLE:", game.puzzles.maybe_auto_prompt())


class TestHintModeDoesNotSkewStanding(unittest.TestCase):
    """area_standing read attempted_puzzles, which learning mode stops writing,
    so a beginner was classified 'strong' and served the hardest puzzle first."""

    def _play_identically(self, mode):
        game = build_real_game()
        game.puzzles.hint_mode = mode
        for puzzle_id in ("l1_lru_basic", "l1_associativity_2way"):
            game.player.solved_puzzles.add(puzzle_id)
            game.player.attempted_puzzles.add(puzzle_id)
        game.player.location = game.game_map.rooms["l2_cache1"]
        game.puzzles.start("l2_fifo_eviction")
        game.puzzles.hint()
        game.puzzles.hint()
        game.puzzles.skip()
        return game.puzzles.area_standing("memory")

    def test_identical_play_gives_the_same_standing_in_every_mode(self):
        standings = {mode: self._play_identically(mode) for mode in HintMode}
        self.assertEqual(len(set(standings.values())), 1, standings)

    def test_a_struggling_beginner_is_never_called_strong(self):
        self.assertNotEqual(self._play_identically(HintMode.LEARNING), "strong")


class TestCompletionRespectsTheGate(unittest.TestCase):
    """Explicit `solve <id>` deliberately bypasses the gate, so offering a
    locked id as a completion handed over progression for one keypress."""

    def test_solve_offers_only_what_the_gate_shows(self):
        game = build_real_game()
        for room_id in ("core1_l1", "core1", "l3_cache"):
            game.player.location = game.game_map.rooms[room_id]
            gated = {p.id for p in game._gated_room_puzzles()}
            with self.subTest(room=room_id):
                self.assertEqual(set(game.completions("solve ")), gated)

    def test_a_solved_puzzle_is_not_offered_again(self):
        game = build_real_game()
        game.player.location = game.game_map.rooms["core1_l1"]
        game.player.solved_puzzles.add("l1_lru_basic")
        self.assertNotIn("l1_lru_basic", game.completions("solve "))


class TestStateWritingVerbsDirtyTheSave(unittest.TestCase):
    """Schemas 1.2 and 1.3 made these persist state, so quitting after them
    skipped the save prompt and lost the work."""

    def _dirty_after(self, *commands):
        game = build_real_game()
        game.player.location = game.game_map.rooms["core1"]
        game.puzzles.start("pipeline_forwarding_intro")
        game.changes_since_save = False
        for command in commands:
            game.feed(command)
        return game.changes_since_save

    def test_difficulty_marks_the_game_dirty(self):
        self.assertTrue(self._dirty_after("difficulty strict"))

    def test_hint_marks_the_game_dirty(self):
        self.assertTrue(self._dirty_after("hint"))

    def test_solve_marks_the_game_dirty(self):
        self.assertTrue(self._dirty_after("solve pipeline_forwarding_intro"))

    def test_genuinely_read_only_verbs_stay_clean(self):
        for command in ("look", "objectives", "knowledge", "status", "help"):
            with self.subTest(command=command):
                self.assertFalse(self._dirty_after(command))


class TestConcurrentKeystrokesAreNotLost(unittest.TestCase):
    """flask-socketio runs with async_handlers on, so each event is dispatched
    in its own thread. Reading the line buffer at entry and writing it at exit
    let two overlapping keystrokes race, and the later write silently dropped
    the other's characters."""

    SID = "race-sid"

    def setUp(self):
        for store in (server._sessions, server._input_buffers, server._in_escape):
            store.clear()
        server._sessions[self.SID] = build_real_game()
        server._input_buffers[self.SID] = ""

    def tearDown(self):
        for store in (server._sessions, server._input_buffers, server._in_escape):
            store.clear()
        server._session_locks.clear()

    def _type_concurrently(self, first, second):
        """Type two chunks at once. The echo is slowed because it lands between
        the buffer read and the buffer write, which is precisely the window the
        race lives in; a delay anywhere else leaves it too narrow to observe."""
        def slow_emit(*_args, **_kwargs):
            time.sleep(0.15)

        with unittest.mock.patch.object(server, "_session_id", lambda: self.SID), \
             unittest.mock.patch.object(server, "emit", slow_emit):
            threads = [
                threading.Thread(target=server.handle_input, args=({"input": chunk},))
                for chunk in (first, second)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
        return server._input_buffers[self.SID]

    def test_every_typed_character_reaches_the_buffer(self):
        buffered = self._type_concurrently("aaa", "bbb")
        self.assertEqual(len(buffered), 6, f"lost characters: {buffered!r}")

    def test_each_chunk_stays_contiguous(self):
        buffered = self._type_concurrently("aaa", "bbb")
        self.assertIn(buffered, ("aaabbb", "bbbaaa"))


class TestPerCommandHelpCoversTheRegistry(unittest.TestCase):
    """The old assertion only checked the output was non-empty, so 33 of 79
    commands answered 'No help for X. Did you mean: X?' and it stayed green."""

    def test_every_registered_command_returns_a_real_entry(self):
        game = build_real_game()
        missing = []
        for name in game.command_processor.commands:
            out = game.feed(f"help {name}")
            if "No help for" in out:
                missing.append(name)
        self.assertEqual(missing, [], f"{len(missing)} commands have no help entry")

    def test_a_suggestion_never_suggests_the_word_itself(self):
        game = build_real_game()
        out = game.feed("help zzzz")
        self.assertNotIn("Did you mean: zzzz", out)


if __name__ == "__main__":
    unittest.main()
