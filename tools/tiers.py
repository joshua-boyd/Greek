"""Shared fuzzy-matching tiers for lining lexicon headwords up with treebank lemmas.

Perseus lemmas, LSJ headwords and Wiktionary headwords agree most of the time but
differ in diaeresis ("διίστημι" vs "διΐστημι") and in vowel-length marks, so we
try progressively looser keys and take the first that hits.
"""

import unicodedata

ACCENTS = dict.fromkeys(
    [0x0300, 0x0301, 0x0342, 0x0308, 0x0313, 0x0314, 0x0345, 0x0304, 0x0306]
)
LENGTH = dict.fromkeys([0x0304, 0x0306])


def _nfd(s):
    return unicodedata.normalize("NFD", s)


def _nfc(s):
    return unicodedata.normalize("NFC", s)


def k_exact(s):
    return _nfc(_nfd(s).translate(LENGTH))


def k_nodia(s):
    return _nfc(_nfd(s).translate(LENGTH).replace("̈", ""))


def k_loose(s):
    return _nfc(_nfd(s).translate(ACCENTS)).lower()


NAMES = ("exact", "nodia", "loose")
FUNCS = (k_exact, k_nodia, k_loose)


class Matcher:
    """Collects glosses under every key tier, then resolves a lemma to the best hit."""

    def __init__(self, lemmas, limit=3):
        self.limit = limit
        self.wanted = {n: {f(l) for l in lemmas} for n, f in zip(NAMES, FUNCS)}
        self.tables = {n: {} for n in NAMES}

    def interesting(self, headword):
        """True if this headword could match something we are looking for."""
        return any(f(headword) in self.wanted[n] for n, f in zip(NAMES, FUNCS))

    def add(self, headword, glosses):
        for name, keyfn in zip(NAMES, FUNCS):
            key = keyfn(headword)
            if key not in self.wanted[name]:
                continue
            bucket = self.tables[name].setdefault(key, [])
            for g in glosses:
                if g not in bucket and len(bucket) < self.limit:
                    bucket.append(g)

    def get(self, lemma):
        for name, keyfn in zip(NAMES, FUNCS):
            hit = self.tables[name].get(keyfn(lemma))
            if hit:
                return hit
        return None
