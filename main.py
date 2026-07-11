#!/usr/bin/env python3
"""
KodeKloud Computer Quest - Educational Computer Architecture Adventure

Main entry point for the game.
"""

import argparse
import sys
import traceback

from computerquest import __version__
from computerquest.game import Game


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="KodeKloud Computer Quest - Educational Computer Architecture Adventure"
    )
    parser.add_argument("--version", action="store_true", help="Show version information")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()

    if args.version:
        print(f"KodeKloud Computer Quest v{__version__}")
        return

    try:
        # Start the game
        game = Game()

        # Run the main game loop
        game.start()
    except KeyboardInterrupt:
        print("\nGame interrupted. Exiting...")
    except Exception as e:
        print(f"\nError: {e}")
        if args.debug:
            traceback.print_exc()
        else:
            print("Run with --debug for more information")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
