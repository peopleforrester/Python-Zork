# ABOUTME: Multi-match and wildcard virus scanners, the policy knobs signature.py lacks.
# ABOUTME: New simulators by contract: signature.py is never edited in place.

"""Educational virus-scanning simulators with a policy axis.

`signature.py` reports one verdict from exact substring matching and has no
knob, so its puzzles can only ask the player to read the setup back. These two
add the missing degrees of freedom, each paying off an IOU an existing puzzle's
explanation already writes:

* `MultiMatchScanSimulator` reports every match instead of the first. The
  shipped `signature_first_match` explanation ends "real engines report every
  match precisely because cleanup that removes one infection and misses the
  second leaves the machine owned"; this is that engine, on the same bytes.
* `WildcardScanSimulator` carries an exact/wildcard knob. Flipping it turns
  `signature_near_miss`'s "clean" into a match on a byte-identical file, which
  is the heuristic its explanation gestures at.

Fidelity statement (contract: docs/architecture-microquiz.md): both model
pattern matching of file contents against a curated signature list, ordered by
database position. The wildcard scanner supports exactly two metacharacters,
`*` (any run of characters, possibly empty) and `?` (exactly one character);
every other character, including regex syntax, is literal. NOT modeled:
heuristic scoring, behaviour monitoring, emulation or sandboxing, packing and
unpacking, polymorphic decryptor detection, or any notion of confidence. A
wildcard signature here is a crude stand-in for a real fuzzy signature, and it
is deliberately crude: the lesson is that widening a pattern trades false
negatives for false positives, not that this is how a modern engine works.
Verdicts say "this matches the stored pattern for X"; they do not say "this
is, in the world, a virus."
"""

from __future__ import annotations

import re
from typing import Any, ClassVar

from computerquest.mechanics.simulators.base import (
    MAX_FILE_CONTENT_BYTES,
    MAX_SIGNATURES,
    AnswerKind,
    require_within,
)

CLEAN = "clean"


def _read_scan_setup(setup: dict[str, Any]) -> tuple[dict[str, str], str]:
    """Pull and bound the two fields every scanner takes.

    The registry validates a puzzle by running it, so an author-supplied file or
    signature list is executed at load time. These bounds sit orders of
    magnitude above any teachable input; the shipped puzzles use two signatures
    and files under a hundred bytes.
    """
    signatures = {str(k): str(v) for k, v in dict(setup["signatures"]).items()}
    require_within("signature count", len(signatures), MAX_SIGNATURES)
    contents = str(setup["file_contents"])
    require_within("file_contents length", len(contents), MAX_FILE_CONTENT_BYTES)
    return signatures, contents


class MultiMatchScanSimulator:
    """One verdict per database entry, in database order: the signature's name
    where it matched, `clean` where it did not.

    A bare list of the matches would have been the shorter report, but its
    length is then part of the answer, and the command layer treats a
    sequence-length mismatch as a wrong *shape* rather than a wrong answer:
    ungraded, no attempt recorded, retry free. On this puzzle that reply would
    have told the player their count was off, which is most of the answer. One
    slot per entry makes the length fixed by the database the prompt shows, so
    a short answer is genuinely malformed and a wrong verdict is genuinely
    wrong. It is also what a real scan report looks like.
    """

    answer_kind: ClassVar[AnswerKind] = AnswerKind.SEQUENCE

    def run(self, setup: dict[str, Any]) -> list[str]:
        signatures, contents = _read_scan_setup(setup)
        return [
            name if pattern in contents else CLEAN
            for name, pattern in signatures.items()
        ]


def _wildcard_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a signature where only `*` and `?` are special.

    Everything else is escaped, so a signature containing `.` or `(`, which
    real ones routinely do, matches those characters and not their regex
    meaning. Built from escaped literals and `.*`/`.` only, so there is no
    nesting for a pathological pattern to backtrack through.
    """
    parts = []
    for char in pattern:
        if char == "*":
            parts.append(".*")
        elif char == "?":
            parts.append(".")
        else:
            parts.append(re.escape(char))
    return re.compile("".join(parts), re.DOTALL)


class WildcardScanSimulator:
    """First matching signature under the chosen matching policy, or 'clean'.

    `mode: exact` is byte-for-byte the behaviour of SignatureMatchSimulator, so
    a puzzle can flip one key and show the counterfactual on identical input.
    """

    answer_kind: ClassVar[AnswerKind] = AnswerKind.CHOICE

    def run(self, setup: dict[str, Any]) -> str:
        signatures, contents = _read_scan_setup(setup)
        mode = str(setup.get("mode", "exact")).lower()
        if mode not in ("exact", "wildcard"):
            raise ValueError(f"unknown match mode {mode!r}; expected exact or wildcard")

        for name, pattern in signatures.items():
            if mode == "exact":
                if pattern in contents:
                    return name
            elif _wildcard_to_regex(pattern).search(contents):
                return name
        return CLEAN
