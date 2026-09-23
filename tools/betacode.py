"""Minimal Perseus Beta Code -> Unicode converter, enough for LSJ headwords."""

import re
import unicodedata

LETTERS = {
    "a": "α", "b": "β", "g": "γ", "d": "δ", "e": "ε", "z": "ζ", "h": "η",
    "q": "θ", "i": "ι", "k": "κ", "l": "λ", "m": "μ", "n": "ν", "c": "ξ",
    "o": "ο", "p": "π", "r": "ρ", "s": "σ", "t": "τ", "u": "υ", "f": "φ",
    "x": "χ", "y": "ψ", "w": "ω", "v": "ϝ", "j": "ϳ",
}
BREATHING = {")": "̓", "(": "̔"}
ACCENT = {"/": "́", "\\": "̀", "=": "͂"}
DIAERESIS = {"+": "̈"}
SUBSCRIPT = {"|": "ͅ"}
MARKS = {}
for _d in (BREATHING, ACCENT, DIAERESIS, SUBSCRIPT):
    MARKS.update(_d)

TRAILING_DIGITS = re.compile(r"\d+$")


def convert(beta):
    """Convert a Beta Code string to composed (NFC) Unicode Greek."""
    out = []
    i = 0
    n = len(beta)
    while i < n:
        ch = beta[i]
        upper = False
        if ch == "*":
            upper = True
            i += 1
            pre = []
            while i < n and beta[i] in MARKS:
                pre.append(MARKS[beta[i]])
                i += 1
            if i >= n:
                break
            base = beta[i].lower()
            marks = pre
        elif ch.lower() in LETTERS:
            base = ch.lower()
            marks = []
            upper = ch.isupper()
        else:
            out.append(ch)
            i += 1
            continue

        i += 1
        while i < n and beta[i] in MARKS:
            marks.append(MARKS[beta[i]])
            i += 1

        letter = LETTERS[base]
        if base == "s" and not upper:
            nxt = beta[i] if i < n else ""
            if nxt == "" or (nxt.lower() not in LETTERS and nxt not in MARKS):
                letter = "ς"
        if upper:
            letter = letter.upper()

        # canonical ordering: breathing/diaeresis, accent, iota subscript
        order = {"̓": 0, "̔": 0, "̈": 0,
                 "́": 1, "̀": 1, "͂": 1, "ͅ": 2}
        marks.sort(key=lambda m: order.get(m, 3))
        out.append(letter + "".join(marks))
        continue

    return unicodedata.normalize("NFC", "".join(out))


def headword(beta):
    """Convert an LSJ key, dropping the homograph number LSJ appends."""
    return convert(TRAILING_DIGITS.sub("", beta))


if __name__ == "__main__":
    tests = [
        ("*)axilleu/s", "Ἀχιλλεύς"),
        ("mh=nis", "μῆνις"),
        ("a)ei/dw", "ἀείδω"),
        ("qea/", "θεά"),
        ("*zeu/s", "Ζεύς"),
        ("ou)lo/menos", "οὐλόμενος"),
        ("yuxh/", "ψυχή"),
        ("o(", "ὁ"),
        ("a)nh/r", "ἀνήρ"),
        ("ku/wn", "κύων"),
        ("ti/qhmi", "τίθημι"),
        ("dii+/sthmi", "διίστημι"),
        ("*(/aidhs", "Ἅιδης"),
        ("qeo/s", "θεός"),
        ("a)/lgos", "ἄλγος"),
        ("gi/gnomai", "γίγνομαι"),
        ("w)|dh/", "ᾠδή"),
        ("*)aqh=nai", "Ἀθῆναι"),
    ]
    bad = 0
    for beta, want in tests:
        got = headword(beta)
        ok = got == unicodedata.normalize("NFC", want)
        if not ok:
            bad += 1
        print(("ok  " if ok else "FAIL"), beta, "->", got, "" if ok else ("want " + want))
    print("failures:", bad)
