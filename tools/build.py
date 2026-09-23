#!/usr/bin/env python3
"""Regenerate everything under data/ from the upstream sources.

    python3 tools/build.py            # download what's missing, then build
    python3 tools/build.py --offline  # build from an already-populated cache

Downloads land in tools/cache/ (about 700 MB) and are not committed; only the
generated JSON under data/ is.
"""

import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, "cache")
DATA = os.path.join(ROOT, "data")

TREEBANK_URL = ("https://raw.githubusercontent.com/PerseusDL/treebank_data/master/"
                "v2.1/Greek/texts/tlg0012.tlg001.perseus-grc1.tb.xml")
LSJ_URL = ("https://raw.githubusercontent.com/PerseusDL/lexica/master/"
           "CTS_XML_TEI/perseus/pdllex/grc/lsj/grc.lsj.perseus-eng%d.xml")
LSJ_PARTS = 27
WIKT_URL = ("https://kaikki.org/dictionary/Ancient%20Greek/"
            "kaikki.org-dictionary-AncientGreek.jsonl")


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
    treebank = os.path.join(CACHE, "iliad.tb.xml")
    wikt = os.path.join(CACHE, "wiktionary-grc.jsonl")
    lsj_dir = os.path.join(CACHE, "lsj")

    if not offline:
        fetch(TREEBANK_URL, treebank)
        fetch(WIKT_URL, wikt)
        for i in range(1, LSJ_PARTS + 1):
            fetch(LSJ_URL % i, os.path.join(lsj_dir, "lsj%02d.xml" % i))

    for path in (treebank, wikt, lsj_dir):
        if not os.path.exists(path):
            sys.exit("missing source: %s (run without --offline)" % path)

    iliad = os.path.join(DATA, "iliad")
    run("build_text.py", treebank, iliad)
    run("build_lexicon.py", os.path.join(DATA, "lemmas.txt"), lsj_dir, wikt,
        os.path.join(DATA, "lexicon.json"))
    print("\ndone — data/ regenerated")


if __name__ == "__main__":
    main()
