"""
Script to read dictonary entry data from CCL XML file and produce .json
files for dictionary front end search
"""

from turtle import pos
import xml.etree.ElementTree as ET
import json
import os
import shutil
import math
import glob
from collections import defaultdict

# TEI Namespace
NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
XML_NS = '{http://www.w3.org/XML/1998/namespace}'


def pos_map(pos, subc, orthstring, tla_id):
    pos = str(pos).replace('?', '')
    subc = str(subc)
    orthstring = str(orthstring)

    if tla_id in ["C1896","C6420","C4445","C2176","C2177","C4901"]: return "IMOD"
    if tla_id in ["C6534","C1900"]: return "N"  # B. man, hli
    if tla_id in ["C220"]: return "CONJ"  # B. ⲁⲥⲑⲉⲙ
    if pos in ["Subst.", "Adj.", "Nominalpräfix", "Adjektivpräfix", "Kompositum"]: return 'N'
    if "Ausdruck der Nichtexistenz" in subc or "Ausdruck des Nicht-Habens" in subc: return 'EXIST'
    if pos == "Adv.": return 'ADV'
    if pos in ["Vb.", "unpersönlicher Ausdruck"]:
        if subc == "Qualitativ": return 'VSTAT'
        if subc == "Suffixkonjugation": return 'VBD'
        if subc == "Imperativ": return 'VIMP'
        if "ⲟⲩⲛ-" in orthstring or "ⲟⲩⲛⲧⲉ-" in orthstring: return "EXIST"
        return 'V'
    if pos == "Präp.": return 'PREP'
    if pos in ["Zahlzeichen", "Zahlwort", "Präfix der Ordinalzahlen"]: return 'NUM'
    if pos in ["Partikel", "Interjektion", "Partikel, enklitisch"]: return 'PTC'
    if pos in ["Selbst. Pers. Pron.", "Suffixpronomen", "Präfixpronomen (Präsens I)"]: return 'PPER'
    if pos == "Konj.": return 'CONJ'
    if pos == "Dem. Pron.": return "PDEM"
    if pos in ["bestimmter Artikel", "unbestimmter Artikel"]: return 'ART'
    if pos in ["Possessivartikel", "Possessivpräfix"]: return 'PPOS'
    if pos == "Poss. Pron.": return 'PPERO'
    if pos == "Interr. Pron.": return 'PINT'
    if pos == "Verbalpräfix":
        if subc in ["Imperativpräfix ⲁ-", "Negierter Imperativ ⲙⲡⲣ-"]: return 'NEG'
        if subc in ["im negativen Bedingungssatz", "Perfekt II ⲉⲛⲧⲁ-"]: return 'C'
        return 'A'
    if pos == "Pron.":
        if subc == "None": return 'PPER'
        if subc in ["Indefinitpronomen", "Fragepronomen"]: return 'PINT'
        if subc == "Reflexivpronomen": return 'PREP'
    if pos == "Satzkonverter": return 'C'
    if pos == "Präfix":
        if "ⲧⲁ-" in orthstring: return "PPOS"
        if "ⲧⲃⲁⲓ-" in orthstring: return "N"
        if "ⲧⲣⲉ-" in orthstring: return "A"
    if pos in ["None", "?", ""]:
        if subc == "Qualitativ": return 'VSTAT'
        if subc == "None": return 'UNKNOWN'
    if "ϭⲁⲛⲛⲁⲥ" in orthstring: return "UNKNOWN"
    if ("Hilfsverb" in pos or "Pron." in pos) and ("ⲟⲩⲛ" in orthstring or "ⲟⲩⲟⲛ" in orthstring): return "EXIST"
    return "UNKNOWN"


def load_frequencies(filepath):
    freqs = {}
    total_n = 0
    if not os.path.exists(filepath):
        return freqs, total_n
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                word = parts[0]
                count = int(parts[1])
                freqs[word] = count
                total_n += count
    return freqs, total_n


def get_freq_stats(freq_dict, total_n):
    stats = {}
    sorted_items = sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)
    for rank, (word, count) in enumerate(sorted_items, 1):
        rate = round((count / total_n) * 10000, 2) if total_n > 0 else 0.0
        stats[word] = {"rate": rate, "rank": rank, "count": count}
    return stats


def is_zero_freq(stats):
    return stats.get("rate", 0.0) == 0.0 and stats.get("rank", 0) == 0 and stats.get("count", 0) == 0


def load_entity_mapping(data_dir):
    """
    json data like:
    {
    "ⲡⲁⲩⲗⲟⲥ": [
        "person"
    ],
    "ⲓⲏⲥⲟⲩⲥ": [
        "person"
    ],
    "ⲟⲩⲱϣ": [
        "abstract",
        "place"
    ],...
    """
    entity_mapping = {}
    mapping_file = os.path.join(data_dir, "entities.json")
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            entity_mapping = json.load(f)
    return entity_mapping


def load_hyperlemma_mapping(data_dir):
    """
    Load data like:

    word	pos	lemma	hyperlemma
    ⲁ	CFOC	ⲁⲣⲉ	ⲉⲣⲉ
    ⲁⲓⲁⲓ	V	ⲁⲓⲁⲓ	ⲁⲓⲁⲓ
    """
    hyperlemma_mapping = {}
    mapping_file = os.path.join(data_dir, "hyperlemmas.tab")
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 4:
                    word, pos, lemma, hyperlemma = parts
                    hyperlemma_mapping[lemma] = hyperlemma
    return hyperlemma_mapping


def load_collocations(filepath, lemma_freqs, norm_freqs, total_n, collocations_dict, hyperlemma_mapping, dialect):
    if not os.path.exists(filepath) or total_n == 0: return
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 3:
                lemma, collocate, co_freq_str = parts
                if dialect != "S":
                    # Needs hyperlemma mapping
                    lemma = hyperlemma_mapping.get(lemma, lemma)
                if collocate == '·': continue
                co_freq = int(co_freq_str)
                f_a = lemma_freqs.get(lemma, 1)
                f_b = norm_freqs.get(collocate, lemma_freqs.get(collocate, 1))
                try:
                    mi3 = math.log2(((co_freq ** 3) * total_n) / (f_a * f_b))
                except ValueError:
                    mi3 = 0.0
                collocations_dict[lemma][dialect].append([collocate, co_freq, round(mi3, 3)])
    for lemma in collocations_dict:
        if dialect in collocations_dict[lemma]:
            collocations_dict[lemma][dialect].sort(key=lambda x: x[2], reverse=True)
            collocations_dict[lemma][dialect] = collocations_dict[lemma][dialect][:20]  # Top 20!


def load_networks(filepath, networks_dict, dialect, top_k=20):
    if not os.path.exists(filepath): return

    # Step 1: Collect all phrases per lemma
    lemma_phrases = defaultdict(list)

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                lemma, phrase, freq = parts[1], parts[2], int(parts[3])
                lemma_phrases[lemma].append((phrase, freq))

    # Step 2: Sort, slice, and build the network for each lemma
    for lemma, phrases in lemma_phrases.items():
        # Sort phrases by frequency (index 1) descending
        phrases.sort(key=lambda x: x[1], reverse=True)
        top_phrases = phrases[:top_k]

        nodes = defaultdict(int)
        edges = defaultdict(int)

        for phrase, freq in top_phrases:
            tokens = phrase.split()

            # Legacy logic: cap at 6 tokens, and ensure the target node is present
            if len(tokens) > 6:
                tokens = tokens[:6]
                if f"{lemma}_0_node" not in tokens:
                    continue

            current_words, increment, processed_tokens = [], 1, []
            for token in tokens:
                if token in current_words:
                    token = f"{token}_{increment}"
                    increment += 1
                current_words.append(token)
                processed_tokens.append(token)

            prev_token = None
            for token in processed_tokens:
                nodes[token] += freq
                if prev_token is not None:
                    # Edge weight increases by 1 per phrase occurrence, as in legacy code
                    edges[(prev_token, token)] += 1
                prev_token = token

        # Save to the main dictionary
        networks_dict[lemma][dialect] = {
            "nodes": [[node, count] for node, count in nodes.items()],
            "edges": [[src, tgt, count] for (src, tgt), count in edges.items()]
        }


def load_supplemental_entries(filepath):
    sup_forms = defaultdict(list)
    if not os.path.exists(filepath): return sup_forms
    with open(filepath, 'r', encoding='utf-8') as f:
        next(f, None)
        for line in f:
            parts = line.strip('\n').split('\t')
            if len(parts) > 6:
                word, sahidic_word, tlas = parts[1].strip(), parts[5].strip(), parts[6].strip()
                invalid_vals = {"", "_", "x", "ⲭ"}
                tlas = tlas.split(",")
                for tla in tlas:
                    form_orth, dialect = None, None
                    if word not in invalid_vals:
                        form_orth, dialect = word, "B"
                    if form_orth and tla:
                        sup_forms[tla].append({"orth": form_orth, "dialect": dialect, "id": None})
                    if sahidic_word not in invalid_vals:
                        form_orth, dialect = sahidic_word, "S"
                    if form_orth and tla:
                        sup_forms[tla].append({"orth": form_orth, "dialect": dialect, "id": None})
    return sup_forms


def load_inflections(filepath):
    inf_forms = defaultdict(list)
    if not os.path.exists(filepath): return inf_forms
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip(): continue
            parts = line.strip('\n').split('\t')
            if len(parts) >= 7:
                tla, raw_variants = parts[0].strip(), parts[2:7]
                for cell in raw_variants:
                    if cell == '_': continue
                    for form in cell.split(','):
                        form = form.strip()
                        if form and form != '_':
                            # TODO: Support infl forms with other dialects - defaults to "S"
                            form = form.replace("=","⸗")
                            inf_forms[tla].append({"orth": form, "dialect": "S", "id": None})
            elif len(parts) == 3:  # irregular noun plurals
                tla, lemma, variant = parts
                inf_forms[tla].append({"orth": variant, "dialect": "S", "id": None})
    return inf_forms


def load_egyptian_etymologies(filepath):
    egy_etym = defaultdict(dict)
    if not os.path.exists(filepath): return egy_etym
    with open(filepath, 'r', encoding='utf-8') as f:
        next(f, None)
        for line in f:
            parts = line.strip('\n').split('\t')
            if len(parts) >= 10:
                tla = parts[0].strip()
                egy_etym[tla] = {
                    "egy_num": parts[2].strip(), "egy_lemma": parts[3].strip(),
                    "demo_num": parts[4].strip(), "demo_lemma": parts[5].strip(),
                    "english": parts[6].strip(), "german": parts[7].strip(),
                    "tla_link": parts[8].strip(), "tla_link_d": parts[9].strip()
                }
    return egy_etym


def load_examples(data_dir):
    examples_dict = defaultdict(list)
    for filepath in glob.glob(os.path.join(data_dir, 'examples_*.tab')):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip('\n').split('\t')
                if len(parts) >= 9:
                    try:
                        priority = int(parts[7].strip())
                    except ValueError:
                        priority = 999
                    examples_dict[parts[1].strip()].append({
                        "coptic": parts[3].strip(), "english": parts[4].strip(),
                        "source": parts[5].strip(), "urn": parts[6].strip(),
                        "priority": priority, "dialect": parts[8].strip()
                    })
    for tla_id in examples_dict:
        examples_dict[tla_id].sort(key=lambda x: x['priority'])
        for ex in examples_dict[tla_id]: del ex['priority']
    return examples_dict


def normalize_example_sentence(text):
    # Example strings can differ only by '*' highlighting; normalize those away.
    return " ".join((text or "").replace("*", "").split())


def load_corpus_data(data_dir='.', hyperlemma_mapping={}):
    corpus_data = {
        'collocations': defaultdict(lambda: defaultdict(list)),
        'networks': defaultdict(lambda: defaultdict(dict)),
        'freq_stats': defaultdict(lambda: {'lemma': {}, 'norm': {}})
    }
    colloc_files = glob.glob(os.path.join(data_dir, 'tt_collocs_*.tab'))
    dialects = [os.path.basename(f).replace('tt_collocs_', '').replace('.tab', '') for f in colloc_files]

    # Map the long filenames to the XML's short sigla
    LONG_TO_SHORT = {
        "sahidic": "S",
        "bohairic": "B",
        "akhmimic": "A",
        "fayyumic": "F",
        "lycopolitan": "L",
        "mesokemic": "M"
    }

    print(f"Discovered dialects: {', '.join(dialects)}")
    for dialect in dialects:
        # Get the short siglum (fallback to the long name if it's not in the map)
        short_dialect = LONG_TO_SHORT.get(dialect, dialect)
        print(f"Processing {dialect} corpus data as '{short_dialect}'...")

        lemma_freqs, total_n_lemma = load_frequencies(os.path.join(data_dir, f'cache_freqs_lemma_{dialect.lower()}.tab'))
        norm_freqs, total_n_norm = load_frequencies(os.path.join(data_dir, f'cache_freqs_norm_{dialect.lower()}.tab'))

        corpus_data['freq_stats'][short_dialect]['lemma'] = get_freq_stats(lemma_freqs, total_n_lemma)
        corpus_data['freq_stats'][short_dialect]['norm'] = get_freq_stats(norm_freqs, total_n_norm)

        load_collocations(os.path.join(data_dir, f'tt_collocs_{dialect.lower()}.tab'), lemma_freqs, norm_freqs, total_n_lemma,
                          corpus_data['collocations'], hyperlemma_mapping, short_dialect)
        load_networks(os.path.join(data_dir, f'phrase_freqs_{dialect.lower()}.tab'), corpus_data['networks'], short_dialect)

    return corpus_data


def extract_entry_lemma(entry_node):
    lemma_node = entry_node.find('./tei:form[@type="lemma"]/tei:orth', NS)
    if lemma_node is not None and lemma_node.text:
        lemma = lemma_node.text.strip()
        if lemma and lemma != '___':
            return lemma

    for orth_node in entry_node.findall('./tei:form/tei:orth', NS):
        if orth_node.text:
            candidate = orth_node.text.strip()
            if candidate and candidate != '___':
                return candidate

    return ""


def extract_entry_grammar(entry_node):
    grammar = {}

    def merge_gramgrp(gramgrp_node):
        for child in gramgrp_node:
            tag_name = child.tag.replace(f"{{{NS['tei']}}}", "")
            text_val = child.text.strip() if child.text else ""
            if tag_name == 'gram' and child.get('type'):
                key = child.get('type')
            else:
                key = tag_name
            if key not in grammar or not grammar[key]:
                grammar[key] = text_val

    gram_node = entry_node.find('./tei:gramGrp', NS)
    if gram_node is not None:
        merge_gramgrp(gram_node)
    else:
        # Some entries keep grammatical analyses at the form level
        form_nodes = entry_node.findall('./tei:form', NS)
        lemma_form_node = next((f for f in form_nodes if f.get('type') == 'lemma'), None)
        ordered_forms = []
        if lemma_form_node is not None:
            ordered_forms.append(lemma_form_node)
        ordered_forms.extend(f for f in form_nodes if f is not lemma_form_node)

        for form_node in ordered_forms:
            form_gram_node = form_node.find('./tei:gramGrp', NS)
            if form_gram_node is not None:
                merge_gramgrp(form_gram_node)

    # Subc fallback
    if "subc" not in grammar or not grammar["subc"]:
        fallback_subc = entry_node.find('.//tei:subc', NS)
        if fallback_subc is not None and fallback_subc.text:
            grammar["subc"] = fallback_subc.text.strip()
        else:
            fallback_gram_subc = entry_node.find('.//tei:gram[@type="subc"]', NS)
            if fallback_gram_subc is not None and fallback_gram_subc.text:
                grammar["subc"] = fallback_gram_subc.text.strip()

    return grammar


def extract_preferred_gloss(entry_node):
    preferred_langs = ['en', 'de', 'fr']
    translations_by_lang = defaultdict(list)

    for sense_node in entry_node.findall('./tei:sense', NS):
        for quote in sense_node.findall('.//tei:quote', NS):
            lang = quote.get(f'{XML_NS}lang')
            text = quote.text.strip() if quote.text else ""
            if lang and text:
                translations_by_lang[lang].append(text)

    for lang in preferred_langs:
        if translations_by_lang.get(lang):
            return '; '.join(translations_by_lang[lang])

    for values in translations_by_lang.values():
        if values:
            return '; '.join(values)

    return ""


def is_redundant_ref_subentry(entry_node):
    # Exclude redundant lemma subentries (e.g., C12454) whose lemma form is a ref
    # to another form target; these duplicate data already represented by that target.
    lemma_form = entry_node.find('./tei:form[@type="lemma"]', NS)
    if lemma_form is None:
        return False

    # Normal entries carry orth/usg directly under form and should be kept.
    if lemma_form.find('./tei:orth', NS) is not None:
        return False

    form_ref = lemma_form.find('./tei:ref[@type="form"]', NS)
    if form_ref is None or not form_ref.get('target'):
        return False

    # Keep the exclusion narrow to the observed redundant pattern.
    return form_ref.find('./tei:orth', NS) is not None


def build_superentry_crossrefs(root_node):
    superentry_refs = defaultdict(list)

    for super_entry_node in root_node.findall('.//tei:superEntry', NS):
        members = []
        for child_entry in super_entry_node.findall('./tei:entry', NS):
            if is_redundant_ref_subentry(child_entry):
                continue
            child_id = child_entry.get(f'{XML_NS}id')
            if not child_id:
                continue

            lemma = extract_entry_lemma(child_entry)
            if not lemma:
                lemma = child_id

            grammar = extract_entry_grammar(child_entry)
            pos = pos_map(grammar.get("pos", "") or "", grammar.get("subc", "") or "", lemma, child_id)
            gloss = extract_preferred_gloss(child_entry)

            members.append({
                "target": child_id,
                "label": lemma,
                "pos": pos,
                "gloss": gloss
            })

        for member in members:
            siblings = []
            for candidate in members:
                if candidate["target"] == member["target"]:
                    continue
                siblings.append(candidate.copy())
            if siblings:
                superentry_refs[member["target"]].extend(siblings)

    for entry_id in list(superentry_refs.keys()):
        seen_targets = set()
        deduped = []
        for ref in superentry_refs[entry_id]:
            target = ref.get("target")
            if not target or target in seen_targets:
                continue
            seen_targets.add(target)
            deduped.append(ref)
        deduped.sort(key=lambda item: (item.get("label") or item.get("target") or "").lower())
        superentry_refs[entry_id] = deduped

    return superentry_refs


def process_dictionary(xml_file, output_dir="public", data_dir="data"):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    index_data = []
    details_dir = os.path.join('local-data', 'details')  # Needs to be copied to details/ on deployed server
    unique_forms = set([])  # Store to serialize forms, we'll use the list to exclude them from seg_data etc.
    unique_example_sentences = set()
    total_sense_count = 0
    os.makedirs(details_dir, exist_ok=True)

    hyperlemma_mapping = load_hyperlemma_mapping(data_dir)
    entity_mapping = load_entity_mapping(data_dir)
    corpus_data = load_corpus_data(data_dir, hyperlemma_mapping)
    sup_entries_data = load_supplemental_entries(os.path.join(data_dir, 'supplemental_entries.tab'))
    inflections_data = load_inflections(os.path.join(data_dir, 'inflections.tab'))
    egy_etym_data = load_egyptian_etymologies(os.path.join(data_dir, 'egyptian_etymologies.tab'))
    examples_data = load_examples(data_dir)
    superentry_crossrefs = build_superentry_crossrefs(root)

    # Polysemous TLA IDs with special entity handling
    manual_entity_exceptions = {
        "C998": ["plant"], "C992": ["person"], "C993": ["person"],  # ⲉⲓⲱⲧ
    }

    print("Processing XML entries...")
    for entry in root.findall('.//tei:entry', NS):
        if is_redundant_ref_subentry(entry):
            continue
        entry_id, entry_type = entry.get(f'{XML_NS}id'), entry.get('type')
        all_forms, lemma_str, lemma_form_index, is_placeholder_entry = [], "", -1, False

        for form_node in entry.findall('./tei:form', NS):
            form_id = form_node.get(f'{XML_NS}id')
            orth = form_node.findtext('./tei:orth', default="", namespaces=NS).strip()
            if orth == '___':
                is_placeholder_entry = True
                break
            unique_forms.add(orth)
            if not form_id: continue

            dialect = form_node.findtext('./tei:usg[@type="geo"]', namespaces=NS)
            form_dict = {"id": form_id, "orth": orth, "dialect": dialect}

            form_type = form_node.get('type', 'variant')
            if form_type != 'variant': form_dict["type"] = form_type
            oref = form_node.findtext('./tei:oRef', namespaces=NS)
            if oref: form_dict["oRef"] = oref

            all_forms.append(form_dict)
            if form_type == 'lemma':
                lemma_str, lemma_form_index = orth, len(all_forms) - 1

        if is_placeholder_entry or not all_forms: continue

        if lemma_form_index == -1:
            all_forms[0]["type"] = "lemma"
            lemma_str, lemma_form_index = all_forms[0]["orth"], 0

        existing_orths = {(f.get("orth").replace("-","").replace("+","").replace("⸗","").strip(), f.get("dialect")) for f in all_forms}
        for sup_form in sup_entries_data.get(entry_id, []):
            if (sup_form["orth"], sup_form["dialect"]) not in existing_orths:
                all_forms.append(sup_form)
                existing_orths.add((sup_form["orth"].replace("-","").replace("+","").replace("⸗","").strip(), sup_form["dialect"]))
                unique_forms.add(sup_form["orth"])
        for inf_form in inflections_data.get(entry_id, []):
            clean = inf_form["orth"].replace("-","").replace("+","").replace("⸗","").strip()
            if clean == "ⲃⲏⲗ":
                a=4
            if (clean, "S") not in existing_orths:
                all_forms.append(inf_form)
                existing_orths.add((inf_form["orth"].replace("-","").replace("+","").replace("⸗","").strip(), inf_form["dialect"]))
                unique_forms.add(sup_form["orth"])

        lemma_freqs_by_dialect = {}

        # Inject form frequency stats into forms and collect lemma frequency stats per dialect
        for form in all_forms:
            d = form.get("dialect")
            o = form.get("orth")
            form_stats = {"rate": 0.0, "rank": 0, "count": 0}
            lemma_stats = {"rate": 0.0, "rank": 0, "count": 0}
            if d and d in corpus_data['freq_stats']:
                form_stats = corpus_data['freq_stats'][d]['norm'].get(o, form_stats)
                lemma_stats = corpus_data['freq_stats'][d]['lemma'].get(lemma_str, lemma_stats)
            if not is_zero_freq(form_stats):
                form["freq_form"] = form_stats
            if not is_zero_freq(lemma_stats):
                lemma_freqs_by_dialect[d] = lemma_stats

        details_forms = all_forms.copy()
        lemma_form = all_forms[lemma_form_index]
        is_redundant = any(
            f != lemma_form and f.get('orth') == lemma_form.get('orth') and f.get('dialect') == lemma_form.get(
                'dialect') for f in all_forms)
        if is_redundant: details_forms.pop(lemma_form_index)

        # Build index structures
        index_forms = []
        form_ids = []
        for f in details_forms:  # FIXED: We now iterate over details_forms to build index lists
            idx_form = {"orth": f["orth"]}
            if f.get("dialect"): idx_form["dialect"] = f["dialect"]
            if f.get("id"):
                idx_form["id"] = f["id"]
                if f["id"] not in form_ids:
                    form_ids.append(f["id"])

            if idx_form not in index_forms: index_forms.append(idx_form)

        grammar = extract_entry_grammar(entry)

        raw_pos = grammar.get("pos", "") or ""
        raw_subc = grammar.get("subc", "") or ""
        scriptorium_pos = pos_map(raw_pos, raw_subc, lemma_str, entry_id)
        grammar["tlapos"] = raw_pos
        grammar["pos"] = scriptorium_pos

        etym_data = {}
        etym_node = entry.find('./tei:etym', NS)
        if etym_node is not None:
            for ref_node in etym_node.findall('./tei:ref', NS):
                ref_type = ref_node.get('type')
                if ref_type and ref_type.startswith('greek_lemma::'):
                    etym_data[ref_type.split('::')[1]] = ref_node.text
        if entry_id in egy_etym_data:
            for k, v in egy_etym_data[entry_id].items():
                if v and v not in ("NA", "_"): etym_data[k] = v

        cross_refs = []
        for xr_node in entry.findall('./tei:xr', NS):
            ref_type = xr_node.get('type')
            for ref_node in xr_node.findall('./tei:ref', NS):
                target = ref_node.get('target', '').replace('#', '')
                label = ref_node.text.strip() if ref_node.text else ""
                if target:
                    cross_refs.append({"target": target, "type": ref_type, "label": label})

        index_senses, details_senses = [], []
        for sense_node in entry.findall('./tei:sense', NS):
            sense_id = sense_node.get(f'{XML_NS}id')
            cu_node = sense_node.find('./tei:ref[@type="coptic_usage::cu_ID"]', NS)
            cu_id = cu_node.text if cu_node is not None else None
            translations = defaultdict(list)
            for quote in sense_node.findall('.//tei:quote', NS):
                lang = quote.get(f'{XML_NS}lang')
                if lang and quote.text: translations[lang].append(quote.text)
            if translations: index_senses.append({"id": sense_id, "translations": dict(translations)})
            bibl_text = sense_node.findtext('.//tei:bibl', namespaces=NS)
            sense_detail = {"id": sense_id, "bibliography": bibl_text}
            if cu_id: sense_detail["cu_ID"] = cu_id
            details_senses.append(sense_detail)

        detail_data = {
            "id": entry_id, "forms": details_forms, "grammar": grammar,
            "senses": details_senses, "examples": examples_data.get(entry_id, []),
            "collocations": corpus_data['collocations'].get(lemma_str, {}),
            "network": corpus_data['networks'].get(lemma_str, {})
        }

        total_sense_count += len(index_senses)
        for example in detail_data["examples"]:
            normalized_coptic = normalize_example_sentence(example.get("coptic", ""))
            if normalized_coptic:
                unique_example_sentences.add(normalized_coptic)

        if lemma_freqs_by_dialect:
            detail_data["lemma_freqs"] = lemma_freqs_by_dialect
        if entry_type: detail_data["type"] = entry_type
        if cross_refs: detail_data["crossReferences"] = cross_refs
        if superentry_crossrefs.get(entry_id): detail_data["superEntryReferences"] = superentry_crossrefs[entry_id]
        if etym_data: detail_data["etym"] = etym_data

        with open(os.path.join(details_dir, f"{entry_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(detail_data, f, ensure_ascii=False, indent=2)

        # Calculate absolute lemma frequency across all available dialects for this entry
        total_lemma_freq = 0
        for d in corpus_data['freq_stats']:
            total_lemma_freq += corpus_data['freq_stats'][d]['lemma'].get(lemma_str, {}).get("count", 0)

        index_entry = {
            "id": entry_id,
            "lemma": lemma_str,
            "pos": scriptorium_pos,
            "tlapos": grammar.get("tlapos") or "",
            "subc": grammar.get("subc") or "",
            "form_ids": form_ids,
            "forms": index_forms,
            "senses": index_senses
        }

        if lemma_str in entity_mapping:
            if scriptorium_pos in ["N", "NPROP", "ART", "PDEM", "NUM", "PPOS"]:
                # Exceptions
                if entry_id in manual_entity_exceptions:
                    index_entry["entities"] = manual_entity_exceptions[entry_id]
                else:
                    index_entry["entities"] = entity_mapping[lemma_str]

        if total_lemma_freq:
            index_entry["lemma_freq"] = total_lemma_freq
        if etym_data: index_entry["etym"] = etym_data
        index_data.append(index_entry)

    with open(os.path.join(output_dir, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, separators=(',', ':'))

    stats_data = {
        "entries": len(index_data),
        "senses": total_sense_count,
        "uniqueExampleSentences": len(unique_example_sentences),
        "uniqueForms": len(unique_forms)
    }
    with open(os.path.join(output_dir, 'stats.json'), 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, ensure_ascii=False, separators=(',', ':'))

    with open("data/covered_base_forms.tab", 'w', encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sorted(unique_forms)))
    print("Build complete!")


if __name__ == "__main__":
    if not os.path.exists("data/coptic_dict.xml"):
        # Copy from old xml/Comprehensive_Coptic_Lexicon-v1.2-2020.xml - may not contain hot fixes
        shutil.copyfile("xml/Comprehensive_Coptic_Lexicon-v1.2-2020.xml", "data/coptic_dict.xml")
        
    process_dictionary("data/coptic_dict.xml", output_dir="public", data_dir="data")