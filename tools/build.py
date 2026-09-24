#!/usr/bin/env python3
"""Regenerate everything under data/ from the upstream sources.

    python3 tools/build.py            # download what's missing, then build
    python3 tools/build.py --offline  # build from an already-populated cache

Downloads land in tools/cache/ (about 700 MB) and are not committed; only the
generated JSON under data/ is.

To add another treebanked text, append an entry to WORKS. A verse work is one
source file split into books by citation; a prose work lists its parts, each
its own file. Everything else — the JSON, the shared lexicon and the site's
pickers — follows from that list.
"""

import glob
import json
import os
import subprocess
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_text

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, "cache")
DATA = os.path.join(ROOT, "data")

TREEBANK_URL = ("https://raw.githubusercontent.com/PerseusDL/treebank_data/master/"
                "v2.1/Greek/texts/%s.tb.xml")
LSJ_URL = ("https://raw.githubusercontent.com/PerseusDL/lexica/master/"
           "CTS_XML_TEI/perseus/pdllex/grc/lsj/grc.lsj.perseus-eng%d.xml")
LSJ_PARTS = 27
WIKT_URL = ("https://kaikki.org/dictionary/Ancient%20Greek/"
            "kaikki.org-dictionary-AncientGreek.jsonl")

WORKS = [
    {
        "id": "iliad",
        "title": "Iliad",
        "author": "Ὅμηρος",
        "label": "Iliad",
        "greek": "Ἰλιάς",
        "ref": "Il.",
        "kind": "verse",
        "unit": "line",
        "noun": "Book",
        # Book letters: the Iliad is cited by capitals, the Odyssey lower case.
        "letters": "upper",
        "source": "tlg0012.tlg001.perseus-grc1",
    },
    {
        "id": "odyssey",
        "title": "Odyssey",
        "author": "Ὅμηρος",
        "label": "Odyssey",
        "greek": "Ὀδύσσεια",
        "ref": "Od.",
        "kind": "verse",
        "unit": "line",
        "noun": "Book",
        "letters": "lower",
        "source": "tlg0012.tlg002.perseus-grc1",
    },
    {
        "id": "lysias",
        "title": "Lysias",
        "author": "Λυσίας",
        "label": "Speeches",
        "greek": "Λυσίας",
        "ref": "Lys.",
        "kind": "prose",
        # The treebank carries no cite attributes and gives every sentence the
        # whole-speech subdoc, so canonical section numbers are unavailable and
        # the sentence is the finest unit we can honestly number by.
        "unit": "sentence",
        "noun": "Oration",
        "parts": [
            {"n": 1, "source": "tlg0540.tlg001.perseus-grc1",
             "title": "On the Murder of Eratosthenes"},
            {"n": 14, "source": "tlg0540.tlg014.perseus-grc1",
             "title": "Against Alcibiades I"},
            {"n": 15, "source": "tlg0540.tlg015.perseus-grc1",
             "title": "Against Alcibiades II"},
            {"n": 23, "source": "tlg0540.tlg023.perseus-grc1",
             "title": "Against Pancleon"},
        ],
    },
]


def cache_path(urn):
    return os.path.join(CACHE, urn.split(".perseus")[0] + ".tb.xml")


def sources_of(work):
    if work["kind"] == "prose":
        return [p["source"] for p in work["parts"]]
    return [work["source"]]


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print("downloading", os.path.basename(dest), flush=True)
    tmp = dest + ".part"
    urllib.request.urlretrieve(url, tmp)
    os.replace(tmp, dest)


def main():
    offline = "--offline" in sys.argv
    wikt = os.path.join(CACHE, "wiktionary-grc.jsonl")
    lsj_dir = os.path.join(CACHE, "lsj")

    if not offline:
        for work in WORKS:
            for urn in sources_of(work):
                fetch(TREEBANK_URL % urn, cache_path(urn))
        fetch(WIKT_URL, wikt)
        for i in range(1, LSJ_PARTS + 1):
            fetch(LSJ_URL % i, os.path.join(lsj_dir, "lsj%02d.xml" % i))

    needed = [wikt, lsj_dir]
    for work in WORKS:
        needed += [cache_path(u) for u in sources_of(work)]
    for path in needed:
        if not os.path.exists(path):
            sys.exit("missing source: %s (run without --offline)" % path)

    index = []
    for work in WORKS:
        out = os.path.join(DATA, work["id"])
        print("\n--- %s ---" % work["title"], flush=True)
        titles = {}
        if work["kind"] == "prose":
            divisions = []
            for part in work["parts"]:
                divisions += build_text.build_prose(
                    cache_path(part["source"]), out, part["n"])
                titles[part["n"]] = part.get("title")
        else:
            divisions = build_text.build_verse(cache_path(work["source"]), out)

        entry = {k: work[k] for k in
                 ("id", "title", "author", "label", "greek", "ref", "kind", "unit", "noun")}
        if "letters" in work:
            entry["letters"] = work["letters"]
        entry["divisions"] = [
            {"n": d["n"], "units": d["units"],
             **({"title": titles[d["n"]]} if titles.get(d["n"]) else {})}
            for d in divisions
        ]
        index.append(entry)

    # One lexicon serves every work, so feed it the union of their lemmas.
    lemmas = set()
    for path in glob.glob(os.path.join(DATA, "*", "book-*.json")):
        with open(path, encoding="utf-8") as fh:
            lemmas.update(l for l in json.load(fh)["lemmas"] if l)
    union = os.path.join(DATA, "lemmas.txt")
    with open(union, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(lemmas)))
    print("\n--- lexicon (%d distinct lemmas across %d works) ---"
          % (len(lemmas), len(WORKS)), flush=True)
    subprocess.check_call(
        [sys.executable, os.path.join(HERE, "build_lexicon.py"), union, lsj_dir,
         wikt, os.path.join(DATA, "lexicon.json")], cwd=HERE)

    with open(os.path.join(DATA, "works.json"), "w", encoding="utf-8") as fh:
        json.dump({"works": index}, fh, ensure_ascii=False, indent=1)
    print("\ndone — data/ regenerated")


if __name__ == "__main__":
    main()
