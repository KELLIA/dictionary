#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3 as lite
import xml.etree.ElementTree as ET
import re
import glob


def check_chars(word):
    """
    was used to check for inconsistencies/unexpected characters in the xml; not currently called anywhere
    """
    mapping = {u'ⲁ': 'A', u'ⲃ': 'B', u'ⲅ': 'C', u'ⲇ': 'D', u'ⲉ': 'E', u'ⲍ': 'F', u'ⲏ': 'G', u'ⲑ': 'H', u'ⲓ': 'I', u'Ⲓ': 'I',
                   u'ⲕ': 'J', u'ⲹ': 'J', u'ⲗ': 'K', u'ⲙ': 'L', u'ⲛ': 'M', u'ⲝ': 'N', u'ⲟ': 'O', u'ⲡ': 'P', u'ⲣ': 'Q', u'ⲥ': 'R',
                   u'ⲧ': 'S', u'ⲩ': 'T', u'ⲫ': 'U', u'ⲭ': 'V', u'ⲯ': 'W', u'ⲱ': 'X', u'ϣ': 'Y', u'ϥ': 'Z', u'ⳉ': 'a',
                   u'ϧ': 'b', u'ϩ': 'c', u'ϫ': 'd', u'ϭ': 'e', u'ϯ': 'SI'}
    expected_chars = u'()[]?,.*/ -– 	︤̅ˉ̣︦̄̈ ⸗= o'
    for char in word:
        if char not in mapping and char not in expected_chars:
            print word + "\t" + char


def process_entry(id, super_id, entry):
    """
    :param id: int, id of the entry
    :param super_id: int, id of the superentry
    :param entry: Element representing the entry
    :return: tuple representing new row to add to the db
    """
    forms = entry.findall('{http://www.tei-c.org/ns/1.0}form')

    # ORTHSTRING -- "name" column in the db
    # Includes morphological info, followed by orthographic forms and corresponding dialect (geo) info
    # ||| separates forms
    # \n separates orth-geo pairs
    # ~ separates orth from geo
    orthstring = ""
    for form in forms:
        orths = form.findall('{http://www.tei-c.org/ns/1.0}orth')
        if form.text is not None:
            if re.search(r'[^\s]', form.text) is not None:
                orths.append(form)

        gramGrp = form.find('{http://www.tei-c.org/ns/1.0}gramGrp')
        gram_string = ""
        if gramGrp is None:
            gramGrp = entry.find('{http://www.tei-c.org/ns/1.0}gramGrp')

        if gramGrp is not None:
            for child in gramGrp:
                gram_string += child.text + " "
            gram_string = gram_string[:-1]

        orthstring += gram_string + "\n"

        all_geos = form.find('{http://www.tei-c.org/ns/1.0}usg')
        if all_geos is not None:
            if all_geos.text is not None:
                geos = re.sub(r'[\(\)]', r'', all_geos.text)
                geos = re.sub(r'Ak', r'K', geos).split(' ')
                geos = filter(lambda g: len(g) == 1, geos)
            else: geos = []
        else:
            geos = []
        for orth in orths:
            remove_whitespace = re.search(r'[^\s].*[^\s]', orth.text)

            if remove_whitespace is not None:
                orth_text = remove_whitespace.group(0)
                #check_chars(orth_text)

            else:
                orth_text = orth.text
            for geo in geos:
                orthstring += orth_text + "~" + geo + "\n"
            if len(geos) == 0:
                orthstring += orth_text + "~\n"

        orthstring += "|||"
    orthstring = re.sub(r'\|\|\|$', '', orthstring)

    first_orth_re = re.search(r'\n(.*?)~', orthstring)
    if first_orth_re is not None:
        first_orth = first_orth_re.group(1)
        ascii_orth = ''
        mapping = {u'ⲁ': 'A', u'ⲃ': 'B', u'ⲅ': 'C', u'ⲇ': 'D', u'ⲉ': 'E', u'ⲍ': 'F', u'ⲏ': 'G', u'ⲑ': 'H', u'ⲓ': 'I',
                   u'ⲕ': 'J', u'ⲗ': 'K', u'ⲙ': 'L', u'ⲛ': 'M', u'ⲝ': 'N', u'ⲟ': 'O', u'ⲡ': 'P', u'ⲣ': 'Q', u'ⲥ': 'R',
                   u'ⲧ': 'S', u'ⲩ': 'T', u'ⲫ': 'U', u'ⲭ': 'V', u'ⲯ': 'W', u'ⲱ': 'X', u'ϣ': 'Y', u'ϥ': 'Z', u'ⳉ': 'a',
                   u'ϧ': 'b', u'ϩ': 'c', u'ϫ': 'd', u'ϭ': 'e', u'ϯ': 'SI', u' ': ' '}
        for char in first_orth:
            if char in mapping:
                ascii_orth += mapping[char]
    else:
        ascii_orth = ''



    # SENSES -- 3 different columns for the 3 languages: de, en, fr
    # each string contains definitions as well as corresponding bibl/ref/xr info
    # definition part, which may come from 'quote' or 'def' in the xml or both, is preceded by ~~~ and followed by ;;;
    # different senses separated by |||
    de = ""
    en = ""
    fr = ""
    senses = entry.findall('{http://www.tei-c.org/ns/1.0}sense')
    sense_n = 1
    for sense in senses:
        sense_start_string = str(sense_n) + "|"
        de += sense_start_string
        en += sense_start_string
        fr += sense_start_string
        for sense_child in sense:
            if sense_child.tag == '{http://www.tei-c.org/ns/1.0}cit':
                bibl = sense_child.find('{http://www.tei-c.org/ns/1.0}bibl')
                if bibl is not None:
                    bibl_text = bibl.text + " "
                    de += bibl_text
                    en += bibl_text
                    fr += bibl_text

                else:
                    lang = sense_child.get('{http://www.w3.org/XML/1998/namespace}lang')
                    quote = sense_child.find('{http://www.tei-c.org/ns/1.0}quote')
                    definition = sense_child.find('{http://www.tei-c.org/ns/1.0}def')

                    quote_text = "~~~"
                    if quote is not None and quote.text is not None:
                        quote_text += quote.text
                        if definition is None:
                            quote_text += ";;;"
                        else:
                            quote_text += "; "
                    if lang == 'de':
                        de += quote_text
                    elif lang == 'en':
                        en += quote_text
                    elif lang == 'fr':
                        fr += quote_text
                    if definition is not None:
                        definition_text = definition.text + ";;;"
                        if lang == 'de':
                            de += definition_text
                        elif lang == 'en':
                            en += definition_text
                        elif lang == 'fr':
                            fr += definition_text
            elif sense_child.tag == '{http://www.tei-c.org/ns/1.0}ref':
                ref = "ref: " + sense_child.text + " "
                de += ref
                en += ref
                fr += ref
            elif sense_child.tag == '{http://www.tei-c.org/ns/1.0}xr':
                for ref in sense_child:
                    ref = sense_child.tag[29:] + ". " + ref.attrib['target'] + "# " + ref.text + " "
                    de += ref
                    en += ref
                    fr += ref

        de += "|||"
        en += "|||"
        fr += "|||"
        sense_n += 1

    de = re.sub(r'\|\|\|$', r'', de)
    en = re.sub(r'\|\|\|$', r'', en)
    fr = re.sub(r'\|\|\|$', r'', fr)

    # POS -- a single Scriptorium POS tag for each entry
    pos_list = []
    for gramgrp in entry.iter("{http://www.tei-c.org/ns/1.0}gramGrp"):
        pos = gramgrp.find("{http://www.tei-c.org/ns/1.0}pos")
        if pos is not None:
            pos_text = pos.text
        else:
            pos_text = "None"
        subc = gramgrp.find("{http://www.tei-c.org/ns/1.0}subc")
        if subc is not None:
            subc_text = subc.text
        else:
            subc_text = "None"
        new_pos = pos_map(pos_text, subc_text, orthstring)
        if new_pos not in pos_list:
            pos_list.append(new_pos)
    if len(pos_list) > 1:
        pos_list = filter(lambda p: p not in ['NULL', 'NONE', '?'], pos_list)
    if len(pos_list) == 0:
        pos_list.append('NULL')
    pos_string = pos_list[0] # on the rare occasion pos_list has len > 1 at this point, the first one is the most valid

    #ETYM
    etym_string = ""
    etym = entry.find("{http://www.tei-c.org/ns/1.0}etym")
    if etym is not None:
        for child in etym:
            if child.tag == "{http://www.tei-c.org/ns/1.0}note":
                etym_string += child.text
            elif child.tag == "{http://www.tei-c.org/ns/1.0}ref":
                if 'type' in child.attrib and 'target' in child.attrib:
                    etym_string += child.attrib['type'] + ": " + child.attrib['target'] + " "
                elif 'targetLang' in child.attrib:
                    etym_string += child.attrib['targetLang'] + ": " + child.text + " "
            elif child.tag == "{http://www.tei-c.org/ns/1.0}xr":
                for ref in child:
                    etym_string += child.attrib['type'] + ". " + ref.attrib['target'] + "# " + ref.text + " "

    xrs = entry.findall("{http://www.tei-c.org/ns/1.0}xr")
    for xr in xrs:
        for ref in xr:
            etym_string += xr.attrib['type'] + ". " + ref.attrib['target'] + "# " + ref.text + " "



    row = (id, super_id, orthstring, pos_string, de, en, fr, etym_string, ascii_orth)
    return row


def process_super_entry(entry_id, super_id, super_entry):
    row_list = []
    for entry in super_entry:
        row_list.append(process_entry(entry_id, super_id, entry))
        entry_id += 1

    entry_rows = tuple(row_list)

    return entry_rows


def pos_map(pos, subc, orthstring):
    """
    :param pos: string
    :param subc: string
    :return: string
    """
    pos = pos.replace('?', '')
    if pos == u"Subst." or pos == u"Adj." or pos == u"Adv." or pos == u"Nominalpräfix" or pos == u"Adjektivpräfix" \
            or pos == u"Kompositum":
        return 'N'
    elif pos == u"Vb." or pos == u"unpersönlicher Ausdruck":
        return 'V'
    elif pos == u"Präp.":
        return 'PREP'
    elif pos == u"Zahlzeichen" or pos == u"Zahlwort" or pos == u"Präfix der Ordinalzahlen":
        return 'NUM'
    elif pos == u"Partikel" or pos == u"Interjektion" or pos == u"Partikel, enklitisch":
        return 'PTC'
    elif pos == u"Selbst. Pers. Pron." or pos == u"Suffixpronomen" or pos == u"Präfixpronomen (Präsens I)":
        return 'PPER'
    elif pos == u"Konj.":
        return 'CONJ'
    elif pos == u"Dem. Pron.":
        return "PDEM"
    elif pos == u"bestimmter Artikel" or pos == u"unbestimmter Artikel":
        return 'ART'
    elif pos == u"Possessivartikel" or pos == u"Possessivpräfix":
        return 'PPOS'
    elif pos == u"Poss. Pron.":
        return 'PPERO'
    elif pos == u"Interr. Pron.":
        return 'PINT'
    elif pos == u"Verbalpräfix":
        if subc == u"Imperativpräfix ⲁ-" or subc == u"Negierter Imperativ ⲙⲡⲣ-":
            return 'NEG'
        if subc == u"im negativen Bedingungssatz" or subc == u"Perfekt II ⲉⲛⲧⲁ-":
            return 'NONE'
        else:
            return 'A'
    elif pos == u"Pron.":
        if subc == "None":
            return 'PPER'
        elif subc == u"Indefinitpronomen" or subc == u"Fragepronomen":
            return 'PINT'
        elif subc == u"Reflexivpronomen":
            return 'PREP'
    elif pos == u"Satzkonverter":
        return 'C'
    elif pos == u"Präfix":
        if u"ⲧⲁ-" in orthstring:
            return "PPOS"
        elif u"ⲧⲃⲁⲓ-" in orthstring:
            return "N"
        elif u"ⲧⲣⲉ-" in orthstring:
            return "A"
    elif pos == u"None" or pos == u"?":
        if subc == u"None":
            return 'NULL'
        if subc == u"Qualitativ":
            return 'V'
    elif u"ϭⲁⲛⲛⲁⲥ" in orthstring:
        return "NULL"

    return "?"


con = lite.connect('alpha_kyima_rc1.db')

with con:
    cur = con.cursor()

    cur.execute("DROP TABLE IF EXISTS entries")
    cur.execute("CREATE TABLE entries(Id INT, Super_Ref INT, Name TEXT, POS TEXT, De TEXT, En TEXT, Fr TEXT, Etym TEXT, Ascii TEXT)")
    cur.execute("DROP TABLE IF EXISTS lemmas")
    cur.execute("CREATE TABLE lemmas(Id INT, Word TEXT, POS TEXT, Lemma TEXT)")

    super_id = 1
    entry_id = 1

    for letter_filename in glob.glob('*.xml'):
        tree = ET.parse(letter_filename)
        root = tree.getroot()
        body = root.find('{http://www.tei-c.org/ns/1.0}text').find('{http://www.tei-c.org/ns/1.0}body')

        for child in body:
            if child.tag == "{http://www.tei-c.org/ns/1.0}entry":
                row = process_entry(entry_id, super_id, child)
                cur.execute("INSERT INTO entries VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
                super_id += 1
                entry_id += 1
            elif child.tag == "{http://www.tei-c.org/ns/1.0}superEntry":
                rows = process_super_entry(entry_id, super_id, child)
                cur.executemany("INSERT INTO entries VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
                super_id += 1
                entry_id += len(rows)

