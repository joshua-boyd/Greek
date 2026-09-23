#!/usr/bin/env python3
"""Extract short English glosses from the Perseus LSJ TEI files.

LSJ entries are long and citation-heavy. The useful part is the <tr> elements,
which hold the editors' own translations of the headword; everything else is
quotations, cognates and bibliography.
"""

import glob
import os
import re
import unicodedata
import xml.etree.ElementTree as ET

from betacode import headword

ENTRY_RE = re.compile(r"<entryFree\b.*?</entryFree>", re.S)
KEY_RE = re.compile(r'\bkey="([^"]*)"')

# elements whose content is never part of a gloss
DROP = {"bibl", "cit", "quote", "foreign", "etym", "gramGrp", "gram", "orth",
        "gen", "date", "author", "title", "biblScope", "pb", "cb", "ref",
        "itype", "pron", "usg", "abbr"}

ENGLISH_OK = re.compile(r"^[A-Za-z0-9 ,;:'’&()/.\-—…!?\[\]]+$")
JUNK = re.compile(r"^(cf|v|sq|etc|ib|Ib|NT|LXX|sc|prob|abs|pl|sg|Adj|Adv|Subst)\.?$")

# treebank spellings that use a spacing character where a combining mark belongs
SPACING_ACCENTS = {
    "~": "͂",
    "´": "́",
    "ˊ": "́",
    "ˋ": "̀",
    "`": "̀",
}
STRAY_PREFIX = re.compile("^[̓̔ʽʼ᾽῾]+")


def clean(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^[\s,;:.\-—·]+", "", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\s+([,;.])", r"\1", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip(" ,;:.—- ")


def tr_text(el):
    """Text of a <tr>, minus any citation apparatus nested inside it."""
    parts = [el.text or ""]
    for child in el:
        if child.tag not in DROP:
            parts.append("".join(child.itertext()))
        parts.append(child.tail or "")
    return clean("".join(parts))


def usable(txt):
    """Keep plain-English glosses; drop Sanskrit/Latin cognates and stubs."""
    if not txt or len(txt) < 2 or len(txt) > 120:
        return False
    if not ENGLISH_OK.match(txt):
        return False
    if JUNK.match(txt):
        return False
    return any(c.isalpha() for c in txt)


def gloss_from_entry(xml):
    """Prefer <tr> translations that gloss the headword itself."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None

    # <tr> inside <etym> renders cognates ("nar", "nṛ"), not a definition.
    in_etym = set()
    for etym in root.iter("etym"):
        for el in etym.iter("tr"):
            in_etym.add(id(el))

    trs = []
    for sense in root.iter("sense"):
        for child in sense:
            if child.tag != "tr" or id(child) in in_etym:
                continue
            txt = tr_text(child)
            if usable(txt) and txt.lower() not in (t.lower() for t in trs):
                trs.append(txt)
        if len(trs) >= 4:
            break
    if trs:
        return "; ".join(trs[:4])

    # Fall back to the running prose of the first sense.
    sense = root.find(".//sense")
    if sense is None:
        sense = root  # short entries put their gloss straight in <entryFree>
    parts = []
    if sense.text:
        parts.append(sense.text)
    for child in sense:
        if child.tag in DROP:
            if child.tail:
                parts.append(child.tail)
            continue
        parts.append("".join(child.itertext()))
        if child.tail:
            parts.append(child.tail)
    txt = clean("".join(parts))
    txt = re.split(r"(?<=[a-z])[.;](?=\s|$)", txt)[0]
    txt = clean(txt)
    if len(txt) > 160:
        txt = txt[:157].rsplit(" ", 1)[0] + "…"
    return txt or None


def norm_lemma(raw):
    """Clean up annotation noise in treebank lemmas.

    A few carry a stray leading breathing character ('ʽἁλοσύδνη'), or spell a
    circumflex as '~' and an acute as a spacing accent ('ει´κω').
    """
    s = unicodedata.normalize("NFC", raw.strip())
    s = STRAY_PREFIX.sub("", s)
    if any(c in s for c in SPACING_ACCENTS):
        d = unicodedata.normalize("NFD", s)
        for bad, good in SPACING_ACCENTS.items():
            d = d.replace(bad, good)
        s = unicodedata.normalize("NFC", d)
    return s


def load(lsj_dir, matcher):
    for path in sorted(glob.glob(os.path.join(lsj_dir, "*.xml"))):
        data = open(path, encoding="utf-8").read()
        for m in ENTRY_RE.finditer(data):
            block = m.group(0)
            km = KEY_RE.search(block)
            if not km:
                continue
            key = headword(km.group(1))
            if not key or not matcher.interesting(key):
                continue
            g = gloss_from_entry(block)
            if g:
                matcher.add(key, [g])
