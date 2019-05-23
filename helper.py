#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, platform
import __main__
import unicodedata
from base64 import urlsafe_b64encode
import sqlite3 as lite

def make_active(html_input,button_id):
	return re.sub(r'(id="'+button_id+'")',r'class="active" \\1',html_input)

def wrap(html_input):
	wrapper = open(os.path.dirname(__file__) + os.sep + "templates" + os.sep + "wrapper.html",'r').read()
	calling_script = __main__.__file__
	bug_report = ""
	bug_string = """<div id="bug_report">
				Found a bug or a problem? Please report it at: <a href="https://github.com/KELLIA/dictionary/issues">https://github.com/KELLIA/dictionary/issues</a>
				</div>"""
	if calling_script.endswith("results.cgi"):
		title = "Search results"
		activate = "none"
		bug_report += bug_string
	elif calling_script.endswith("entry.cgi"):
		title = "Entry detail"
		activate = "none"
		bug_report += bug_string
	elif calling_script.endswith("search.cgi"):
		title = "Search"
		activate = "home"
	elif calling_script.endswith("about.cgi"):
		title = "About"
		activate = "about"
	elif calling_script.endswith("help.cgi"):
		title = "How to search"
		activate = "help"
	else:
		title = calling_script
		activate = "home"

	wrapped = wrapper.replace("**pagecontent**",html_input+bug_report)

	titled = wrapped.replace("**pagetitle**",title)

	activated = make_active(titled, activate)

	return activated


def separate_coptic(search_text):
	#coptic = search_text.split(" ")[0]
	#english = search_text.split(" ")[1]
	#return ([coptic],[english])
	words = search_text.split(" ")
	coptic_words = []
	non_coptic_words = []
	for word in words:
		coptic = ("COPTIC" in unicodedata.name(chr) for chr in unicode(word.decode("utf8")))
		if any(coptic):
			coptic_words.append(word)
		else:
			non_coptic_words.append(word)

	return (coptic_words, non_coptic_words)


def strip_hyphens(text):
	text = text.replace('-', '')
	text = text.replace(ur'\u2013', '')
	text = text.replace(ur"\u2E17","")
	return text


def get_annis_query(coptic, oref, cs_pos=None):
	coptic = strip_hyphens(coptic).encode("utf8")
	oref = strip_hyphens(oref).encode("utf8")

	annis_base = "https://corpling.uis.georgetown.edu/annis/scriptorium#"
	corpus_list = "_c=YmVzYS5sZXR0ZXJzLHNoZW5vdXRlLmEyMixqb2hhbm5lcy5jYW5vbnMsc2hlbm91dGUuZWFnZXJuZXNzLHNoZW5vdXRlLmRpcnQsc2FoaWRpYy5vdCxhcG9waHRoZWdtYXRhLnBhdHJ1bSxzYWhpZGljYS5udCxzYWhpZGljYS4xY29yaW50aGlhbnMscHNldWRvLnRoZW9waGlsdXMsc2hlbm91dGUuZm94LHNhaGlkaWNhLm1hcmssZG9jLnBhcHlyaSxtYXJ0eXJkb20udmljdG9yLHNoZW5vdXRlLmFicmFoYW0"  # List of scriptorium corpora
	segmentation = "_bt=bm9ybV9ncm91cA"  # Norm segmentation
	if " " in coptic:
		coptic = coptic.replace(" ","")
		query = "_q=" + urlsafe_b64encode('norm_group=/.*' + coptic + '.*/')
	elif " " in oref:
		oref_parts = oref.split(" ")
		morph_list =[]
		norm_list = []
		for part in oref_parts:
			morph_list.append('morph="'+part+'"')
			norm_list.append('norm="'+part+'"')
		query = " . ".join(morph_list) + " | "
		query += " . ".join(norm_list)
		query = "_q=" + urlsafe_b64encode(query)

	elif cs_pos in ["VSTAT","VIMP"]: # This is an inflected entry, look for norm and pos
		query = "_q=" + urlsafe_b64encode('norm="'+ coptic + '" _=_ pos="'+str(cs_pos)+'"')
	else:
		query = "_q=" + urlsafe_b64encode('lemma="'+ coptic + '"')

	return annis_base + "&".join([query,corpus_list,segmentation])


def lemma_exists(word):
	lemma_count = len(generic_query("select lemmas.Word from lemmas where lemmas.Word = ? and not lemmas.lemma = lemmas.word;",(word.decode("utf8"),)))>0
	if lemma_count > 0:
		lemma = get_lemmas_for_word(word)[0][0]
		regex_word = '.*\n' + lemma + '~.*'
		regex_word = regex_word
		found = generic_query("SELECT * FROM entries WHERE entries.name REGEXP ? ORDER BY ascii", (regex_word,))
		if len(found) > 0:
			return True
	return False


def get_lemmas_for_word(word):
	return generic_query("select Lemma, POS from lemmas where Word = ?;",(word.decode("utf8"),))


def generic_query(sql,params):

	if platform.system() == 'Linux':
		con = lite.connect('alpha_kyima_rc1.db')
	elif platform.system() == "Windows":
		con = lite.connect('coptic-dictionary' + os.sep + 'alpha_kyima_rc1.db')
	else:
		con = lite.connect('alpha_kyima_rc1.db')

	with con:
		con.create_function("REGEXP", 2, lambda expr, item: re.search(expr.lower(), item.lower()) is not None)
		cur = con.cursor()
		cur.execute(sql,params)
		return cur.fetchall()


def only_coptic(text):
	text = re.sub(r'[^ⲁⲃⲅⲇⲉⲍⲏⲑⲓⲕⲗⲙⲛⲥⲟⲝⲡⲣⲥⲧⲫⲭⲩⲱϭϫϩϥϯ]','',text)
	return text
