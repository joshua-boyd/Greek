# Greek Reader

A static website for reading Homer's *Iliad* and *Odyssey* and the speeches of
Lysias in Greek. Pick a work and a book from the sidebar, then click any word
to see its dictionary form, a full morphological parse, its syntactic function
and an English definition. The popup stays open until you click somewhere else.

In the spirit of [greekbible.com](https://www.greekbible.com/), but for
classical Greek.

## How the annotations work

Every token is addressed **by its position in the text**, not by its spelling.
Each word in `data/<work>/book-N.json` is a separate record carrying its own
lemma, morphology tag and dependency relation, exactly as the Perseus
annotators assigned them at that spot. Two identically spelled words therefore
never share an analysis — ambiguous forms like `τε`, `ἣ` or `τοῦ` each get
whatever was annotated in that specific place.

The only thing looked up by key is the English definition, which is keyed on the
lemma the annotators already chose for that token.

## Coverage

| Work | Divisions | Units | Tokens |
| --- | --- | --- | --- |
| Iliad | 24 books | 15,683 lines | 128,102 |
| Odyssey | 24 books | 12,057 lines | 104,200 |
| Lysias | 4 orations (1, 14, 15, 23) | 298 sentences | 7,123 |

All three share one lexicon, covering 90.4% of 9,287 distinct lemmas. The
remaining gaps are almost entirely minor proper names, absent from both
dictionaries; the reader labels those as names and flags patronymics.

### A caveat about Lysias

Homer's treebank tags every word with `cite="urn:...:BOOK.LINE"`, so those
texts are navigable and citable by canonical line. **The Lysias files carry no
`cite` attributes at all**, and give every sentence the same whole-speech
`subdoc` (`1-50` for Oration 1). Canonical section numbers are therefore simply
not present in the data.

Rather than invent them, the reader numbers Lysias **by sentence** and says so
both on the page and in the popup, which reads `Lys. 1 · sentence 12` instead
of pretending to be `Lys. 1.4`. Recovering true sections would mean aligning
the treebank against the sectioned TEI text in Perseus's `canonical-greekLit`
word by word — doable, but a separate job.

Only four of Lysias's speeches are treebanked; the rest of the corpus has no
morphological annotation in this dataset.

## Adding another text

Append an entry to `WORKS` in `tools/build.py` and rerun the build. A *verse*
work is one source file split into books by citation; a *prose* work lists its
parts, each its own file, with a title per part. The JSON, the shared lexicon
and the site's pickers all follow from that list; no front-end change is
needed. Hesiod, the tragedians, Herodotus Book 1 and several Plato dialogues
are all available in the same treebank.

## URLs

`#iliad.1.1` and `#odyssey.9.105` link to a work, book and line;
`#lysias.23.5` works the same way for a speech and sentence. A bare `#6.440`
still resolves to the Iliad.

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
| `tools/build_text.py` | Treebank XML → one JSON file per book or speech |
| `tools/build_lexicon.py` | Merges both dictionaries into `data/lexicon.json` |
| `tools/lsj.py` | Pulls glosses out of LSJ's TEI markup |
| `tools/wiktionary.py` | Pulls glosses out of the Wiktionary dump |
| `tools/betacode.py` | Beta Code → Unicode, for LSJ headwords |
| `tools/tiers.py` | Tolerant headword matching across the three sources |

### Notes on the build

- Nodes marked `artificial="elliptic"` are annotator placeholders for words the
  author omits. They carry no text and are dropped.
- Punctuation has no citation of its own and inherits the line of the word
  beside it (verse only; prose groups by sentence).
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
