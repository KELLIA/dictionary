#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, platform
import __main__
import unicodedata
from base64 import b64encode
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
	

def get_annis_query(coptic):
	coptic = coptic.encode("utf8").replace("-","")

	annis_base = "https://corpling.uis.georgetown.edu/annis/scriptorium#"
	corpus_list = "_c=YXBvcGh0aGVnbWF0YS5wYXRydW0sYmVzYS5sZXR0ZXJzLGRvYy5wYXB5cmksc2FoaWRpY2EuMWNvcmludGhpYW5zLHNhaGlkaWNhLm1hcmssc2FoaWRpY2EubnQsc2hlbm91dGUuYTIyLHNoZW5vdXRlLmFicmFoYW0ub3VyLmZhdGhlcixzaGVub3V0ZS5lYWdlcm5lc3Msc2hlbm91dGUuZm94"  # List of scriptorium corpora
	segmentation = "_bt=bm9ybV9ncm91cA"  # Norm segmentation
	#query = "_q=bGVtbWE9IuKygSI"
	query = "_q=" + b64encode('lemma="'+ coptic + '"') 
	return annis_base + "&".join([query,corpus_list,segmentation])


def lemma_exists(word):
	lemma_count = len(generic_query("select lemmas.Word from lemmas where lemmas.Word = ? and not lemmas.lemma = lemmas.word;",(word.decode("utf8"),)))>0
	if lemma_count > 0:
		lemma = get_lemmas_for_word(word)[0][0]
		#lemma = lemma.decode("utf8")
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
	else:
		con = lite.connect('coptic-dictionary' + os.sep + 'alpha_kyima_rc1.db')

	with con:
		con.create_function("REGEXP", 2, lambda expr, item: re.search(expr.lower(), item.lower()) is not None)
		cur = con.cursor()
		cur.execute(sql,params)
		return cur.fetchall()


def only_coptic(text):
	text = re.sub(r'[^ⲁⲃⲅⲇⲉⲍⲏⲑⲓⲕⲗⲙⲛⲥⲟⲝⲡⲣⲥⲧⲫⲭⲩⲱϭϫϩϥϯ]','',text)
	return text
