#!/usr/bin/env python3
"""Turn the Perseus Ancient Greek Dependency Treebank Iliad file into per-book JSON."""

import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

SRC = sys.argv[1]
OUT = sys.argv[2]

CITE_RE = re.compile(r":(\d+)\.(\d+)")


def main():
    tree = ET.parse(SRC)
    root = tree.getroot()

    # Tokens carry their own citation except for punctuation, which inherits the
    # location of the neighbouring word (the preceding one, or the following one
    # when the sentence opens with punctuation).
    books = {}
    dropped = 0
    for s_idx, sentence in enumerate(root.iter("sentence")):
        sid = sentence.get("id")
        recs = []
        for w_idx, word in enumerate(sentence.findall("word")):
            # Annotators insert artificial="elliptic" nodes to stand in for words
            # Homer omits; they carry no text and must not be displayed.
            if word.get("artificial"):
                continue
            m = CITE_RE.search(word.get("cite") or "")
            recs.append(
                {
                    "loc": (int(m.group(1)), int(m.group(2))) if m else None,
                    "s": s_idx,
                    "w": w_idx,
                    "id": word.get("id") or "0",
                    "form": word.get("form") or "",
                    "lemma": word.get("lemma") or "",
                    "postag": word.get("postag") or "",
                    "rel": word.get("relation") or "",
                    "head": word.get("head") or "0",
                    "sid": sid,
                }
            )
        last = None
        for r in recs:  # inherit backwards
            if r["loc"] is None:
                r["loc"] = last
            else:
                last = r["loc"]
        last = None
        for r in reversed(recs):  # then forwards, for a leading-punctuation sentence
            if r["loc"] is None:
                r["loc"] = last
            else:
                last = r["loc"]
        for r in recs:
            if r["loc"] is None:
                dropped += 1
                continue
            books.setdefault(r["loc"][0], []).append(r)
    if dropped:
        print("warning: %d tokens had no resolvable citation" % dropped)

    os.makedirs(OUT, exist_ok=True)
    index = []
    total_words = 0
    for book in sorted(books):
        recs = books[book]
        recs.sort(key=lambda r: (r["loc"][1], r["s"], r["w"]))

        lemmas, postags, rels = Table(), Table(), Table()
        lines = []
        cur_n, cur = None, None
        for r in recs:
            n = r["loc"][1]
            if n != cur_n:
                cur_n, cur = n, []
                lines.append({"n": n, "w": cur})
            cur.append(
                [
                    r["form"],
                    lemmas.idx(r["lemma"]),
                    postags.idx(r["postag"]),
                    rels.idx(r["rel"]),
                    int(r["sid"]),
                    int(r["id"]),
                    int(r["head"] or 0),
                ]
            )
        total_words += len(recs)
        data = {
            "book": book,
            "lemmas": lemmas.items,
            "postags": postags.items,
            "rels": rels.items,
            "lines": lines,
        }
        with open(os.path.join(OUT, "book-%d.json" % book), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        index.append({"book": book, "lines": len(lines), "first": lines[0]["n"], "last": lines[-1]["n"]})
        print("book %2d: %5d lines, %6d tokens" % (book, len(lines), len(recs)))

    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({"books": index}, fh, ensure_ascii=False, separators=(",", ":"))

    # every distinct lemma, for the gloss builder
    alllem = set()
    for recs in books.values():
        for r in recs:
            if r["lemma"]:
                alllem.add(r["lemma"])
    with open(os.path.join(OUT, "lemmas.txt"), "w", encoding="utf-8") as fh:
        for l in sorted(alllem):
            fh.write(l + "\n")
    print("total tokens", total_words, "unique lemmas", len(alllem))


class Table:
    def __init__(self):
        self.items = []
        self._map = {}

    def idx(self, val):
        if val not in self._map:
            self._map[val] = len(self.items)
            self.items.append(val)
        return self._map[val]


if __name__ == "__main__":
    main()
