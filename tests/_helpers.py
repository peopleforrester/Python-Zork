# ABOUTME: Shared real-collaborator builders for the Python-Zork test suite.
# ABOUTME: Replaces MagicMock-heavy fixtures with actual Game / Player / world.

import contextlib
import io

from computerquest.game import Game


def build_real_game():
    """Construct a real Game instance with stdout suppressed during welcome.

    The Game constructor builds the full ComputerArchitecture (≈30 components)
    and prints the welcome banner. The world is small enough to construct
    per-test; suppressing stdout keeps test output pristine.
    """
    with contextlib.redirect_stdout(io.StringIO()):
        return Game()
