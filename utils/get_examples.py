import os, io, sys, re
from nltk.corpus import stopwords
from collections import defaultdict
import sqlite3 as lite
from glob import glob
from random import shuffle, seed

pub_corpora = ""  # Path to clone of CopticScriptorium/Corpora
nlp_data_dir = ""   # Path to data dir of CopticScriptorium/Coptic-NLP
if not pub_corpora.endswith(os.sep):
    pub_corpora += os.sep
if not nlp_data_dir.endswith(os.sep):
    nlp_data_dir += os.sep


seed(42)

stop_words = set(stopwords.words('english'))

bigrams = set()
trigrams = set()
lines = io.open(nlp_data_dir + "mwe.tab",encoding="utf8").read().strip().split("\n")
for line in lines:
    words = line.split(" ")
    if len(words) == 2:
        bigrams.add(tuple(words))
    elif len(words)==3:
        trigrams.add(tuple(words))


class Citation:

    def __init__(self, lemma, norm, pos, sent, translation, sent_position, bg_position, doc, corpus, urn, seg_quality):
        self.lemma = lemma
        self.norm = norm
        self.pos = pos
        self.sent = sent
        self.translation = translation
        self.translation_words = just_words(translation)
        self.position = sent_position
        self.bg_position = bg_position
        self.subwords = ""
        self.doc = doc
        self.corpus = corpus
        self.urn = urn
        self.seg_quality = seg_quality

    def __repr__(self):
        short_doc = self.doc if len(self.doc)<10 else self.doc[:10]
        return self.lemma + " (" + self.norm+"/"+self.pos+", " + short_doc + "): " + self.sent

    def __str__(self):
        word_count = self.norm.count(" ") + 1
        words = self.sent.split()
        subwords = self.subwords.split()
        if word_count == 1:
            subwords[self.bg_position-1] = '<span class="ex-sub-match">' +subwords[self.bg_position-1] + '</span>'
            words[self.position-1] = '<span class="ex-group-match">' + "".join(subwords) + "</span>"
        else:
            # Check if everything is inside this BG
            if self.bg_position >= word_count:
                subwords[self.bg_position - word_count] = '<span class="ex-sub-match">' + subwords[self.bg_position - word_count]
                subwords[self.bg_position - 1] = subwords[self.bg_position - 1] + '</span>'
                words[self.position - 1] = '<span class="ex-group-match">' + "".join(subwords) + "</span>"
            else:  # MWE match spans multiple BGs
                #subwords[self.bg_position - word_count] = '<span class="ex-sub-match">' + subwords[self.bg_position - word_count]
                subwords[self.bg_position - 1] = '<span class="ex-sub-match">' +subwords[self.bg_position - 1] + '</span>'
                words[self.position - 2] = '<span class="ex-sub-match ex-group-match">' + words[self.position - 2]
                words[self.position - 1] = "".join(subwords) + "</span>"

        return '<div class="example"><span class="ex-sent">' + " ".join(words) + "</span>\n" + \
               '<span class="ex-trans">'+self.translation + "</span>\n" + \
               '<span class="ex-source">' + self.doc + ' (<a href="http://data.copticscriptorium.org/' + \
               self.urn + '">' + self.urn +'</a>)</span>\n'


def get_score(citation, prev_citations_list, n_readings, definition_words):
    """
    Score a citation example given previous selection, number of readings and words in the definition.
    TODO: Tune the weights of the different constraints, these are just some fairly sane(?) initial ones
    """

    def blank(val):
        return val in ["","...","…"]

    prev_citations = [c[1] for c in prev_citations_list]

    score = 0.0

    # Segmentation quality
    if citation.seg_quality == "gold":
        score += 2
    elif citation.seg_quality == "checked":
        score += 1

    # Prefer place 1 to be identical to citation form
    if citation.lemma == citation.norm:
        score += 0.2

    # Penalize no translation
    if blank(citation.translation):
        score -= 3
    else:
        definition_weight = 0 if n_readings == 1 else n_readings * 1.5
        overlaps_definition = definition_overlap(definition_words, citation.translation_words)
        if overlaps_definition:
            score += definition_weight

    if len(citation.translation) > 50:  # too long
        score -= 2
    elif len(citation.translation) > 30:  # too long
        score -= 0.5
    if len(citation.translation) < 20:  # too short
        score -= 0.5
    elif len(citation.translation) < 10:  # too short
        score -= 1

    # Compare to other citations
    if any([c.translation == citation.translation for c in prev_citations]):
        score -= 500  # Example with this translation already known
    if any([c.sent == citation.sent for c in prev_citations]):
        score -= 500  # Example with this sent already known
    if any([c.pos == citation.pos for c in prev_citations]):
        score -= 0.5  # Example with this POS already known
    if any([c.norm == citation.norm for c in prev_citations]):
        score -= 0.5  # Example with this norm already known
    if any([c.doc == citation.doc for c in prev_citations]):
        score -= 1.5  # Example with this doc already known

    return score


def definition_overlap(definition_words, example):
    if any([w in definition_words for w in example]):
        return True
    return False


def n_best(lemma, data, db_entries, n=3):

    if lemma not in data:
        return []
    selected = []
    best_candidate = None
    cits = list(data[lemma])
    n_readings = len(db_entries[lemma])
    shuffle(cits)
    for tla_id in db_entries[lemma]:
        definition_words = db_entries[lemma][tla_id]
        seen_ex_strings = set()
        for i in range(n):
            best_score = -1000
            for cit in cits:
                score = get_score(cit, selected, n_readings, definition_words)
                if score > best_score:
                    best_candidate = cit
                    best_score = score
            if best_candidate is None or best_candidate in selected or str(best_candidate) in seen_ex_strings:
                break
            else:
                seen_ex_strings.add(str(best_candidate))
            selected.append((tla_id,best_candidate))

    output = []
    first = None
    for tla_id, ex in selected:
        if ex.lemma == ex.norm and first is None:
            first = (tla_id, ex)
        else:
            output.append((tla_id,ex))
    output.sort(key=lambda x: (x[1].pos, x[1].norm))  # Sort by POS (V > VSTAT) then norm
    if first is not None:
        output = [first] + output

    return output


def get(line,attr):
    return re.search(' ' + attr + '="([^"]*)"',line).group(1)


def get_citations(sgml, filename, db_entries):
    lemma = norm = pos = translation = title = segmentation = corpus = urn = ""
    prev_norm = prev_lemma = ""
    prev_prev_norm = prev_prev_lemma = ""
    prev_prev_pos = prev_pos = ""
    subwords = words = sent_citations = []
    output = defaultdict(set)
    lines = sgml.split("\n")
    sent_position = 0
    bg_position = 0
    for line in lines:
        if ' title="' in line:
            title = get(line, 'title')
            segmentation = "automatic"
            corpus = filename.split(os.sep)[-2]
        if ' corpus=' in line:
            corpus = get(line, 'corpus')
        if ' document_cts_urn=' in line:
            urn = get(line, 'document_cts_urn')
        if ' segmentation="' in line:
            segmentation = get(line, 'segmentation')
        if ' lemma="' in line:
            prev_prev_lemma = prev_lemma
            prev_lemma = lemma
            lemma = get(line, 'lemma')
        if ' translation=' in line:
            translation = get(line, 'translation')
            if len(words) > 0:
                for c in sent_citations:
                    c.sent = " ".join(words)
                    output[c.lemma].add(c)
            words = []
            sent_citations = []
            sent_position = 0
        if " pos=" in line:
            prev_prev_pos = prev_pos
            prev_pos = pos
            pos = get(line, 'pos')
        if " norm=" in line:
            prev_prev_norm = prev_norm
            prev_norm = norm
            norm = get(line, 'norm')
            bg_position +=1
        if ' norm_group' in line:
            norm_group = get(line, 'norm_group')
            words.append(norm_group)
            sent_position += 1
            bg_position = 0
        if '</norm_group>' in line:
            for cit in sent_citations:
                if cit.position == sent_position:
                    cit.subwords = " ".join(subwords)
            subwords = []
        if '</norm>' in line:
            if lemma=="ⲥⲁⲙⲓⲧ":
                a=3
            if lemma in db_entries:
                cit = Citation(lemma, norm, pos, " ".join(words), translation, sent_position, bg_position, title, corpus, urn, segmentation)
                sent_citations.append(cit)
            subwords.append(norm)
            ngram = lemmagram = ""
            if (prev_prev_norm, prev_norm, norm) in trigrams:
                ngram = " ".join([prev_prev_norm, prev_norm, norm])
                lemmagram = " ".join([prev_prev_lemma, prev_lemma, lemma])
                prev_pos = prev_prev_pos  # We'll use prev_pos as the POS for this ngram either wayx
            elif (prev_norm, norm) in bigrams:
                ngram = " ".join([prev_norm, norm])
                lemmagram = " ".join([prev_lemma, lemma])
            if ngram != "" and lemmagram in db_entries:
                cit = Citation(lemmagram, ngram, prev_pos, " ".join(words), translation, sent_position, bg_position, title, corpus, urn, segmentation)
                sent_citations.append(cit)

    return output


def format_pos(pos):
    pos = pos.replace("NPROP","N").replace("PPERS","PPER").replace("PPERI","PPER")
    pos = pos.replace("VIMP","V")
    pos = re.sub(r'^A[^R]+','A',pos)
    pos = re.sub(r'^C[^O]+','C',pos)
    return pos


def update_db(in_dict, db_entries):
    con = lite.connect('alpha_kyima_rc1.db')

    rows = []
    for lemma in in_dict:
        tla_cits = n_best(lemma, in_dict, db_entries)
        for i, tla_cit in enumerate(tla_cits):
            tla_id, cit = tla_cit
            row = [lemma, tla_id, format_pos(cit.pos), str(cit), i]
            rows.append(row)

    with con:
        cur = con.cursor()

        cur.execute("DROP TABLE IF EXISTS examples;")
        cur.execute("CREATE TABLE examples(lemma TEXT, tla TEXT, pos TEXT, citation TEXT, priority INT);")

        cur.executemany(
            "INSERT INTO examples (lemma, tla, pos, citation, priority) VALUES " +
            "(?, ?, ?, ?, ?);", rows)
        con.commit()


def just_words(text,remove_stop_words=False):
    # Return unique alphabetic lower cased words, separated by space
    text = re.sub(r'[^A-Za-z]',' ',text)
    text = re.sub(r'\s+',' ',text)
    words = list(set(text.lower().split()))
    if remove_stop_words:
        if any([w not in stop_words for w in words]):
            words = [w for w in words if w not in stop_words]
    return set(words)


def get_db_entries():

    con = lite.connect('alpha_kyima_rc1.db')

    output = defaultdict(dict)
    with con:
        cur = con.cursor()

        rows = cur.execute("SELECT DISTINCT Search, POS, En, xml_id from entries")

    for row in rows:
        entry, pos, definition, TLA = row
        forms = entry.strip().split("\n")
        lemma = forms[0].split("~")[0]
        senses = definition.split("|||")
        all_senses = []
        for sense in senses:
            if "~~~" in sense:
                sense = sense.split("~~~")[1].split(";;;")[0]
            elif "ref:" in sense:
                sense = sense.split("ref:")[1].split(";;;")[0]
            elif "xr." in sense:
                sense = sense.split("xr.")[1].split(";;;")[0]
            else:
                sys.stderr.write("! No sense for TLA ID " + TLA + ": " + sense + "\n")
                sense = ""
            all_senses.append(sense)
        all_senses = " ".join(all_senses)
        all_senses = just_words(all_senses,remove_stop_words=True)
        output[lemma][TLA] = all_senses

    return output


db_entries = get_db_entries()

files = glob(pub_corpora + "**" + os.sep + "*.tt",recursive=True)
files = [f for f in files if "coptic-treebank" not in f]  # Exclude coptic-treebank to avoid repetitions

lemma2citations = defaultdict(set)

for i, file_ in enumerate(files):
    sgml = io.open(file_,encoding="utf8").read()

    doc_citations = get_citations(sgml, file_, db_entries)

    for lemma in doc_citations:
        if lemma in lemma2citations:
            lemma2citations[lemma].update(doc_citations[lemma])
        else:
            lemma2citations[lemma] = doc_citations[lemma]

# Print some examples as a sanity check
ex = n_best("ⲥⲁⲙⲓⲧ",lemma2citations, db_entries)
for tla_id, cit in ex:
    print(tla_id + "\n" + str(cit))

update_db(lemma2citations, db_entries)
