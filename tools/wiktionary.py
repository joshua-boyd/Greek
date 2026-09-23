"""Extract short English glosses for Ancient Greek lemmas from a kaikki.org dump."""

import json
import re

FORM_OF = re.compile(
    r"^(inflection|inflected form|form|alternative form|alternative spelling|"
    r"misspelling|abbreviation|contraction|obsolete form|"
    r"nominative|genitive|dative|accusative|vocative|first|second|third|"
    r"singular|plural|dual|present|aorist|perfect|imperfect|future|"
    r"masculine|feminine|neuter|comparative|superlative|verbal noun)\b.*\bof\b",
    re.I,
)
PAREN_ONLY = re.compile(r"^\(.*\)$")
LEADING_LABEL = re.compile(r"^\((?:[^()]*)\)\s*")

SKIP_POS = {"suffix", "prefix", "infix", "interfix", "phrase", "proverb",
            "character", "punct", "romanization", "abbrev"}


def load(path, matcher):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            word = d.get("word")
            if not word or d.get("pos") in SKIP_POS:
                continue
            if not matcher.interesting(word):
                continue
            glosses = []
            for sense in d.get("senses", []):
                tags = sense.get("tags") or []
                if "form-of" in tags or "alt-of" in tags:
                    continue
                for g in sense.get("glosses") or []:
                    g = re.sub(r"\s+", " ", g).strip()
                    g = LEADING_LABEL.sub("", g)  # drop "(poetic)" style prefixes
                    g = g.rstrip(" .")  # glosses get joined with "; "
                    if not g or len(g) > 140 or FORM_OF.match(g) or PAREN_ONLY.match(g):
                        continue
                    if g not in glosses:
                        glosses.append(g)
                if len(glosses) >= 3:
                    break
            if glosses:
                matcher.add(word, glosses[:3])
