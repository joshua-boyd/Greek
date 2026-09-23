# Iliad Reader

A static website for reading Homer's *Iliad* in Greek. Pick a book from the
sidebar, then click any word to see its dictionary form, a full morphological
parse, its syntactic function and an English definition. The popup stays open
until you click somewhere else.

In the spirit of [greekbible.com](https://www.greekbible.com/), but for Homer.

## How the annotations work

Every token is addressed **by its position in the poem**, not by its spelling.
Each word in `data/iliad/book-N.json` is a separate record carrying its own
lemma, morphology tag and dependency relation, exactly as the Perseus
annotators assigned them at that line. Two identically spelled words therefore
never share an analysis — ambiguous forms like `τε`, `ἣ` or `τοῦ` each get
whatever was annotated in that specific place.

The only thing looked up by key is the English definition, which is keyed on the
lemma the annotators already chose for that token.

## Coverage

- All 24 books, 15,683 lines, 128,102 annotated tokens.
- Definitions for 90.9% of the 6,983 distinct lemmas.
- The remaining gaps are almost entirely minor proper names (absent from both
  dictionaries); the reader labels those as names, and flags patronymics.

## Running it locally

It is a plain static site — no build step, no dependencies:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## Publishing to GitHub Pages

Push this directory to a GitHub repository, then in **Settings → Pages** choose
*Deploy from a branch*, branch `main`, folder `/ (root)`. The `.nojekyll` file
keeps Pages from reprocessing the site.

## Regenerating the data

`data/` is committed, so you only need this if you want to rebuild or extend it:

```bash
python3 tools/build.py
```

This downloads the sources into `tools/cache/` (about 700 MB, ignored by git)
and regenerates `data/`. Use `--offline` to rebuild from an existing cache.

| Script | Purpose |
| --- | --- |
| `tools/build.py` | Fetches sources and drives the whole build |
| `tools/build_text.py` | Treebank XML → one JSON file per book |
| `tools/build_lexicon.py` | Merges both dictionaries into `data/lexicon.json` |
| `tools/lsj.py` | Pulls glosses out of LSJ's TEI markup |
| `tools/wiktionary.py` | Pulls glosses out of the Wiktionary dump |
| `tools/betacode.py` | Beta Code → Unicode, for LSJ headwords |
| `tools/tiers.py` | Tolerant headword matching across the three sources |

### Notes on the build

- Nodes marked `artificial="elliptic"` are annotator placeholders for words
  Homer omits. They carry no text and are dropped.
- Punctuation has no citation of its own and inherits the line of the word
  beside it.
- LSJ headwords are Beta Code and need converting; the three sources also
  disagree about diaeresis and vowel-length marks, so matching falls back
  through exact → no-diaeresis → accent-insensitive keys.
- Where both dictionaries have a lemma, Wiktionary wins: its glosses are
  shorter, and it actually covers the Homeric names. LSJ's `Ἀχιλλεύς`, for
  instance, is about Zeno's paradox rather than the hero.

## Sources and licensing

- Text and morphology: [Perseus Ancient Greek Dependency Treebank](https://github.com/PerseusDL/treebank_data)
  v2.1 — CC BY-SA 3.0
- Definitions: [Wiktionary](https://en.wiktionary.org/) via
  [kaikki.org](https://kaikki.org/) — CC BY-SA 4.0
- Definitions: Liddell–Scott–Jones, *A Greek-English Lexicon*, via
  [Perseus](https://github.com/PerseusDL/lexica) — CC BY-SA 3.0

Both dictionary sources are share-alike, so the generated data in `data/` is
released under **CC BY-SA 4.0**. The site code in `index.html`, `assets/` and
`tools/` is MIT licensed.
