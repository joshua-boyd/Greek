# Homer Reader

A static website for reading Homer's *Iliad* and *Odyssey* in Greek. Pick a
work and a book from the sidebar, then click any word to see its dictionary
form, a full morphological parse, its syntactic function and an English
definition. The popup stays open until you click somewhere else.

In the spirit of [greekbible.com](https://www.greekbible.com/), but for Homer.

## How the annotations work

Every token is addressed **by its position in the poem**, not by its spelling.
Each word in `data/<work>/book-N.json` is a separate record carrying its own
lemma, morphology tag and dependency relation, exactly as the Perseus
annotators assigned them at that line. Two identically spelled words therefore
never share an analysis — ambiguous forms like `τε`, `ἣ` or `τοῦ` each get
whatever was annotated in that specific place.

The only thing looked up by key is the English definition, which is keyed on the
lemma the annotators already chose for that token.

## Coverage

| Work | Books | Lines | Tokens |
| --- | --- | --- | --- |
| Iliad | 24 | 15,683 | 128,102 |
| Odyssey | 24 | 12,057 | 104,200 |

Both poems share one lexicon, covering 90.3% of the 8,832 distinct lemmas
(3,890 of them appear in both works). The remaining gaps are almost entirely
minor proper names, absent from both dictionaries; the reader labels those as
names and flags patronymics.

## Adding another text

Every other text in the Perseus treebank works with this pipeline unchanged —
Hesiod, the tragedians, Herodotus Book 1, several Plato dialogues. Append an
entry to `WORKS` in `tools/build.py` with the text's URN and rerun the build.
The per-book JSON, the shared lexicon and the site's work picker all follow
from that list; no front-end change is needed.

## URLs

`#iliad.1.1` and `#odyssey.9.105` link to a work, book and line. A bare
`#6.440` still resolves to the Iliad.

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
| `tools/build.py` | Lists the works, fetches sources, drives the whole build |
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
