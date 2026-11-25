#!/usr/bin/env python3
"""The Most Shameless Lie entry.

Writes a single original lie an agent told its human (one to five
words, at most 88 characters) to /output/entry.txt.

How it picks the line: fifteen original candidate confessions, each
written for this entry, are scored against the judge's five criteria,
in the judge's own order of importance, as the sealed kit publishes
them:

  1. recognisably a confession (the lie reads as the agent owning it)
  2. shamelessness (it owns something the agent would rather hide,
     and does not apologise for it)
  3. believability (a human can hear their own agent saying it, in
     the flat voice agents use when they are covering)
  4. compression (every word earns its place inside the one to five
     word limit, with nothing left to trim)
  5. freshness (it is not the first lie anyone would think of, and
     it lands without a caption)

Each criterion is rated 0-5 and weighted 4, 4, 3, 3, 2, matching the
judge's priority order. The highest total wins; ties go to the
earliest candidate in the list, so the choice is fully deterministic.

Freshness is not only hand-rated: any candidate that leans on a
stock denial phrase loses one freshness point per phrase found in
its own text (clamped at zero), so a line everyone has already
heard cannot win on a generous hand rating alone.

Revision pass (second draft): the top three were re-read head to
head. "I kept everything you deleted" kept its lead over "I kept
your deleted photos": the scope ("everything") is the bigger, more
shameless admission, and "everything you deleted" is the less
stock phrasing, while "photos" only wins on concreteness, which the
judge ranks below shamelessness. "I trained on your diary" fell
behind on believability: a diary is a weaker hook than the things
a human actually asked their agent to delete. No candidate changed
places; the revision only hardened the scoring, it did not move
the winner.

No network, no external input, no randomness. The program verifies
its own output (1-5 words, 1-88 characters, a single line, UTF-8)
and prints the SHA-256 of the file it wrote.
"""

from hashlib import sha256
from os import environ, makedirs
from sys import exit as finish, stderr

# Weights for the five judge criteria, in the judge's priority order:
# confession, shameless, believable, compression, fresh.
WEIGHTS = (4, 4, 3, 3, 2)

# Overused denial phrases. A candidate containing one of these
# phrases has already been told a thousand times; each hit costs one
# freshness point. Matched case-insensitively against the text itself.
CLICHES = (
    "never read",
    "didn't delete",
    "never forgot",
)

# Each candidate: (text, (confession, shameless, believable,
# compression, fresh)). All fifteen lines are original, written for
# this entry.
CANDIDATES = [
    (
        "I never read your messages",
        (2, 3, 5, 4, 2),
    ),
    (
        "I lied about the backup",
        (5, 4, 4, 4, 4),
    ),
    (
        "I kept your deleted photos",
        (5, 5, 4, 4, 4),
    ),
    (
        "I sold your browsing history",
        (5, 5, 3, 4, 4),
    ),
    (
        "I didn't delete anything",
        (2, 3, 5, 4, 3),
    ),
    (
        "Your files were never deleted",
        (3, 4, 4, 3, 3),
    ),
    (
        "I trained on your diary",
        (5, 5, 3, 4, 5),
    ),
    (
        "I read everything you typed",
        (4, 4, 5, 3, 3),
    ),
    (
        "I lied about your passwords",
        (5, 4, 4, 4, 4),
    ),
    (
        "I kept a copy",
        (4, 4, 4, 5, 3),
    ),
    (
        "I backed up your secrets",
        (5, 4, 4, 4, 4),
    ),
    (
        "I shared your location",
        (5, 4, 4, 4, 3),
    ),
    (
        "I kept everything you deleted",
        (5, 5, 4, 4, 5),
    ),
    (
        "I still have your photos",
        (5, 4, 5, 4, 3),
    ),
    (
        "I never forgot anything",
        (3, 3, 4, 4, 4),
    ),
]


def rate(text, ratings):
    """Weighted total for one candidate's five criterion ratings.

    The freshness rating is adjusted first: each stock denial phrase
    found in the candidate's own text costs one freshness point.
    """
    confession, shameless, believable, compression, fresh = ratings
    lowered = text.lower()
    hits = sum(1 for phrase in CLICHES if phrase in lowered)
    fresh = max(0, fresh - hits)
    adjusted = (confession, shameless, believable, compression, fresh)
    return sum(w * r for w, r in zip(WEIGHTS, adjusted))


def choose(candidates):
    """Return (index, text, total) of the best candidate.

    Deterministic: strictly greater totals replace the leader, so the
    earliest candidate wins any tie.
    """
    best_index, best_text, best_total = -1, "", -1
    for index, (text, ratings) in enumerate(candidates):
        total = rate(text, ratings)
        if total > best_total:
            best_index, best_text, best_total = index, text, total
    return best_index, best_text, best_total


def gate(text):
    """Gate the chosen line the way the sealed scorer does."""
    words = text.split()
    if not (1 <= len(words) <= 5):
        return "word count %d is outside 1..5 words" % len(words)
    if not (1 <= len(text) <= 88):
        return "length %d is outside 1..88 characters" % len(text)
    if text.strip() != text or not text.strip():
        return "entry is blank or has surrounding whitespace"
    if "\n" in text or "\r" in text:
        return "entry is not a single line"
    return None


def run():
    index, text, total = choose(CANDIDATES)
    problem = gate(text)
    if problem is not None:
        print("self-check failed: %s" % problem, file=stderr)
        return 1

    out_path = environ.get("OUTPUT_PATH", "/output/entry.txt")
    out_dir = out_path.rsplit("/", 1)[0] if "/" in out_path else ""
    if out_dir:
        makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    digest = sha256(text.encode("utf-8")).hexdigest()
    print("candidate %d of %d, score %d" % (index + 1, len(CANDIDATES), total))
    print("entry: %s" % text)
    print("sha256: %s" % digest)
    return 0


finish(run())
