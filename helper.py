#!/usr/bin/python2
# -*- coding: utf-8 -*-

import io, os, re, platform, json, unicodedata
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
	elif calling_script.endswith("network.cgi"):
		title = "Term network"
		activate = "none"
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
	text = text.replace('-', '').replace(ur"\u0304","").replace(ur"\ufe26","").replace(ur"\ufe24","").replace(ur"\ufe25","")
	text = text.replace(ur'\u2013', '')
	text = text.replace(ur"\u2E17","")
	return text


def get_annis_query(coptic, oref, cs_pos=None):
	coptic = strip_hyphens(coptic).encode("utf8")
	oref = strip_hyphens(oref).encode("utf8")

	annis_base = "https://annis.copticscriptorium.org/annis/scriptorium#"
	corpus_list = "_c=YmVzYS5sZXR0ZXJzLHNoZW5vdXRlLmEyMixsaWZlLmpvaG4ua2FseWJpdGVzLGpvaGFubmVzLmNhbm9ucyxwc2V1ZG8uYXRoYW5hc2l1cy5kaXNjb3Vyc2VzLHNoZW5vdXRlLmFicmFoYW0scHNldWRvLmJhc2lsLHNoZW5vdXRlLmRpcnQsc2FoaWRpYy5vdCxkb3JtaXRpb24uam9obixsaWZlLnBoaWIscHNldWRvLmVwaHJlbSxsaWZlLm9ubm9waHJpdXMsYXBvcGh0aGVnbWF0YS5wYXRydW0sc2hlbm91dGUuc2Vla3MsbGlmZS5wYXVsLnRhbW1hLHBzZXVkby50aW1vdGh5LHBzZXVkby5jaHJ5c29zdG9tLG15c3Rlcmllcy5qb2huLHNhaGlkaWMucnV0aCxwc2V1ZG8udGhlb3BoaWx1cyxzYWhpZGljYS5tYXJrLGRvYy5wYXB5cmkscGFjaG9taXVzLmluc3RydWN0aW9ucyxzaGVub3V0ZS5lYWdlcm5lc3MsbGlmZS5hcGhvdSxzaGVub3V0ZS51bmtub3duNV8xLGxpZmUuY3lydXMscHJvY2x1cy5ob21pbGllcyxqb2huLmNvbnN0YW50aW5vcGxlLG1hZ2ljYWwucGFweXJpLHNoZW5vdXRlLnRob3NlLHNhaGlkaWNhLm50LHNhaGlkaWNhLjFjb3JpbnRoaWFucyxzaGVub3V0ZS5mb3gsbGlmZS5sb25naW51cy5sdWNpdXMsbGlmZS5waXNlbnRpdXMsbWFydHlyZG9tLnZpY3RvcixsaWZlLmV1c3RhdGhpdXMudGhlb3Bpc3RlLHBpc3Rpcy5zb3BoaWEscHNldWRvLmNlbGVzdGludXMscHNldWRvLmZsYXZpYW51cyxzaGVub3V0ZS5wcmluY2Usc2hlbm91dGUubmlnaHQ"
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


def get_annis_entity_query(coptic, entity_type):
	if " " in coptic:
		coptic = coptic.replace(" ","")
	coptic = strip_hyphens(coptic).encode("utf8")

	annis_base = "https://annis.copticscriptorium.org/annis/scriptorium#"
	corpus_list = "_c=Y29wdGljLnRyZWViYW5r"  # Currently just treebank
	segmentation = "_bt=bm9ybV9ncm91cA"  # norm segmentation
	q = 'entity="'+str(entity_type)+'" ->head lemma="' + coptic + '"'
	query = "_q=" + urlsafe_b64encode(q)

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

def link_greek(etym):

	m = re.search(r"cf\. Gr\.[^<>]+</span>([^<>]+)<i>",etym)
	if m is None:
		return etym
	else:
		greek = m.group(1).strip()
		greek= greek.decode("utf8")

	try:
		# Convert polytonic Greek to beta-code using perseids-tools/beta-code-py conversion table
		betamap = io.open("unicode_to_beta_code.tab", encoding="utf8").read().split("\n")
		UNICODE_TO_BETA_CODE_MAP  = dict((line.split("\t")[0],line.split("\t")[1]) for line in betamap)

		updated_map = {}
		updated_map.update(UNICODE_TO_BETA_CODE_MAP)

		chars = [c for c in greek]
		if not all([c in updated_map for c in chars]):
			return etym
		else:
			mapped = "".join((list(map(lambda x: updated_map.get(x, x), chars))))

			link = ' <a title="Look up in Perseus" href="http://www.perseus.tufts.edu/hopper/resolveform?type=exact&lookup='+mapped+'&lang=greek">'+greek + '&nbsp;<img src="img/perseus.png" style="border: 1px solid black;"/></a> '
			linked = re.sub(r'(cf\. Gr\.[^<>]*</span>)[^<>]+(<i>)',r'\1'+link+r'\2',etym)

			return linked.encode("utf8")
	except:
		# Beta code conversion failed, return unaltered string
		return etym


