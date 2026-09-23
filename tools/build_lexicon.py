#!/usr/bin/env python3
"""Merge Wiktionary and LSJ glosses into one lemma -> definition file.

Wiktionary supplies short modern glosses and covers the Homeric proper names
LSJ omits; LSJ fills in rare poetic vocabulary Wiktionary lacks.
"""

import json
import sys

import lsj
import tiers
import wiktionary

LEMMA_FILE, LSJ_DIR, WIKT_FILE, OUT_FILE = sys.argv[1:5]


STUBS = {"fem", "masc", "neut", "sq", "pl", "sg", "dual", "adj", "adv", "v", "cf",
         "dim", "name", "nom", "gen", "dat", "acc", "voc", "prop"}


def solid(text):
    """Reject leftovers like a bare 'fem' from a cross-reference-only entry."""
    t = text.strip().strip(".").lower()
    return len(t) > 2 and t not in STUBS


def main():
    raw_lemmas = [l.strip() for l in open(LEMMA_FILE, encoding="utf-8") if l.strip()]
    keyed = {l: lsj.norm_lemma(l) for l in raw_lemmas}
    targets = sorted(set(keyed.values()))

    wikt = tiers.Matcher(targets)
    print("scanning Wiktionary…", flush=True)
    wiktionary.load(WIKT_FILE, wikt)

    lsjm = tiers.Matcher(targets, limit=2)
    print("scanning LSJ…", flush=True)
    lsj.load(LSJ_DIR, lsjm)

    out = {}
    stats = {"both": 0, "wikt only": 0, "lsj only": 0, "miss": 0}
    misses = []
    for raw, key in sorted(keyed.items()):
        w = [g for g in (wikt.get(key) or []) if solid(g)]
        l = [g for g in (lsjm.get(key) or []) if solid(g)]
        if w and l:
            stats["both"] += 1
        elif w:
            stats["wikt only"] += 1
        elif l:
            stats["lsj only"] += 1
        else:
            stats["miss"] += 1
            misses.append(raw)
            continue
        # Wiktionary wins when both have the lemma: its glosses are short and it
        # covers the Homeric proper names, where LSJ's entry for e.g. Ἀχιλλεύς is
        # about Zeno's paradox rather than the hero.
        if w:
            out[raw] = ["; ".join(w[:3]), 0]
        else:
            out[raw] = [" | ".join(l[:2]), 1]

    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    with open(OUT_FILE + ".misses.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(misses))
    print(stats, "coverage %.1f%%" % (100.0 * len(out) / max(1, len(keyed))))


if __name__ == "__main__":
    main()
