#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3 as lite
import xml.etree.ElementTree as ET
import re, sys
import glob
import os, io
from collections import OrderedDict, defaultdict
from argparse import ArgumentParser
import logging

utils_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep
entity_types = defaultdict(set)


def check_chars(word):
	"""
	was used to check for inconsistencies/unexpected characters in the xml; not currently called anywhere
	"""
	mapping = {u'ⲁ': 'A', u'ⲃ': 'B', u'ⲅ': 'C', u'ⲇ': 'D', u'ⲉ': 'E', u'ⲍ': 'F', u'ⲏ': 'G', u'ⲑ': 'H', u'ⲓ': 'I', u'Ⲓ': 'I',
				   u'ⲕ': 'J', u'ⲹ': 'J', u'ⲗ': 'K', u'ⲙ': 'L', u'ⲛ': 'M', u'ⲝ': 'N', u'ⲟ': 'O', u'ⲡ': 'P', u'ⲣ': 'Q', u'ⲥ': 'R',
				   u'ⲧ': 'S', u'ⲩ': 'T', u'ⲫ': 'U', u'ⲭ': 'V', u'ⲯ': 'W', u'ⲱ': 'X', u'ϣ': 'Y', u'ϥ': 'Z', u'ⳉ': 'a',
				   u'ϧ': 'b', u'ϩ': 'c', u'ϫ': 'd', u'ϭ': 'e', u'ϯ': 'SI'}
	expected_chars = u'()[]?,.*/ -–	 ︤̅ˉ̣︦̄̈ ⸗= o'
	for char in word:
		if char not in mapping and char not in expected_chars:
			print(word + "\t" + char)


def order_forms(formlist):
	temp = []
	for form in formlist:
		orths = form.findall('{http://www.tei-c.org/ns/1.0}orth')
		text = ""
		dialect = ""
		for orth in orths:
			text = orth.text.replace("⸗","--")  # Sort angle dash after hyphen
			geo = form.find('{http://www.tei-c.org/ns/1.0}usg')
			if geo is not None:
				dialect = geo.text.replace("Ak","K")
				if dialect != "S":
					dialect = "_" + dialect  # Sahidic always first

		temp.append((text,dialect,form))

	output = []
	for t, d, f in sorted(temp, key=lambda x: (x[0],x[1])):
		output.append(f)

	return output


def get(attr,line):
	return re.search(' ' + attr + r'="([^"]*)"',line).group(1)


def get_entity_types(pub_corpora_dir):
	if not pub_corpora_dir.endswith(os.sep):
		pub_corpora_dir += os.sep
	tt_files = glob.glob(pub_corpora_dir + "**" + os.sep + "*.tt", recursive=True)
	entity_types = defaultdict(set)
	for file_ in tt_files:
		sgml = io.open(file_, encoding="utf8").read()
		if ' entities="gold"' not in sgml:
			continue  # Only use gold entities
		lines = sgml.split("\n")
		# Pass 1 - get head lemmas
		id2lemma = {}
		for line in lines:
			if 'norm' in line and 'xml:id' in line:
				xml_id = get('xml:id',line)
				lemma = get('lemma', line)
				id2lemma[xml_id] = lemma
		# Pass 2 - get entity types for each lemma
		for line in lines:
			if ' entity="' in line:
				ent_type = get('entity',line)
				head_id = get('head_tok',line).replace("#","")
				lemma = id2lemma[head_id]
				entity_types[lemma].add(ent_type)
	return entity_types


def process_entry(id, super_id, entry,entry_xml_id, entity_types):
	"""
	:param id: int, id of the entry
	:param super_id: int, id of the superentry
	:param entry: Element representing the entry
	:return: tuple representing new row to add to the db
	"""
	#global entity_types
	if "status" in entry.attrib:
		if entry.attrib["status"] == "deprecated":
			return None  # Entire entry is deprecated, used by DDGLC entries
	if "change" in entry.attrib:
		if "deprecated" in entry.attrib["change"]:
			return None  # Same for @change notation

	forms = entry.findall('{http://www.tei-c.org/ns/1.0}form')

	# ORTHSTRING -- "name" column in the db
	# Includes morphological info, followed by orthographic forms and corresponding dialect (geo) info
	# ||| separates forms
	# \n separates orth-geo pairs
	# ~ separates orth from geo

	# SEARCHSTRING -- "search" column in db
	# similar to orthstring but forms are stripped of anything but coptic letters and spaces
	# morphological info not included
	orthstring = ""
	oref_string = ""
	oref_text = ''
	search_string = "\n"

	lemma = None
	for form in forms:
		is_lemma = False
		if "status" in form.attrib:
			if form.attrib["status"] == "deprecated":
				continue
		if "change" in form.attrib:
			if "deprecated" in form.attrib["change"]:
				continue
		if "type" in form.attrib:
			if form.attrib["type"] == "lemma":
				is_lemma = True
		orths = form.findall('{http://www.tei-c.org/ns/1.0}orth')
		if form.text is not None:
			if re.search(r'[^\s]', form.text) is not None:
				orths.append(form)
		if len(orths)>0:
			first_orth = orths[0]
			if is_lemma:
				lemma = first_orth
	if lemma is None:
		logging.error("No lemma type for entry of " + orths[0].text)

	first = []
	last = []
	for form in forms:
		if "status" in form.attrib:
			if form.attrib["status"] == "deprecated":
				continue
		if "change" in form.attrib:
			if "deprecated" in form.attrib["change"]:
				continue
		orths = form.findall('{http://www.tei-c.org/ns/1.0}orth')
		if form.text is not None:
			if re.search(r'[^\s]', form.text) is not None:
				orths.append(form)
		if type(lemma).__name__ == "Element":
			if any([orth.text == lemma.text for orth in orths]):
				first.append(form)
			else:
				last.append(form)
		else:
			if any([orth.text == lemma for orth in orths]):
				first.append(form)
			else:
				last.append(form)

	first = order_forms(first)
	last = order_forms(last)
	ordered_forms = first + last

	for form in ordered_forms:
		if "type" in form.attrib:
			if form.attrib["type"] == "lemma":
				continue
		orths = form.findall('{http://www.tei-c.org/ns/1.0}orth')
		if form.text is not None:
			if re.search(r'[^\s]', form.text) is not None:
				orths.append(form)

		orefs = form.findall('{http://www.tei-c.org/ns/1.0}oRef')

		gramGrp = form.find('{http://www.tei-c.org/ns/1.0}gramGrp')
		gram_string = ""
		if gramGrp is None:
			gramGrp = entry.find('{http://www.tei-c.org/ns/1.0}gramGrp')

		if gramGrp is not None:
			for child in gramGrp:
				gram_string += re.sub(r'\s+',' ',child.text).strip() + " "
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

		form_id = form.attrib['{http://www.w3.org/XML/1998/namespace}id'] if '{http://www.w3.org/XML/1998/namespace}id' in form.attrib else ""
		geos_with_ids = []
		for geo in geos:
			geos_with_ids.append(geo + "^^" + form_id)
		geos = geos_with_ids

		for orth in orths:
			remove_whitespace = re.search(r'[^\s].*[^\s]', orth.text)

			if remove_whitespace is not None:
				orth_text = remove_whitespace.group(0)
				#check_chars(orth_text)

			else:
				orth_text = orth.text

			if len(orefs) > 0:
				oref_text = orefs[0].text

			else:
				oref_text = orth_text

			search_text = re.sub(u'[^ⲁⲃⲅⲇⲉⲍⲏⲑⲓⲕⲗⲙⲛⲝⲟⲡⲣⲥⲧⲩⲫⲭⲯⲱϣϥⳉϧϩϫϭϯ ]', u'', orth_text)
			oref_text = re.sub(u'[^ⲁⲃⲅⲇⲉⲍⲏⲑⲓⲕⲗⲙⲛⲝⲟⲡⲣⲥⲧⲩⲫⲭⲯⲱϣϥⳉϧϩϫϭϯ ]', u'', oref_text)

			for geo in geos:
				orthstring += orth_text + "~" + geo + "\n"
				search_string += search_text + "~" + geo + "\n"
			if len(list(geos)) == 0:
				orthstring += orth_text + "~S^^"+form_id+"\n"
				search_string += search_text + "~S\n"

		oref_string += oref_text
		oref_string += "|||"
		orthstring += "|||"
		#search_string += "|||"
	orthstring = re.sub(r'\|\|\|$', '', orthstring)
	oref_string = re.sub(r'\|\|\|$', '', oref_string)
	#search_string = re.sub(r'\|\|\|$', '', search_string)

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
		sense_id = sense.attrib['{http://www.w3.org/XML/1998/namespace}id'] if '{http://www.w3.org/XML/1998/namespace}id' in sense.attrib else ""
		sense_start_string = str(sense_n) + "@"+sense_id+"|"
		de += sense_start_string
		en += sense_start_string
		fr += sense_start_string
		for sense_child in sense:
			if sense_child.tag == '{http://www.tei-c.org/ns/1.0}cit':
				bibl = sense_child.find('{http://www.tei-c.org/ns/1.0}bibl')
				no_bibl = True
				if bibl is not None:
					if bibl.text is not None:
						no_bibl = False
						bibl_text = bibl.text + " "
				quotes = sense_child.findall('{http://www.tei-c.org/ns/1.0}quote')
				definitions = sense_child.findall('{http://www.tei-c.org/ns/1.0}def')

				quote_text = "~~~"
				for quote in quotes:
					if quote is not None and quote.text is not None:
						quote_text += re.sub(r' +',' ',quote.text.strip().replace("\n",''))
						if definitions is None or len(definitions) == 0:
							quote_text += ";;;"
						else:
							quote_text += "; "
						lang = quote.get('{http://www.w3.org/XML/1998/namespace}lang')
						if lang == 'de':
							de += quote_text
						elif lang == 'en':
							en += quote_text
						elif lang == 'fr':
							fr += quote_text
						quote_text = "~~~"
				for definition in definitions:
					if definition is not None:
						if definition.text is not None:
							definition_text = re.sub(r' +',' ',definition.text.strip().replace("\n",'')) + ";;;"
							lang = definition.get('{http://www.w3.org/XML/1998/namespace}lang')
							if lang == 'de':
								if de.endswith("|"):
									de += "~~~"
								de += definition_text
							elif lang == 'en':
								if en.endswith("|"):
									en += "~~~"
								en += definition_text
							elif lang == 'fr':
								if fr.endswith("|"):
									fr += "~~~"
								fr += definition_text
				if not no_bibl:
					de += bibl_text
					en += bibl_text
					fr += bibl_text
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
	de = re.sub(r'\s+', r' ', de).strip()
	en = re.sub(r'\s+', r' ', en).strip()
	fr = re.sub(r'\s+', r' ', fr).strip()

	# POS -- a single Scriptorium POS tag for each entry
	if oref_string == u"ⲟⲩⲛ":
		d=3
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
	if len(list(pos_list)) > 1:
		pos_list = filter(lambda p: p not in ['NULL', 'NONE', '?'], pos_list)
		pos_list = list(pos_list)
	if len(pos_list) == 0:
		pos_list.append('NULL')
	pos_string = pos_list[0] # on the rare occasion pos_list has len > 1 at this point, the first one is the most valid

	#ETYM
	etym_string = ""
	etym = entry.find("{http://www.tei-c.org/ns/1.0}etym")
	greek_id = ""
	if etym is not None:
		greek_dict = OrderedDict()
		for child in etym:
			if child.tag == "{http://www.tei-c.org/ns/1.0}note":
				etym_string += re.sub(r'\s+',' ',child.text).strip()
			elif child.tag == "{http://www.tei-c.org/ns/1.0}ref":
				if 'type' in child.attrib and 'target' in child.attrib:
					etym_string += child.attrib['type'] + ": " + child.attrib['target'] + " "
				elif 'targetLang' in child.attrib:
					etym_string += child.attrib['targetLang'] + ": " + child.text + " "
				elif 'type' in child.attrib:
					if "greek" in child.attrib["type"]:
						greek_dict[child.attrib["type"]] = child.text
			elif child.tag == "{http://www.tei-c.org/ns/1.0}xr":
				for ref in child:
					etym_string += child.attrib['type'] + ". " + ref.attrib['target'] + "# " + ref.text + " "
		if len(greek_dict) > 0:
			greek_parts = []
			greek_id = ""
			for key in sorted(list(greek_dict.keys())):
				if greek_dict[key] is None:
					#import sys
					#sys.stderr.write(str(greek_dict))
					# Incomplete Greek entry
					greek_parts = []
					break
				val = greek_dict[key].strip()
				if "grl_ID" in key:
					greek_id = val
				if "grl_lemma" in key:
					part = '<span style="color:darkred">cf. Gr.'
					if greek_id != "":
						part += " (DDGLC lemma ID "+greek_id+")"
					part += '</span> ' + val
					greek_parts.append(part)
				elif "meaning" in key:
					greek_parts.append("<i>"+val+"</i>.")
				elif "_pos" in key and len(val) > 0:
					greek_parts.append('<span style="color:grey">'+ val+ '</span>')
				elif "grl_ref" in key:
					if "LSJ" in val:
						m = re.search(r'LSJ ([0-9]+)',val)
						if m is not None:
							lsj_pg_num = m.group(1)
							#url = "http://stephanus.tlg.uci.edu/lsj/#page=**page**&context=lsj".replace("**page**",lsj_pg_num)
							#val = '<a href="'+url+'">' + val + "</a>"
					greek_parts.append('<span style="color:grey">('+ val+ ')</span>')
			etym_string += " ".join(greek_parts)

	xrs = entry.findall("{http://www.tei-c.org/ns/1.0}xr")
	for xr in xrs:
		for ref in xr:
			ref_target = re.sub(u'[^ⲁⲃⲅⲇⲉⲍⲏⲑⲓⲕⲗⲙⲛⲝⲟⲡⲣⲥⲧⲩⲫⲭⲯⲱϣϥⳉϧϩϫϭϯ ]', u'', ref.attrib['target']).strip()
			etym_string += xr.attrib['type'] + ". " + "#" + ref_target + "# " + ref.text + " "

	ents = ""
	if "~" in search_string:
		row_lemma = search_string.strip().split("~")[0]
		if row_lemma == "ⲉⲓⲱⲧ":  # Hardwired behavior for barley vs. father
			if entry_xml_id == "C998":
				ents = "plant"
			else:
				ents = "person"
		elif row_lemma in entity_types and pos_string in ["ART","PDEM","PPOS","N","NUM","PINT"]:
			ents = ";".join(sorted(list(entity_types[row_lemma])))

	row = (id, super_id, orthstring, pos_string, de, en, fr, etym_string, ascii_orth, search_string, oref_string, greek_id, ents)
	return row


def process_super_entry(entry_id, super_id, super_entry, entity_types):
	row_list = []
	for entry in super_entry:
		entry_xml_id = entry.attrib['{http://www.w3.org/XML/1998/namespace}id'] if '{http://www.w3.org/XML/1998/namespace}id' in entry.attrib else ""

		# Get lemma form ID
		forms = [f for f in entry.findall('{http://www.tei-c.org/ns/1.0}form') if "type" in f.attrib]
		lemma = [f for f in forms if f.attrib["type"] == "lemma"]
		if len(lemma) > 0:
			lemma_form_id = lemma[0].attrib["{http://www.w3.org/XML/1998/namespace}id"]
		else:
			lemma_form_id = ""

		row = process_entry(entry_id, super_id, entry,entry_xml_id, entity_types)
		if row is None:
			continue
		row_list.append(tuple(list(row)+[entry_xml_id, lemma_form_id]))
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
	if pos == u"Subst." or pos == u"Adj." or pos == u"Nominalpräfix" or pos == u"Adjektivpräfix" \
			or pos == u"Kompositum":
		return 'N'
	elif u"Ausdruck der Nichtexistenz" in subc or u"Ausdruck des Nicht-Habens" in subc:
		return 'EXIST'
	elif pos == u"Adv.":
		return 'ADV'
	elif pos == u"Vb." or pos == u"unpersönlicher Ausdruck":
		if subc == u"Qualitativ":
			return 'VSTAT'
		elif subc == u"Suffixkonjugation":
			return 'VBD'
		elif subc == u"Imperativ":
			return 'VIMP'
		elif u"ⲟⲩⲛ-" in orthstring or u"ⲟⲩⲛⲧⲉ-" in orthstring:
			return "EXIST"
		else:
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
			return 'VSTAT'
	elif u"ϭⲁⲛⲛⲁⲥ" in orthstring:
		return "NULL"

	return "?"

def dictionary_xml_to_database(xml_path, pub_corpora=None):

	# Gather entity data
	if pub_corpora is None:
		pub_corpora = "pub_corpora"
	if pub_corpora is not None:
		entity_types = get_entity_types(pub_corpora)

	con = lite.connect(utils_dir + 'alpha_kyima_rc1.db')

	with con:
		cur = con.cursor()

		cur.execute("DROP TABLE IF EXISTS entries")
		cur.execute("CREATE TABLE entries(Id INT, Super_Ref INT, Name TEXT, POS TEXT, De TEXT, En TEXT, Fr TEXT, " +
					"Etym TEXT, Ascii TEXT, Search TEXT, oRef TEXT, grkId TEXT, entities TEXT, xml_id TEXT UNIQUE, lemma_form_id TEXT)")

		super_id = 1
		entry_id = 1

		for letter_filename in glob.glob(xml_path + '*.xml'):
			sys.stderr.write("o Reading " + letter_filename + "\n")
			tree = ET.parse(letter_filename)
			root = tree.getroot()
			try:
				body = root.find('{http://www.tei-c.org/ns/1.0}text').find('{http://www.tei-c.org/ns/1.0}body')
			except:
				sys.stderr.write("! ERR: Can't find root>text>body in" +letter_filename + "\n")
				sys.exit()

			for child in body:
				if child.tag == "{http://www.tei-c.org/ns/1.0}entry":
					entry_xml_id = child.attrib['{http://www.w3.org/XML/1998/namespace}id'] if '{http://www.w3.org/XML/1998/namespace}id' in child.attrib else ""

					# Get lemma form ID
					forms = [f for f in child.findall('{http://www.tei-c.org/ns/1.0}form') if "type" in f.attrib]
					lemma = [f for f in forms if f.attrib["type"]=="lemma"]
					if len(lemma)>0:
						lemma_form_id = lemma[0].attrib["{http://www.w3.org/XML/1998/namespace}id"]
					else:
						lemma_form_id = ""

					row = process_entry(entry_id, super_id, child, entry_xml_id, entity_types)
					if row is None:
						continue
					row = tuple(list(row) + [entry_xml_id, lemma_form_id])
					cur.execute("INSERT INTO entries VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
					super_id += 1
					entry_id += 1
				elif child.tag == "{http://www.tei-c.org/ns/1.0}superEntry":
					rows = process_super_entry(entry_id, super_id, child, entity_types)
					cur.executemany("INSERT INTO entries VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
					super_id += 1
					entry_id += len(rows)

		# Handle network graphs
		cur.execute("DROP TABLE IF EXISTS networks")
		cur.execute("CREATE TABLE networks(pos TEXT, word TEXT, phrase TEXT, freq INTEGER)")

		data = io.open(utils_dir + "phrase_freqs.tab", encoding="utf8").read().strip().split("\n")
		data = [row.split("\t") for row in data]
		data = [row[:-1] + [int(row[-1])] for row in data]
		cur.executemany("INSERT INTO networks VALUES(?, ?, ?, ?)", data)

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument("xml_directory", help="directory with dictionary XML files")
	parser.add_argument("--pub_corpora", default=None, help="directory with dictionary Coptic Scriptorium Corpora repo")
	options = parser.parse_args()

	xml_path = options.xml_directory

	if not xml_path.endswith(os.sep):
		xml_path += os.sep

	dictionary_xml_to_database(xml_path, options.pub_corpora)

