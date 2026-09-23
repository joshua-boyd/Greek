/* Homer, Iliad — an annotated reader.
 *
 * Every token rendered here is a distinct record from the Perseus treebank,
 * addressed by its position in the poem. Nothing is looked up by spelling, so
 * two identically spelled words keep their own separate annotations.
 */
(function () {
  "use strict";

  var BOOK_NAMES = [
    "Α", "Β", "Γ", "Δ", "Ε", "Ζ", "Η", "Θ", "Ι", "Κ", "Λ", "Μ",
    "Ν", "Ξ", "Ο", "Π", "Ρ", "Σ", "Τ", "Υ", "Φ", "Χ", "Ψ", "Ω"
  ];

  /* Perseus/AGDT nine-character postag, one slot per feature. */
  var MORPH = [
    { key: "pos", map: {
      n: "noun", v: "verb", t: "participle", a: "adjective", d: "adverb",
      l: "article", g: "particle", c: "conjunction", r: "preposition",
      p: "pronoun", m: "numeral", i: "interjection", e: "exclamation",
      u: "punctuation", x: "unclassified"
    } },
    { key: "person", map: { 1: "1st person", 2: "2nd person", 3: "3rd person" } },
    { key: "number", map: { s: "singular", p: "plural", d: "dual" } },
    { key: "tense", map: {
      p: "present", i: "imperfect", r: "perfect", l: "pluperfect",
      t: "future perfect", f: "future", a: "aorist"
    } },
    { key: "mood", map: {
      i: "indicative", s: "subjunctive", o: "optative", n: "infinitive",
      m: "imperative", p: "participle", d: "gerund", g: "gerundive"
    } },
    { key: "voice", map: {
      a: "active", p: "passive", m: "middle", e: "medio-passive"
    } },
    { key: "gender", map: { m: "masculine", f: "feminine", n: "neuter" } },
    { key: "case", map: {
      n: "nominative", g: "genitive", d: "dative", a: "accusative",
      v: "vocative", l: "locative"
    } },
    { key: "degree", map: { c: "comparative", s: "superlative" } }
  ];

  /* AGDT dependency labels. */
  var RELATIONS = {
    PRED: "main verb of the sentence",
    SBJ: "subject",
    OBJ: "object",
    ATR: "modifies a noun",
    ATV: "predicative complement",
    AtvV: "predicative complement",
    PNOM: "predicate noun (with “to be”)",
    OCOMP: "object complement",
    ADV: "adverbial",
    COORD: "coordinating word",
    APOS: "appositive marker",
    AuxP: "preposition",
    AuxC: "subordinating conjunction",
    AuxV: "auxiliary verb",
    AuxR: "reflexive passive",
    AuxX: "comma",
    AuxG: "bracketing punctuation",
    AuxK: "sentence-final punctuation",
    AuxY: "sentence adverbial",
    AuxZ: "emphasising particle",
    ExD: "governing word is omitted",
    UNDEFINED: "unannotated"
  };

  var el = {
    text: document.getElementById("text"),
    list: document.getElementById("book-list"),
    popup: document.getElementById("popup"),
    sidebar: document.getElementById("sidebar"),
    reader: document.getElementById("reader"),
    jump: document.getElementById("jump"),
    form: document.getElementById("p-form"),
    ref: document.getElementById("p-ref"),
    gloss: document.getElementById("p-gloss"),
    lemma: document.getElementById("p-lemma"),
    parse: document.getElementById("p-parse"),
    rel: document.getElementById("p-rel"),
    src: document.getElementById("p-src"),
    logeion: document.getElementById("p-logeion")
  };

  var lexicon = null;
  var current = null;       // the book currently rendered
  var tokens = [];          // flat token list for the rendered book
  var activeWord = null;
  var bookCache = {};

  /* ---------------- data ---------------- */

  function getJSON(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error(url + " → " + r.status);
      return r.json();
    });
  }

  function loadBook(n) {
    if (bookCache[n]) return Promise.resolve(bookCache[n]);
    return getJSON("data/iliad/book-" + n + ".json").then(function (d) {
      bookCache[n] = d;
      return d;
    });
  }

  /* ---------------- morphology ---------------- */

  function isPunct(tag) {
    return tag.charAt(0) === "u";
  }

  function describe(tag) {
    if (!tag) return [];
    var out = [];
    for (var i = 0; i < MORPH.length && i < tag.length; i++) {
      var c = tag.charAt(i);
      if (c === "-" || c === "") continue;
      var name = MORPH[i].map[c];
      if (name) out.push(name);
    }
    return out;
  }

  function feat(tag, slot) {
    var c = tag.charAt(slot);
    if (!c || c === "-") return "";
    return MORPH[slot].map[c] || "";
  }

  var SLOT = { POS: 0, PERSON: 1, NUMBER: 2, TENSE: 3, MOOD: 4, VOICE: 5,
               GENDER: 6, CASE: 7, DEGREE: 8 };

  /* Say it the way a grammar would: "present medio-passive participle,
     masculine nominative singular" rather than raw slot order. */
  function parseLine(tag) {
    if (!tag) return "not annotated";

    var pos = feat(tag, SLOT.POS) || "word";
    var mood = feat(tag, SLOT.MOOD);
    var tense = feat(tag, SLOT.TENSE);
    var voice = feat(tag, SLOT.VOICE);
    var person = feat(tag, SLOT.PERSON);
    var number = feat(tag, SLOT.NUMBER);
    var gender = feat(tag, SLOT.GENDER);
    var kase = feat(tag, SLOT.CASE);
    var degree = feat(tag, SLOT.DEGREE);

    var nominal = [gender, kase, number].filter(Boolean).join(" ");
    var groups = [];

    if (mood === "participle") {
      groups.push([tense, voice, "participle"].filter(Boolean).join(" "));
      if (nominal) groups.push(nominal);
    } else if (mood === "infinitive") {
      groups.push([tense, voice, "infinitive"].filter(Boolean).join(" "));
    } else if (mood) {
      groups.push([tense, voice, mood].filter(Boolean).join(" "));
      var agree = [person, number].filter(Boolean).join(" ");
      if (agree) groups.push(agree);
    } else if (nominal) {
      groups.push(nominal);
    } else {
      var rest = [tense, voice, person, number].filter(Boolean).join(" ");
      if (rest) groups.push(rest);
    }

    if (degree) groups.push(degree);
    return groups.length ? pos + " — " + groups.join(", ") : pos;
  }

  function relationLabel(rel) {
    if (!rel) return "—";
    var base = rel.replace(/_(CO|AP)$/, "");
    var note = RELATIONS[base] || base;
    if (/_CO$/.test(rel)) note += " (one of two or more coordinated)";
    if (/_AP$/.test(rel)) note += " (part of an appositive)";
    return note + " · " + rel;
  }

  /* ---------------- glosses ---------------- */

  var PATRONYMIC = /(ίδης|ιάδης|άδης|ΐδης|ίδαο|ιάδαο)$/;

  function glossFor(lemma, tag) {
    var hit = lexicon && Object.prototype.hasOwnProperty.call(lexicon, lemma)
      ? lexicon[lemma] : null;
    if (hit) return { text: hit[0], src: hit[1] === 0 ? "Wiktionary" : "LSJ" };

    // Most gaps are minor Homeric names, absent from both dictionaries.
    if (lemma && lemma.charAt(0) !== lemma.charAt(0).toLowerCase()) {
      if (PATRONYMIC.test(lemma)) {
        return { text: "proper name (patronymic — “son/descendant of”)", src: null, weak: true };
      }
      return { text: "proper name", src: null, weak: true };
    }
    if (!lemma) return { text: "no dictionary form recorded", src: null, weak: true };
    return { text: "no definition available", src: null, weak: true };
  }

  /* ---------------- rendering ---------------- */

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function render(book) {
    current = book;
    tokens = [];

    var html = ['<h2 class="book-title"><small>Iliad · Book ' + book.book +
      "</small>Ἰλιάς " + BOOK_NAMES[book.book - 1] + "</h2>"];

    for (var i = 0; i < book.lines.length; i++) {
      var line = book.lines[i];
      var n = line.n;
      var showNum = (n % 5 === 0) || n === 1 || i === book.lines.length - 1;
      var pieces = [];

      for (var j = 0; j < line.w.length; j++) {
        var w = line.w[j];
        var form = w[0];
        var lemma = book.lemmas[w[1]];
        var tag = book.postags[w[2]] || "";
        var rel = book.rels[w[3]] || "";
        var idx = tokens.length;
        tokens.push({ form: form, lemma: lemma, tag: tag, rel: rel, line: n });

        if (isPunct(tag) || (!tag && /^[.,;·:!?'"’·;]+$/.test(form))) {
          pieces.push('<span class="punct">' + esc(form) + "</span>");
        } else {
          var unknown = !lemma ? " unknown" : "";
          pieces.push(
            (pieces.length ? " " : "") +
            '<span class="w' + unknown + '" data-t="' + idx + '">' + esc(form) + "</span>"
          );
        }
      }

      html.push(
        '<div class="line" id="l' + book.book + "-" + n + '">' +
        '<span class="lnum">' + (showNum ? n : "") + "</span>" +
        '<span class="line-text">' + pieces.join("") + "</span>" +
        "</div>"
      );
    }

    el.text.innerHTML = html.join("");
    hidePopup();
  }

  /* ---------------- popup ---------------- */

  function showPopup(span) {
    var t = tokens[+span.dataset.t];
    if (!t) return;

    if (activeWord) activeWord.classList.remove("active");
    activeWord = span;
    span.classList.add("active");

    var g = glossFor(t.lemma, t.tag);

    el.form.textContent = t.form;
    el.ref.textContent = "Il. " + current.book + "." + t.line;
    el.gloss.textContent = g.text;
    el.gloss.className = "p-gloss" + (g.weak ? " none" : "");
    el.lemma.textContent = t.lemma || "—";
    el.lemma.className = t.lemma ? "greek-val" : "";
    el.parse.textContent = parseLine(t.tag);
    el.rel.textContent = relationLabel(t.rel);
    el.src.textContent = g.src ? g.src : "";

    if (t.lemma) {
      el.logeion.href = "https://logeion.uchicago.edu/" + encodeURIComponent(t.lemma);
      el.logeion.hidden = false;
    } else {
      el.logeion.hidden = true;
    }

    el.popup.hidden = false;
    position(span);
  }

  var GAP = 10;      // space between the word and the popup
  var MARGIN = 8;    // keep this far clear of the viewport edges

  function position(span) {
    var pop = el.popup;
    pop.classList.remove("below");

    // The popup is a child of <body>, so it is placed in document coordinates.
    var sx = window.pageXOffset;
    var sy = window.pageYOffset;
    var word = span.getBoundingClientRect();
    var col = el.text.getBoundingClientRect();
    var bar = document.querySelector(".topbar").getBoundingClientRect().bottom;

    // Pick whichever side of the word has more room, then cap the popup to it
    // so it never runs off a short window.
    var roomAbove = word.top - bar - GAP - MARGIN;
    var roomBelow = window.innerHeight - word.bottom - GAP - MARGIN;
    pop.style.maxHeight = "";
    var natural = pop.offsetHeight;
    var below = natural > roomAbove && roomBelow > roomAbove;
    var room = below ? roomBelow : roomAbove;
    pop.style.maxHeight = Math.max(120, room) + "px";

    var h = pop.offsetHeight;
    var w = pop.offsetWidth;

    // centred on the word, but kept inside the text column and the viewport
    var centre = word.left + word.width / 2;
    var left = centre - w / 2;
    var minLeft = Math.max(MARGIN, Math.min(col.left, window.innerWidth - w - MARGIN));
    var maxLeft = Math.max(minLeft, Math.min(col.right, window.innerWidth - MARGIN) - w);
    if (left < minLeft) left = minLeft;
    if (left > maxLeft) left = maxLeft;

    var top = below ? word.bottom + GAP : word.top - h - GAP;
    pop.classList.toggle("below", below);

    pop.style.left = (left + sx) + "px";
    pop.style.top = (top + sy) + "px";

    // keep the arrow pointing at the word even when the popup was clamped;
    // it would scroll away from the edge once the popup scrolls internally
    pop.classList.toggle("clipped", pop.scrollHeight > pop.clientHeight + 1);
    var arrow = pop.querySelector(".popup-arrow");
    var ax = centre - left - 5.5;
    arrow.style.left = Math.min(Math.max(ax, 12), w - 23) + "px";
  }

  function hidePopup() {
    el.popup.hidden = true;
    if (activeWord) activeWord.classList.remove("active");
    activeWord = null;
  }

  /* ---------------- navigation ---------------- */

  function selectBook(n, lineNo, push) {
    n = Math.min(24, Math.max(1, n | 0));
    el.text.innerHTML = '<p class="loading">Loading Book ' + n + "…</p>";

    Array.prototype.forEach.call(el.list.querySelectorAll("button"), function (b) {
      b.setAttribute("aria-current", String(+b.dataset.book === n));
    });

    return loadBook(n).then(function (book) {
      render(book);
      if (lineNo) {
        goToLine(n, lineNo);
      } else {
        el.reader.scrollTop = 0;
        window.scrollTo(0, 0);
      }
      if (push !== false) {
        history.replaceState(null, "", "#" + n + (lineNo ? "." + lineNo : ""));
      }
      el.sidebar.classList.remove("open");
    }).catch(function (e) {
      el.text.innerHTML = '<p class="error">Could not load Book ' + n +
        ". " + esc(e.message) + "</p>";
    });
  }

  function goToLine(book, line) {
    var target = document.getElementById("l" + book + "-" + line);
    if (!target) return false;
    Array.prototype.forEach.call(el.text.querySelectorAll(".line.target"),
      function (d) { d.classList.remove("target"); });
    target.classList.add("target");
    target.scrollIntoView({ block: "center", behavior: "smooth" });
    return true;
  }

  function parseRef(s) {
    var m = /^\s*(\d{1,2})(?:[.:\s]+(\d{1,4}))?\s*$/.exec(s || "");
    if (!m) return null;
    return { book: +m[1], line: m[2] ? +m[2] : 0 };
  }

  function fromHash() {
    return parseRef(location.hash.replace(/^#/, "")) || { book: 1, line: 0 };
  }

  /* ---------------- wiring ---------------- */

  function buildSidebar() {
    var html = "";
    for (var i = 1; i <= 24; i++) {
      html += '<li><button type="button" data-book="' + i + '">' +
        "<span>Book " + i + "</span>" +
        '<span class="greek">' + BOOK_NAMES[i - 1] + "</span></button></li>";
    }
    el.list.innerHTML = html;
    el.list.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-book]");
      if (b) selectBook(+b.dataset.book);
    });
  }

  function wire() {
    el.text.addEventListener("click", function (e) {
      var span = e.target.closest(".w");
      if (span) {
        e.stopPropagation();
        if (span === activeWord) hidePopup();
        else showPopup(span);
      }
    });

    document.addEventListener("click", function (e) {
      if (el.popup.hidden) return;
      if (!el.popup.contains(e.target)) hidePopup();
    });

    el.popup.querySelector(".popup-close").addEventListener("click", hidePopup);

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") hidePopup();
    });

    window.addEventListener("resize", function () {
      if (!el.popup.hidden && activeWord) position(activeWord);
    });

    el.jump.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      var ref = parseRef(el.jump.value);
      if (!ref) return;
      if (current && ref.book === current.book) {
        goToLine(ref.book, ref.line);
        history.replaceState(null, "", "#" + ref.book + "." + ref.line);
      } else {
        selectBook(ref.book, ref.line);
      }
      el.jump.blur();
    });

    document.getElementById("menu-toggle").addEventListener("click", function () {
      var open = el.sidebar.classList.toggle("open");
      this.setAttribute("aria-expanded", String(open));
    });

    var theme = document.getElementById("theme");
    if (localStorage.getItem("iliad-theme") === "dark") {
      document.body.classList.add("dark");
    }
    theme.addEventListener("click", function () {
      var dark = document.body.classList.toggle("dark");
      localStorage.setItem("iliad-theme", dark ? "dark" : "light");
    });

    window.addEventListener("hashchange", function () {
      var ref = fromHash();
      if (current && ref.book === current.book) {
        if (ref.line) goToLine(ref.book, ref.line);
      } else {
        selectBook(ref.book, ref.line, false);
      }
    });
  }

  function start() {
    buildSidebar();
    wire();

    var ref = fromHash();
    // The text is readable before the dictionary arrives; glosses fill in after.
    getJSON("data/lexicon.json").then(function (d) { lexicon = d; }).catch(function () {
      lexicon = {};
    });
    selectBook(ref.book, ref.line);
  }

  start();
})();
