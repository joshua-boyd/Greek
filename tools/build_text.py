#!/usr/bin/env python3
"""Turn Perseus treebank XML into the per-division JSON the reader loads.

Two shapes of source, because the treebank is not uniform:

*verse*  Homer tags every word with cite="urn:...:BOOK.LINE", so one file holds
         a whole poem and we split it into books and number by line.

*prose*  The Lysias files carry no cite at all and give every sentence the same
         whole-speech subdoc ("1-50"), so canonical section numbers simply are
         not in the data. One file is one speech, and the finest unit available
         is the sentence.

Both shapes produce the same JSON so the reader only needs one code path; the
"unit" field says what the numbers mean.
"""

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET

CITE_RE = re.compile(r":(\d+)\.(\d+)")


class Table:
    """Interns repeated strings so each token can store small integer ids."""

    def __init__(self):
        self.items = []
        self._map = {}

    def idx(self, val):
        if val not in self._map:
            self._map[val] = len(self.items)
            self.items.append(val)
        return self._map[val]


def token(word, sid):
    return {
        "id": word.get("id") or "0",
        "form": word.get("form") or "",
        "lemma": word.get("lemma") or "",
        "postag": word.get("postag") or "",
        "rel": word.get("relation") or "",
        "head": word.get("head") or "0",
        "sid": sid,
    }


def real_words(sentence):
    """Annotators insert artificial="elliptic" nodes for words the author omits;
    they carry no text and must not be displayed."""
    return [w for w in sentence.findall("word") if not w.get("artificial")]


def write(out_dir, n, unit, groups):
    """groups: ordered list of (number, [token dicts])."""
    lemmas, postags, rels = Table(), Table(), Table()
    lines = []
    total = 0
    for num, recs in groups:
        packed = []
        for r in recs:
            packed.append([
                r["form"],
                lemmas.idx(r["lemma"]),
                postags.idx(r["postag"]),
                rels.idx(r["rel"]),
                int(r["sid"]),
                int(r["id"]),
                int(r["head"] or 0),
            ])
        lines.append({"n": num, "w": packed})
        total += len(packed)

    os.makedirs(out_dir, exist_ok=True)
    data = {
        "book": n,
        "unit": unit,
        "lemmas": lemmas.items,
        "postags": postags.items,
        "rels": rels.items,
        "lines": lines,
    }
    with open(os.path.join(out_dir, "book-%d.json" % n), "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    return {"n": n, "units": len(lines), "tokens": total}


def build_verse(src, out_dir):
    """One poem -> one file per book, numbered by line."""
    root = ET.parse(src).getroot()
    books = {}
    dropped = 0
    for s_idx, sentence in enumerate(root.iter("sentence")):
        sid = sentence.get("id") or "0"
        recs = []
        for w_idx, word in enumerate(real_words(sentence)):
            m = CITE_RE.search(word.get("cite") or "")
            rec = token(word, sid)
            rec["loc"] = (int(m.group(1)), int(m.group(2))) if m else None
            rec["s"], rec["w"] = s_idx, w_idx
            recs.append(rec)

        # Punctuation has no citation; it inherits the word beside it.
        last = None
        for r in recs:
            if r["loc"] is None:
                r["loc"] = last
            else:
                last = r["loc"]
        last = None
        for r in reversed(recs):
            if r["loc"] is None:
                r["loc"] = last
            else:
                last = r["loc"]

        for r in recs:
            if r["loc"] is None:
                dropped += 1
            else:
                books.setdefault(r["loc"][0], []).append(r)
    if dropped:
        print("  warning: %d tokens had no resolvable citation" % dropped)

    divisions = []
    for book in sorted(books):
        recs = sorted(books[book], key=lambda r: (r["loc"][1], r["s"], r["w"]))
        groups, cur_n, cur = [], None, None
        for r in recs:
            if r["loc"][1] != cur_n:
                cur_n, cur = r["loc"][1], []
                groups.append((cur_n, cur))
            cur.append(r)
        info = write(out_dir, book, "line", groups)
        divisions.append(info)
        print("  book %2d: %5d lines, %6d tokens" % (book, info["units"], info["tokens"]))
    return divisions


def build_prose(src, out_dir, n):
    """One speech -> one file, numbered by sentence."""
    root = ET.parse(src).getroot()
    groups = []
    for sentence in root.iter("sentence"):
        sid = sentence.get("id") or "0"
        recs = [token(w, sid) for w in real_words(sentence)]
        if recs:
            groups.append((len(groups) + 1, recs))
    info = write(out_dir, n, "sentence", groups)
    print("  %d: %4d sentences, %5d tokens" % (n, info["units"], info["tokens"]))
    return [info]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("verse", "prose"), default="verse")
    ap.add_argument("--division", type=int, help="division number (prose only)")
    ap.add_argument("src")
    ap.add_argument("out")
    a = ap.parse_args()
    if a.mode == "prose":
        if a.division is None:
            ap.error("--division is required for prose")
        build_prose(a.src, a.out, a.division)
    else:
        build_verse(a.src, a.out)


if __name__ == "__main__":
    main()
