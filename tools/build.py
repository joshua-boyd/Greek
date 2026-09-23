#!/usr/bin/env python3
"""Regenerate everything under data/ from the upstream sources.

    python3 tools/build.py            # download what's missing, then build
    python3 tools/build.py --offline  # build from an already-populated cache

Downloads land in tools/cache/ (about 700 MB) and are not committed; only the
generated JSON under data/ is.

To add another treebanked text, append an entry to WORKS: everything else —
the per-book JSON, the shared lexicon and the site's work picker — follows from
that list.
"""

import json
import os
import subprocess
import sys
import urllib.request

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

# "case" is the convention for numbering books: the Iliad by capital letters,
# the Odyssey by lower case.
WORKS = [
    {
        "id": "iliad",
        "title": "Iliad",
        "greek": "Ἰλιάς",
        "ref": "Il.",
        "case": "upper",
        "urn": "tlg0012.tlg001.perseus-grc1",
    },
    {
        "id": "odyssey",
        "title": "Odyssey",
        "greek": "Ὀδύσσεια",
        "ref": "Od.",
        "case": "lower",
        "urn": "tlg0012.tlg002.perseus-grc1",
    },
]


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print("downloading", os.path.basename(dest), flush=True)
    tmp = dest + ".part"
    urllib.request.urlretrieve(url, tmp)
    os.replace(tmp, dest)


def run(script, *args):
    cmd = [sys.executable, os.path.join(HERE, script)] + list(args)
    print("$", " ".join(os.path.basename(c) for c in cmd), flush=True)
    subprocess.check_call(cmd, cwd=HERE)


def main():
    offline = "--offline" in sys.argv
    wikt = os.path.join(CACHE, "wiktionary-grc.jsonl")
    lsj_dir = os.path.join(CACHE, "lsj")
    for work in WORKS:
        work["src"] = os.path.join(CACHE, work["id"] + ".tb.xml")

    if not offline:
        for work in WORKS:
            fetch(TREEBANK_URL % work["urn"], work["src"])
        fetch(WIKT_URL, wikt)
        for i in range(1, LSJ_PARTS + 1):
            fetch(LSJ_URL % i, os.path.join(lsj_dir, "lsj%02d.xml" % i))

    for path in [wikt, lsj_dir] + [w["src"] for w in WORKS]:
        if not os.path.exists(path):
            sys.exit("missing source: %s (run without --offline)" % path)

    index = []
    for work in WORKS:
        out = os.path.join(DATA, work["id"])
        print("\n--- %s ---" % work["title"], flush=True)
        run("build_text.py", work["src"], out)
        with open(os.path.join(out, "index.json"), encoding="utf-8") as fh:
            books = json.load(fh)["books"]
        index.append({
            "id": work["id"],
            "title": work["title"],
            "greek": work["greek"],
            "ref": work["ref"],
            "case": work["case"],
            "books": len(books),
        })

    # One lexicon covers every work, so feed it the union of their lemmas.
    lemmas = set()
    for work in WORKS:
        with open(os.path.join(DATA, work["id"], "lemmas.txt"), encoding="utf-8") as fh:
            lemmas.update(l.strip() for l in fh if l.strip())
    union = os.path.join(DATA, "lemmas.txt")
    with open(union, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(lemmas)))
    print("\n--- lexicon (%d distinct lemmas across %d works) ---"
          % (len(lemmas), len(WORKS)), flush=True)
    run("build_lexicon.py", union, lsj_dir, wikt, os.path.join(DATA, "lexicon.json"))

    with open(os.path.join(DATA, "works.json"), "w", encoding="utf-8") as fh:
        json.dump({"works": index}, fh, ensure_ascii=False, indent=1)
    print("\ndone — data/ regenerated")


if __name__ == "__main__":
    main()
