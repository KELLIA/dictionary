import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import NetworkGraph from './NetworkGraph';
import { preloadIndexData } from './indexDataCache';
import { SiteHeader, SiteFooter } from './SiteChrome';
import useSharedSearchNavbarSettings from './useSharedSearchNavbarSettings';
import { withBasePath } from './basePath';

// -- CACHE DEFINITION --
// Persists detail file JSONs in memory for the duration of the session
const detailsCache = new Map();

// Mapping of dictionary abbreviation patterns to their full citations
const BIBL_SOURCES = [
  { regex: /(Kasser )?CDC/, expansion: "R. Kasser, Compléments au dictionnaire copte de Crum, Kairo: Inst. Français d'Archéologie Orientale, 1964" },
  { regex: /KoptHWb/, expansion: "Koptisches Handwörterbuch / W. Westendorf" },
  { regex: /CED/, expansion: "J. Černý, Coptic Etymological Dictionary, Cambridge: Cambridge Univ. Press, 1976" },
  { regex: /DELC/, expansion: "W. Vycichl, Dictionnaire étymologique de la langue copte, Leuven: Peeters, 1983" },
  { regex: /ChLCS/, expansion: "P. Cherix, Lexique Copte (dialecte sahidique), Copticherix, 2006-2018" },
  { regex: /ONB/, expansion: "T. Orlandi, Koptische Papyri theologischen Inhalts (Mitteilungen aus der Papyrussammlung der Österreichischen Nationalbibliothek (Papyrus Erzherzog Rainer) / Neue Serie, 9), Wien: Hollinek, 1974" },
  { regex: /WbGWKDT/, expansion: "H. Förster, Wörterbuch der griechischen Wörter in den koptischen dokumentarischen Texten. Berlin/Boston: de Gruyter, 2002" },
  { regex: /LCG/, expansion: "B. Layton, A Coptic grammar: with a chrestomathy and glossary; Sahidic dialect, Wiesbaden: Harrassowitz, 2000" },
  { regex: /Till D\.?/, expansion: "W. Till, Koptische Dialektgrammatik: mit Lesestücken und Wörterbuch, München: Beck, 1961" },
  { regex: /Osing, Pap\. Ox\./, expansion: "J. Osing: Der spätägyptische Papyrus BM 10808, Harrassowitz, Wiesbaden 1976" },
  { regex: /Bauer/, expansion: "W. Bauer, K. Aland, B. Aland, Griechisch-deutsches Wörterbuch zu den Schriften des Neuen Testaments und der frühchristlichen Literatur, Berlin: de Gruyter, 1988" },
  { regex: /BDAG/, expansion: "F.W. Danker, W. Bauer, A Greek-English Lexicon of the New Testament and other Early Christian Literature, Chicago/London: University of Chicago Press, 2000" },
  { regex: /Daris 1991/, expansion: "S. Daris, Il lessico Latino nel Greco d'Egitto (Estudis de Papirologia i Filologia Biblica 2), Barcelona: Ediciones Aldecoa, 1991" },
  { regex: /Denniston 1959/, expansion: "J.D. Denniston, The Greek Particles, London: Clarendon Press, 1959" },
  { regex: /du Cange/, expansion: "C. F. du Cange, Glossarium ad scriptores mediae et infimae Graecitatis I-II, Graz: Akademische Druck- und Verlagsanstalt, 1958" },
  { regex: /Hatch\/Redpath 1906/, expansion: "E. Hatch, H.A. Redpath, A concordance to the Septuagint and the other Greek versions of the Old Testament (including the apocryphal books), Supplement, Graz: Akademische Druck- und Verlagsanstalt, 1906" },
  { regex: /Kontopoulos/, expansion: "N. Kontopoulos, A Lexicon of Modern Greek-English and English-Modern Greek, Smyrna/London: B. Tatikidos, Trübner & Co., 1868" },
  { regex: /Lampe/, expansion: "G.W.H. Lampe, A patristic Greek lexicon, Oxford: Clarendon Press, 1978" },
  { regex: /LBG/, expansion: "E. Trapp, Lexikon zur byzantinischen Gräzität, besonderes des 9.-12. Jahrhunderts, Philosophisch-historische Klasse, Denkschriften (Veröffentlichungen der Kommission für Byzantinistik 238; VI/1-4) , Wien: Österreichische Akademie der Wissenschaften, 2001" },
  { regex: /LSJ Suppl\./, expansion: "H.G. Liddell, R. Scott, H.S. Jones, E.A. Barber, A Greek-English lexicon/Supplement, Oxford: Clarendon Press, 1968" },
  { regex: /LSJ/, expansion: "H.G. Liddell, R. Scott, H.S. Jones, A Greek-English lexicon, Oxford: Clarendon Press, 1968" },
  { regex: /Muraoka 2009/, expansion: "T. Muraoka, A Greek-English Lexicon of the Septuagint, Louvain/Paris/Walpole: Peeters, 2009" },
  { regex: /Passow/, expansion: "F. Passow, V.CF Rost, F. Palm, Handwörterbuch der griechischen Sprache, Leipzig: Vogel, 1841" },
  { regex: /Preisigke/, expansion: "F. Preisigke, Wörterbuch der griechischen Papyrusurkunden mit Einschluß der griechischen Inschriften, Aufschriften, Ostraka, Mumienschilder usw. aus Ägypten, Berlin: Selbstverlag der Erben, 1925-1931" },
  { regex: /Sophocles/, expansion: "E.A. Sophocles, Greek Lexicon of the Roman and Byzantine Periods (From B. C. 146 to A. D. 1100. Memorial Edition), Cambridge/Leipzig: Harvard University Press/Harrassowitz, 1914" },
  { regex: /T\. S\. Richter 2014b/, expansion: "T.S. Richter, Neue koptische medizinische Rezepte (Zeitschrift für Ägyptische Sprache und Altertumskunde ZÄS 141(2), 154-194), 2014" },
  { regex: /Till 1951a/, expansion: "W.C. Till, Arzneikunde der Kopten, Berlin: Akademie Verlag, 1951" },
  { regex: /TLG/, expansion: "L. Berkowitz, K.A. Squitier, Thesaurus Linguae Graecae (Canon of Greek Authors and Works), New York/Oxford: University Press, 1990" }
];

// ANNIS Search Configuration
const ANNIS_BASE_URL = "https://annis.copticscriptorium.org/annis/scriptorium#";
const ANNIS_SUFFIX = "&_bt=bm9ybV9ncm91cA&o=random";

// Add/modify ANNIS corpora for each dialect here
const ANNIS_CORPORA = {
  'B': 'bohairic.1corinthians,bohairic.mark,bohairic.life.isaac,bohairic.nt,bohairic.ot',
  'S': 'shenoute.a22,johannes.canons,shenoute.abraham,pseudo.basil,shenoute.dirt,sahidic.ot,shenoute.night,pistis.sophia,shenoute.true,pseudo.timothy,shenoute.thundered,pseudo.chrysostom,pseudo.theophilus,doc.papyri,pachomius.instructions,shenoute.house,shenoute.unknown5_1,shenoute.listen,life.cyrus,shenoute.errs,magical.papyri,pseudo.celestinus,shenoute.those,sahidica.nt,shenoute.crushed,martyrdom.victor,besa.letters,life.john.kalybites,shenoute.uncertain.xr,pseudo.athanasius.discourses,dormition.john,life.phib,pseudo.ephrem,life.onnophrius,apophthegmata.patrum,shenoute.seeks,life.paul.tamma,mysteries.john,sahidic.ruth,sahidica.mark,shenoute.place,shenoute.eagerness,life.aphou,shenoute.witness,life.eustathius.theopiste,proclus.homilies,john.constantinople,shenoute.considering,sahidica.1corinthians,shenoute.prince,shenoute.fox,pseudo.flavianus,life.longinus.lucius,life.pisentius,acts.pilate,book.bartholomew,helias,lament.mary,mercurius,theodosius.alexandria,thomas.gospel,sahidic.jonah',
};

const ENTITY_ICON_MAP = {
  'person': 'male',
  'time': 'clock-o',
  'abstract': 'cloud',
  'object': 'cube',
  'animal': 'paw',
  'plant': 'pagelines',
  'place': 'map-marker',
  'substance': 'flask',
  'organization': 'bank',
  'event': 'bell'
};

// Safely Base64 encode unicode strings for URLs
const unicodeBase64Encode = (str) => {
  return btoa(unescape(encodeURIComponent(str)));
};

// URL-safe Base64 encode string for ANNIS entity search
const urlsafeBase64Encode = (str) => {
  return btoa(unescape(encodeURIComponent(str)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
};

const getEntitySearchUrl = (lemma, entityType) => {
  if (!lemma) return null;

  let coptic = lemma
    .replace(/-/g, '')
    .replace(/\u0304/g, "")
    .replace(/\ufe26/g, "")
    .replace(/\ufe24/g, "")
    .replace(/\ufe25/g, "")
    .replace(/\u2013/g, '')
    .replace(/\u2E17/g, "");

  const annis_base = "https://annis.copticscriptorium.org/annis/scriptorium#";
  const corpus_list = "_c=Y29wdGljLnRyZWViYW5r"; 
  const segmentation = "_bt=bm9ybV9ncm91cA"; 
  const ordering = "o=random";
  const q = `entity="${entityType}" ->head lemma="${coptic}"`;
  const query = `_q=${urlsafeBase64Encode(q)}`;

  return `${annis_base}${query}&${corpus_list}&${segmentation}&${ordering}`;
};

// URL generators for ANNIS
const getAnnisFormUrl = (form, pos, dialect) => {
  form = form.replace(/[⸗-]/g, '');
  if (!dialect) return null;
  const corpora = ANNIS_CORPORA[dialect];
  if (!corpora) return null;
  
  const queryString = pos && pos !== "?" 
    ? `norm="${form}" _=_ pos="${pos}"`
    : `norm="${form}"`;
    
  return `${ANNIS_BASE_URL}_q=${unicodeBase64Encode(queryString)}&_c=${unicodeBase64Encode(corpora)}${ANNIS_SUFFIX}`;
};

const DIALECT_ALIASES = {
  SAHIDIC: 'S',
  BOHAIRIC: 'B',
};

const getAnnisLemmaUrl = (lemma, dialect) => {
  if (!dialect) return null;

  const rawDialect = String(dialect).trim();
  const normalizedDialect = DIALECT_ALIASES[rawDialect.toUpperCase()] || rawDialect;
  const corpora =
    ANNIS_CORPORA[normalizedDialect] ||
    ANNIS_CORPORA[normalizedDialect.toUpperCase()] ||
    ANNIS_CORPORA[normalizedDialect.toLowerCase()];

  if (!corpora) return null;
  
  const queryString = `lemma="${lemma.replace(/[⸗-]/g, '')}"`;
  return `${ANNIS_BASE_URL}_q=${unicodeBase64Encode(queryString)}&_c=${unicodeBase64Encode(corpora)}${ANNIS_SUFFIX}`;
};

const getUrnResolverUrl = (urn) => {
  if (!urn) return null;
  const normalizedUrn = String(urn).trim().replace(/^\/+/, '');
  return `https://data.copticscriptorium.org/${normalizedUrn}`;
};

const GREEK_TO_PERSEUS = {
  "́": "/", "̈": "+", "͂": "=", ",": ",", "-": "-", ".": ".", ";": ";", "`": "\\", "·": ":", "ʹ": "#", "ʼ": ")", "ʽ": "(", "Ά": "*/a", "Έ": "*/e", "Ή": "*/h", "Ί": "*/i", "Ό": "*/o", "Ύ": "*/u", "Ώ": "*/w", "ΐ": "i/+", "Α": "*a", "Β": "*b", "Γ": "*g", "Δ": "*d", "Ε": "*e", "Ζ": "*z", "Η": "*h", "Θ": "*q", "Ι": "*i", "Κ": "*k", "Λ": "*l", "Μ": "*m", "Ν": "*n", "Ξ": "*c", "Ο": "*o", "Π": "*p", "Ρ": "*r", "Σ": "*s", "Τ": "*t", "Υ": "*u", "Φ": "*f", "Χ": "*x", "Ψ": "*y", "Ω": "*w", "Ϊ": "*+i", "Ϋ": "*+u", "ά": "a/", "έ": "e/", "ή": "h/", "ί": "i/", "ΰ": "u/+", "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "h", "θ": "q", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "c", "ο": "o", "π": "p", "ρ": "r", "ς": "s", "σ": "s", "τ": "t", "υ": "u", "φ": "f", "χ": "x", "ψ": "y", "ω": "w", "ϊ": "i+", "ϋ": "u+", "ό": "o/", "ύ": "u/", "ώ": "w/", "ϲ": "s3", "Ϲ": "*s3", "ἀ": "a)", "ἁ": "a(", "ἂ": "a)\\", "ἃ": "a(\\", "ἄ": "a)/", "ἅ": "a(/", "ἆ": "a)=", "ἇ": "a(=", "Ἀ": "*)a", "Ἁ": "*(a", "Ἂ": "*)\\a", "Ἃ": "*(\\a", "Ἄ": "*)/a", "Ἅ": "*(/a", "Ἆ": "*)=a", "Ἇ": "*(=a", "ἐ": "e)", "ἑ": "e(", "ἒ": "e)\\", "ἓ": "e(\\", "ἔ": "e)/", "ἕ": "e(/", "Ἐ": "*)e", "Ἑ": "*(e", "Ἒ": "*)\\e", "Ἓ": "*(\\e", "Ἔ": "*)/e", "Ἕ": "*(/e", "ἠ": "h)", "ἡ": "h(", "ἢ": "h)\\", "ἣ": "h(\\", "ἤ": "h)/", "ἥ": "h(/", "ἦ": "h)=", "ἧ": "h(=", "Ἠ": "*)h", "Ἡ": "*(h", "Ἢ": "*)\\h", "Ἣ": "*(\\h", "Ἤ": "*)/h", "Ἥ": "*(/h", "Ἦ": "*)=h", "Ἧ": "*(=h", "ἰ": "i)", "ἱ": "i(", "ἲ": "i)\\", "ἳ": "i(\\", "ἴ": "i)/", "ἵ": "i(/", "ἶ": "i)=", "ἷ": "i(=", "Ἰ": "*)i", "Ἱ": "*(i", "Ἲ": "*)\\i", "Ἳ": "*(\\i", "Ἴ": "*)/i", "Ἵ": "*(/i", "Ἶ": "*)=i", "Ἷ": "*(=i", "ὀ": "o)", "ὁ": "o(", "ὂ": "o)\\", "ὃ": "o(\\", "ὄ": "o)/", "ὅ": "o(/", "̔": "(", "ὅ": "o(/", "Ὀ": "*)o", "Ὁ": "*(o", "Ὂ": "*)\\o", "Ὃ": "*(\\o", "Ὄ": "*)/o", "Ὅ": "*(/o", "ὐ": "u)", "ὑ": "u(", "ὒ": "u)\\", "ὓ": "u(\\", "ὔ": "u)/", "ὕ": "u(/", "ὖ": "u)=", "ὗ": "u(=", "Ὑ": "*(u", "Ὓ": "*(\\u", "Ὕ": "*(/u", "Ὗ": "*(=u", "ὠ": "w)", "ὡ": "w(", "ὢ": "w)\\", "ὣ": "w(\\", "ὤ": "w)/", "ὥ": "w(/", "ὦ": "w)=", "ὧ": "w(=", "Ὠ": "*)w", "Ὡ": "*(w", "Ὢ": "*)\\w", "Ὣ": "*(\\w", "Ὤ": "*)/w", "Ὥ": "*(/w", "Ὦ": "*)=w", "Ὧ": "*(=w", "ὰ": "a\\", "ὲ": "e\\", "ὴ": "h\\", "ὶ": "i\\", "ὸ": "o\\", "ὺ": "u\\", "ὼ": "w\\", "ᾀ": "a)|", "ᾁ": "a(|", "ᾂ": "a)\\|", "ᾃ": "a(\\|", "ᾄ": "a)/|", "ᾅ": "a(/|", "ᾆ": "a)=|", "ᾇ": "a(=|", "ᾈ": "*)|a", "ᾉ": "*(|a", "ᾊ": "*)\\|a", "ᾋ": "*(\\|a", "ᾌ": "*)/|a", "ᾍ": "*(/|a", "ᾎ": "*)=|a", "ᾏ": "*(=|a", "ᾐ": "h)|", "ᾑ": "h(|", "ᾒ": "h)\\|", "ᾓ": "h(\\|", "ᾔ": "h)/|", "ᾕ": "h(/|", "ᾖ": "h)=|", "ᾗ": "h(=|", "ᾘ": "*)|h", "ᾙ": "*(|h", "ᾚ": "*)\\|h", "ᾛ": "*(\\|h", "ᾜ": "*)/|h", "ᾝ": "*(/|h", "ᾞ": "*)=|h", "ᾟ": "*(=|h", "ᾠ": "w)|", "ᾡ": "w(|", "ᾢ": "w)\\|", "ᾣ": "w(\\|", "ᾤ": "w)/|", "ᾥ": "w(/|", "ᾦ": "w)=|", "ᾧ": "w(=|", "ᾨ": "*)|w", "ᾩ": "*(|w", "ᾪ": "*)\\|w", "ᾫ": "*(\\|w", "ᾬ": "*)/|w", "ᾭ": "*(/|w", "ᾮ": "*)=|w", "ᾯ": "*(=|w", "ᾲ": "a\\|", "ᾳ": "a|", "ᾴ": "a/|", "ᾶ": "a=", "ᾷ": "a=|", "Ὰ": "*\\a", "ᾼ": "*|a", "᾽": "'", "ῂ": "h\\|", "ῃ": "h|", "ῄ": "h/|", "ῆ": "h=", "ῇ": "h=|", "Ὲ": "*\\e", "Ὴ": "*\\h", "ῌ": "*|h", "ῒ": "i\\+", "ῖ": "i=", "ῗ": "i=+", "Ὶ": "*\\i", "ῢ": "u\\+", "ῤ": "r)", "ῥ": "r(", "ῦ": "u=", "ῧ": "u=+", "Ὺ": "*\\u", "Ῥ": "*(r", "ῲ": "w\\|", "ῳ": "w|", "ῴ": "w/|", "ῶ": "w=", "ῷ": "w=|", "Ὸ": "*\\o", "Ὼ": "*\\w", "ῼ": "*|w", "—": "_"
};

const convertGreekToPerseusAscii = (text) => {
  if (!text) return '';

  // Source data uses precomposed Greek polytonic code points, so direct lookup is sufficient.
  return Array.from(String(text)).map((ch) => GREEK_TO_PERSEUS[ch] ?? ch).join('');
};

const getLogeionUrl = (lemma) => {
  if (!lemma) return null;
  return `https://logeion.uchicago.edu/${encodeURIComponent(lemma)}`;
};

const getPerseusUrl = (lemma) => {
  if (!lemma) return null;
  const asciiLookup = convertGreekToPerseusAscii(lemma);
  if (!asciiLookup) return null;
  return `http://www.perseus.tufts.edu/hopper/resolveform?type=exact&lookup=${encodeURIComponent(asciiLookup)}&lang=greek`;
};

const getBiblTooltipHtml = (chunk) => {
  for (const src of BIBL_SOURCES) {
    if (src.regex.test(chunk)) {
      const safeExpansion = src.expansion.replace(/"/g, '&quot;');
      return `<a class="hint" data-tooltip="${safeExpansion}">?</a>`;
    }
  }
  return '';
};

const formatGreekReferences = (referenceString) => {
  if (!referenceString) return '';

  return referenceString
    .split(';')
    .map((chunk) => chunk.trim())
    .filter(Boolean)
    .map((chunk) => `${chunk}${getBiblTooltipHtml(chunk)}`)
    .join('; ');
};

// Helper to inject tooltips and special hyperlinks into the bibliography string
const formatBibliography = (biblString, tlaId) => {
  if (!biblString) return "";
  
  return biblString.split(';').map(chunk => {
    const cdRegex = /(CD ([0-9]+[ab]?)-?[0-9]*[ab]?)/;
    if (cdRegex.test(chunk)) {
      return chunk.replace(cdRegex, (match, p1, p2) => {
        return `<a href="https://coptot.manuscriptroom.com/crum-coptic-dictionary/?docID=800000&pageID=${p2}&tla=${tlaId}" target="_blank" rel="noreferrer" style="text-decoration-style: solid;">${p1}</a><a class="hint" data-tooltip="W.E. Crum's Dictionary">?</a>`;
      });
    }

    let tooltip;
    tooltip = getBiblTooltipHtml(chunk);
    return chunk + tooltip;
  }).join(';');
};

const compareExampleDialects = ([leftDialect], [rightDialect]) => {
  const priority = { sahidic: 0, bohairic: 1 };
  const leftPriority = priority[leftDialect] ?? 2;
  const rightPriority = priority[rightDialect] ?? 2;

  if (leftPriority !== rightPriority) {
    return leftPriority - rightPriority;
  }
  return leftDialect.localeCompare(rightDialect);
};

const getFormDialectSortKey = (dialect) => {
  const rawDialect = String(dialect || '').trim();
  const normalizedDialect = (DIALECT_ALIASES[rawDialect.toUpperCase()] || rawDialect).toUpperCase();

  if (normalizedDialect === 'S') return { priority: 0, label: normalizedDialect };
  if (normalizedDialect === 'B') return { priority: 1, label: normalizedDialect };

  return { priority: 2, label: normalizedDialect || '?' };
};

const sortEntryFormsByDialect = (forms = []) => {
  if (!Array.isArray(forms) || forms.length <= 1) return forms || [];

  return forms
    .map((form, index) => ({ form, index }))
    .sort((left, right) => {
      const leftDialect = getFormDialectSortKey(left.form?.dialect);
      const rightDialect = getFormDialectSortKey(right.form?.dialect);

      if (leftDialect.priority !== rightDialect.priority) {
        return leftDialect.priority - rightDialect.priority;
      }

      const labelComparison = leftDialect.label.localeCompare(rightDialect.label);
      if (labelComparison !== 0) {
        return labelComparison;
      }

      return left.index - right.index;
    })
    .map(({ form }) => form);
};

const getFreqStatValue = (stats, key) => stats?.[key] ?? 0;

const getLemmaFreqStatsForForm = (entry, form) => {
  const dialect = form?.dialect;
  if (!dialect) return null;
  return entry?.lemma_freqs?.[dialect] ?? null;
};

const getCollocationsForDialect = (collocations, dialect) => {
  if (!collocations || !dialect) return [];

  const rawDialect = String(dialect).trim();
  const normalizedDialect = DIALECT_ALIASES[rawDialect.toUpperCase()] || rawDialect;

  return (
    collocations[normalizedDialect] ||
    collocations[normalizedDialect.toUpperCase()] ||
    collocations[normalizedDialect.toLowerCase()] ||
    []
  );
};

const getTopFormForDialect = (forms, dialect) => {
  if (!Array.isArray(forms) || forms.length === 0 || !dialect) return null;

  const rawDialect = String(dialect).trim();
  const normalizedDialect = (DIALECT_ALIASES[rawDialect.toUpperCase()] || rawDialect).toUpperCase();

  return forms.find((form) => {
    const formDialect = String(form?.dialect || '').trim();
    if (!formDialect) return false;
    const normalizedFormDialect = (DIALECT_ALIASES[formDialect.toUpperCase()] || formDialect).toUpperCase();
    return normalizedFormDialect === normalizedDialect;
  }) || null;
};

const formMergeKey = (form) => {
  if (!form) return null;
  if (form.id) return `id:${form.id}`;
  const orth = form.orth || '';
  const dialect = form.dialect || '';
  const type = form.type || '';
  return `odt:${orth}|${dialect}|${type}`;
};

const mergeEntryForms = (detailForms = [], baseForms = []) => {
  if (!Array.isArray(baseForms) || baseForms.length === 0) return detailForms || [];
  if (!Array.isArray(detailForms) || detailForms.length === 0) return baseForms;

  const detailByKey = new Map();
  detailForms.forEach((form) => {
    const key = formMergeKey(form);
    if (key) detailByKey.set(key, form);
  });

  const baseKeys = new Set();
  const mergedBaseForms = baseForms.map((baseForm) => {
    const key = formMergeKey(baseForm);
    if (key) baseKeys.add(key);
    const detailForm = key ? detailByKey.get(key) : null;
    return {
      ...(baseForm || {}),
      ...(detailForm || {}),
    };
  });

  const trailingDetailForms = detailForms.filter((detailForm) => {
    const key = formMergeKey(detailForm);
    return !key || !baseKeys.has(key);
  });

  return [...mergedBaseForms, ...trailingDetailForms];
};

const mergeEntrySenses = (detailSenses = [], baseSenses = []) => {
  if (!Array.isArray(baseSenses) || baseSenses.length === 0) return detailSenses || [];
  if (!Array.isArray(detailSenses) || detailSenses.length === 0) return baseSenses;

  const detailById = new Map();
  detailSenses.forEach((sense) => {
    if (sense?.id) detailById.set(sense.id, sense);
  });

  const baseIds = new Set();
  baseSenses.forEach((sense) => {
    if (sense?.id) baseIds.add(sense.id);
  });

  const mergedBaseSenses = baseSenses.map((baseSense, index) => {
    const detailSense = (baseSense?.id && detailById.get(baseSense.id)) || detailSenses[index] || null;
    return {
      ...(detailSense || {}),
      ...(baseSense || {}),
    };
  });

  const trailingDetailSenses = detailSenses.filter((detailSense, index) => {
    if (detailSense?.id) {
      return !baseIds.has(detailSense.id);
    }
    return index >= baseSenses.length;
  });

  return [...mergedBaseSenses, ...trailingDetailSenses];
};

const getCrossReferenceTypeLabel = (type) => {
  const normalized = String(type || '').trim();
  if (!normalized) return 'cf.';
  if (normalized.toLowerCase() === 'cf') return 'cf.';
  return `${normalized}.`;
};

export default function Entry() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [entry, setEntry] = useState(() => {
    if (location.state?.preloadedEntry?.id === id) {
      return location.state.preloadedEntry;
    }
    return null;
  });
  
  // Split loading states to manage initial core render vs heavy data render
  const [isInitialLoading, setIsInitialLoading] = useState(!entry);
  const [isDetailLoading, setIsDetailLoading] = useState(!detailsCache.has(id));
  const [error, setError] = useState(null);
  const [searchInput, setSearchInput] = useState(() => location.state?.searchQuery || '');
  const [knownEntities, setKnownEntities] = useState([]);
  const shouldAutoFocusSearch = Boolean(location.state?.keepSearchFocus);
  
  const { navbarSettingsProps } = useSharedSearchNavbarSettings();

  useEffect(() => {
    let isSubscribed = true;
    const preloaded = location.state?.preloadedEntry;

    if (!entry || entry.id !== id) {
      setIsInitialLoading(true);
    }
    
    if (!detailsCache.has(id)) {
      setIsDetailLoading(true);
    } else {
      setIsDetailLoading(false);
    }

    const loadData = async () => {
      try {
        // 1. Fire BOTH network requests concurrently (using cache if available)
        const detailsPromise = (async () => {
          if (detailsCache.has(id)) {
            return detailsCache.get(id);
          }
          const res = await fetch(withBasePath(`details/${id}.json`));
          if (!res.ok) throw new Error("Entry not found");
          const data = await res.json();
          detailsCache.set(id, data);
          return data;
        })();

        const indexPromise = (preloaded && preloaded.id === id)
          ? Promise.resolve(null) // Skip fetch if we have the index data in router state
          : preloadIndexData().catch(() => fetch(withBasePath('index.json')).then(r => r.json()));

        const [detailsData, indexDataResult] = await Promise.all([
          detailsPromise, 
          indexPromise
        ]);

        if (!isSubscribed) return;

        // 2. Find the core index.json data
        let baseData = preloaded && preloaded.id === id ? preloaded : null;
        if (!baseData && Array.isArray(indexDataResult)) {
          baseData = indexDataResult.find(e => e.id === id);
        }

        const fullIndexData = Array.isArray(indexDataResult)
          ? indexDataResult
          : await preloadIndexData().catch(() => []);

        const lemmaById = new Map(
          (Array.isArray(fullIndexData) ? fullIndexData : [])
            .filter((entryItem) => entryItem?.id)
            .map((entryItem) => [entryItem.id, entryItem.lemma])
        );

        const explicitCrossReferences = (detailsData.crossReferences || []).map((ref) => ({
          ...ref,
          targetLemma: lemmaById.get(ref.target) || null,
        }));

        const mergedForms = mergeEntryForms(detailsData.forms, baseData?.forms);
        const mergedSenses = mergeEntrySenses(detailsData.senses, baseData?.senses);

        // 3. Assemble
        setEntry({
          ...detailsData,
          ...(baseData || {}),
          forms: mergedForms,
          senses: mergedSenses,
          examples: detailsData.examples || [],
          network: detailsData.network || {},
          collocations: detailsData.collocations || {},
          etym: detailsData.etym || null,
          crossReferences: explicitCrossReferences,
          superEntryReferences: detailsData.superEntryReferences || []
        });

        // 4. Set recognized entity types from index data
        setKnownEntities(baseData?.entities || []);
        
        setIsInitialLoading(false);
        setIsDetailLoading(false);
        setError(null);
      } catch (err) {
        if (!isSubscribed) return;
        console.error(err);
        setError(err.message);
        setIsInitialLoading(false);
        setIsDetailLoading(false);
      }
    };

    loadData();

    return () => { isSubscribed = false; };
  }, [id, location.state?.preloadedEntry]);

  const examplesByDialect = useMemo(() => {
    if (!entry || !entry.examples) return {};
    return entry.examples.reduce((acc, ex) => {
      if (!acc[ex.dialect]) acc[ex.dialect] = [];
      acc[ex.dialect].push(ex);
      return acc;
    }, {});
  }, [entry]);

  const orderedExamplesByDialect = useMemo(
    () => Object.entries(examplesByDialect).sort(compareExampleDialects),
    [examplesByDialect]
  );

  const orderedForms = useMemo(
    () => sortEntryFormsByDialect((entry?.forms || []).filter((form) => form?.type !== 'lemma')),
    [entry?.forms]
  );

  const formatExampleText = (text) => {
    if (!text) return null;
    const parts = text.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, i) => 
      i % 2 === 1 ? <span key={i} className="ex-sub-match" style={{ fontWeight: 'bold', color: '#d9534f' }}>{part}</span> : part
    );
  };

  const today = new Date().toISOString().split('T')[0];
  const lemmaForm = entry?.forms?.find(f => f.type === 'lemma') || entry?.forms?.[0] || {};
  const originalPos = entry?.grammar?.tlapos || entry?.pos || ""; 
  const scriptoriumPos = entry?.grammar?.pos || "?";
  const demoticLemma = entry?.etym?.demo_lemma && entry.etym.demo_lemma !== 'NA' ? entry.etym.demo_lemma : null;
  const egyptianLemma = entry?.etym?.egy_lemma || null;
  const greekEtymId = entry?.etym?.grl_ID || null;
  const greekEtymLemma = entry?.etym?.grl_lemma || null;
  const greekEtymMeaning = entry?.etym?.grl_meaning || null;
  const greekEtymPos = entry?.etym?.grl_pos || null;
  const greekEtymRef = entry?.etym?.grl_ref || null;
  const greekEtymPosTitle = greekEtymPos
    ? `${greekEtymPos.charAt(0).toUpperCase()}${greekEtymPos.slice(1)}`
    : null;
  const greekLogeionUrl = getLogeionUrl(greekEtymLemma);
  const greekPerseusUrl = getPerseusUrl(greekEtymLemma);
  const hasCompactEtymology = Boolean(demoticLemma || egyptianLemma);
  const hasGreekEtymology = Boolean(greekEtymId || greekEtymLemma || greekEtymMeaning || greekEtymPos || greekEtymRef);

  return (
    <div className="container">
      <SiteHeader
        sectionStyle={{ marginBottom: '15px' }}
        searchNavbarProps={{
          searchInput,
          onSearchInputChange: (nextValue) => {
            setSearchInput(nextValue);
            const trimmedValue = nextValue.trim();
            if (trimmedValue) {
              preloadIndexData().catch(() => {});
              navigate(`/?q=${encodeURIComponent(trimmedValue)}`, {
                replace: true,
                state: { keepSearchFocus: true },
              });
            } else {
              navigate('/', {
                replace: true,
                state: { keepSearchFocus: true },
              });
            }
          },
          autoFocus: shouldAutoFocusSearch,
          availablePos: [],
          ...navbarSettingsProps,
        }}
      />

    {/* Main Content Area */}
      {error ? (
        <div className="row"><div className="col-lg-12"><h3>Error: {error}</h3></div></div>
      ) : isInitialLoading || !entry ? (
        <div className="row"><div className="col-lg-12"><h3 className="text-muted">Loading entry core data...</h3></div></div>
      ) : (
        <>
          {/* Header */}
          <div className="bs-docs-section">
            <div className="row">
              <div className="col-lg-12">
                <div className="page-header">
                  <h2>
                    <span className="tla_no_header text-muted">TLA lemma no. {entry.id}</span><br/>
                    <span style={{ fontFamily: 'antinoouRegular, sans-serif', fontSize: 'larger' }}>{lemmaForm.orth}</span>
                  </h2>
                </div>
              </div>
            </div>

            <div className="row">
              <div className="col-lg-12">
                <div className="bs-component">
                  <div className="content">
                    
                    {/* FLEX LAYOUT: Prevents NetworkGraph from forcing tables to wrap arbitrarily */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '30px', alignItems: 'flex-start' }}>
                      
                      {/* Left Column: Core Forms and Senses */}
                      <div style={{ flex: '1 1 60%', minWidth: 'min(100%, 350px)' }}>

                        {/* Forms Table */}
                        <div style={{ minHeight: '100px' }}>
                          <style>{`
                            @media (max-width: 768px) {
                              #orths col { width: auto !important; }
                              #orths td, #orths th { 
                                word-break: break-word; 
                                padding-left: 4px !important; 
                                padding-right: 4px !important; 
                              }
                            }
                          `}
                          </style>
                            <table id="orths" style={{ borderCollapse: 'collapse', border: 'none', width: 'auto', maxWidth: '100%' }}>
                            <colgroup>
                              <col />
                              <col style={{ width: '52px' }} />
                              <col style={{ width: '90px' }} />
                              <col style={{ width: '110px' }} />
                              <col style={{ width: '32px' }} />
                              <col style={{ width: '32px' }} />
                              <col style={{ width: '32px' }} />
                            </colgroup>
                            <thead>
                              <tr className="orth_table_header">
                                <th>Form</th>
                                <th>Dial.</th>
                                <th className="tla_orth_id">Form ID</th>
                                <th className="tla_orth_id">POS</th>
                                <th colSpan="3" className="annis_link">Attestation</th>
                              </tr>
                            </thead>
                            <tbody>
                              {orderedForms.map((form, i) => {
                                const collocationsForForm = getCollocationsForDialect(entry.collocations, form.dialect);
                                const showsScriptoriumFallback = !form.id;
                                return (
                                  <tr key={i} style={{ transition: 'all 0.3s ease' }}>
                                    <td className="orth_entry">{form.orth}</td>
                                    <td className="dialect">{form.dialect || '?'}</td>
                                    {showsScriptoriumFallback ? (
                                      <td colSpan="2" className="tla_orth_id text-muted" style={{ fontSize: '0.9em', border: 'none', padding: '8px', whiteSpace: 'nowrap' }}>
                                        <span className="suppl_orth_id">(from Coptic Scriptorium)</span>
                                      </td>
                                    ) : (
                                      <>
                                        <td className="tla_orth_id text-muted" style={{ fontSize: '0.9em', border: 'none', padding: '8px' }}>
                                          {form.type === 'lemma' ? '' : form.id}
                                        </td>
                                        <td className="morphology">{originalPos}</td>
                                      </>
                                    )}
                                    
                                    {/* 1. ANNIS Link */}
                                    <td className="annis_link">
                                      {getAnnisFormUrl(form.orth, originalPos, form.dialect) && (
                                        <a href={getAnnisFormUrl(form.orth, scriptoriumPos, form.dialect)} target="_blank" rel="noreferrer" title={`Search for form ${form.orth} in Coptic Scriptorium`}>
                                          <img src={withBasePath('img/scriptorium.png')} className="scriptorium_logo" alt="Scriptorium"/>
                                        </a>
                                      )}
                                    </td>

                                    {/* 2. Frequency Tooltip */}
                                    <td className="freq">
                                      <div className="custom-tooltip-container">
                                        <a className="dict_tooltip">
                                        <i className="fa fa-sort-numeric-asc freq_icon"></i>
                                        <div className="custom-tooltip-content" style={{ fontFamily: 'antinoouRegular, serif' }}>
                                          <b>ANNIS frequencies:</b><br/>
                                          <ul style={{ margin: 0, paddingLeft: '20px' }}>
                                            <li>Word form frequency per 10,000: {getFreqStatValue(form.freq_form, 'rate')} (# {getFreqStatValue(form.freq_form, 'rank')})</li>
                                            <li>Lemma frequency per 10,000: {getFreqStatValue(getLemmaFreqStatsForForm(entry, form), 'rate')} (# {getFreqStatValue(getLemmaFreqStatsForForm(entry, form), 'rank')})</li>
                                          </ul>
                                        </div>
                                        </a>
                                      </div>
                                    </td>

                                    {/* 3. Collocations Tooltip */}
                                    <td className="colloc" style={{ maxWidth: '20px' }}>
                                      {isDetailLoading ? (
                                        <span className="text-muted" style={{ fontSize: '0.7em' }}><i className="fa fa-spinner fa-spin"></i></span>
                                      ) : collocationsForForm.length > 0 && (
                                        <div className="custom-tooltip-container">
                                          <a className="dict_tooltip">
                                          <div className="fa-stack" style={{ fontSize: '0.7em', color: 'rgb(119, 119, 119)', display: 'inline-block' }}>
                                          <i className="fa fa-share-alt fa-stack-1x fa-rotate-315"></i>
                                          <i className="fa fa-share-alt fa-stack-1x fa-rotate-45"></i>
                                          </div>
                                              <div className="custom-tooltip-content" style={{ fontFamily: 'antinoouRegular, serif' }}>
                                                <b>Top collocations in ANNIS ({form.dialect}): (5 word window)</b><br/>
                                                <table className="table table-condensed" style={{ marginTop: '10px', marginBottom: 0, border: 'none' }}>
                                                  <thead>
                                                    <tr>
                                                      <th style={{ border: 'none' }}></th>
                                                      <th style={{ border: 'none' }}>Word</th>
                                                      <th style={{ border: 'none' }}>Co-occurrences</th>
                                                      <th style={{ border: 'none' }}>Association (MI3)</th>
                                                    </tr>
                                                  </thead>
                                                  <tbody>
                                                    {collocationsForForm.map((colloc, idx) => (
                                                      <tr key={idx}>
                                                        <td style={{ textAlign: 'right', border: 'none', padding: '4px' }}>{idx + 1}.</td>
                                                        <td style={{ border: 'none', padding: '4px' }}>
                                                          <Link to={`/?q=${encodeURIComponent(colloc[0])}`} style={{ fontFamily: 'antinoouRegular, sans-serif' }}>
                                                            {colloc[0]}
                                                          </Link>
                                                        </td>
                                                        <td style={{ textAlign: 'center', border: 'none', padding: '4px' }}>{colloc[1]}</td>
                                                        <td style={{ textAlign: 'center', border: 'none', padding: '4px' }}>
                                                          {Number.isFinite(Number(colloc[2])) ? Number(colloc[2]).toFixed(2) : colloc[2]}
                                                        </td>
                                                      </tr>
                                                    ))}
                                                  </tbody>
                                                </table>
                                              </div>
                                          </a>
                                        </div>
                                      )}
                                    </td>

                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>

                        {/* Scriptorium tag */}
                        <div className="tag" style={{ margin: '15px 0 15px 0' }}>
                          Scriptorium tag: {scriptoriumPos}
                        </div>
                        
                        {/* Known Entity Types Search Icons */}
                        {knownEntities && knownEntities.length > 0 && (
                          <div className="tag" style={{ margin: '0 0 15px 0' }}>
                            Known entity types: 
                            {knownEntities.map((entityType) => (
                              <React.Fragment key={entityType}>
                                &nbsp;&nbsp;
                                <a 
                                  href={getEntitySearchUrl(lemmaForm.orth, entityType)} 
                                  target="_blank" 
                                  rel="noreferrer" 
                                  title={`Find attestations as a ${entityType} entity in Coptic Scriptorium`}
                                >
                                  <i className={`fa fa-${ENTITY_ICON_MAP[entityType] || 'cloud'} known-entity`}>&nbsp;</i>
                                </a>
                              </React.Fragment>
                            ))}
                          </div>
                        )}

                        {/* Senses / Definitions */}
                        <div className="sense_info" style={{ overflowX: 'auto', width: '100%' }}>
                          <table id="senses" style={{ borderCollapse: 'collapse', border: 'none', fontFamily: 'antinoouRegular, sans-serif', width: '100%' }}>
                            <tbody>
                              {entry.senses?.map((sense, i) => {
                                const langs = sense.translations ? Object.keys(sense.translations) : [];
                                return (
                                  <React.Fragment key={sense.id || i}>
                                    {langs.map((lang, lIndex) => (
                                      <tr key={`${sense.id}-${lang}`}>
                                        {lIndex === 0 ? (
                                          <td title={`Sense ID: ${sense.id}`} className="entry_num">
                                            <a className="hint sense_id" data-tooltip={`Sense ID: ${sense.id}`}>&nbsp;{i + 1}.&nbsp;</a>
                                          </td>
                                        ) : (
                                          <td style={{ padding: '4px 8px' }}></td>
                                        )}
                                        <td className="sense_lang">
                                          ({lang.charAt(0).toUpperCase() + lang.slice(1)})
                                        </td>
                                        <td className="trans">
                                          {sense.translations[lang].join('; ')}
                                        </td>
                                      </tr>
                                    ))}
                                    
                                    {/* Bibliography skeleton or actual data */}
                                    {sense.bibliography ? (
                                      <tr>
                                        <td style={{ padding: '4px 8px' }}></td>
                                        <td colSpan="2" className="bibl" style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                                          Bibliography: <span dangerouslySetInnerHTML={{ __html: formatBibliography(sense.bibliography, entry.id) }} />{sense.cu_ID ? ` (ID ${sense.cu_ID})` : ''}
                                        </td>
                                      </tr>
                                    ) : isDetailLoading ? (
                                      <tr>
                                        <td style={{ padding: '4px 8px' }}></td>
                                        <td colSpan="2" className="bibl text-muted">
                                          <span style={{ display: 'inline-block', width: '250px', height: '1.2em', backgroundColor: 'rgba(255, 255, 255, 0.0)', borderRadius: '3px' }}></span>
                                        </td>
                                      </tr>
                                    ) : null}
                                  </React.Fragment>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Right Column: Network Graph Area */}
                      <div style={{ flex: '0 0 300px' }}>
                        {isDetailLoading ? (
                          <div style={{ width: '100%', height: '220px', backgroundColor: '#f9f9f9', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '4px', border: '1px dashed #e0e0e0' }}>
                             <span className="text-muted"><i className="fa fa-spinner fa-spin" style={{ marginRight: '8px' }}></i> Loading graph...</span>
                          </div>
                        ) : entry.network && Object.keys(entry.network).length > 0 ? (
                          <div>
                            <NetworkGraph 
                              networkData={entry.network['S'] || entry.network[Object.keys(entry.network)[0]]} 
                              targetLemma={lemmaForm.orth} 
                              targetFormId={lemmaForm.id || null}
                            />
                          </div>
                        ) : null}
                      </div>

                    </div>
                    {/* End Flex Layout */}

                    {/* Heavy Data Bottom Section */}
                    <div style={{ marginTop: '30px', minHeight: '150px' }}>
                      {isDetailLoading ? (
                        <div className="text-muted" style={{ padding: '20px 0', borderTop: '1px solid #eee' }}>
                           <i className="fa fa-spinner fa-spin" style={{ marginRight: '10px' }}></i> Fetching dictionary examples and etymology...
                        </div>
                      ) : (
                        <div style={{ transition: 'opacity 0.3s ease-in' }}>
                          
                          {/* Etymology */}
                          {(hasCompactEtymology || hasGreekEtymology) && (
                            <div id="etym" className="etym" style={{ marginBottom: '20px' }}>
                              {hasCompactEtymology && (
                                <span className="eg_etym">
                                  Descended from{' '}
                                  {demoticLemma && (
                                    <>
                                      Demotic <i>{demoticLemma}</i>
                                      {egyptianLemma ? ', ' : ''}
                                    </>
                                  )}
                                  {egyptianLemma && (
                                    <>
                                      Hieroglyphic Egyptian <i>{egyptianLemma}</i>
                                      {entry.etym.english ? ` ${entry.etym.english}` : ''}
                                    </>
                                  )}
                                  ; see TLA:{' '}
                                  {demoticLemma && entry.etym.tla_link_d && (
                                    <>
                                      [<a href={entry.etym.tla_link_d} target="_blank" rel="noreferrer">Demotic</a>]
                                      {egyptianLemma && entry.etym.tla_link ? ' ' : ''}
                                    </>
                                  )}
                                  {egyptianLemma && entry.etym.tla_link && (
                                    <>
                                      [<a href={entry.etym.tla_link} target="_blank" rel="noreferrer">Hieroglyphic Egyptian</a>]
                                    </>
                                  )}
                                </span>
                              )}

                              {hasGreekEtymology && (
                                <div className="gr_etym" style={{ marginTop: hasCompactEtymology ? '8px' : 0 }}>
                                  Cf. Gr.{greekEtymId ? ` (DDGLC lemma ID ${greekEtymId})` : ''}{' '}
                                  {greekEtymLemma && greekLogeionUrl ? (
                                    <a href={greekLogeionUrl} target="_blank" rel="noreferrer" style={{ fontFamily: 'antinoouRegular, sans-serif' }}>
                                      {greekEtymLemma}{' '}
                                      <img src={withBasePath('img/logeion.png')} alt="Logeion" style={{ height: '14px', verticalAlign: 'text-bottom', border: '1px solid #000' }} />
                                    </a>
                                  ) : greekEtymLemma ? (
                                    <span style={{ fontFamily: 'antinoouRegular, sans-serif' }}>{greekEtymLemma}</span>
                                  ) : null}
                                  {greekPerseusUrl && (
                                    <>
                                      {' '}
                                      <a href={greekPerseusUrl} target="_blank" rel="noreferrer">
                                        <img src={withBasePath('img/perseus.png')} alt="Perseus" style={{ height: '14px', verticalAlign: 'text-bottom', border: '1px solid #000' }} />
                                      </a>
                                    </>
                                  )}
                                  {greekEtymMeaning ? (
                                    <>
                                      {' '}<i>{greekEtymMeaning}</i>
                                    </>
                                  ) : null}
                                  {greekEtymPosTitle ? `. ${greekEtymPosTitle}` : ''}
                                  {greekEtymRef ? (
                                    <span style={{ color: '#888' }}>
                                      {' '}(
                                      <span dangerouslySetInnerHTML={{ __html: formatGreekReferences(greekEtymRef) }} />
                                      )
                                    </span>
                                  ) : null}
                                </div>
                              )}
                            </div>
                          )}

                          {/* Examples */}
                          {orderedExamplesByDialect.length > 0 && (
                            <div className="examples-section" style={{ marginTop: '20px' }}>
                              <div className="tag text-muted" style={{ marginBottom: '10px' }}>
                                Example usage: (automatically extracted, use with caution and <a href="https://github.com/KELLIA/dictionary/issues/new?assignees=&labels=&template=bad-example-usage-report.md&title=Bad+example+sentence+for+the+entry+%3CENTRY%3E" target="_blank" rel="noreferrer">report bad examples</a>)
                              </div>

                              {orderedExamplesByDialect.map(([dialect, examples]) => (
                                <div key={dialect} style={{ marginBottom: '20px' }}>
                                  {(() => {
                                    const dialectTopForm = getTopFormForDialect(entry.forms, dialect);
                                    const lemmaForDialect = dialectTopForm?.orth || lemmaForm.orth;
                                    const annisLemmaUrl = getAnnisLemmaUrl(lemmaForDialect, dialect);

                                    return (
                                      <>
                                  <div className="ex-dialect" style={{ fontWeight: 'bold', borderBottom: '1px solid #eee', marginBottom: '10px' }}>
                                    {dialect.charAt(0).toUpperCase() + dialect.slice(1).toLowerCase()}:
                                  </div>
                                  <ul style={{ listStyleType: 'none', paddingLeft: '10px' }}>
                                    {examples.map((ex, i) => (
                                      <li key={i} style={{ marginBottom: '15px' }}>
                                        <div className="example">
                                          <span className="ex-sent" style={{ display: 'block', fontFamily: 'antinoouRegular, sans-serif', fontSize: '1.2em' }}>
                                            {formatExampleText(ex.coptic)}
                                          </span>
                                          <span className="ex-trans" style={{ display: 'block', fontStyle: 'italic', color: '#555', fontFamily: 'antinoouRegular, sans-serif' }}>
                                            {ex.english}
                                          </span>
                                          <span className="ex-source" style={{ display: 'block', fontSize: '0.85em', color: '#888' }}>
                                            {ex.source} (<a href={getUrnResolverUrl(ex.urn)} target="_blank" rel="noreferrer">{ex.urn}</a>)
                                          </span>
                                        </div>
                                      </li>
                                    ))}
                                  </ul>
                                  {annisLemmaUrl && (
                                    <p className="ex-more text-muted" style={{ fontSize: '0.9em', marginLeft: '10px' }}>
                                      Search for <a href={annisLemmaUrl} target="_blank" rel="noreferrer">more examples</a> for the lemma {lemmaForDialect} with any sense in {dialect} (ANNIS search)
                                    </p>
                                  )}
                                      </>
                                    );
                                  })()}
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Explicit dictionary cross references (xr) */}
                          {entry.crossReferences && entry.crossReferences.length > 0 && (
                            <div className="cross_refs" style={{ marginTop: '30px', fontFamily: 'antinoouRegular, sans-serif' }}>
                              {entry.crossReferences.map((ref, i) => (
                                <div key={i} style={{ marginBottom: '4px' }}>
                                  <span style={{ marginRight: '5px' }}>{getCrossReferenceTypeLabel(ref.type)}</span>
                                  <Link to={`/entry/${ref.target}`}>{ref.targetLemma || ref.target}</Link>
                                  {ref.label ? <span style={{ marginLeft: '5px' }}>{ref.label}</span> : null}
                                </div>
                              ))}
                            </div>
                          )}

                          {/* SuperEntry sibling references */}
                          {entry.superEntryReferences && entry.superEntryReferences.length > 0 && (
                            <div className="see_also" style={{ marginTop: '24px', fontFamily: 'antinoouRegular, sans-serif' }}>
                              <b>See also:</b>
                              <table className="entrylist table table-condensed" style={{ width: 'auto', border: 'none', marginTop: '6px', marginBottom: 0 }}>
                                <tbody>
                                  {entry.superEntryReferences.map((ref, i) => (
                                    <tr key={i}>
                                      <td className="related_orth" style={{ border: 'none', padding: '2px 10px 2px 0' }}>
                                        <Link to={`/entry/${ref.target}`}>{ref.label || ref.target}</Link>
                                      </td>
                                      <td className="text-muted" style={{ border: 'none', padding: '2px 10px 2px 0', whiteSpace: 'nowrap' }}>
                                        {ref.pos || '?'}
                                      </td>
                                      <td style={{ border: 'none', padding: '2px 0' }}>
                                        {ref.gloss || ''}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}

                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Footer Info Box */}
          <div id="citation_info_box" style={{ padding: '15px', backgroundColor: '#f9f9f9', border: '1px solid #ddd', marginTop: '30px', fontSize: '0.9em', fontFamily: 'antinoouRegular, sans-serif' }}>
            Please cite as: TLA lemma no. {entry.id} (<span style={{ fontSize: 'larger' }}>{lemmaForm.orth}</span>), in: <i style={{ fontFamily: 'sans-serif' }}>Coptic Dictionary Online</i>, ed. by the Koptische/Coptic Electronic Language and Literature International Alliance (KELLIA), <span style={{ fontFamily: 'sans-serif' }}>https://coptic-dictionary.org/entry/{entry.id}</span> (accessed {today}).
          </div>
        </>
      )}

      <SiteFooter />
    </div>
  );
}