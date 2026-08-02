#!/usr/bin/env python3
# ABOUTME: Deploys to Railway and proves the new commit is actually serving.
# ABOUTME: Neither `railway up`'s exit code nor "Online" confirms a deploy.

"""Deploy and verify.

Railway reports a service as "Online" whenever it is up on its last *successful*
build, and `railway up` can exit 0 while the build later stalls or fails. On
2026-07-31 that combination served two-day-old code for an hour while every
surface said healthy. This script therefore refuses to call a deploy done until
the live `/api/health` reports the exact commit that was uploaded.

Usage:
    uv run python scripts/deploy.py              # deploy HEAD and verify
    uv run python scripts/deploy.py --verify-only  # just check what is live
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HEALTH_URL = "https://python-zork-production.up.railway.app/api/health"

TERMINAL_OK = {"SUCCESS"}
TERMINAL_BAD = {"FAILED", "CRASHED", "REMOVED"}

_DEPLOY_ID = re.compile(r"[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}", re.IGNORECASE)

# git's own short-sha width. Anything narrower is not evidence of a match.
MIN_SHA_WIDTH = 7


# --- pure helpers (unit-tested) ---------------------------------------------

def parse_deployments(text: str) -> list[tuple[str, str]]:
    """Parse `railway deployment list` into [(id, state), ...], newest first.

    Requires a UUID-shaped first column. A bare "no spaces" test let a column
    header through, and the caller would then poll a deployment named ID until
    the build timeout expired.
    """
    rows = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2 and _DEPLOY_ID.fullmatch(parts[0]):
            rows.append((parts[0], parts[1]))
    return rows


def parse_variable(text: str, key: str) -> str:
    """Read one value out of `railway variable list --kv` (KEY=value lines)."""
    prefix = f"{key}="
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            return line[len(prefix):]
    return ""


def classify(state: str) -> str:
    """Map a deployment state to 'ok', 'bad', or 'pending'."""
    upper = (state or "").strip().upper()
    if upper in TERMINAL_OK:
        return "ok"
    if upper in TERMINAL_BAD:
        return "bad"
    return "pending"


def commit_matches(payload: dict, expected: str) -> bool:
    """True when the live service reports the commit we uploaded.

    Compares on the shorter of the two lengths so a short SHA still matches a
    full one; an 'unknown' or missing commit never matches. The comparison has
    a floor, because on the shorter-of-the-two rule alone a truncated or
    single-character stamp matched almost any HEAD and read as a green deploy.
    """
    live = str(payload.get("commit", "")).strip()
    if not live or live == "unknown" or not expected:
        return False
    width = min(len(live), len(expected))
    if width < MIN_SHA_WIDTH:
        return False
    return live[:width].lower() == expected[:width].lower()


# --- side-effecting steps ----------------------------------------------------

def _run(args: list[str], timeout: int = 180) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return 124, "timed out"
    except FileNotFoundError:
        # `railway` not installed is the likeliest local failure; a traceback
        # here is far less useful than the name of the missing command.
        return 127, f"command not found: {args[0]}"
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def head_commit() -> str:
    code, out = _run(["git", "rev-parse", "HEAD"], timeout=30)
    if code != 0:
        raise SystemExit(f"cannot resolve HEAD: {out.strip()}")
    return out.strip()


def fetch_health(url: str = HEALTH_URL, timeout: int = 15) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except (urllib.error.URLError, ValueError, TimeoutError, OSError):
        return {}


def newest_deployment(retries: int = 4) -> tuple[str, str] | None:
    """Newest (id, state), retrying because the Railway API is not reliable."""
    for _ in range(retries):
        code, out = _run(["railway", "deployment", "list"])
        rows = parse_deployments(out) if code == 0 else []
        if rows:
            return rows[0]
        time.sleep(15)
    return None


def wait_for_build(deploy_id: str, minutes: int) -> str:
    """Poll one deployment until it reaches a terminal state."""
    deadline = time.time() + minutes * 60
    last = "pending"
    while time.time() < deadline:
        code, out = _run(["railway", "deployment", "list"])
        if code == 0:
            for did, state in parse_deployments(out):
                if did == deploy_id:
                    last = classify(state)
                    print(f"  build {deploy_id[:8]}: {state}")
                    if last != "pending":
                        return last
                    break
        time.sleep(30)
    return last


def wait_for_commit(expected: str, minutes: int) -> bool:
    """Poll the live health endpoint until it reports `expected`."""
    deadline = time.time() + minutes * 60
    while time.time() < deadline:
        payload = fetch_health()
        live = payload.get("commit", "<no response>")
        if commit_matches(payload, expected):
            print(f"  live commit: {live} (match)")
            return True
        print(f"  live commit: {live} (waiting for {expected[:12]})")
        time.sleep(20)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true",
                        help="check what is live without deploying")
    parser.add_argument("--build-timeout", type=int, default=15,
                        help="minutes to wait for the build (default 15)")
    parser.add_argument("--verify-timeout", type=int, default=10,
                        help="minutes to wait for the commit to go live (default 10)")
    args = parser.parse_args()

    expected = head_commit()
    print(f"HEAD is {expected[:12]}")

    if args.verify_only:
        payload = fetch_health()
        print(f"live: {json.dumps(payload) or '<no response>'}")
        if commit_matches(payload, expected):
            print("VERIFIED: production is serving HEAD.")
            return 0
        print("MISMATCH: production is NOT serving HEAD.")
        return 1

    # Read the stamp before overwriting it. If this deploy fails, the variable
    # has to go back: it takes effect on the *next* build, so a stale stamp
    # would make some later unrelated deploy report a commit it never served,
    # which is the exact lie this script exists to catch.
    code, out = _run(["railway", "variable", "list", "--kv"], timeout=60)
    previous_sha = parse_variable(out, "DEPLOY_SHA") if code == 0 else ""

    def restore_stamp() -> None:
        if not previous_sha or previous_sha == expected:
            return
        print(f"  restoring DEPLOY_SHA={previous_sha[:12]}")
        _run(["railway", "variable", "set", f"DEPLOY_SHA={previous_sha}",
              "--skip-deploys"], timeout=180)

    # Stamp the service before uploading. --skip-deploys so setting it does not
    # kick off a build of the *old* code that we would then have to wait out.
    print(f"stamping DEPLOY_SHA={expected[:12]}")
    code, out = _run(["railway", "variable", "set", f"DEPLOY_SHA={expected}",
                      "--skip-deploys"], timeout=180)
    if code != 0:
        print(f"FAILED: could not set DEPLOY_SHA: {out.strip()[:200]}")
        return 1

    print("uploading...")
    code, out = _run(["railway", "up", "--ci"], timeout=900)
    # A non-zero exit is worth reporting but is not decisive either way: the
    # upload often succeeds while log streaming fails.
    if code != 0:
        print(f"  railway up exited {code}; continuing to check the build")

    # If the new deployment has not registered yet this can pick up the
    # previous one. That is tolerable: the build watch is a progress display,
    # and the commit check below is what actually decides success, so watching
    # the wrong build only means reaching that check sooner.
    newest = newest_deployment()
    if newest is None:
        print("FAILED: could not read the deployment list.")
        restore_stamp()
        return 1
    deploy_id, state = newest
    print(f"watching deployment {deploy_id[:8]} (currently {state})")

    outcome = wait_for_build(deploy_id, args.build_timeout)
    if outcome == "bad":
        print("FAILED: the build did not succeed.")
        restore_stamp()
        return 1
    if outcome == "pending":
        print("FAILED: the build did not finish in time.")
        restore_stamp()
        return 1

    print("build succeeded; confirming the live commit")
    if not wait_for_commit(expected, args.verify_timeout):
        print("FAILED: build succeeded but production is not serving HEAD.")
        restore_stamp()
        return 1

    print("DEPLOYED and VERIFIED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
